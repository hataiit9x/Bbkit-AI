#!/usr/bin/env bash
install_amass() {
  install_go_tool "github.com/owasp-amass/amass/v4/...@master"
}

update_amass() {
  install_amass
}

doctor_amass() {
  if need_cmd "amass"; then echo "✓ amass"; else echo "✗ amass"; fi
}
