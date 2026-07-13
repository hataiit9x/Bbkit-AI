# Scope & engagements

## Why

Recon without an allowlist risks out-of-program scanning. BBKit optional scope keeps you honest.

## Workflow

```bash
bb scope new acme-h1
$EDITOR ~/BugBounty/engagements/acme-h1/scope.md   # list domains / contracts
bb scope use acme-h1
bb scope check api.acme.com
bb full acme.com
```

## Enforcement

| Mode | Behavior |
|------|----------|
| Default | Warn if no scope; **block** if scope active and host not listed |
| `BB_REQUIRE_SCOPE=1` | Also **block** if no active scope |

## Files

- Templates: `templates/engagement/`
- Runtime: `$BB_ROOT/engagements/<slug>/`
- Pointer: `$BB_ROOT/.active-scope`
