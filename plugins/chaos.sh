#!/usr/bin/env bash
install_chaos() {
  install_go_tool "github.com/projectdiscovery/chaos-client/cmd/chaos@latest"
}

update_chaos() {
  install_chaos
}

doctor_chaos() {
  if need_cmd "chaos"; then echo "✓ chaos"; else echo "✗ chaos"; fi
}
