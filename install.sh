#!/usr/bin/env bash
set -euo pipefail

BBKIT_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BB_ROOT="${BB_ROOT:-$HOME/BugBounty}"
BB_BIN="$BB_ROOT/bin"
BB_AI_SRC="$BBKIT_SRC/ref/claude-bug-bounty"
BB_AI_DST="$BB_ROOT/ai/bug-bounty"

mkdir -p "$BB_ROOT" "$BB_BIN" "$BB_ROOT/logs" "$BB_ROOT/output" "$BB_ROOT/tools" "$BB_ROOT/ai"
mkdir -p "$BB_ROOT/wordlists"/{dns,content,params,api,resolvers}
mkdir -p "$BB_ROOT/templates"/{nuclei,gf,engagement}
mkdir -p "$BB_ROOT/ref" "$BB_ROOT/engagements" "$BB_ROOT/skills"

echo "[+] Installing BBKit to $BB_ROOT"

sudo apt update || true
sudo apt install -y \
  git curl wget unzip zip jq whois dnsutils build-essential \
  python3 python3-pip python3-venv \
  rustc cargo libpcap-dev nmap dirb gobuster ca-certificates

# Install Go if missing or too old
if ! command -v go >/dev/null 2>&1; then
  echo "[+] Go not found. Installing Go..."
  ARCH="$(uname -m)"
  case "$ARCH" in
    aarch64|arm64) GOARCH="arm64" ;;
    x86_64|amd64) GOARCH="amd64" ;;
    *) echo "Unsupported arch: $ARCH"; exit 1 ;;
  esac
  GO_VERSION="${GO_VERSION:-1.24.4}"
  cd /tmp
  wget -q "https://go.dev/dl/go${GO_VERSION}.linux-${GOARCH}.tar.gz"
  sudo rm -rf /usr/local/go
  sudo tar -C /usr/local -xzf "go${GO_VERSION}.linux-${GOARCH}.tar.gz"
fi

if ! grep -q "BBKit" "$HOME/.bashrc"; then
cat >> "$HOME/.bashrc" <<'EOF'

# BBKit
export BB_ROOT="$HOME/BugBounty"
export GOPATH="$HOME/go"
export PATH="$PATH:/usr/local/go/bin:$HOME/go/bin:$HOME/BugBounty/bin"
EOF
fi

export BB_ROOT="$BB_ROOT"
export GOPATH="$HOME/go"
export PATH="$PATH:/usr/local/go/bin:$HOME/go/bin:$BB_BIN"

# Copy bb CLI and framework files
cp -R "$BBKIT_SRC/lib" "$BB_ROOT/"
cp -R "$BBKIT_SRC/plugins" "$BB_ROOT/"
cp -R "$BBKIT_SRC/recon" "$BB_ROOT/"
cp -R "$BBKIT_SRC/config" "$BB_ROOT/"
cp -R "$BBKIT_SRC/ref" "$BB_ROOT/"
if [[ -d "$BBKIT_SRC/skills" ]]; then
  cp -R "$BBKIT_SRC/skills" "$BB_ROOT/"
fi
if [[ -d "$BBKIT_SRC/templates/engagement" ]]; then
  cp -R "$BBKIT_SRC/templates/engagement" "$BB_ROOT/templates/"
fi
if [[ -d "$BBKIT_SRC/scripts" ]]; then
  mkdir -p "$BB_ROOT/scripts"
  cp -R "$BBKIT_SRC/scripts/." "$BB_ROOT/scripts/" || true
  chmod +x "$BB_ROOT"/scripts/*.sh 2>/dev/null || true
fi
cp "$BBKIT_SRC/bin/bb" "$BB_BIN/bb"
chmod +x "$BB_BIN/bb" "$BB_ROOT"/recon/* || true
# Drop Python caches if any were copied
find "$BB_ROOT/lib" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true

if [[ -d "$BB_AI_SRC" ]]; then
  rm -rf "$BB_AI_DST"
  mkdir -p "$BB_AI_DST"
  for dir in agents commands hooks mcp memory rules skills tools web3; do
    [[ -d "$BB_AI_SRC/$dir" ]] && cp -R "$BB_AI_SRC/$dir" "$BB_AI_DST/"
  done
  for file in AGENTS.md CLAUDE.md OPENCODE.md SKILL.md README.md FAQ.md TERMS.md CHANGELOG.md requirements.txt engine.py brain.py agent.py config.example.json install.sh install_tools.sh uninstall.sh uninstall_tools.sh; do
    [[ -e "$BB_AI_SRC/$file" ]] && cp "$BB_AI_SRC/$file" "$BB_AI_DST/$file"
  done
fi

echo "[+] Installing core tools..."
"$BB_BIN/bb" update

if [[ -f "$BB_AI_DST/requirements.txt" ]]; then
  echo "[+] Installing AI runtime dependencies..."
  python3 -m pip install --user -U -r "$BB_AI_DST/requirements.txt" certifi ollama || true
fi

if [[ -x "$BB_ROOT/recon/ai-sync" ]]; then
  echo "[+] Syncing Claude Code, Codex, .agents, and Factory Droid assets..."
  "$BB_BIN/bb" ai sync || true
fi

echo "[+] Done."
echo "Run:"
echo "  source ~/.bashrc"
echo "  bb doctor"
echo "  bb scope new my-program   # edit engagements/.../scope.md"
echo "  bb scope use my-program"
echo "  bb full in-scope.example.com"
echo "  bb ai sync                # Claude + web3 + bbkit skill"
