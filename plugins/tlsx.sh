#!/usr/bin/env bash
install_tlsx() {
  install_go_tool "github.com/projectdiscovery/tlsx/cmd/tlsx@latest"
}

update_tlsx() {
  install_tlsx
}

doctor_tlsx() {
  if need_cmd "tlsx"; then echo "✓ tlsx"; else echo "✗ tlsx"; fi
}
