#!/usr/bin/env bash
set -e
BB_ROOT="${BB_ROOT:-$HOME/BugBounty}"
echo "This will remove $BB_ROOT"
read -r -p "Continue? [y/N] " ans
if [[ "$ans" == "y" || "$ans" == "Y" ]]; then
  rm -rf "$BB_ROOT"
  echo "Removed."
else
  echo "Cancelled."
fi
