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
    "bugcrowd.com",
    "bugrap.io",
    "hackerone.com",
    "intigriti.com",
    "immunefi.com",
    "nvd.nist.gov",
    "youtube.com",
    "www.bugrap.io",
    "www.youtube.com",
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


def classify_program(page_data: dict[str, Any]) -> list[str]:
    haystack = " ".join(
        [
            page_data.get("title", ""),
            page_data.get("text", ""),
            " ".join(page_data.get("links", [])),
        ]
    ).lower()
    labels = []
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
        )
    ):
        labels.append("api")
    if not labels:
        labels.append("web")
    return labels


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
    skills = ["bug-bounty", "bb-methodology", "report-writing", "triage-validation"]
    if "web" in labels or "api" in labels:
        skills.extend(["web2-recon", "web2-vuln-classes", "security-arsenal"])
    if "web3" in labels:
        skills.extend(["web3-audit", "security-arsenal"])
    haystack = " ".join(page_data.get("links", []) + page_data.get("urls_in_text", [])).lower()
    if "graphql" in haystack:
        skills.append("graphql-audit")
    ordered = []
    for skill in skills:
        if skill not in ordered:
            ordered.append(skill)
    return ordered


def build_command_plan(program_url: str, targets: list[ScanTarget], labels: list[str]) -> list[str]:
    commands = [f"bb bounty {program_url}"]
    for target in targets[:4]:
        if target.allow_subdomains:
            commands.append(f"bb subs {target.host}")
        commands.append(f"bb alive {target.host}")
        commands.append(f"bb urls {target.host}")
        if target.kind != "docs":
            commands.append(f"bb nuclei {target.host}")
    if "web3" in labels:
        commands.append("Đọc `program-intake.md`, repo, docs, contract addresses trước khi chạy các kiểm tra Web3 chuyên sâu.")
    if "api" in labels:
        commands.append("Ưu tiên rà soát authz/BOLA/GraphQL trên các asset API trong `report.md`.")
    ordered = []
    for command in commands:
        if command not in ordered:
            ordered.append(command)
    return ordered


def build_handoff_markdown(
    program_url: str,
    workspace_dir: Path,
    labels: list[str],
    skills: list[str],
    commands: list[str],
    obstacles: list[str],
    repo_refs: list[str],
) -> str:
    obstacle_block = "\n".join(f"- {item}" for item in obstacles) if obstacles else "- Không ghi nhận blocker lớn ở bước intake."
    repo_block = "\n".join(f"- `{repo}`" for repo in repo_refs) if repo_refs else "- Chưa trích xuất được repo tham chiếu."
    return f"""# BBKit Agent Handoff

## Program
- URL: {program_url}
- Workspace: `{workspace_dir}`
- Phân loại: {", ".join(labels)}

## File quan trọng
- `program-intake.md`
- `report.md`
- `scan-results.json` (nếu có)
- `program-intake.json`

## Skill nên dùng
{chr(10).join(f"- `{skill}`" for skill in skills)}

## Repo / tài liệu nên kiểm tra trước
{repo_block}

## Command nên chạy tiếp
{chr(10).join(f"- `{command}`" if command.startswith("bb ") else f"- {command}" for command in commands)}

## Blocker / lưu ý
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


def build_agent_prompt(program_url: str, labels: list[str], workspace_dir: Path, skills: list[str], commands: list[str]) -> str:
    label_text = ", ".join(labels)
    return f"""Thực hiện cuộc săn lỗi bảo mật có ủy quyền

Bối cảnh
- Không gian làm việc: {workspace_dir}
- URL mục tiêu: {program_url}
- Phân loại ban đầu: {label_text}
- Người dùng đã yêu cầu rõ ràng quy trình bug bounty trên mục tiêu này.

Ràng buộc:
- Tuân thủ nghiêm ngặt phạm vi và ủy quyền của chương trình săn lỗi được nêu trên trang mục tiêu.
- Không thực hiện bất kỳ hành động phá hoại, gây ồn ào hoặc nằm ngoài phạm vi nào.
- Tập trung vào các phát hiện thực tế, có giá trị cao về bảo mật, bề mặt tấn công, diễn giải phạm vi và hướng dẫn săn lùng các bước tiếp theo.
- Nếu trang chương trình săn lỗi tham chiếu đến kho mã nguồn, tài liệu, hợp đồng, chuỗi hoặc địa chỉ đã triển khai, hãy sử dụng chúng làm điểm xoay chuyển.
- Không bịa đặt phát hiện. Phân biệt rõ ràng giữa phát hiện đã xác nhận, đầu mối đáng ngờ và các bước tiếp theo được khuyến nghị.

Các câu hỏi cần trả lời / các bước cần thực hiện:
1. Đọc `program-intake.md`, `report.md`, và `agent-handoff.md`.
2. Xác định kiến trúc giao thức và bề mặt tấn công có khả năng xảy ra.
3. Dùng các skill phù hợp sau nếu cần: {", ".join(skills)}.
4. Ghi chú bất kỳ đầu mối hứa hẹn, phát hiện cụ thể hoặc trở ngại nào.
5. Nếu cần chạy thêm lệnh BBKit, ưu tiên theo thứ tự: {", ".join(commands[:6])}.
6. Đề xuất các bước kiểm tra thủ công tiếp theo có giá trị cao nhất.

Định dạng đầu ra mong đợi:
- Tóm tắt phạm vi
- Sơ đồ bề mặt tấn công
- Các phát hiện (chỉ những phát hiện đã xác nhận)
- Đầu mối đáng để điều tra
- Trở ngại / thiếu quyền truy cập
- Các bước tiếp theo được khuyến nghị
- Tài sản / URL đã tham chiếu
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Run BBKit intake + scoped initial hunt from a program URL.")
    parser.add_argument("program_url", help="Bug bounty program URL or local HTML file path")
    parser.add_argument("--browser", choices=("off", "auto", "standard"), default="auto")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--skip-scan", action="store_true")
    parser.add_argument("--max-targets", type=int, default=6)
    args = parser.parse_args()

    bb_root = os.environ.get("BB_ROOT")
    if not bb_root:
        print("BB_ROOT is required", file=sys.stderr)
        return 1

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
        obstacles.append("Trang chương trình hiển thị anti-bot/WAF, cần mở thủ công bằng browser adapter trong phạm vi được phép.")

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
        elif render_error and args.browser == "standard":
            obstacles.append(render_error)

    if not html:
        html = "<html><body>Unavailable program page</body></html>"

    page_data = extract_page_data(html, final_url)
    labels = classify_program(page_data)
    skills = build_skill_plan(labels, page_data)

    source_host = (urlparse(final_url).hostname or "").lower()
    targets = build_scan_targets(page_data, source_host)[: args.max_targets]
    if not targets:
        obstacles.append("Không xác định được asset rõ scope để quét tự động từ trang chương trình.")
    commands = build_command_plan(args.program_url, targets, labels)

    program_name = page_data.get("title") or source_host or "program"
    slug = slugify(program_name)
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
                "labels": labels,
                "targets": [asdict(target) for target in targets],
                "page": page_data,
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
        f"# Program Intake\n\n- Program URL: {args.program_url}\n- Final URL: {final_url}\n- Phân loại: {', '.join(labels)}\n\n## Scope / Rules / Rewards\n{intake_md}\n",
        encoding="utf-8",
    )

    (workspace_dir / "agent-prompt.md").write_text(
        build_agent_prompt(args.program_url, labels, workspace_dir, skills, commands),
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
        ),
        encoding="utf-8",
    )

    if not args.skip_scan and targets:
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
