#!/usr/bin/env bash
install_katana() {
  install_go_tool "github.com/projectdiscovery/katana/cmd/katana@latest"
}

update_katana() {
  install_katana
}

doctor_katana() {
  if need_cmd "katana"; then echo "✓ katana"; else echo "✗ katana"; fi
}
