#!/usr/bin/env bash
install_assetfinder() {
  install_go_tool "github.com/tomnomnom/assetfinder@latest"
}

update_assetfinder() {
  install_assetfinder
}

doctor_assetfinder() {
  if need_cmd "assetfinder"; then echo "✓ assetfinder"; else echo "✗ assetfinder"; fi
}
