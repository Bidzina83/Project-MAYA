#!/usr/bin/env bash
set -euo pipefail

# ensure_runtime_scripts.sh
# Copies runtime helper scripts from SOURCE_DIR into DEST_DIR (default /opt/data/.hermes/scripts)
# Usage: ensure_runtime_scripts.sh [--source DIR] [--dest DIR] [--chown user:group] [--mode 755]

SOURCE_DIR="${1:-/opt/data/maya-dev/tools/maya-dev}"
DEST_DIR="/opt/data/.hermes/scripts"
CHOWN_SPEC=""
MODE=755

# parse args
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --source)
      SOURCE_DIR="$2"; shift 2;;
    --dest)
      DEST_DIR="$2"; shift 2;;
    --chown)
      CHOWN_SPEC="$2"; shift 2;;
    --mode)
      MODE="$2"; shift 2;;
    --help|-h)
      echo "Usage: $0 [--source DIR] [--dest DIR] [--chown user:group] [--mode octal]"; exit 0;;
    *)
      echo "Unknown arg: $1"; exit 1;;
  esac
done

echo "Source: $SOURCE_DIR"
echo "Dest:   $DEST_DIR"

if [ ! -d "$SOURCE_DIR" ]; then
  echo "ERROR: source dir does not exist: $SOURCE_DIR" >&2
  exit 2
fi

mkdir -p "$DEST_DIR"

copied=0
for f in "$SOURCE_DIR"/*; do
  [ -e "$f" ] || continue
  base=$(basename "$f")
  dest="$DEST_DIR/$base"
  echo "Copying $f -> $dest"
  cp -a "$f" "$dest"
  chmod "$MODE" "$dest" || true
  if [ -n "$CHOWN_SPEC" ]; then
    chown "$CHOWN_SPEC" "$dest" 2>/dev/null || echo "Warning: chown $CHOWN_SPEC failed (insufficient privileges)" >&2
  fi
  copied=$((copied+1))
done

if [ "$copied" -eq 0 ]; then
  echo "No files found in source: $SOURCE_DIR" >&2
  exit 3
fi

echo "Successfully copied $copied files to $DEST_DIR"
# list dest files
ls -la "$DEST_DIR"
