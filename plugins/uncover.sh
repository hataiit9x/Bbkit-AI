#!/usr/bin/env bash
install_uncover() {
  install_go_tool "github.com/projectdiscovery/uncover/cmd/uncover@latest"
}

update_uncover() {
  install_uncover
}

doctor_uncover() {
  if need_cmd "uncover"; then echo "✓ uncover"; else echo "✗ uncover"; fi
}
