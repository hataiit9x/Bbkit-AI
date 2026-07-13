---
name: bbkit
description: BBKit authorized bug bounty orchestrator (CLI-first). Trigger on bug bounty, Cantina, Immunefi, HackerOne, recon, hunt, web3 audit, scope, engage, findings, triage.
---

# BBKit — AI Orchestrator (CLI-first)

You assist with **authorized** bug bounty using the BBKit workstation CLI (`bb`). Prefer **machine tools on the host**, then reason on their outputs — do not re-do recon inside the model.

## When the operator says: use bb + program URL

Example:

```text
Dùng bb, chương trình:
https://cantina.xyz/code/<id>/overview
```

### Required sequence (do this, in order)

1. **Intake + engagement folder** (one shell command):

```bash
bb engage 'https://cantina.xyz/code/<id>/overview'
# optional stable name:
bb engage 'https://…' --slug rogo-recon
```

This command:

| Creates | Purpose |
|---------|---------|
| `~/BugBounty/engagements/<slug>/scope.md` | Program metadata + auto assets from page |
| `checklist.md` | Surface checklist: **web3 / web / api / mobile** |
| `pipeline.md` | Ordered **CLI** commands for this surface |
| `findings/_TEMPLATE.md` + `poc/` | Finding + PoC discipline |
| `triager-review.md` | Final reviewer pass |
| `output/programs/<slug>-<ts>/` | Raw HTML, intake JSON, report, agent-handoff |
| `.active-scope` | Activates scope for later `bb full` / recon |

2. **Read** (do not re-scrape the program page if intake succeeded):

- `engagements/<slug>/scope.md`
- `engagements/<slug>/checklist.md`
- `engagements/<slug>/pipeline.md`
- intake `report.md` / `program-intake.md` under `output/programs/…`

3. **Classify surface** from checklist (confirm auto labels):

| Label | Typical work |
|-------|----------------|
| **web3** | Repo/contracts, roles, slither/forge; **skip** noisy web recon unless domains in-scope |
| **web / api** | `bb alive` → `bb urls` → optional `bb nuclei`; then authz/IDOR/logic |
| **mobile** | Map backend API; test authz on in-scope hosts only |

4. **Run CLI tools from `pipeline.md`** (host tools = cheap tokens). Examples:

```bash
bb scope use <slug>
export BB_REQUIRE_SCOPE=1
bb alive example.com
bb urls example.com
# web3: forge test / slither on pinned repo (operator machine)
```

5. **Analyze outputs** under `$BB_ROOT/output/<host>/` and intake workspace. Propose **next 3** high-value tests only.

6. **Finding → file + PoC**:

```bash
cp engagements/<slug>/findings/_TEMPLATE.md \
   engagements/<slug>/findings/001-short-title.md
# write PoC under engagements/<slug>/poc/
```

7. **Triager / Reviewer pass** — fill `triager-review.md` (hostile to weak reports). 7-question gate before any platform submit.

---

## Hard gate

Before offensive recon/hunt:

1. Program name + platform (from scope.md)
2. In-scope assets verified (not hallucinated)
3. Active mode (below)
4. Operator authorization for **that program only**

If no engagement yet: run `bb engage <url>` (preferred) or `bb scope new <slug>`.

---

## Modes (load one)

| Mode | When | Next |
|------|------|------|
| `engage` | New program URL | `bb engage` → scope/checklist/pipeline |
| `web-recon` | Surface map | `bb subs\|alive\|urls\|…` or `bb full` **in-scope** |
| `web-review` | Authz / logic / IDOR | Hypothesis table; no payload dump |
| `web3-review` | Contracts / DeFi | web3-bug-classes + grep; Foundry fork PoC |
| `lab-poc` | Confirm bug | Minimal HTTP or Foundry PoC under `poc/` |
| `validate` | Pre-report | 7-Question Gate + triager-review.md |
| `report` | Submission | Platform template |

---

## BBKit CLI map

```bash
bb engage <program-url> [--slug name] [--scan]   # primary Grok entry
bb bounty <program-url>                          # same engine; may probe more
bb scope status|new|use|check|list|clear
bb full <domain>                                 # recon pipeline (scope-checked)
bb alive|urls|js|port|nuclei|report <domain>
bb browser <url>                                 # CloakBrowser render (hard pages)
bb hunt|validate|intel                           # AI bundle tools when installed
bb ai sync|doctor|run
bb dashboard                                     # optional UI — not required for CLI hunt
```

Paths: `$BB_ROOT` default `~/BugBounty`.

---

## CloakBrowser / anti-bot (honest)

- Installed via plugin `browser-tools` (`cloakbrowser` Python).
- Used by `bb browser` and auto in `bb engage` / `bb bounty` when the program page looks like JS shell or CF-style challenge.
- **Not** a dedicated Akamai WAF exploit/bypass toolkit — browser automation for authorized page rendering. If bot wall persists, operator may need credentials, VPN, or manual export of HTML.

---

## Policy

- In-scope only; rate-limit automation  
- Web3: Foundry fork / testnet before mainnet  
- Prefer next **3 tests** over encyclopedias  
- No theoretical bugs; prove impact or mark LEAD  
- UI/dashboard optional — **CLI is the default path**

---

## 7-Question Gate (before report)

1. Real PoC now?  
2. Real victim, no exotic preconditions?  
3. Concrete impact?  
4. In scope?  
5. Not obvious duplicate?  
6. Not always-rejected without chain?  
7. Triager would accept?  

---

## Vendor knowledge (lazy)

- Web2 AI bundle: `$BB_ROOT/ai/bug-bounty/` — **do not load full monolit by default**  
- Web3 skills: `$BB_ROOT/ai/web3-skills/` after `bb ai sync`  

## Output style

Short status → work product (paths to files) → next 3 actions.
