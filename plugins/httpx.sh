#!/usr/bin/env bash
install_httpx() {
  install_go_tool "github.com/projectdiscovery/httpx/cmd/httpx@latest"
}

update_httpx() {
  install_httpx
}

doctor_httpx() {
  if need_cmd "httpx"; then echo "✓ httpx"; else echo "✗ httpx"; fi
}
