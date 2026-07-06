#!/usr/bin/env bash
install_naabu() {
  install_go_tool "github.com/projectdiscovery/naabu/v2/cmd/naabu@latest"
}

update_naabu() {
  install_naabu
}

doctor_naabu() {
  if need_cmd "naabu"; then echo "✓ naabu"; else echo "✗ naabu"; fi
}
