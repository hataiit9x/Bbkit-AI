# CLI Reference

```bash
bb help
bb doctor
bb update
bb version

# Engagement (any platform URL — CLI-first)
bb engage <program-url> [--slug name] [--scan] [--browser auto|off|standard]
bb bounty <program-url> [program_hunt flags]
bb scope status|list|new <slug>|use <slug>|check <host>|clear
bb browser <url>

# Recon (scope-checked when active)
bb subs|alive|urls|js|port|nuclei|report|full <domain>
bb full --passive-only|--no-ports|--no-nuclei|--severity LIST|--rate N|--threads N <domain>

# Config / optional UI
bb config
bb dashboard [--host 127.0.0.1] [--port 8787]

# AI bundle (multi-agent sync)
bb ai sync|doctor|run <tool> …
bb hunt|validate|intel|scan-cves|arsenal
```

## Agent workflow (platform-agnostic)

Works the same for Intigriti, HackenProof, HackerOne, Bugcrowd, YesWeHack, Immunefi, Cantina, Code4rena, private programs, …

```bash
bb engage 'https://app.intigriti.com/…/…' --slug acme-intigriti
# or
bb engage 'https://hackenproof.com/…' --slug acme-hp
# → $BB_ROOT/engagements/<slug>/{scope,checklist,pipeline,triager-review}.md
# → findings/_TEMPLATE.md, poc/ ; scope activated

# Agent (Codex / Claude / Factory / Grok / Z.ai / …) reads checklist + pipeline, runs CLI:
bb alive <in-scope-host>
bb urls <in-scope-host>

# Finding:
cp $BB_ROOT/engagements/<slug>/findings/_TEMPLATE.md \
   $BB_ROOT/engagements/<slug>/findings/001-title.md
# fill triager-review.md before submit
```

## engage vs bounty

| Command | Default | Use when |
|---------|---------|----------|
| `bb engage` | Intake + engagement, **no** auto scan | Any agent start |
| `bb bounty` | Same engine; may probe | Auto first-pass probes |
| `bb engage … --scan` | Engage + probes | Hybrid |

## Platforms

`bb engage` auto-tags platform when the URL/host is known (HackerOne, Bugcrowd, Intigriti, HackenProof, YesWeHack, Immunefi, Cantina, Code4rena, Sherlock, CodeHawks, Synack, Cobalt, …). Unknown URL → Platform `unknown`; still creates engagement — fill scope manually.

## Agents

| Agent | Skill after `bb ai sync` |
|-------|---------------------------|
| Claude Code | `~/.claude/skills/bbkit` |
| Codex | `~/.codex/skills/bbkit` |
| Factory Droid | `~/.factory/skills/bbkit` |
| Shared | `~/.agents/skills/bbkit` |
| Z.ai / Cursor / OpenCode / others | set `BB_EXTRA_SKILL_ROOTS` then `bb ai sync` |

Shell-only (no skill path): operator pastes “use `bb engage <url>` then checklist” — still works.

## CloakBrowser

```bash
bb browser 'https://hard-page.example'
```

Light anti-bot / JS render. Not a full Akamai bypass product.

## Paths

```text
$BB_ROOT/engagements/<slug>/
$BB_ROOT/output/<domain>/
$BB_ROOT/output/programs/<slug>-<timestamp>/
$BB_ROOT/config/config.yaml
```
