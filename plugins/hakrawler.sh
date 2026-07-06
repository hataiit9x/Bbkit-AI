#!/usr/bin/env bash
install_hakrawler() {
  install_go_tool "github.com/hakluke/hakrawler@latest"
}

update_hakrawler() {
  install_hakrawler
}

doctor_hakrawler() {
  if need_cmd "hakrawler"; then echo "✓ hakrawler"; else echo "✗ hakrawler"; fi
}
