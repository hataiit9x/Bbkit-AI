# AI integration

BBKit is **CLI-first** and **agent-agnostic**. Any model/agent that can run shell commands can drive a hunt; skills are optional glue.

## Bundles

| Path | Content |
|------|---------|
| `$BB_ROOT/ai/bug-bounty` | Tools/skills/commands from `ref/claude-bug-bounty` |
| `$BB_ROOT/ai/web3-skills` | Cloned on `bb ai sync` |
| `$BB_ROOT/skills/bbkit` | Thin orchestrator — prefer as agent entry |

## Multi-agent sync

```bash
bb ai sync      # push bbkit (+ vendor skills) to agent homes
bb ai doctor
bb ai run <tool> [args…]
bb hunt | validate | intel | arsenal
```

Default destinations:

| Home | Typical product |
|------|-----------------|
| `~/.claude/` | Claude Code |
| `~/.codex/` | OpenAI Codex CLI |
| `~/.agents/` | Shared skills (multi-tool) |
| `~/.factory/` | Factory Droid |

Extra products (Z.ai / ZCode, Cursor, OpenCode, custom harnesses):

```bash
export BB_EXTRA_SKILL_ROOTS="$HOME/.cursor/skills:$HOME/.zai/skills:$HOME/.opencode/skills"
bb ai sync
```

Override roots: `BB_CLAUDE_ROOT`, `BB_CODEX_ROOT`, `BB_AGENTS_ROOT`, `BB_FACTORY_ROOT`.

## Platforms (not agent-specific)

`bb engage <program-url>` works for **any** policy page URL. Auto platform labels include HackerOne, Bugcrowd, Intigriti, HackenProof, YesWeHack, Immunefi, Cantina, Code4rena, Sherlock, Synack, Cobalt, and more. Unknown hosts still create a full engagement folder.

## Agent workflow (all agents)

1. Load **bbkit** skill if available (or just use `bb` on PATH).  
2. Operator gives program URL → **`bb engage <url> [--slug …]`**.  
3. Read `engagements/<slug>/{scope,checklist,pipeline}.md`.  
4. Run **host CLI**; reason on outputs (token-saving).  
5. Findings → `findings/` + `poc/`; `triager-review.md` last.  
6. Lazy-load web2/web3 vendor skills only for the active mode.  

## Prompt starter (copy into any agent)

```text
Use bbkit skill if installed. Authorized only.
bb engage '<PROGRAM_POLICY_URL>' --slug <name>
Follow checklist.md + pipeline.md (CLI tools first).
Findings + PoC; triager-review before submit.
Platform does not matter — same flow for Intigriti, HackenProof, H1, web3 contests, …
```

## Policy

- Do not dump full payload bibles every turn.  
- Dashboard UI is optional.  
- Prefer next 3 tests over monolit skill load.
