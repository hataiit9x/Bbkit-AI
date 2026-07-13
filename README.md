# BBKit (Bbkit-AI)

**Bug bounty workstation** for Linux / **WSL** / VPS (Ubuntu/Debian, ARM64 + x86_64): recon CLI, plugin tool install, authorized **scope**, and AI skill sync (Claude Code, Codex, agents) + Web3 knowledge pack.

> Use only on assets you own or have **explicit permission** to test.

**Version:** see `VERSION` (current: **0.4.0**)

---

## What you get

| Layer | Role |
|-------|------|
| **`bb` CLI** | Recon pipeline, doctor, update, scope, AI sync |
| **Plugins** | Install subfinder, httpx, nuclei, katana, naabu, … |
| **Scope** | Engagement `scope.md` + allowlist checks before recon |
| **AI bundle** | Vendored methodology/tools from `ref/claude-bug-bounty` → `~/BugBounty/ai/bug-bounty` |
| **bbkit skill** | Thin orchestrator (`skills/bbkit/`) — scope-first, lazy modes |
| **Web3 skills** | Auto-cloned on `bb ai sync` (Immunefi-oriented classes / Foundry) |

---

## Quick start (WSL)

```bash
git clone https://github.com/hataiit9x/Bbkit-AI.git
cd Bbkit-AI
chmod +x install.sh bin/bb recon/*
./install.sh
source ~/.bashrc

bb doctor
bb config
bb ai sync
bb dashboard          # http://127.0.0.1:8787/
```

### Docker (optional)

```bash
docker build -t bbkit:0.4 .
docker run --rm bbkit:0.4 doctor
docker run --rm -p 8787:8787 -v "$PWD/out:/data/BugBounty/output" \
  bbkit:0.4 dashboard --host 0.0.0.0
# see docs/DOCKER.md
```

### CLI-first program intake (Cantina / Immunefi / H1)

Preferred for **Grok Build** and agents — create engagement folder + checklist, then run host tools:

```bash
bb engage 'https://cantina.xyz/code/<uuid>/overview' --slug rogo-recon
# → engagements/rogo-recon/{scope,checklist,pipeline,triager-review}.md
# → findings/_TEMPLATE.md, poc/ ; scope activated
# → output/programs/rogo-recon-<ts>/ (raw page + handoff)

# AI reads checklist (web3 vs web/api vs mobile), runs e.g.:
bb alive <in-scope-host>
bb urls <in-scope-host>
# Web3: forge/slither on pinned repo; skip noisy web scan if pure SC

# Finding + PoC + triager
cp ~/BugBounty/engagements/rogo-recon/findings/_TEMPLATE.md \
   ~/BugBounty/engagements/rogo-recon/findings/001-title.md
# fill triager-review.md before submit
```

`bb engage` defaults to **intake only** (no auto nuclei). Pass `--scan` or use `bb bounty` for first-pass probes.

### Authorized recon flow

```bash
bb scope new acme-h1
# edit ~/BugBounty/engagements/acme-h1/scope.md  (list in-scope domains)
bb scope use acme-h1
bb scope check api.acme.com

bb full acme.com                 # subs → alive → urls → js → ports → nuclei → report
bb full --passive-only acme.com  # no ports / nuclei
bb full --severity critical,high --rate 200 acme.com
# output: ~/BugBounty/output/acme.com/  (+ report.html, report.md)
```

Enforce scope hard:

```bash
export BB_REQUIRE_SCOPE=1        # refuse recon if no active scope / OOS host
bb full acme.com
```

### AI (Grok Build / Claude Code / Cursor)

```bash
bb ai sync                       # skills + commands + web3 + bbkit
bb ai doctor
bb hunt …                        # when AI bundle tools present
bb validate …
```

Prompt starter:

```text
Use bbkit skill. Authorized only.
bb engage 'https://cantina.xyz/code/<id>/overview' --slug <name>
Follow checklist.md + pipeline.md (CLI tools first). Findings + PoC; triager-review last.
```

Optional UI: `bb dashboard` — not required for the CLI hunt path.

### CloakBrowser

`bb browser <url>` and auto-render in `bb engage` use **cloakbrowser** (plugin `browser-tools`) for JS / light anti-bot pages. Not a dedicated Akamai bypass product.

---

## Commands

```bash
bb help | doctor | update | version

bb scope status|list|new <slug>|use <slug>|check <host>|clear
bb engage <program-url> [--slug name] [--scan]

bb subs|alive|urls|js|port|nuclei|report|full <domain>

bb bounty <program-url>
bb browser <url>
bb hunt | validate | intel | scan-cves | arsenal

bb ai sync | doctor | run <tool> [args…]
bb config | dashboard
```

---

## Layout

```text
Bbkit-AI/                 # this repo
  bin/bb                  # CLI
  lib/                    # common.sh, program_hunt.py
  plugins/                # tool installers
  recon/                  # workflows
  skills/bbkit/           # thin AI orchestrator
  templates/engagement/   # scope.md templates
  ref/claude-bug-bounty/  # AI methodology vendor (upstream MIT)
  install.sh

~/BugBounty/              # default BB_ROOT after install
  bin/ output/ tools/ wordlists/
  engagements/<slug>/scope.md
  ai/bug-bounty/          # installed AI tools/skills
  ai/web3-skills/         # after bb ai sync
  skills/bbkit/
```

---

## Config

- `config/config.yaml` — threads, rate, nuclei severity, recon flags, dashboard (see **docs/CONFIG.md**)  
- `bb config` — print effective values  
- Env overrides: `BB_ROOT`, `BB_REQUIRE_SCOPE=1`, `BB_NUCLEI_SEVERITY`, `BB_RATE`, `BB_THREADS`, `BB_SCOPE_FILE`, `BB_WEB3_URL`, `BB_DASH_PORT`

---

## Safety

1. Prefer `bb scope use` before recon.  
2. Set `BB_REQUIRE_SCOPE=1` on shared VPS.  
3. Never commit `.private/` cookies or API keys.  
4. Nuclei defaults to critical/high/medium (override with env).  

---

## Docs

See `docs/` (architecture, plugins, roadmap). AI depth lives under installed `ai/bug-bounty` + web3 skills after sync.

---

## Attribution

- Recon workstation: BBKit contributors  
- AI methodology/tools vendor: [shuvonsec/claude-bug-bounty](https://github.com/shuvonsec/claude-bug-bounty) (MIT) under `ref/`  
- Web3 skills (synced): [shuvonsec/web3-bug-bounty-hunting-ai-skills](https://github.com/shuvonsec/web3-bug-bounty-hunting-ai-skills) (MIT)  

---

## License

MIT — see `LICENSE`.
