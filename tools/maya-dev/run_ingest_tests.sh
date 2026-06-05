#!/bin/sh
# Wrapper to run plugin ingest tests using project venv and the shim
export PYTHONPATH=/opt/data/.hermes_shim
/opt/hermes/.venv/bin/pytest -c /dev/null -q /opt/hermes/plugins/memory/ingest/tests -p no:xdist
