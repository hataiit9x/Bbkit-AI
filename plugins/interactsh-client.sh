#!/usr/bin/env bash
install_interactsh_client() {
  install_go_tool "github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest"
}

update_interactsh_client() {
  install_interactsh_client
}

doctor_interactsh_client() {
  if need_cmd "interactsh-client"; then echo "✓ interactsh-client"; else echo "✗ interactsh-client"; fi
}
