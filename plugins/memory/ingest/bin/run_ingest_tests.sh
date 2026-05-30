#!/usr/bin/env bash
set -euo pipefail

# Run ingest plugin tests only (clears parent pyproject addopts to avoid xdist surprises)
PYTHONPATH=/opt/hermes /opt/hermes/.venv/bin/pytest -o 'addopts=' /opt/hermes/plugins/memory/ingest/tests -q
