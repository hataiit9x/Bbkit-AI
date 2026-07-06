#!/usr/bin/env bash
install_hakrevdns() {
  install_go_tool "github.com/hakluke/hakrevdns@latest"
}

update_hakrevdns() {
  install_hakrevdns
}

doctor_hakrevdns() {
  if need_cmd "hakrevdns"; then echo "✓ hakrevdns"; else echo "✗ hakrevdns"; fi
}
