#!/usr/bin/env bash
install_gau() {
  install_go_tool "github.com/lc/gau/v2/cmd/gau@latest"
}

update_gau() {
  install_gau
}

doctor_gau() {
  if need_cmd "gau"; then echo "✓ gau"; else echo "✗ gau"; fi
}
