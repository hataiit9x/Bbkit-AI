# Recon Pipeline

```mermaid
flowchart LR
  A[Subdomains] --> B[Resolved]
  B --> C[Alive]
  C --> D[URLs]
  D --> E[JS]
  C --> F[Ports]
  C --> G[Nuclei]
  E --> H[Report]
  G --> H
```
