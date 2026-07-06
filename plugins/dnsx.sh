#!/usr/bin/env bash
install_dnsx() {
  install_go_tool "github.com/projectdiscovery/dnsx/cmd/dnsx@latest"
}

update_dnsx() {
  install_dnsx
}

doctor_dnsx() {
  if need_cmd "dnsx"; then echo "✓ dnsx"; else echo "✗ dnsx"; fi
}
