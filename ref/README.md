# Vendor / reference material

## `claude-bug-bounty/`

Sparse vendored copy of [shuvonsec/claude-bug-bounty](https://github.com/shuvonsec/claude-bug-bounty) (MIT).

**Kept** (used by `install.sh` → `$BB_ROOT/ai/bug-bounty`):

- `agents/`, `commands/`, `skills/`, `tools/`, `hooks/`, `mcp/`, `memory/`, `rules/`, `web3/`
- Core docs/runtime: `SKILL.md`, `AGENTS.md`, `engine.py`, `brain.py`, …

**Intentionally omitted** (bloat / not needed at runtime):

- `site/` (marketing HTML)
- `demo/` (local vulnerable app)
- `logo.png`
- `tests/`
- `wordlists/` (BBKit uses its own `$BB_ROOT/wordlists`)

To refresh from upstream without re-adding bloat:

```bash
./scripts/sparse-vendor-sync.sh
```
