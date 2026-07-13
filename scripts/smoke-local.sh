#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export BB_ROOT="${TMPDIR:-/tmp}/bbkit-smoke-$$"
rm -rf "$BB_ROOT"
mkdir -p "$BB_ROOT/bin" "$BB_ROOT/config"
cp -R "$ROOT/lib" "$ROOT/plugins" "$ROOT/recon" "$ROOT/config" "$ROOT/skills" "$ROOT/templates" "$ROOT/bin" "$BB_ROOT/"
cp "$ROOT/bin/bb" "$BB_ROOT/bin/bb"
cp "$ROOT/config/config.yaml" "$BB_ROOT/config/config.yaml"
chmod +x "$BB_ROOT/bin/bb" "$BB_ROOT"/recon/*
export PATH="$BB_ROOT/bin:$PATH"

echo "== config =="
bb config >"$BB_ROOT/cfg.out"
head -15 "$BB_ROOT/cfg.out" || true
grep -q 'BB_THREADS         = 50' "$BB_ROOT/cfg.out" || { echo "threads fail"; cat "$BB_ROOT/cfg.out"; exit 1; }
echo "config ok"

echo "== full help =="
bb full --help | grep -q passive-only || { echo "full help fail"; exit 1; }
echo "full help ok"

echo "== dashboard =="
python3 -m py_compile "$BB_ROOT/lib/dashboard.py" || { echo "py_compile fail"; exit 1; }
bb dashboard --host 127.0.0.1 --port 18791 &
pid=$!
sleep 1
if ! curl -sf "http://127.0.0.1:18791/" | grep -q BBKit; then
  echo "dashboard HTML fail"; kill "$pid" 2>/dev/null || true; exit 1
fi
if ! curl -sf "http://127.0.0.1:18791/api/targets" | grep -q '\['; then
  echo "dashboard API fail"; kill "$pid" 2>/dev/null || true; exit 1
fi
kill "$pid" 2>/dev/null || true
wait "$pid" 2>/dev/null || true
echo "dashboard ok"

rm -rf "$BB_ROOT"
echo "SMOKE_OK"
