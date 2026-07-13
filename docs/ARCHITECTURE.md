# Architecture

```mermaid
flowchart TD
  A[bb CLI] --> S[Scope gate]
  S --> B[Command Dispatcher]
  B --> C[Recon Workflows]
  B --> D[Plugin Manager]
  B --> I[AI sync / hunt tools]
  D --> E[Tools on PATH]
  C --> F[Output under BB_ROOT/output]
  I --> J[Claude Codex agents skills]
  I --> K[Web3 skill pack]
  I --> L[bbkit thin orchestrator]
```

## Components

- `bin/bb` — main CLI dispatcher  
- `lib/common.sh` — logging, tool helpers, **scope allowlist**  
- `lib/program_hunt.py` — program-oriented helpers (`bb bounty`)  
- `plugins/` — install/update/doctor for external tools  
- `recon/` — workflows (subs, full, scope, ai-sync, …)  
- `skills/bbkit/` — thin AI orchestrator (scope-first modes)  
- `templates/engagement/` — scope.md templates  
- `ref/claude-bug-bounty/` — vendored AI methodology (upstream MIT)  
- Runtime `$BB_ROOT` (`~/BugBounty`) — output, engagements, installed AI  
- `config/config.yaml` → `load_bb_config`  
- `lib/dashboard.py` + `bb dashboard`  
- `Dockerfile` / `docker-compose.yml` for VPS  

