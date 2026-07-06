#!/usr/bin/env bash
install_qsreplace() {
  install_go_tool "github.com/tomnomnom/qsreplace@latest"
}

update_qsreplace() {
  install_qsreplace
}

doctor_qsreplace() {
  if need_cmd "qsreplace"; then echo "✓ qsreplace"; else echo "✗ qsreplace"; fi
}
