#!/usr/bin/env bash
install_nuclei() {
  install_go_tool "github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"
}

update_nuclei() {
  install_nuclei
}

doctor_nuclei() {
  if need_cmd "nuclei"; then echo "✓ nuclei"; else echo "✗ nuclei"; fi
}
