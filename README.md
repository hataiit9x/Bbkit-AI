# BBKit (Bbkit-AI)

**Bug bounty workstation** for Linux / **WSL** / VPS (Ubuntu/Debian, ARM64 + x86_64): recon CLI, plugin tool install, authorized **scope**, and AI skill sync (Claude Code, Codex, agents) + Web3 knowledge pack.

> Use only on assets you own or have **explicit permission** to test.

**Version:** see `VERSION` (current: **0.5.0**)

---

## What you get

| Layer | Role |
|-------|------|
| **`bb` CLI** | Recon pipeline, doctor, update, scope, engage, AI sync |
| **Plugins** | Install subfinder, httpx, nuclei, katana, naabu, … |
| **Scope / engage** | Program intake → `engagements/<slug>/` + allowlist before recon |
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
bb dashboard          # optional UI — http://127.0.0.1:8787/
```

### Docker (optional)

```bash
docker build -t bbkit:0.5 .
docker run --rm bbkit:0.5 doctor
docker run --rm -p 8787:8787 -v "$PWD/out:/data/BugBounty/output" \
  bbkit:0.5 dashboard --host 0.0.0.0
# see docs/DOCKER.md
```

---

## `bb engage` flow (primary hunt path)

Works for **any program policy URL** (Intigriti, HackenProof, HackerOne, Bugcrowd, YesWeHack, Immunefi, Cantina, Code4rena, private HTML, …) and **any agent** with shell (Codex, Claude Code, Factory Droid, Grok Build, Z.ai/ZCode, Cursor, plain terminal).

### End-to-end

```text
Operator / AI agent
        │
        │  bb engage '<PROGRAM_URL>' [--slug name]
        ▼
┌───────────────────────────────────────────────────────────┐
│ 1. FETCH program page                                     │
│    httpx/requests → if JS/anti-bot → CloakBrowser (auto)  │
└───────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────┐
│ 2. PARSE + CLASSIFY                                       │
│    · Platform (H1 / Intigriti / HackenProof / … / unknown)│
│    · Surface labels: web3 | web | api | mobile            │
│    · Domains, contracts, repos from page text             │
└───────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────┐
│ 3. WRITE engagement + intake                              │
│    engagements/<slug>/                                    │
│      scope.md          program + assets + surface table   │
│      checklist.md      gates by surface type              │
│      pipeline.md       ordered host CLI commands          │
│      findings/         _TEMPLATE.md                       │
│      poc/              PoC artifacts                      │
│      triager-review.md final reviewer pass                │
│      notes.md                                             │
│    output/programs/<slug>-<timestamp>/                    │
│      program-page.html, program-intake.md/.json          │
│      report.md, agent-handoff.md, agent-prompt.md         │
│    .active-scope → points at scope.md                     │
└───────────────────────────────────────────────────────────┘
        │
        │  default: STOP here (no auto nuclei) — save tokens
        │  optional: --scan → scoped alive/urls/nuclei
        ▼
┌───────────────────────────────────────────────────────────┐
│ 4. AGENT / OPERATOR                                       │
│    Read scope.md + checklist.md + pipeline.md             │
│    Confirm surface (web3 vs web/api vs mobile)            │
│    Run CLI tools from pipeline (not model-only recon)     │
│    Analyze $BB_ROOT/output/<host>/ → next 3 tests         │
└───────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────┐
│ 5. FINDING + PoC                                          │
│    findings/001-title.md + poc/…                          │
└───────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────┐
│ 6. TRIAGER / REVIEWER                                     │
│    Fill triager-review.md (7-question gate) → submit      │
└───────────────────────────────────────────────────────────┘
```

### Commands

```bash
# Intake only (default) — recommended for AI agents
bb engage 'https://app.intigriti.com/…/…' --slug acme-intigriti
bb engage 'https://hackenproof.com/…' --slug acme-hp
bb engage 'https://hackerone.com/…' --slug acme-h1

# Intake + first-pass probes (when domains are clearly in-scope)
bb engage 'https://…' --slug acme --scan

# Same engine, historical name (may probe more by default path)
bb bounty 'https://…'
```

### After engage — what to read / run

| Step | Action |
|------|--------|
| 1 | Open `~/BugBounty/engagements/<slug>/scope.md` — verify assets (auto extract can miss/mis-parse) |
| 2 | Open `checklist.md` — mark surface: **web3 / web / api / mobile** |
| 3 | Follow `pipeline.md` CLI order, e.g. `bb alive host` → `bb urls host` → optional `bb nuclei host` |
| 4 | Pure **web3**: prefer repo/contracts + forge/slither; skip noisy web recon unless domains in-scope |
| 5 | Read tool output under `~/BugBounty/output/<host>/` (and intake `report.md`) |
| 6 | Finding: `cp findings/_TEMPLATE.md findings/001-title.md` + PoC under `poc/` |
| 7 | Fill `triager-review.md` before any platform submit |

```bash
bb scope use acme-intigriti   # already set by engage; re-run if needed
export BB_REQUIRE_SCOPE=1

bb alive api.example.com
bb urls api.example.com
# bb nuclei api.example.com   # only if checklist says web/api

cp ~/BugBounty/engagements/acme-intigriti/findings/_TEMPLATE.md \
   ~/BugBounty/engagements/acme-intigriti/findings/001-short-title.md
# write poc/… then edit triager-review.md
```

### Flags

| Flag | Meaning |
|------|---------|
| `--slug NAME` | Engagement folder name (`engagements/NAME/`) |
| `--scan` | Also run scoped probes after intake |
| `--browser auto\|off\|standard` | CloakBrowser for hard pages (default `auto`) |
| `--timeout N` | Fetch / browser timeout |
| `--no-engage` | Only `output/programs/…` (no engagements/ bundle) |

### Agent prompt (any product)

```text
Use bbkit skill if present. Authorized only.
bb engage '<PROGRAM_POLICY_URL>' --slug <name>
Then: scope.md → checklist.md → pipeline.md (CLI first).
Findings + PoC under findings/ and poc/. triager-review.md last.
```

---

### Authorized recon flow (manual scope, no program URL)

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

### AI (multi-agent)

```bash
bb ai sync                       # Claude / Codex / .agents / Factory
bb ai doctor
bb hunt …                        # when AI bundle tools present
bb validate …
```

```bash
# Optional: Z.ai, Cursor, OpenCode skill dirs
export BB_EXTRA_SKILL_ROOTS="$HOME/.cursor/skills:$HOME/.zai/skills"
bb ai sync
```

Optional UI: `bb dashboard` — not required for the CLI path. See **`bb engage` flow** above for the agent hunt sequence.

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
  engagements/<slug>/     # after bb engage
    scope.md checklist.md pipeline.md triager-review.md
    findings/  poc/  notes.md  .private/
  output/programs/<slug>-<ts>/   # raw page + handoff
  output/<host>/                 # recon tool output
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
