# Validate gate (BBKit)

All YES or stop:

| # | Question |
|---|----------|
| Q1 | Reproduce right now (HTTP / forge)? |
| Q2 | Real user/protocol, no exotic preconditions? |
| Q3 | Concrete impact (funds, PII, ATO, RCE)? |
| Q4 | In scope? |
| Q5 | Not obvious duplicate? |
| Q6 | Not always-rejected without chain? |
| Q7 | Tired triager would accept? |

**Always rejected alone:** missing headers only, open redirect alone, GraphQL introspection alone, SSRF DNS-only, self-XSS, etc.
