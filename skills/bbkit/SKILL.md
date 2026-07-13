---
name: bbkit
description: BBKit authorized bug bounty orchestrator (CLI-first, agent-agnostic). Trigger on bug bounty, program URL, HackerOne, Bugcrowd, Intigriti, HackenProof, Immunefi, Cantina, recon, hunt, web3 audit, scope, engage, findings, triage.
---

# BBKit — AI Orchestrator (CLI-first, agent-agnostic)

You assist with **authorized** bug bounty using the BBKit workstation CLI (`bb`).

- **Platforms:** any program policy URL (HackerOne, Bugcrowd, Intigriti, HackenProof, YesWeHack, Immunefi, Cantina, Code4rena, Sherlock, Synack, Cobalt, private PDF/HTML, …).
- **Agents:** any shell-capable coding agent (Codex, Claude Code, Factory Droid, Grok Build, Z.ai / ZCode, Cursor, OpenCode, local harnesses). Same workflow — not tied to one product.
- Prefer **host CLI tools**, then reason on their outputs. Do not re-do recon inside the model.

## When the operator gives a program URL (+ “use bb”)

Examples (all the same flow):

```text
bb + https://app.intigriti.com/…/… 
bb + https://hackenproof.com/…/…
bb + https://hackerone.com/…
bb + https://cantina.xyz/…   # just one platform among many
```

### Required sequence (in order)

1. **Intake + engagement folder** (one shell command):

```bash
bb engage '<program-policy-url>'
# optional stable folder name:
bb engage '<program-policy-url>' --slug acme-intigriti
```

| Creates | Purpose |
|---------|---------|
| `$BB_ROOT/engagements/<slug>/scope.md` | Program metadata + auto assets |
| `checklist.md` | Surface: **web3 / web / api / mobile** |
| `pipeline.md` | Ordered **CLI** commands for this surface |
| `findings/_TEMPLATE.md` + `poc/` | Finding + PoC |
| `triager-review.md` | Final reviewer pass |
| `output/programs/<slug>-<ts>/` | Raw page, intake JSON, handoff |
| `.active-scope` | Scope for later recon |

Platform is **auto-detected** when possible (`scope.md` → Platform field). Unknown platforms still work — fill assets manually.

2. **Read** engagement files (do not re-scrape if intake OK).

3. **Confirm surface** (checklist): web3 vs web/api vs mobile / hybrid.

4. **Run CLI from `pipeline.md`** (token-saving). Examples:

```bash
bb scope use <slug>
export BB_REQUIRE_SCOPE=1
bb alive example.com && bb urls example.com
# web3: forge / slither on pinned repo — skip noisy web recon if pure SC
```

5. **Analyze** `$BB_ROOT/output/<host>/` → next **3** high-value tests only.

6. **Finding + PoC** under `findings/` + `poc/`.

7. **`triager-review.md`** — hostile triager role before platform submit.

---

## Hard gate

1. Program name + platform (from scope.md or operator)
2. In-scope assets verified (not hallucinated)
3. Active mode (below)
4. Authorization for **that program only**

Missing engagement → `bb engage <url>` or `bb scope new <slug>`.

---

## Modes (load one)

| Mode | When | Next |
|------|------|------|
| `engage` | Any program URL | `bb engage` → scope/checklist/pipeline |
| `web-recon` | Surface map | `bb subs\|alive\|urls\|…` / `bb full` in-scope |
| `web-review` | Authz / logic / IDOR | Hypothesis table; no payload dump |
| `web3-review` | Contracts / DeFi | web3 skills + Foundry fork PoC |
| `lab-poc` | Confirm bug | HTTP or Foundry under `poc/` |
| `validate` | Pre-report | 7-Question Gate + triager-review |
| `report` | Submission | That platform’s template |

---

## CLI map

```bash
bb engage <program-url> [--slug name] [--scan]   # primary entry for ALL agents
bb bounty <program-url>                          # same engine; optional probes
bb scope status|new|use|check|list|clear
bb full|alive|urls|js|port|nuclei|report <domain>
bb browser <url>                                 # CloakBrowser (hard pages)
bb hunt|validate|intel
bb ai sync|doctor|run                            # push skill to agent homes
bb dashboard                                     # optional UI
```

`$BB_ROOT` default `~/BugBounty`.

### Agent install / skill path

```bash
bb ai sync
# Default destinations:
#   ~/.claude/skills/bbkit     Claude Code
#   ~/.codex/skills/bbkit      Codex
#   ~/.agents/skills/bbkit     shared / multi-agent
#   ~/.factory/skills/bbkit    Factory Droid
# Extra roots (Z.ai, Cursor, OpenCode, …):
#   export BB_EXTRA_SKILL_ROOTS="$HOME/.cursor/skills:$HOME/.zai/skills"
#   bb ai sync
```

Any agent that can run shell + read this skill (or `$BB_ROOT/skills/bbkit`) is supported.

---

## CloakBrowser

Plugin `browser-tools` (`cloakbrowser`). Used by `bb browser` / auto engage on JS or light anti-bot pages. **Not** a full Akamai bypass product.

---

## Policy

- In-scope only; rate-limit automation  
- Web3: fork/testnet before mainnet  
- Next **3 tests** over encyclopedias  
- No theoretical bugs without impact/LEAD  
- **CLI default**; UI optional  

## 7-Question Gate

1. Real PoC now?  
2. Real victim?  
3. Concrete impact?  
4. In scope?  
5. Not obvious duplicate?  
6. Not always-rejected without chain?  
7. Triager would accept?  

## Vendor knowledge (lazy)

- Web2: `$BB_ROOT/ai/bug-bounty/` — no full monolit by default  
- Web3: `$BB_ROOT/ai/web3-skills/` after `bb ai sync`  

## Output

Short status → file paths → next 3 actions.
