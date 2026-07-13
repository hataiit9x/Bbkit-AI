#!/usr/bin/env bash

BB_ROOT="${BB_ROOT:-$HOME/BugBounty}"
BB_BIN="$BB_ROOT/bin"
BB_TOOLS="$BB_ROOT/tools"
BB_OUTPUT="$BB_ROOT/output"
BB_WORDLISTS="$BB_ROOT/wordlists"
BB_TEMPLATES="$BB_ROOT/templates"
BB_REF="$BB_ROOT/ref"
BB_AI_ROOT="$BB_ROOT/ai/bug-bounty"
BB_ENGAGEMENTS="${BB_ENGAGEMENTS:-$BB_ROOT/engagements}"
BB_ACTIVE_SCOPE="${BB_ACTIVE_SCOPE:-$BB_ROOT/.active-scope}"
BB_SKILLS_ROOT="${BB_SKILLS_ROOT:-$BB_ROOT/skills}"
BB_WEB3_ROOT="${BB_WEB3_ROOT:-$BB_ROOT/ai/web3-skills}"

mkdir -p "$BB_BIN" "$BB_TOOLS" "$BB_OUTPUT" "$BB_WORDLISTS" "$BB_TEMPLATES" "$BB_ROOT/logs" "$BB_ENGAGEMENTS"

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

# Active engagement scope file (path), if any.
active_scope_file() {
  if [[ -n "${BB_SCOPE_FILE:-}" && -f "$BB_SCOPE_FILE" ]]; then
    echo "$BB_SCOPE_FILE"
    return 0
  fi
  if [[ -f "$BB_ACTIVE_SCOPE" ]]; then
    local p
    p="$(tr -d '\r\n' <"$BB_ACTIVE_SCOPE")"
    if [[ -n "$p" && -f "$p" ]]; then
      echo "$p"
      return 0
    fi
  fi
  return 1
}

# Extract hostnames/domains from a scope.md (lines under ## In-scope or bare domain-looking tokens).
scope_allowlist() {
  local scope_file="${1:-}"
  [[ -n "$scope_file" && -f "$scope_file" ]] || return 1
  # Prefer fenced or table cells and simple domain tokens; ignore markdown headers.
  grep -Eio '([a-z0-9]([a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}|(\*\.)?([a-z0-9-]+\.)+[a-z]{2,}' "$scope_file" 2>/dev/null \
    | sed 's/^\*\.//' \
    | tr '[:upper:]' '[:lower:]' \
    | sort -u
}

# Return 0 if target host is allowed by active scope (or no scope is active).
# Wildcard semantics: allowlisted "example.com" matches "a.example.com".
scope_allows_target() {
  local target="${1:-}"
  [[ -n "$target" ]] || return 1
  target="$(echo "$target" | tr '[:upper:]' '[:lower:]' | sed 's#^https\?://##; s#/.*##; s#:.*##')"

  local scope_file
  if ! scope_file="$(active_scope_file)"; then
    # No active scope → allow (with optional warn from caller)
    return 0
  fi

  local entry
  while IFS= read -r entry; do
    [[ -z "$entry" ]] && continue
    entry="$(echo "$entry" | tr '[:upper:]' '[:lower:]' | sed 's/^\*\.//')"
    if [[ "$target" == "$entry" || "$target" == *".$entry" ]]; then
      return 0
    fi
  done < <(scope_allowlist "$scope_file")

  return 1
}

# Hard stop if active scope exists and target is not listed.
require_in_scope() {
  local target="${1:-}"
  require_target "$target"

  local scope_file
  if ! scope_file="$(active_scope_file)"; then
    if [[ "${BB_REQUIRE_SCOPE:-0}" == "1" ]]; then
      err "No active scope. Run: bb scope use <engagement-slug>  (or set BB_SCOPE_FILE)"
      err "Or create one: bb scope new <slug>"
      exit 2
    fi
    warn "No active scope file — proceeding without allowlist check (set BB_REQUIRE_SCOPE=1 to enforce)"
    return 0
  fi

  if scope_allows_target "$target"; then
    log "Scope OK: $target (from $scope_file)"
    return 0
  fi

  err "Target '$target' is NOT in active scope: $scope_file"
  err "Update scope.md in-scope assets, or: bb scope clear"
  exit 3
}
