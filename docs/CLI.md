# CLI Reference

```bash
bb help
bb doctor
bb update
bb version

# Engagement (Grok / CLI-first)
bb engage <program-url> [--slug name] [--scan] [--browser auto|off|standard]
bb bounty <program-url> [same program_hunt flags]
bb scope status|list|new <slug>|use <slug>|check <host>|clear
bb browser <url>

# Recon (scope-checked when active)
bb subs example.com
bb alive example.com
bb urls example.com
bb js example.com
bb port example.com
bb nuclei example.com
bb report example.com
bb full example.com
bb full --passive-only|--no-ports|--no-nuclei|--severity LIST|--rate N|--threads N example.com

# Config / optional UI
bb config
bb dashboard [--host 127.0.0.1] [--port 8787]

# AI bundle
bb ai sync|doctor|run <tool> …
bb hunt|validate|intel|scan-cves|arsenal
```

## Grok Build workflow (Cantina example)

```bash
bb engage 'https://cantina.xyz/code/<uuid>/overview' --slug my-program
# → ~/BugBounty/engagements/my-program/{scope,checklist,pipeline,triager-review}.md
# → findings/_TEMPLATE.md, poc/
# → scope activated

# Then AI reads checklist + pipeline, runs e.g.:
bb alive <in-scope-host>
bb urls <in-scope-host>
# Web3: use forge/slither on pinned repo; skip noisy web scan if pure SC

# Finding:
cp ~/BugBounty/engagements/my-program/findings/_TEMPLATE.md \
   ~/BugBounty/engagements/my-program/findings/001-title.md
# PoC under …/poc/
# Fill triager-review.md before submit
```

## engage vs bounty

| Command | Default | Use when |
|---------|---------|----------|
| `bb engage` | Intake + engagement bundle, **no** auto scan | Grok Build / agent start |
| `bb bounty` | Same engine; may run scoped probes | Want automatic first-pass probes |
| `bb engage … --scan` | Engage + probes | Hybrid |

## CloakBrowser

```bash
bb plugins …   # or install browser-tools via doctor/plugins
bb browser 'https://hard-page.example'
```

Renders JS / light anti-bot pages. Not a full Akamai bypass product.

## Paths

```text
$BB_ROOT/engagements/<slug>/
$BB_ROOT/output/<domain>/
$BB_ROOT/output/programs/<slug>-<timestamp>/
$BB_ROOT/config/config.yaml
```
