#!/usr/bin/env bash
install_subjs() {
  install_go_tool "github.com/lc/subjs@latest"
}

update_subjs() {
  install_subjs
}

doctor_subjs() {
  if need_cmd "subjs"; then echo "✓ subjs"; else echo "✗ subjs"; fi
}
