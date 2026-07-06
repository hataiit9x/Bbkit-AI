# BBKit

BBKit is a lightweight Bug Bounty workstation and recon framework for Linux, optimized for Ubuntu/Debian, ARM64, x86_64, VPS, and Oracle Cloud ARM.

## Goals

- One-command installation
- Works on ARM64 and x86_64
- Plugin-based tool management
- Automated recon workflows
- Clean output structure
- Easy to extend
- Future-ready for AI reports and dashboard

## Quick Start

```bash
chmod +x install.sh
./install.sh
source ~/.bashrc
bb doctor
```

Run recon:

```bash
bb full example.com
```

Output:

```text
~/BugBounty/output/example.com/
```

## Commands

```bash
bb help
bb doctor
bb update
bb version

bb subs example.com
bb alive example.com
bb urls example.com
bb js example.com
bb port example.com
bb nuclei example.com
bb report example.com
bb full example.com
```

## Legal Notice

Use BBKit only on assets you own or have explicit permission to test.
