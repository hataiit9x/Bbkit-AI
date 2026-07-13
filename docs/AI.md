# AI integration

## Bundles

| Path | Content |
|------|---------|
| `$BB_ROOT/ai/bug-bounty` | Tools/skills/commands from `ref/claude-bug-bounty` |
| `$BB_ROOT/ai/web3-skills` | Cloned on `bb ai sync` (web3 bug classes, Foundry, …) |
| `$BB_ROOT/skills/bbkit` | Thin orchestrator — prefer this as agent entry |

## Commands

```bash
bb ai sync      # push skills to Claude Code, Codex, .agents, Factory; fetch web3
bb ai doctor    # path checks
bb ai run <tool> [args…]
bb hunt | validate | intel | arsenal
```

## Agent guidance (Grok Build / Claude)

1. Load **bbkit** skill first (scope gate + engage workflow).  
2. Operator prompt with program URL → run **`bb engage <url> [--slug …]`** (not free-form folder invent).  
3. Read `engagements/<slug>/{scope,checklist,pipeline}.md`; run **host CLI tools**; reason on outputs.  
4. Findings → `findings/` + `poc/`; final pass `triager-review.md`.  
5. Lazy-load web2 monolit / web3 classes only for the active mode.  
6. Do not dump full payload bibles into every turn. Dashboard UI is optional.

## Prompt starter

```text
Use bbkit skill. Authorized only.
bb engage 'https://cantina.xyz/code/<id>/overview' --slug <name>
Then follow checklist.md + pipeline.md (CLI first). Findings + PoC; triager-review last.
```

## Future

- Tighter agent-handoff → multi-turn memory of leads (optional)
