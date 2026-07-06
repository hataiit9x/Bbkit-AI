#!/usr/bin/env bash
set -e
export BB_ROOT=${BB_ROOT:-$HOME/BugBounty}
$BB_ROOT/bin/bb update
