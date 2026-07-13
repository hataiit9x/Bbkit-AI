#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

from browser_adapter import render_page, strip_html_text

try:
    import requests
except Exception:
    requests = None


URL_RE = re.compile(r"https?://[^\s'\"<>()]+", re.IGNORECASE)
DOMAIN_RE = re.compile(r"(?<![\w.-])(?:\*\.)?(?:[a-zA-Z][a-zA-Z0-9-]*\.)+[a-zA-Z]{2,}(?![\w.-])")
ADDRESS_RE = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
REPO_RE = re.compile(r"\b([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)\b")
# Program platform hosts (not in-scope customer assets)
PLATFORM_HOST_MARKERS: list[tuple[str, str]] = [
    # host substring → display name (first match wins; more specific first)
    ("hackerone.com", "HackerOne"),
    ("bugcrowd.com", "Bugcrowd"),
    ("intigriti.com", "Intigriti"),
    ("hackenproof.com", "HackenProof"),
    ("yeswehack.com", "YesWeHack"),
    ("immunefi.com", "Immunefi"),
    ("cantina.xyz", "Cantina"),
    ("code4rena.com", "Code4rena"),
    ("sherlock.xyz", "Sherlock"),
    ("codehawks.com", "CodeHawks"),
    ("hats.finance", "Hats Finance"),
    ("spearbit.com", "Spearbit"),
    ("synack.com", "Synack"),
    ("cobalt.io", "Cobalt"),
    ("yogosha.com", "Yogosha"),
    ("federacy.com", "Federacy"),
    ("bugbase.ai", "BugBase"),
    ("bugrap.io", "BugRap"),
    ("hacken.io", "Hacken"),
    ("hackenproof", "HackenProof"),
    ("safehats.com", "SafeHats"),
    ("hacktrophy.com", "HackTrophy"),
    ("bugbounty.jp", "Bugbounty.jp"),
    ("detectify.com", "Detectify"),
    ("integrity.pt", "Integrity"),
    ("hackerspace.gov.il", "Hackerspace"),
    ("security.googlebugbounty", "Google VRP"),
    ("bughunters.google.com", "Google VRP"),
    ("msrc.microsoft.com", "Microsoft MSRC"),
    ("bugbounty.microsoft.com", "Microsoft MSRC"),
    ("facebook.com/whitehat", "Meta"),
    ("bugbounty.apple.com", "Apple"),
]

IGNORE_HOSTS = {
    "github.com",
    "gitlab.com",
    "bitbucket.org",
    "docs.github.com",
    "x.com",
    "twitter.com",
    "discord.com",
    "discord.gg",
    "t.me",
    "telegram.me",
    "medium.com",
    "mirror.xyz",
    "notion.so",
    "www.notion.so",
    "nvd.nist.gov",
    "youtube.com",
    "www.youtube.com",
    # platforms (not customer assets)
    "hackerone.com",
    "bugcrowd.com",
    "intigriti.com",
    "hackenproof.com",
    "yeswehack.com",
    "immunefi.com",
    "cantina.xyz",
    "code4rena.com",
    "sherlock.xyz",
    "codehawks.com",
    "synack.com",
    "cobalt.io",
    "yogosha.com",
    "bugrap.io",
    "www.bugrap.io",
    "bughunters.google.com",
    "msrc.microsoft.com",
}
EXPLORER_HOST_HINTS = (
    "etherscan",
    "arbiscan",
    "basescan",
    "bscscan",
    "snowtrace",
    "optimistic.etherscan",
    "polygonscan",
    "solscan",
)
ASSET_LINE_KEYWORDS = (
    "core scope",
    "normal scope",
    "scope",
    "in scope",
    "out of scope",
    "domain",
    "app",
    "extension",
    "api",
    "endpoint",
    "host",
    "open source",
    "repo",
    "github",
    "gitlab",
    "docs",
    "contract",
    "reward",
    "reporting rule",
    "rule",
)
DOMAIN_LINE_KEYWORDS = (
    "core scope",
    "normal scope",
    "scope",
    "in scope",
    "out of scope",
    "domain",
    "app",
    "extension",
    "api",
    "endpoint",
    "host",
    "open source",
    "repo",
    "github",
    "gitlab",
    "docs",
    "contract",
)


class SimpleHTMLExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.text_chunks: list[str] = []
        self._title_mode = False
        self._ignored_tags: list[str] = []
        self.title = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized_tag = tag.lower()
        if normalized_tag in {"script", "style", "noscript"}:
            self._ignored_tags.append(normalized_tag)
            return
        if normalized_tag == "a":
            for key, value in attrs:
                if key.lower() == "href" and value:
                    self.links.append(value.strip())
        elif normalized_tag == "title":
            self._title_mode = True

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.lower()
        if self._ignored_tags and self._ignored_tags[-1] == normalized_tag:
            self._ignored_tags.pop()
            return
        if normalized_tag == "title":
            self._title_mode = False

    def handle_data(self, data: str) -> None:
        if self._ignored_tags:
            return
        text = " ".join(data.split())
        if text:
            self.text_chunks.append(text)
            if self._title_mode:
                self.title += text


@dataclass
class ScanTarget:
    host: str
    kind: str
    allow_subdomains: bool = False
    reasons: list[str] = field(default_factory=list)
    source_urls: list[str] = field(default_factory=list)


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return cleaned or "program"


def registrable_domain(host: str) -> str:
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def is_local_input(value: str) -> bool:
    return value.startswith("file://") or Path(value).exists()


def read_local_input(value: str) -> tuple[str, str]:
    path = Path(value[7:] if value.startswith("file://") else value)
    resolved = path.resolve()
    return resolved.read_text(encoding="utf-8"), resolved.as_uri()


def fetch_url(url: str, timeout: int) -> tuple[str, str, int | None, str | None]:
    if requests is not None:
        try:
            response = requests.get(
                url,
                timeout=timeout,
                headers={
                    "User-Agent": "BBKit/1.0 (+authorized bug bounty workflow)",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
            )
            return response.text, response.url, response.status_code, None
        except Exception as exc:
            return "", url, None, str(exc)
    try:
        from urllib.request import Request, urlopen

        request = Request(
            url,
            headers={
                "User-Agent": "BBKit/1.0 (+authorized bug bounty workflow)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        with urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace"), response.geturl(), response.status, None
    except Exception as exc:
        return "", url, None, str(exc)


def is_antibot_page(html: str) -> bool:
    lowered = html.lower()
    indicators = (
        "attention required",
        "checking your browser",
        "cf-chl",
        "cloudflare",
        "turnstile",
        "captcha",
        "access denied",
        "just a moment",
    )
    return any(indicator in lowered for indicator in indicators)


def should_render_in_browser(html: str) -> bool:
    lowered = html.lower()
    text_len = len(strip_html_text(html))
    script_count = lowered.count("<script")
    return text_len < 1200 or (script_count >= 8 and text_len < 2500)


def render_with_cloakbrowser(url: str, timeout: int) -> tuple[str, str | None]:
    html, error, _ = render_page(url, timeout=timeout, headless=True)
    return html, error


def extract_page_data(html: str, base_url: str) -> dict[str, Any]:
    parser = SimpleHTMLExtractor()
    parser.feed(html)
    parser.close()

    resolved_links = []
    for raw_link in parser.links:
        if raw_link.startswith("#"):
            continue
        if raw_link.startswith("mailto:") or raw_link.startswith("javascript:"):
            continue
        resolved_links.append(urljoin(base_url, raw_link))

    text = "\n".join(parser.text_chunks)
    text_lines = [line.strip() for line in text.splitlines() if line.strip()]

    def collect_contextual_lines(lines: list[str], keywords: tuple[str, ...], trailing: int = 1) -> list[str]:
        indexes: set[int] = set()
        for idx, line in enumerate(lines):
            lowered = line.lower()
            if any(keyword in lowered for keyword in keywords):
                for offset in range(0, trailing + 1):
                    if idx + offset < len(lines):
                        indexes.add(idx + offset)
        return [lines[idx] for idx in sorted(indexes)]

    summary_lines = collect_contextual_lines(text_lines, ASSET_LINE_KEYWORDS, trailing=1)
    domain_lines = collect_contextual_lines(text_lines, DOMAIN_LINE_KEYWORDS, trailing=2)
    domain_text = "\n".join(domain_lines)
    repo_refs = sorted(
        {
            match
            for match in REPO_RE.findall(text)
            if "." not in match.split("/", 1)[0]
            and "." not in match.split("/", 1)[1]
            and not match.lower().startswith(("http/", "https/"))
        }
    )
    return {
        "title": parser.title.strip(),
        "text": text,
        "text_lines": text_lines,
        "asset_lines": summary_lines,
        "domain_lines": domain_lines,
        "links": sorted(set(resolved_links)),
        "urls_in_text": sorted(set(URL_RE.findall(domain_text))),
        "domains_in_text": sorted(set(DOMAIN_RE.findall(domain_text))),
        "contract_addresses": sorted(set(ADDRESS_RE.findall(text))),
        "repo_refs": repo_refs,
    }


def classify_program(page_data: dict[str, Any], program_url: str = "") -> list[str]:
    haystack = " ".join(
        [
            page_data.get("title", ""),
            page_data.get("text", ""),
            " ".join(page_data.get("links", [])),
            program_url,
        ]
    ).lower()
    labels: list[str] = []
    if any(
        keyword in haystack
        for keyword in (
            "web3",
            "smart contract",
            "solidity",
            "evm",
            "token",
            "bridge",
            "defi",
            "dao",
            "mainnet",
            "testnet",
            "contract address",
            "immunefi",
            "cantina",
            "code4rena",
            "sherlock",
            "codehawks",
            "hats finance",
            "foundry",
            "hardhat",
            "anchor",
            "solana",
            "move language",
        )
    ) or page_data.get("contract_addresses"):
        labels.append("web3")
    if any(
        keyword in haystack
        for keyword in (
            "api",
            "swagger",
            "openapi",
            "postman",
            "graphql",
            "rest api",
            "backend",
            "microservice",
        )
    ):
        labels.append("api")
    if any(
        keyword in haystack
        for keyword in (
            "android",
            "ios",
            "mobile app",
            "apk",
            "ipa",
            "react native",
            "flutter",
            "play store",
            "app store",
        )
    ):
        labels.append("mobile")
    if any(
        keyword in haystack
        for keyword in (
            "web app",
            "website",
            "frontend",
            "browser",
            "cookie",
            "session",
            "oauth",
            "sso",
        )
    ):
        if "web" not in labels:
            labels.append("web")
    if not labels:
        labels.append("web")
    # Primary surface first for checklist convenience
    priority = ["web3", "api", "web", "mobile"]
    ordered = [label for label in priority if label in labels]
    for label in labels:
        if label not in ordered:
            ordered.append(label)
    return ordered


def classify_link(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    lowered = url.lower()
    if not host:
        return "other"
    if host in IGNORE_HOSTS:
        if host in {"github.com", "gitlab.com", "bitbucket.org"}:
            return "source"
        return "reference"
    if any(hint in host for hint in EXPLORER_HOST_HINTS):
        return "explorer"
    if any(token in lowered for token in ("/docs", "docs.", "developer", "developers", "/whitepaper", "/audit")):
        return "docs"
    if any(token in lowered for token in ("/api", "api.", "swagger", "openapi", "graphql", "postman")):
        return "api"
    return "asset"


def build_scan_targets(page_data: dict[str, Any], source_host: str) -> list[ScanTarget]:
    targets: dict[str, ScanTarget] = {}
    wildcard_roots = []
    for domain in page_data.get("domains_in_text", []):
        if domain.startswith("*."):
            wildcard_roots.append(domain[2:].lower())

    def add_target(host: str, kind: str, allow_subdomains: bool, reason: str, source_url: str | None = None) -> None:
        host = host.lower().strip().strip(".,;:").strip(".")
        if not host or host in IGNORE_HOSTS:
            return
        target = targets.get(host)
        if target is None:
            target = ScanTarget(host=host, kind=kind, allow_subdomains=allow_subdomains)
            targets[host] = target
        target.allow_subdomains = target.allow_subdomains or allow_subdomains
        if reason not in target.reasons:
            target.reasons.append(reason)
        if source_url and source_url not in target.source_urls:
            target.source_urls.append(source_url)

    for url in page_data.get("links", []) + page_data.get("urls_in_text", []):
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if not host:
            continue
        kind = classify_link(url)
        if kind in {"source", "reference", "explorer"}:
            continue
        allow_subs = host in wildcard_roots or host.count(".") == 1
        add_target(host, kind, allow_subs, f"referenced-{kind}", url)

    for domain in page_data.get("domains_in_text", []):
        cleaned = domain[2:] if domain.startswith("*.") else domain
        cleaned = cleaned.lower()
        if cleaned in IGNORE_HOSTS:
            continue
        if cleaned == source_host:
            continue
        allow_subs = domain.startswith("*.") or cleaned.count(".") == 1
        add_target(cleaned, "asset", allow_subs, "text-domain")

    for root in wildcard_roots:
        add_target(root, "asset", True, "wildcard-scope")

    if source_host and source_host not in IGNORE_HOSTS:
        add_target(source_host, "asset", source_host in wildcard_roots or source_host.count(".") == 1, "program-host")

    ordered_targets = sorted(
        targets.values(),
        key=lambda item: (
            0 if item.kind == "api" else 1 if item.kind == "asset" else 2,
            0 if item.allow_subdomains else 1,
            item.host,
        ),
    )
    return ordered_targets


def collect_lines(text_lines: list[str], keywords: tuple[str, ...], limit: int = 8) -> list[str]:
    selected = []
    for line in text_lines:
        lowered = line.lower()
        if any(keyword in lowered for keyword in keywords):
            selected.append(line)
        if len(selected) >= limit:
            break
    return selected


def ensure_seeded_target(bb_root: str, host: str) -> None:
    resolved = Path(bb_root) / "output" / host / "subs" / "resolved.txt"
    resolved.parent.mkdir(parents=True, exist_ok=True)
    if not resolved.exists():
        resolved.write_text(f"{host}\n", encoding="utf-8")


def run_bb(bb_root: str, command: str, target: str) -> tuple[int, str]:
    bb_bin = Path(bb_root) / "bin" / "bb"
    env = os.environ.copy()
    env["BB_ROOT"] = bb_root
    process = subprocess.run(
        [str(bb_bin), command, target],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    combined = "\n".join(part for part in (process.stdout, process.stderr) if part).strip()
    return process.returncode, combined


def run_program_scan(bb_root: str, labels: list[str], targets: list[ScanTarget], workspace_dir: Path) -> list[dict[str, Any]]:
    results = []
    commands_common = ["alive", "urls", "js"]
    commands_deep = ["nuclei"]

    for target in targets:
        target_commands = []
        if target.allow_subdomains:
            target_commands.append("subs")
        else:
            ensure_seeded_target(bb_root, target.host)
        target_commands.extend(commands_common)
        if target.kind != "docs":
            target_commands.extend(commands_deep)

        for command in target_commands:
            rc, output = run_bb(bb_root, command, target.host)
            results.append(
                {
                    "target": target.host,
                    "kind": target.kind,
                    "command": command,
                    "success": rc == 0,
                    "output": output[-4000:],
                }
            )

    (workspace_dir / "scan-results.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return results


def read_optional_file(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace").strip()
    return ""


def build_skill_plan(labels: list[str], page_data: dict[str, Any]) -> list[str]:
    skills = ["bbkit", "bug-bounty", "bb-methodology", "report-writing", "triage-validation"]
    if "web" in labels or "api" in labels:
        skills.extend(["web2-recon", "web2-vuln-classes", "security-arsenal"])
    if "web3" in labels:
        skills.extend(["web3-audit", "web3-bug-classes", "web3-grep-arsenal", "web3-poc-foundry", "security-arsenal"])
    if "mobile" in labels:
        skills.extend(["web2-vuln-classes", "security-arsenal"])
    haystack = " ".join(page_data.get("links", []) + page_data.get("urls_in_text", [])).lower()
    if "graphql" in haystack:
        skills.append("graphql-audit")
    ordered = []
    for skill in skills:
        if skill not in ordered:
            ordered.append(skill)
    return ordered


def build_command_plan(program_url: str, targets: list[ScanTarget], labels: list[str]) -> list[str]:
    commands = [f"bb engage {program_url}"]
    if "web3" in labels and not any(label in {"web", "api"} for label in labels):
        commands.append("# Surface chính = Web3: ưu tiên đọc repo/contract, Foundry/Slither; recon web chỉ nếu có domain in-scope")
    for target in targets[:4]:
        if target.kind == "docs":
            continue
        if "web3" in labels and target.kind in {"explorer"}:
            continue
        if target.allow_subdomains:
            commands.append(f"bb subs {target.host}")
        commands.append(f"bb alive {target.host}")
        commands.append(f"bb urls {target.host}")
        if "web" in labels or "api" in labels:
            commands.append(f"bb nuclei {target.host}")
    if "web3" in labels:
        commands.append("Đọc checklist.md + repo/contracts; chạy forge/slither khi có source in-scope")
    if "api" in labels:
        commands.append("Ưu tiên BOLA/IDOR/authz trên API trong-scope (Burp/manual sau recon)")
    if "mobile" in labels:
        commands.append("Map mobile API surface; test authz trên backend API, không reverse APK ngoài scope")
    ordered = []
    for command in commands:
        if command not in ordered:
            ordered.append(command)
    return ordered


def detect_platform(program_url: str, page_data: dict[str, Any]) -> str:
    """Identify bounty/contest platform from URL host (preferred) or page text."""
    host = (urlparse(program_url).hostname or "").lower()
    path = (urlparse(program_url).path or "").lower()
    hay_url = f"{host}{path}"
    text = (page_data.get("title", "") + " " + page_data.get("text", "")).lower()

    for marker, name in PLATFORM_HOST_MARKERS:
        if marker in hay_url:
            return name

    # Text fallbacks (local HTML export, redirect pages)
    text_markers = (
        ("hackenproof", "HackenProof"),
        ("intigriti", "Intigriti"),
        ("hackerone", "HackerOne"),
        ("bugcrowd", "Bugcrowd"),
        ("yeswehack", "YesWeHack"),
        ("immunefi", "Immunefi"),
        ("cantina", "Cantina"),
        ("code4rena", "Code4rena"),
        ("sherlock", "Sherlock"),
        ("codehawks", "CodeHawks"),
        ("synack", "Synack"),
        ("cobalt.io", "Cobalt"),
        ("yogosha", "Yogosha"),
    )
    for marker, name in text_markers:
        if marker in text:
            return name
    return "unknown"


def write_engagement_bundle(
    bb_root: str,
    slug: str,
    program_url: str,
    final_url: str,
    platform: str,
    labels: list[str],
    page_data: dict[str, Any],
    targets: list[ScanTarget],
    obstacles: list[str],
    skills: list[str],
    commands: list[str],
    workspace_dir: Path,
) -> Path:
    """Create engagements/<slug>/ with scope, checklist, findings workflow, activate scope."""
    eng_root = Path(bb_root) / "engagements" / slug
    findings_dir = eng_root / "findings"
    poc_dir = eng_root / "poc"
    eng_root.mkdir(parents=True, exist_ok=True)
    findings_dir.mkdir(exist_ok=True)
    poc_dir.mkdir(exist_ok=True)
    (eng_root / ".private").mkdir(exist_ok=True)

    domains = sorted({t.host for t in targets if t.kind in {"asset", "api"}})
    contracts = page_data.get("contract_addresses", [])[:20]
    repos = page_data.get("repo_refs", [])[:20]
    scope_lines = collect_lines(
        page_data.get("text_lines", []),
        ("scope", "in scope", "out of scope", "asset", "rule", "reward", "bounty", "severity", "payout"),
        limit=30,
    )

    domain_table = "\n".join(f"| {d} | domain/host | from program page |" for d in domains) or "| (none parsed) | | fill manually |"
    contract_table = "\n".join(f"| | `{c}` | | from program page |" for c in contracts) or "| | | | |"
    repo_list = "\n".join(f"- https://github.com/{r}" for r in repos) or "- (none parsed)"

    scope_md = f"""# Scope — {slug}

## Program

| Field | Value |
|-------|--------|
| Program name | {page_data.get("title") or slug} |
| Platform | {platform} |
| Policy / program URL | {program_url} |
| Final URL | {final_url} |
| Workspace intake | `{workspace_dir}` |

## Authorization

- [x] Testing only in-scope assets under this program.
- [ ] Credentials stay in `.private/` (never commit).

## Surface classification (auto)

| Label | Present |
|-------|---------|
| web3 | {"yes" if "web3" in labels else "no"} |
| web | {"yes" if "web" in labels else "no"} |
| api | {"yes" if "api" in labels else "no"} |
| mobile | {"yes" if "mobile" in labels else "no"} |

**Primary:** `{labels[0] if labels else "web"}`

## In-scope assets (auto-extracted — verify!)

### Web / hosts

| Asset | Type | Notes |
|-------|------|--------|
{domain_table}

### Smart contracts

| Name | Address | Chain | Notes |
|------|---------|-------|--------|
{contract_table}

### Repos / source

{repo_list}

## Scope / rules snippets (from page)

{chr(10).join(f"- {line}" for line in scope_lines) if scope_lines else "- (parse weak — open program URL and fill manually)"}

## Out of scope

| Asset / behavior | Reason |
|------------------|--------|
| (fill from program page) | |

## Tooling path (CLI first — save tokens)

1. Activate: `bb scope use {slug}`
2. Follow `checklist.md` by surface type
3. Run only commands in `pipeline.md` for this surface
4. Record findings under `findings/` with PoC
5. Run triager review: `triager-review.md`
"""
    (eng_root / "scope.md").write_text(scope_md, encoding="utf-8")

    checklist_md = f"""# Surface checklist — {slug}

Auto labels: **{", ".join(labels)}** · Platform: **{platform}**

Mark with [x] after human/AI confirms.

## A. Identify surface (required)

- [ ] Primary surface is: web3 / web / api / mobile / hybrid
- [ ] Assets in scope.md verified against program page (not hallucinated)
- [ ] Out-of-scope list filled
- [ ] Reward / severity rules understood

## B. If **web3** (contest / Immunefi / Cantina / SC platforms)

- [ ] Repo commit/tag pinned
- [ ] Deployed addresses + chains listed
- [ ] Roles: admin, guardian, oracle, keeper mapped
- [ ] Run static: `slither` / Aderyn if available (operator machine)
- [ ] Foundry fork PoC skeleton ready (`poc/`)
- [ ] Prefer skills: web3-bug-classes, web3-grep-arsenal, web3-poc-foundry
- [ ] Skip noisy web recon unless domains are explicitly in-scope

## C. If **web / api**

- [ ] Auth model mapped (cookie/JWT/OAuth)
- [ ] Two test accounts if IDOR possible
- [ ] Run CLI: `bb alive` → `bb urls` → (optional) `bb nuclei` **in-scope only**
- [ ] Manual: BOLA/IDOR, authz, business logic (not only scanners)
- [ ] Prefer skills: web2-recon, web2-vuln-classes

## D. If **mobile**

- [ ] Identify backend API hosts in scope
- [ ] Test API authz; reverse APK only if program allows
- [ ] Capture traffic only for in-scope hosts

## E. Findings discipline

- [ ] Every finding has steps + evidence + impact
- [ ] PoC is reproducible (HTTP or Foundry)
- [ ] Run triager-review.md before submit
"""
    (eng_root / "checklist.md").write_text(checklist_md, encoding="utf-8")

    pipeline_md = f"""# Pipeline — {slug}

CLI-first. AI reads outputs; does not re-scan blindly.

## 0. Intake (done by `bb engage` / `bb bounty`)

- Program page saved under: `{workspace_dir}`
- Labels: {", ".join(labels)}
- Obstacles: {"; ".join(obstacles) if obstacles else "none recorded"}

## 1. Activate scope

```bash
bb scope use {slug}
export BB_REQUIRE_SCOPE=1
```

## 2. Machine tools (in order)

```bash
{chr(10).join(commands)}
```

## 3. AI analysis (any agent: Codex / Claude / Factory / Grok / Z.ai / …)

Read only:
1. `engagements/{slug}/scope.md`
2. `engagements/{slug}/checklist.md`
3. `{workspace_dir}/report.md` + `scan-results.json` if present
4. Per-host `$BB_ROOT/output/<host>/` summaries

Then propose **next 3 high-value tests** (no full payload dump).

## 4. Finding loop

```bash
# copy template
cp engagements/{slug}/findings/_TEMPLATE.md engagements/{slug}/findings/001-short-title.md
# add PoC under engagements/{slug}/poc/
```

## 5. Triage

Fill `triager-review.md` as Reviewer (kill weak/dup/OOS).
"""
    (eng_root / "pipeline.md").write_text(pipeline_md, encoding="utf-8")

    finding_tpl = """# Finding: <title>

| Field | Value |
|-------|--------|
| ID | 001 |
| Severity (claimed) | |
| Surface | web3 / web / api / mobile |
| Asset | |
| Status | draft / confirmed / killed |

## Summary
(what / where / impact — 3–5 sentences)

## Steps to reproduce
1.
2.
3.

## PoC
- Path: `poc/...`
- Expected vs actual:

## Impact
-

## Fix
-

## Triager notes
- Q1 reproduce now?
- Q2 real victim?
- Q3 concrete impact?
- Q4 in scope?
- Q5 not duplicate?
- Q6 not always-rejected?
- Q7 would triager accept?
"""
    (findings_dir / "_TEMPLATE.md").write_text(finding_tpl, encoding="utf-8")

    triager_md = f"""# Triager / Reviewer pass — {slug}

Role: **platform triager**. Be hostile to weak reports.

For each file in `findings/` (except `_TEMPLATE.md`):

| ID | Title | In scope? | Repro? | Impact real? | Dup risk? | Verdict |
|----|-------|-----------|--------|--------------|-----------|---------|
| | | | | | | accept / need info / reject |

## Kill list (reject)

- Theoretical only / too many preconditions
- Out of scope asset
- Scanner output without manual confirmation
- Missing PoC or non-reproducible
- Best-practice / informational without security impact
- Duplicate of known/disclosed without new impact

## Accept only if

1. In-scope asset
2. Clear steps + evidence
3. Concrete harm (funds, PII, ATO, RCE, protocol insolvency, …)
4. Severity matches program rules

## Final recommendation

- Submit: …
- Hold / more work: …
- Drop: …
"""
    (eng_root / "triager-review.md").write_text(triager_md, encoding="utf-8")

    notes = f"""# Notes — {slug}

## Session log
- Intake from {program_url}
- Skills suggested: {", ".join(skills[:8])}

## Leads
- 

## Dead ends
- 
"""
    (eng_root / "notes.md").write_text(notes, encoding="utf-8")

    # Activate scope for subsequent bb full / recon
    active = Path(bb_root) / ".active-scope"
    active.write_text(str((eng_root / "scope.md").resolve()) + "\n", encoding="utf-8")

    # Symlink/copy pointer from workspace
    (workspace_dir / "ENGAGEMENT.md").write_text(
        f"Engagement directory: `{eng_root}`\nActive scope set to: `{eng_root / 'scope.md'}`\n",
        encoding="utf-8",
    )
    return eng_root


def build_handoff_markdown(
    program_url: str,
    workspace_dir: Path,
    labels: list[str],
    skills: list[str],
    commands: list[str],
    obstacles: list[str],
    repo_refs: list[str],
    eng_dir: Path | None = None,
) -> str:
    obstacle_block = "\n".join(f"- {item}" for item in obstacles) if obstacles else "- Không ghi nhận blocker lớn ở bước intake."
    repo_block = "\n".join(f"- `{repo}`" for repo in repo_refs) if repo_refs else "- Chưa trích xuất được repo tham chiếu."
    eng_block = f"- Engagement: `{eng_dir}` (scope.md, checklist.md, pipeline.md, findings/, triager-review.md)" if eng_dir else "- Engagement: (not created)"
    return f"""# BBKit Agent Handoff

## Program
- URL: {program_url}
- Intake workspace: `{workspace_dir}`
- Surface labels: {", ".join(labels)}
{eng_block}

## Read first (token-saving order)
1. Engagement `scope.md` + `checklist.md` + `pipeline.md` (if engagement exists)
2. `program-intake.md` / `report.md` / `program-intake.json` in intake workspace
3. `$BB_ROOT/output/<host>/` after running CLI tools

## Skills (lazy-load)
{chr(10).join(f"- `{skill}`" for skill in skills)}

## Repos / docs to check
{repo_block}

## CLI next (host tools first)
{chr(10).join(f"- `{command}`" if str(command).startswith("bb ") else f"- {command}" for command in commands)}

## Findings discipline
- Copy `findings/_TEMPLATE.md` → `findings/00N-title.md`
- PoC under `poc/`
- Final pass: `triager-review.md` (triager/reviewer role)

## Blockers
{obstacle_block}
"""


def build_hunt_report(
    workspace_dir: Path,
    program_url: str,
    final_url: str,
    labels: list[str],
    page_data: dict[str, Any],
    targets: list[ScanTarget],
    obstacles: list[str],
    skills: list[str],
    commands: list[str],
) -> str:
    scope_lines = collect_lines(
        page_data["text_lines"],
        ("scope", "in scope", "out of scope", "asset", "rule", "reward", "bounty", "payout"),
    )
    referenced_links = []
    seen_refs: set[str] = set()
    for url in [*page_data.get("urls_in_text", []), *page_data.get("links", [])]:
        if url in seen_refs:
            continue
        seen_refs.add(url)
        kind = classify_link(url)
        referenced_links.append(f"- [{kind}] {url}")
    for repo in page_data.get("repo_refs", []):
        referenced_links.append(f"- [source] https://github.com/{repo}")
    referenced_links = referenced_links[:40]

    leads = []
    if page_data.get("contract_addresses"):
        leads.append(
            "- Contract addresses tham chiếu trên trang chương trình: "
            + ", ".join(page_data["contract_addresses"][:10])
        )
    if page_data.get("repo_refs"):
        leads.append("- Repo tham chiếu trong scope: " + ", ".join(page_data["repo_refs"][:10]))
    for target in targets[:8]:
        nuclei_path = Path(os.environ["BB_ROOT"]) / "output" / target.host / "nuclei" / "nuclei.txt"
        interesting_path = Path(os.environ["BB_ROOT"]) / "output" / target.host / "urls" / "interesting.txt"
        nuclei_text = read_optional_file(nuclei_path)
        if nuclei_text:
            first_line = nuclei_text.splitlines()[0]
            leads.append(f"- `{target.host}` có lead từ nuclei, cần xác minh thủ công: `{first_line}`")
        interesting_text = read_optional_file(interesting_path)
        if interesting_text:
            lines = [line for line in interesting_text.splitlines()[:3] if line]
            if lines:
                leads.append(f"- `{target.host}` có endpoint đáng chú ý: " + ", ".join(lines))
    if not leads:
        leads.append("- Chưa có lead tự động nổi bật, cần đọc kỹ scope và tài liệu tham chiếu trước khi đào sâu.")

    next_steps = []
    if "web3" in labels:
        next_steps.extend(
            [
                "- Đối chiếu repo/hợp đồng/address với tài liệu triển khai để xác định chain, bridge, token, vault, admin roles.",
                "- Kiểm tra luồng privileged actions, oracle assumptions, pause/upgrade paths, và access control trong tài sản Web3 được tham chiếu.",
            ]
        )
    if "api" in labels:
        next_steps.extend(
            [
                "- Rà soát các endpoint auth, upload, GraphQL/OpenAPI, và các flow reset/password/token exchange.",
                "- Ưu tiên kiểm tra BOLA/IDOR, mass assignment, authz và business logic trên các asset API rõ scope.",
            ]
        )
    next_steps.extend(
        [
            "- Xác minh thủ công mọi lead từ nuclei trước khi coi là finding.",
            "- Nếu scope cho phép, dùng agent skill phù hợp trong BBKit để đào sâu từng bề mặt tấn công.",
        ]
    )

    scope_block = "\n".join(f"- {line}" for line in scope_lines) if scope_lines else "- Chưa trích xuất được scope/rules rõ ràng, cần đọc thủ công."
    target_block = "\n".join(
        f"- `{target.host}` ({target.kind}, allow_subdomains={str(target.allow_subdomains).lower()})"
        for target in targets
    ) or "- Chưa xác định được asset rõ ràng để quét tự động."
    obstacle_block = "\n".join(f"- {item}" for item in obstacles) if obstacles else "- Không ghi nhận trở ngại lớn trong bước intake tự động."
    reference_block = "\n".join(referenced_links) if referenced_links else "- Không trích xuất được URL tham chiếu."

    return f"""# BBKit Program Hunt Report

## Tóm tắt phạm vi
- Program URL: {program_url}
- Final URL: {final_url}
- Phân loại: {", ".join(labels)}
- Workspace: `{workspace_dir}`

{scope_block}

## Sơ đồ bề mặt tấn công
{target_block}

## Các phát hiện (chỉ những phát hiện đã xác nhận)
- Chưa có finding đã xác nhận ở lượt săn tự động ban đầu.

## Đầu mối đáng để điều tra
{chr(10).join(leads)}

## Trở ngại / thiếu quyền truy cập
{obstacle_block}

## Các bước tiếp theo được khuyến nghị
{chr(10).join(next_steps)}

## Skill / command đề xuất cho AI Agent
{chr(10).join(f"- skill: `{skill}`" for skill in skills)}
{chr(10).join(f"- command: `{command}`" if command.startswith("bb ") else f"- note: {command}" for command in commands[:8])}

## Tài sản / URL đã tham chiếu
{reference_block}
"""


def build_agent_prompt(
    program_url: str,
    labels: list[str],
    workspace_dir: Path,
    skills: list[str],
    commands: list[str],
    eng_dir: Path | None = None,
    slug: str = "",
) -> str:
    label_text = ", ".join(labels)
    eng_block = ""
    if eng_dir is not None:
        eng_block = f"""
Engagement (CLI-first — đọc TRƯỚC, đừng re-fetch program page):
- Dir: `{eng_dir}`
- `scope.md` — assets + surface labels
- `checklist.md` — web3 / web / api / mobile gates
- `pipeline.md` — lệnh máy cần chạy
- `findings/_TEMPLATE.md` + `poc/` — ghi finding + PoC
- `triager-review.md` — pass cuối góc triager/reviewer
"""
    return f"""Authorized bug bounty engagement (BBKit — agent-agnostic)

Context
- Intake workspace: {workspace_dir}
- Program URL: {program_url}
- Surface labels: {label_text}
- Engagement slug: {slug or "(none)"}
- Works with any shell-capable agent (Codex, Claude Code, Factory Droid, Grok Build, Z.ai/ZCode, Cursor, OpenCode, …)
{eng_block}
Hard rules:
- In-scope only; no destructive / noisy OOS actions.
- Prefer local CLI tools (bb alive/urls/nuclei, slither, forge) over model-only recon — saves tokens.
- Do not invent findings. Separate: confirmed | lead | next step.
- Every finding needs steps + impact + PoC path under findings/ and poc/.
- Before submit: complete triager-review.md (7-question gate).

Workflow:
1. Confirm surface from checklist.md (web3 vs web/api vs mobile).
2. Run machine commands from pipeline.md (in order); read tool outputs from $BB_ROOT/output/.
3. Analyze outputs; propose next 3 high-value tests only.
4. On finding: copy findings/_TEMPLATE.md → 00N-title.md + PoC under poc/.
5. Final pass as triager/reviewer (kill weak/dup/OOS).

Skills (lazy): {", ".join(skills)}
Suggested commands: {"; ".join(commands[:8])}

Output format:
- Scope summary + surface map
- Confirmed findings only (with PoC paths)
- Leads worth investigating
- Blockers
- Next 3 actions
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Run BBKit intake + scoped initial hunt from a program URL.")
    parser.add_argument("program_url", help="Bug bounty program URL or local HTML file path")
    parser.add_argument("--browser", choices=("off", "auto", "standard"), default="auto")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--skip-scan", action="store_true", help="Intake only; do not run bb alive/urls/nuclei")
    parser.add_argument("--max-targets", type=int, default=6)
    parser.add_argument("--slug", default="", help="Engagement folder name under engagements/ (e.g. rogo-recon)")
    parser.add_argument("--no-engage", action="store_true", help="Do not create engagements/ scope bundle")
    parser.add_argument("--intake-only", action="store_true", help="Alias: skip-scan + still create engagement")
    args = parser.parse_args()

    if args.intake_only:
        args.skip_scan = True

    bb_root = os.environ.get("BB_ROOT")
    if not bb_root:
        print("BB_ROOT is required", file=sys.stderr)
        return 1

    # Ensure lib imports work when invoked as python3 program_hunt.py
    lib_dir = str(Path(__file__).resolve().parent)
    if lib_dir not in sys.path:
        sys.path.insert(0, lib_dir)

    obstacles: list[str] = []
    if is_local_input(args.program_url):
        html, final_url = read_local_input(args.program_url)
        status_code = None
    else:
        html, final_url, status_code, fetch_error = fetch_url(args.program_url, args.timeout)
        if fetch_error:
            obstacles.append(f"Không thể tải trang chương trình: {fetch_error}")
            html = ""
        if status_code and status_code >= 400:
            obstacles.append(f"Trang chương trình trả về HTTP {status_code}")

    if html and is_antibot_page(html):
        obstacles.append(
            "Trang chương trình hiển thị anti-bot/WAF — thử CloakBrowser (bb browser / auto). "
            "Không phải Akamai bypass chuyên dụng; chỉ browser automation."
        )

    if html and args.browser in {"auto", "standard"} and not is_antibot_page(html) and should_render_in_browser(html):
        rendered_html, render_error = render_with_cloakbrowser(final_url, args.timeout)
        if rendered_html:
            html = rendered_html
        elif render_error and args.browser == "standard":
            obstacles.append(render_error)
    elif html and args.browser in {"auto", "standard"} and is_antibot_page(html):
        rendered_html, render_error = render_with_cloakbrowser(final_url, args.timeout)
        if rendered_html:
            html = rendered_html
            if not is_antibot_page(rendered_html):
                obstacles = [item for item in obstacles if "anti-bot/WAF" not in item]
        elif render_error:
            obstacles.append(f"CloakBrowser: {render_error}")

    if not html:
        html = "<html><body>Unavailable program page</body></html>"

    page_data = extract_page_data(html, final_url)
    labels = classify_program(page_data, args.program_url)
    platform = detect_platform(args.program_url, page_data)
    skills = build_skill_plan(labels, page_data)

    source_host = (urlparse(final_url).hostname or "").lower()
    targets = build_scan_targets(page_data, source_host)[: args.max_targets]
    if not targets:
        obstacles.append("Không xác định được asset rõ scope để quét tự động từ trang chương trình.")
    commands = build_command_plan(args.program_url, targets, labels)

    program_name = page_data.get("title") or source_host or "program"
    slug = slugify(args.slug) if args.slug else slugify(program_name)
    # Prefer short stable slug for engagement folder
    if len(slug) > 48:
        slug = slug[:48].rstrip("-")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    workspace_dir = Path(bb_root) / "output" / "programs" / f"{slug}-{timestamp}"
    workspace_dir.mkdir(parents=True, exist_ok=True)

    (workspace_dir / "program-page.html").write_text(html, encoding="utf-8")
    (workspace_dir / "program-intake.json").write_text(
        json.dumps(
            {
                "program_url": args.program_url,
                "final_url": final_url,
                "status_code": status_code,
                "platform": platform,
                "labels": labels,
                "slug": slug,
                "targets": [asdict(target) for target in targets],
                "page": {
                    "title": page_data.get("title"),
                    "contract_addresses": page_data.get("contract_addresses"),
                    "repo_refs": page_data.get("repo_refs"),
                    "domains_in_text": page_data.get("domains_in_text"),
                    "asset_lines": page_data.get("asset_lines"),
                },
                "obstacles": obstacles,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    intake_lines = collect_lines(
        page_data["text_lines"],
        ("scope", "in scope", "out of scope", "asset", "rule", "reward", "bounty", "payout"),
        limit=20,
    )
    intake_md = "\n".join(f"- {line}" for line in intake_lines) if intake_lines else "- Chưa trích xuất được nội dung rõ ràng."
    (workspace_dir / "program-intake.md").write_text(
        f"# Program Intake\n\n- Program URL: {args.program_url}\n- Final URL: {final_url}\n"
        f"- Platform: {platform}\n- Phân loại: {', '.join(labels)}\n- Engagement slug: `{slug}`\n\n"
        f"## Scope / Rules / Rewards\n{intake_md}\n",
        encoding="utf-8",
    )

    eng_dir = None
    if not args.no_engage:
        eng_dir = write_engagement_bundle(
            bb_root,
            slug,
            args.program_url,
            final_url,
            platform,
            labels,
            page_data,
            targets,
            obstacles,
            skills,
            commands,
            workspace_dir,
        )

    (workspace_dir / "agent-prompt.md").write_text(
        build_agent_prompt(
            args.program_url,
            labels,
            workspace_dir,
            skills,
            commands,
            eng_dir=eng_dir,
            slug=slug,
        ),
        encoding="utf-8",
    )
    (workspace_dir / "agent-handoff.md").write_text(
        build_handoff_markdown(
            args.program_url,
            workspace_dir,
            labels,
            skills,
            commands,
            obstacles,
            page_data.get("repo_refs", []),
            eng_dir=eng_dir,
        ),
        encoding="utf-8",
    )

    # Web3-primary: default skip noisy nuclei unless web/api also present
    run_scan = not args.skip_scan and bool(targets)
    if run_scan and "web3" in labels and not any(x in labels for x in ("web", "api")):
        # Still allow alive on docs hosts only if operator wants — default skip auto scan
        obstacles.append("Surface chính Web3: bỏ auto web scan (dùng --skip-scan mặc định logic). Chạy tools web chỉ khi domain in-scope.")
        run_scan = False

    if run_scan:
        run_program_scan(bb_root, labels, targets, workspace_dir)

    report = build_hunt_report(
        workspace_dir,
        args.program_url,
        final_url,
        labels,
        page_data,
        targets,
        obstacles,
        skills,
        commands,
    )
    report_path = workspace_dir / "report.md"
    report_path.write_text(report, encoding="utf-8")

    print(f"Workspace: {workspace_dir}")
    print(f"Report: {report_path}")
    print(f"Labels: {', '.join(labels)}")
    print(f"Platform: {platform}")
    if eng_dir:
        print(f"Engagement: {eng_dir}")
        print(f"Scope active: {eng_dir / 'scope.md'}")
        print("Next: read checklist.md + pipeline.md; run CLI tools; then triager-review.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
