#!/usr/bin/env bash

BB_ROOT="${BB_ROOT:-$HOME/BugBounty}"
BB_BIN="$BB_ROOT/bin"
BB_TOOLS="$BB_ROOT/tools"
BB_OUTPUT="$BB_ROOT/output"
BB_WORDLISTS="$BB_ROOT/wordlists"
BB_TEMPLATES="$BB_ROOT/templates"
BB_REF="$BB_ROOT/ref"
BB_AI_ROOT="$BB_ROOT/ai/bug-bounty"

mkdir -p "$BB_BIN" "$BB_TOOLS" "$BB_OUTPUT" "$BB_WORDLISTS" "$BB_TEMPLATES" "$BB_ROOT/logs"

export GOPATH="${GOPATH:-$HOME/go}"
export PATH="/usr/local/go/bin:$GOPATH/bin:$BB_BIN:$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
if [[ -d "$BB_AI_ROOT" ]]; then
  export PYTHONPATH="$BB_AI_ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

log() { echo -e "[+] $*"; }
warn() { echo -e "[!] $*" >&2; }
err() { echo -e "[x] $*" >&2; }

need_cmd() {
  [[ $# -gt 0 ]] || return 1
  command -v "$1" >/dev/null 2>&1
}

install_go_tool() {
  local pkg="${1:-}"
  [[ -n "$pkg" ]] || {
    warn "install_go_tool called without package"
    return 1
  }
  log "go install $pkg"
  go install "$pkg" || warn "failed: $pkg"
}

pip_install() {
  [[ $# -gt 0 ]] || {
    warn "pip_install called without packages"
    return 1
  }
  if python3 -m pip install --user -U "$@" 2>/tmp/bbkit-pip.err; then
    rm -f /tmp/bbkit-pip.err
    return 0
  fi
  if grep -qi "externally-managed-environment" /tmp/bbkit-pip.err 2>/dev/null; then
    warn "pip is externally managed, retrying with --break-system-packages: $*"
    python3 -m pip install --user -U --break-system-packages "$@" || warn "pip install failed: $*"
  else
    cat /tmp/bbkit-pip.err >&2 || true
    warn "pip install failed: $*"
  fi
  rm -f /tmp/bbkit-pip.err
}

download_once() {
  local url="${1:-}"
  local out="${2:-}"
  [[ -n "$url" && -n "$out" ]] || {
    warn "download_once called without url/output"
    return 1
  }
  mkdir -p "$(dirname "$out")"
  if [[ -f "$out" ]]; then
    log "exists: $out"
  else
    wget -q -O "$out" "$url" || warn "download failed: $url"
  fi
}

require_target() {
  if [[ $# -lt 1 || -z "${1:-}" ]]; then
    err "target required"
    exit 1
  fi
}
