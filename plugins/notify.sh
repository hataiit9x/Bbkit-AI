#!/usr/bin/env bash
install_notify() {
  install_go_tool "github.com/projectdiscovery/notify/cmd/notify@latest"
}

update_notify() {
  install_notify
}

doctor_notify() {
  if need_cmd "notify"; then echo "✓ notify"; else echo "✗ notify"; fi
}
