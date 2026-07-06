#!/usr/bin/env bash
install_asnmap() {
  install_go_tool "github.com/projectdiscovery/asnmap/cmd/asnmap@latest"
}

update_asnmap() {
  install_asnmap
}

doctor_asnmap() {
  if need_cmd "asnmap"; then echo "✓ asnmap"; else echo "✗ asnmap"; fi
}
