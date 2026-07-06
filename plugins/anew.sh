#!/usr/bin/env bash
install_anew() {
  install_go_tool "github.com/tomnomnom/anew@latest"
}

update_anew() {
  install_anew
}

doctor_anew() {
  if need_cmd "anew"; then echo "✓ anew"; else echo "✗ anew"; fi
}
