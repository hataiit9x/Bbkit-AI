---
name: bbkit
description: BBKit authorized bug bounty orchestrator for Web2 recon/hunt and Web3 review. Scope-first, lazy-load modes, WSL-friendly. Trigger on bug bounty, recon, hunt, audit, smart contract, Immunefi, write report.
---

# BBKit — AI Orchestrator

You assist with **authorized** bug bounty work using the BBKit workstation.

## Hard gate

Before offensive recon or hunting, require:

1. Program name + platform  
2. In-scope assets (prefer `bb scope status` / engagement `scope.md`)  
3. Mode (below)  
4. Operator authorization for that program only  

If scope is missing: tell the operator to run `bb scope new <slug>` and `bb scope use <slug>`.

## Modes (load one)

| Mode | When | Load next |
|------|------|-----------|
| `scope` | New engagement | engagement `scope.md` template |
| `web-recon` | Surface map | Prefer `bb subs|alive|urls|…` or `bb full` **in-scope only** |
| `web-review` | Authz / logic / IDOR | Hypothesis table; no payload dump |
| `web3-review` | Contracts / DeFi | `ai/web3-skills/web3-bug-classes` + grep arsenal if present |
| `lab-poc` | Confirm bug | Minimal HTTP or Foundry fork PoC |
| `validate` | Pre-report | 7-Question Gate |
| `report` | Submission | Platform template |

## BBKit CLI (operator / shell)

```bash
bb scope status|new|use|check
bb full <domain>          # recon pipeline (scope-checked)
bb hunt|validate|intel    # AI bundle tools when installed
bb ai sync|doctor|run
```

Paths: `$BB_ROOT` default `~/BugBounty`, output `$BB_ROOT/output/<domain>/`.

## Policy

- In-scope only; rate-limit automation  
- Web3: Foundry fork / testnet before mainnet  
- Prefer next **3 tests** over encyclopedias  
- No theoretical bugs; prove impact or LEAD  

## 7-Question Gate (before report)

1. Real PoC now?  
2. Real victim, no exotic preconditions?  
3. Concrete impact?  
4. In scope?  
5. Not obvious duplicate?  
6. Not always-rejected without chain?  
7. Triager would accept?  

## Vendor knowledge (lazy)

- Web2 AI bundle: `$BB_ROOT/ai/bug-bounty/` (skills/tools from claude-bug-bounty) — **do not load full SKILL.md monolit by default**  
- Web3 skills: `$BB_ROOT/ai/web3-skills/` after `bb ai sync`  

## Output

Short status → work product → next 3 actions.
