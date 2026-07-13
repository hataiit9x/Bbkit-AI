# Config

File: `$BB_ROOT/config/config.yaml` (repo default: `config/config.yaml`).

Loaded automatically via `lib/common.sh` → `load_bb_config` (Python stdlib).  
**Environment variables win** if already set.

| YAML | Env | Used by |
|------|-----|---------|
| `threads` | `BB_THREADS` | subfinder, dnsx, katana, nuclei, gospider |
| `rate_limit` | `BB_RATE` | httpx, naabu, nuclei |
| `output` | `BB_OUTPUT` | all recon |
| `wordlists` | `BB_WORDLISTS` | wordlist paths |
| `require_scope` | `BB_REQUIRE_SCOPE` | scope gate |
| `recon.katana_depth` | `BB_KATANA_DEPTH` | urls |
| `recon.naabu_top_ports` | `BB_NAABU_TOP_PORTS` | port |
| `recon.httpx_threads` | `BB_HTTPX_THREADS` | alive |
| `recon.gau_threads` | `BB_GAU_THREADS` | urls |
| `recon.passive_only` | `BB_RECON_PASSIVE_ONLY` | full defaults |
| `recon.ports` / `nuclei` | `BB_RECON_PORTS` / `BB_RECON_NUCLEI` | full defaults |
| `nuclei.severity` | `BB_NUCLEI_SEVERITY` | nuclei, full |
| `resolvers.file` | `BB_RESOLVERS_FILE` | subfinder, dnsx |
| `dashboard.host/port` | `BB_DASH_HOST` / `BB_DASH_PORT` | dashboard |

```bash
bb config          # show effective values
```
