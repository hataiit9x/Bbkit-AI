#!/usr/bin/env bash
install_gf() {
  install_go_tool "github.com/tomnomnom/gf@latest"
}

update_gf() {
  install_gf
}

doctor_gf() {
  if need_cmd "gf"; then echo "✓ gf"; else echo "✗ gf"; fi
}
