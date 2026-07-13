# Dashboard

Lightweight stdlib Python UI listing recon outputs and engagements.

```bash
bb dashboard
# http://127.0.0.1:8787/

bb dashboard --host 0.0.0.0 --port 9000
```

- `/` — HTML index  
- `/output/<target>/report.html` — reports  
- `/engagements/<slug>/scope.md` — scope files  
- `/api/targets`, `/api/engagements` — JSON  

Config: `dashboard.host` / `dashboard.port` in `config.yaml`.
