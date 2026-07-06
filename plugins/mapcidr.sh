#!/usr/bin/env bash
install_mapcidr() {
  install_go_tool "github.com/projectdiscovery/mapcidr/cmd/mapcidr@latest"
}

update_mapcidr() {
  install_mapcidr
}

doctor_mapcidr() {
  if need_cmd "mapcidr"; then echo "✓ mapcidr"; else echo "✗ mapcidr"; fi
}
