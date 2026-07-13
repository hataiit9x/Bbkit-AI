# Changelog

## 0.5.0

- **`bb engage <program-url>`** — CLI-first intake for Grok Build / agents
  - Creates `engagements/<slug>/`: `scope.md`, `checklist.md` (web3/web/api/mobile), `pipeline.md`, `findings/`, `poc/`, `triager-review.md`
  - Activates scope; saves raw page under `output/programs/`
  - Default **no auto scan** (token-saving); `--scan` for probes
- `program_hunt.py`: surface classify, platform detect (Cantina/…), engagement bundle, web3-primary skip noisy web scan, honest CloakBrowser messaging
- bbkit skill + docs: Cantina-style prompt → engage → CLI tools → findings/PoC → triager
- CloakBrowser remains for hard pages (`bb browser`); not marketed as Akamai bypass

## 0.4.0

- Wire `config/config.yaml` → runtime (`load_bb_config`): threads, rate, nuclei severity, scope, katana depth, naabu ports, dashboard host/port, resolvers
- Recon tools honor config/env knobs (subfinder, dnsx, httpx, katana, naabu, nuclei, gau)
- `bb config` shows effective values
- Optional **dashboard** (`bb dashboard`, `lib/dashboard.py`) — reports + engagements + JSON API
- **Docker** + `docker-compose.yml` for VPS (core tools + dashboard)
- `bb full --threads N`; docs CONFIG / DOCKER / DASHBOARD

## 0.3.0

- Sparse vendor: drop `site/`, `demo/`, `logo.png`, `tests/`, `wordlists/` from `ref/claude-bug-bounty`
- `scripts/sparse-vendor-sync.sh` to refresh vendor without bloat
- HTML + Markdown report with **scope metadata**, alive sample, nuclei stubs, engagement findings
- `bb full --passive-only` / `--no-ports` / `--no-nuclei` / `--severity` / `--rate`
- Port scan respects `BB_RATE`
- CI: real shellcheck (no `|| true`) + smoke job for `bb scope` and full flags

## 0.2.0

- Add `bb scope` (new / use / check / list / clear / status) and engagement templates
- Add `require_in_scope` checks on recon commands; `BB_REQUIRE_SCOPE=1` hard mode
- Add thin orchestrator skill `skills/bbkit/`
- `bb ai sync` clones Web3 skill pack if missing; syncs bbkit skill to Claude/Codex/agents
- Nuclei default severity: critical,high,medium (`BB_NUCLEI_SEVERITY` override)
- Expand `.gitignore`; remove `__pycache__`
- Install copies skills + engagement templates
- README rewrite for real AI + scope workflow

## 0.1.0

- Initial BBKit workstation (recon CLI, plugins, AI bundle install)
