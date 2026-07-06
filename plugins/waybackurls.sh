#!/usr/bin/env bash
install_waybackurls() {
  install_go_tool "github.com/tomnomnom/waybackurls@latest"
}

update_waybackurls() {
  install_waybackurls
}

doctor_waybackurls() {
  if need_cmd "waybackurls"; then echo "✓ waybackurls"; else echo "✗ waybackurls"; fi
}
