#!/usr/bin/env bash
install_subfinder() {
  install_go_tool "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"
}

update_subfinder() {
  install_subfinder
}

doctor_subfinder() {
  if need_cmd "subfinder"; then echo "✓ subfinder"; else echo "✗ subfinder"; fi
}
