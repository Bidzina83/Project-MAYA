Project MAYA - developer quickstart

Purpose: store a small set of helper files and scripts under /opt/data so developers (and the cronjob) can run tests and monitoring without needing root writes to /opt/hermes.

Key files and locations
- PYTHONPATH shim (used for test runs): /opt/data/.hermes_shim/hermes/__init__.py
- Project venv: /opt/hermes/.venv
- Storage root (registry, logs, sqlite): /opt/data/maya-memory-repo
- Registry monitor log: /opt/data/maya-memory-repo/registry/monitor.log

Running tests (recommended)
1) From any shell on this machine run:
   export PYTHONPATH=/opt/data/.hermes_shim
   /opt/hermes/.venv/bin/pytest -c /dev/null -q /opt/hermes/plugins/memory/ingest/tests -p no:xdist

Alternative wrapper (included):
- /opt/data/maya-dev/run_ingest_tests.sh - runs the exact command above (executable).

Why this exists
- /opt/hermes top-level is root-owned and write-protected in this environment. This shim and helper scripts live under /opt/data which is writable by the hermes user, avoiding permission issues while preserving the canonical repo at /opt/hermes for production installs.
