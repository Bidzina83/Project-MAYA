#!/usr/bin/env bash
if [ "$#" -lt 2 ]; then
  echo "usage: install_runtime.sh <artifact.tgz> <skill-name>"
  exit 2
fi
ART=$1
SKILL=$2
python3 scripts/install_runtime.py "$ART" "$SKILL"
