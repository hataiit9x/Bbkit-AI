#!/usr/bin/env bash
install_browser_tools() {
  pip_install "cloakbrowser[geoip]"
}

update_browser_tools() {
  install_browser_tools
}

doctor_browser_tools() {
  python3 -c "import cloakbrowser" >/dev/null 2>&1 && echo "✓ cloakbrowser-python" || echo "✗ cloakbrowser-python"
}
