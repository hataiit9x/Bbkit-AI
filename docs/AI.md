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

## Agent guidance

1. Load **bbkit** skill first (scope gate).  
2. Lazy-load web2 monolit / web3 classes only for the active mode.  
3. Do not dump full payload bibles into every turn.  

## Future

- `bb ai report <domain>` summarizing recon output (planned v0.3+)
