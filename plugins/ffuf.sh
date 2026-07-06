#!/usr/bin/env bash
install_ffuf() {
  install_go_tool "github.com/ffuf/ffuf/v2@latest"
}

update_ffuf() {
  install_ffuf
}

doctor_ffuf() {
  if need_cmd "ffuf"; then echo "✓ ffuf"; else echo "✗ ffuf"; fi
}
