# Docker

## Build

```bash
docker build -t bbkit:0.4 .
```

## Run recon

```bash
docker run --rm --network host \
  -v "$PWD/out:/data/BugBounty/output" \
  -v "$PWD/eng:/data/BugBounty/engagements" \
  bbkit:0.4 full --passive-only example.com
```

## Dashboard

```bash
docker run --rm -p 8787:8787 \
  -v "$PWD/out:/data/BugBounty/output" \
  -v "$PWD/eng:/data/BugBounty/engagements" \
  bbkit:0.4 dashboard --host 0.0.0.0 --port 8787
```

## Compose

```bash
docker compose build
docker compose run --rm bbkit doctor
docker compose up dashboard
```

Notes:

- Image includes core Go recon tools; full plugin set still better on bare WSL/VPS via `./install.sh`.
- Mount `output` + `engagements` for persistence.
- Prefer `BB_REQUIRE_SCOPE=1` on shared VPS.
