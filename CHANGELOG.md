# Changelog

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
