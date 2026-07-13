#!/usr/bin/env bash

BB_ROOT="${BB_ROOT:-$HOME/BugBounty}"
BB_BIN="$BB_ROOT/bin"
BB_TOOLS="$BB_ROOT/tools"
BB_TEMPLATES="$BB_ROOT/templates"
BB_REF="$BB_ROOT/ref"
BB_AI_ROOT="$BB_ROOT/ai/bug-bounty"
BB_ENGAGEMENTS="${BB_ENGAGEMENTS:-$BB_ROOT/engagements}"
BB_ACTIVE_SCOPE="${BB_ACTIVE_SCOPE:-$BB_ROOT/.active-scope}"
BB_SKILLS_ROOT="${BB_SKILLS_ROOT:-$BB_ROOT/skills}"
BB_WEB3_ROOT="${BB_WEB3_ROOT:-$BB_ROOT/ai/web3-skills}"
BB_CONFIG="${BB_CONFIG:-$BB_ROOT/config/config.yaml}"

# Leave knobs empty so load_bb_config can apply YAML; defaults after load.

expand_path() {
  local p="${1:-}"
  [[ -z "$p" ]] && { echo ""; return 0; }
  if [[ "$p" == ~* ]]; then
    p="${p/#\~/$HOME}"
  fi
  p="${p//\$BB_ROOT/$BB_ROOT}"
  p="${p//\$HOME/$HOME}"
  echo "$p"
}

# Load YAML knobs via Python (stdlib only). Env vars always win if already set by user
# for BB_RATE / BB_THREADS / BB_NUCLEI_SEVERITY / BB_REQUIRE_SCOPE before source.
load_bb_config() {
  local cfg="${1:-$BB_CONFIG}"
  [[ -f "$cfg" ]] || return 0
  command -v python3 >/dev/null 2>&1 || return 0

  # Export only keys not already set in environment (except we always re-read file for unset).
  eval "$(
    BB_CONFIG_PATH="$cfg" python3 - <<'PY'
import os, re, sys
path = os.environ.get("BB_CONFIG_PATH", "")
try:
    text = open(path, encoding="utf-8").read()
except OSError:
    sys.exit(0)

def get_scalar(key, default=""):
    m = re.search(rf"^{re.escape(key)}:\s*(.+)\s*$", text, re.M)
    if not m:
        return default
    v = m.group(1).strip().strip('"').strip("'")
    if v.startswith("#"):
        return default
    v = v.split("#", 1)[0].strip()
    return v

def get_nested(parent, key, default=""):
    # simple: look for "  key:" under parent block
    m = re.search(rf"^{re.escape(parent)}:\s*$([\s\S]*?)(?=^[a-zA-Z_]|\Z)", text, re.M)
    if not m:
        return default
    block = m.group(1)
    m2 = re.search(rf"^\s+{re.escape(key)}:\s*(.+)\s*$", block, re.M)
    if not m2:
        return default
    v = m2.group(1).strip().strip('"').strip("'").split("#", 1)[0].strip()
    return v

def get_severity_list():
    m = re.search(r"^nuclei:\s*$([\s\S]*?)(?=^[a-zA-Z_]|\Z)", text, re.M)
    if not m:
        return ""
    block = m.group(1)
    if "severity:" not in block:
        return ""
    items = re.findall(r"^\s+-\s+(\S+)", block, re.M)
    # only take list under severity — heuristic: after severity: line
    sev_i = block.find("severity:")
    if sev_i < 0:
        return ""
    sub = block[sev_i:]
    items = re.findall(r"^\s+-\s+(\S+)", sub, re.M)
    return ",".join(items) if items else ""

def sh_export(name, value):
    if not value and value != 0:
        return
    # only set if not already in environment
    if name in os.environ and os.environ.get(name, "") != "":
        return
    value = str(value).replace("'", "'\\''")
    print(f"export {name}='{value}'")

threads = get_scalar("threads", "50")
rate = get_scalar("rate_limit", "200")
out = get_scalar("output", "")
wl = get_scalar("wordlists", "")
req = get_scalar("require_scope", "false").lower()
sev = get_severity_list() or "critical,high,medium"
katana_d = get_nested("recon", "katana_depth", "3")
naabu_tp = get_nested("recon", "naabu_top_ports", "1000")
httpx_t = get_nested("recon", "httpx_threads", "50")
gau_t = get_nested("recon", "gau_threads", "50")
dash_h = get_nested("dashboard", "host", "127.0.0.1")
dash_p = get_nested("dashboard", "port", "8787")
resolvers = get_nested("resolvers", "file", "")

sh_export("BB_THREADS", threads)
sh_export("BB_RATE", rate)
if out:
    sh_export("BB_OUTPUT", out)
if wl:
    sh_export("BB_WORDLISTS", wl)
if req in ("true", "yes", "1"):
    sh_export("BB_REQUIRE_SCOPE", "1")
elif req in ("false", "no", "0"):
    sh_export("BB_REQUIRE_SCOPE", "0")
sh_export("BB_NUCLEI_SEVERITY", sev)
sh_export("BB_KATANA_DEPTH", katana_d)
sh_export("BB_NAABU_TOP_PORTS", naabu_tp)
sh_export("BB_HTTPX_THREADS", httpx_t)
sh_export("BB_GAU_THREADS", gau_t)
sh_export("BB_DASH_HOST", dash_h)
sh_export("BB_DASH_PORT", dash_p)
if resolvers:
    sh_export("BB_RESOLVERS_FILE", resolvers)

# recon block booleans
passive = get_nested("recon", "passive_only", "false").lower()
ports = get_nested("recon", "ports", "true").lower()
nuclei = get_nested("recon", "nuclei", "true").lower()
if passive in ("true", "yes", "1"):
    sh_export("BB_RECON_PASSIVE_ONLY", "1")
if ports in ("false", "no", "0"):
    sh_export("BB_RECON_PORTS", "0")
if nuclei in ("false", "no", "0"):
    sh_export("BB_RECON_NUCLEI", "0")
PY
  )" 2>/dev/null || true

  # Expand paths and re-export
  if [[ -n "${BB_OUTPUT:-}" ]]; then BB_OUTPUT="$(expand_path "$BB_OUTPUT")"; export BB_OUTPUT; fi
  if [[ -n "${BB_WORDLISTS:-}" ]]; then BB_WORDLISTS="$(expand_path "$BB_WORDLISTS")"; export BB_WORDLISTS; fi
  if [[ -n "${BB_RESOLVERS_FILE:-}" ]]; then BB_RESOLVERS_FILE="$(expand_path "$BB_RESOLVERS_FILE")"; export BB_RESOLVERS_FILE; fi
}

load_bb_config

# Defaults after YAML (env and config already applied)
BB_OUTPUT="${BB_OUTPUT:-$BB_ROOT/output}"
BB_WORDLISTS="${BB_WORDLISTS:-$BB_ROOT/wordlists}"
BB_THREADS="${BB_THREADS:-50}"
BB_RATE="${BB_RATE:-200}"
BB_NUCLEI_SEVERITY="${BB_NUCLEI_SEVERITY:-critical,high,medium}"
BB_REQUIRE_SCOPE="${BB_REQUIRE_SCOPE:-0}"
BB_KATANA_DEPTH="${BB_KATANA_DEPTH:-3}"
BB_NAABU_TOP_PORTS="${BB_NAABU_TOP_PORTS:-1000}"
BB_HTTPX_THREADS="${BB_HTTPX_THREADS:-50}"
BB_GAU_THREADS="${BB_GAU_THREADS:-50}"
BB_DASH_HOST="${BB_DASH_HOST:-127.0.0.1}"
BB_DASH_PORT="${BB_DASH_PORT:-8787}"
BB_RESOLVERS_FILE="${BB_RESOLVERS_FILE:-$BB_WORDLISTS/resolvers/resolvers.txt}"
export BB_OUTPUT BB_WORDLISTS BB_THREADS BB_RATE BB_NUCLEI_SEVERITY BB_REQUIRE_SCOPE
export BB_KATANA_DEPTH BB_NAABU_TOP_PORTS BB_HTTPX_THREADS BB_GAU_THREADS
export BB_DASH_HOST BB_DASH_PORT BB_RESOLVERS_FILE

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
