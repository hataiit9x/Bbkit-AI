#!/usr/bin/env bash
install_python_tools() {
  local packages=(
    arjun
    waymore
    "git+https://github.com/devanshbatham/ParamSpider.git"
    dirsearch
    sqlmap
    trufflehog
    uro
  )
  local pkg
  for pkg in "${packages[@]}"; do
    pip_install "$pkg" || true
  done
}
update_python_tools() {
  install_python_tools
}
doctor_python_tools() {
  for t in arjun waymore paramspider dirsearch sqlmap trufflehog uro; do
    if need_cmd "$t"; then echo "✓ $t"; else echo "✗ $t"; fi
  done
}
