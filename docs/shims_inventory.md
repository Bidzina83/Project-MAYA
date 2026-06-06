PYTHONPATH shims and import-time compatibility code — inventory

This file inventories locations in the repository that currently provide
PYTHONPATH shims, workspace mirrors, or test-time import compatibility
code. These entries are being documented for the Packaging Cleanup
preparation PR. Per the PR scope these shims are documented and marked
as deprecated for later removal — they are NOT removed by this PR.

Locations found (scan date: 2026-06-06)

1) /opt/data/.hermes_shim (referenced in README and tooling)
   - Purpose: historical workspace shim used in CI/test runs. Example usage:
     PYTHONPATH=/opt/data/.hermes_shim pytest ...
   - Reference files in repo:
     - README.md examples referencing /opt/data/.hermes_shim
     - tools/maya-dev/README.md documents the shim location
     - tools/maya-dev/run_ingest_tests.sh exports PYTHONPATH=/opt/data/.hermes_shim
   - Status: DEPRECATED (documented). Do NOT remove in this PR.

2) /opt/hermes runtime mirror (used in examples and some scripts)
   - Purpose: alternate runtime mirror location used on some CI runners.
   - Reference files:
     - plugins/memory/ingest/bin/run_ingest_tests.sh (uses PYTHONPATH=/opt/hermes)
     - README.md examples referencing /opt/hermes
   - Status: DEPRECATED (documented). Do NOT remove in this PR.

3) tools/maya-dev/run_ingest_tests.sh
   - Exports: export PYTHONPATH=/opt/data/.hermes_shim
   - Purpose: convenience script to run ingest tests in environments where
     an editable install is not present.
   - Status: DEPRECATED (documented).

4) plugins/memory/ingest/bin/run_ingest_tests.sh
   - Uses PYTHONPATH=/opt/hermes for example test invocations.
   - Status: DEPRECATED (documented).

5) plugins/memory/ingest/tests/conftest.py
   - Contains: a compatibility shim that overrides importlib.util.spec_from_file_location
     to make test imports resilient to absolute /opt/hermes paths used in some mirrors.
   - Purpose: test-time compatibility hack to ensure CI/test collection succeeds
     regardless of workspace mirror layout.
   - Status: KEEP for now (do NOT remove). Marked for later review after editable-install CI is validated.

6) plugins/memory/__init__.py
   - Contains dynamic provider loader logic that may import modules via
     importlib.util.spec_from_file_location when parent packages are not registered.
   - Purpose: supports both bundled and user-installed providers; not strictly a shim,
     but relevant to import layout behavior.
   - Status: KEEP.

7) README.md examples and tools/maya-dev/README.md
   - Contain example commands that use PYTHONPATH shims and mirrors.
   - Status: DOCUMENTED here; update to recommend editable install after CI validation.

Developer notes and TODOs (for later migration)
- After editable-install workflow proven stable in CI (several green runs):
  - Replace README examples with the editable-install commands from the runbook.
  - Remove the tools/maya-dev shim scripts or update them to call the runbook's venv commands.
  - Remove the spec_from_file_location override in tests only after confirming no mirror-based tests remain.

