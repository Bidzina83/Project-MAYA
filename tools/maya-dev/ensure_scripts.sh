#!/bin/sh
# Ensure helper scripts are in the scheduler scripts directory (~/.hermes/scripts)
set -euo pipefail
SRC_DIR="$(dirname "$0")"
TARGET_DIR="/opt/data/.hermes/scripts"
mkdir -p "$TARGET_DIR"
# Copy registry monitor wrapper into the target scripts dir
cp -f "$SRC_DIR/registry_monitor.sh" "$TARGET_DIR/registry_monitor.sh"
chmod +x "$TARGET_DIR/registry_monitor.sh"
echo "Ensured $TARGET_DIR/registry_monitor.sh exists and is executable"
