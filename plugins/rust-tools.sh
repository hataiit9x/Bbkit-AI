#!/usr/bin/env bash
install_rust_tools() {
  if command -v cargo >/dev/null 2>&1; then
    cargo install --locked --version 2.9.0 feroxbuster || true
  fi
}
update_rust_tools() {
  install_rust_tools
}
doctor_rust_tools() {
  if need_cmd feroxbuster; then echo "✓ feroxbuster"; else echo "✗ feroxbuster"; fi
}
