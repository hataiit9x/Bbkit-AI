#!/usr/bin/env bash
# Refresh ref/claude-bug-bounty sparsely (no site/demo/logo/tests/wordlists).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/ref/claude-bug-bounty"
URL="${CLAUDE_BB_URL:-https://github.com/shuvonsec/claude-bug-bounty.git}"
TMP="$(mktemp -d)"

cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

echo "[+] Sparse clone $URL"
git clone --depth 1 "$URL" "$TMP/src"

KEEP=(
  agents commands skills tools hooks mcp memory rules web3
  AGENTS.md CLAUDE.md OPENCODE.md SKILL.md README.md FAQ.md TERMS.md
  CHANGELOG.md requirements.txt engine.py brain.py agent.py
  config.example.json install.sh install_tools.sh uninstall.sh uninstall_tools.sh
  docs
)

rm -rf "$DEST"
mkdir -p "$DEST"

for item in "${KEEP[@]}"; do
  if [[ -e "$TMP/src/$item" ]]; then
    cp -R "$TMP/src/$item" "$DEST/"
    echo "  + $item"
  fi
done

# Drop nested heavy docs images if any
find "$DEST" -name '*.png' -o -name '*.jpg' -o -name '*.gif' 2>/dev/null | while read -r f; do
  rm -f "$f" && echo "  - removed image $f"
done

echo "[+] Done: $DEST ($(du -sh "$DEST" | awk '{print $1}'))"
