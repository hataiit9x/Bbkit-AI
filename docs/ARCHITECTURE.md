# Architecture

```mermaid
flowchart TD
  A[bb CLI] --> B[Command Dispatcher]
  B --> C[Recon Workflows]
  B --> D[Plugin Manager]
  D --> E[Tools]
  C --> F[Output Manager]
  F --> G[HTML Report]
  F --> H[Future AI Engine]
```

## Components

- `bin/bb`: main CLI.
- `lib/common.sh`: shared helper functions.
- `plugins/`: tool installation, update, and doctor definitions.
- `recon/`: workflow commands.
- `wordlists/`: DNS/content/parameter/API wordlists.
- `templates/`: nuclei and gf templates.
- `output/`: scan results.
