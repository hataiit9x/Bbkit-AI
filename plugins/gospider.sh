#!/usr/bin/env bash
install_gospider() {
  install_go_tool "github.com/jaeles-project/gospider@latest"
}

update_gospider() {
  install_gospider
}

doctor_gospider() {
  if need_cmd "gospider"; then echo "✓ gospider"; else echo "✗ gospider"; fi
}
