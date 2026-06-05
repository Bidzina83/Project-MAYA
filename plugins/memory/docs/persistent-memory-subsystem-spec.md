# Persistent Memory Subsystem - Current State Snapshot

Last updated: 2026-06-05T21:55:03+00:00 (UTC)

Purpose
- Snapshot the current architecture and operational state for the persistent-memory (ingest) subsystem so the assistant can resume work next session without re-discovery.

High-level summary
- Root cause of recent CI failures: import-time dependencies and PYTHONPATH mismatches in CI runners (missing runtime packages such as `hermes_state`, `agent`, and `tools.registry`, plus tests expecting repository layout/paths that differ from some runners).
- Local tests pass when run in a controlled environment (venv + repository installed or PYTHONPATH set to include the workspace root and maya-dev/.hermes_shim).

Recent changes (2026-06-05)
- Added defensive fallbacks and hardening to make collection-time imports tolerant in CI/test runners:
  - plugins/memory/holographic/__init__.py: added try/except fallbacks for missing `agent.memory_provider` and `tools.registry` to avoid collection-time ModuleNotFoundError on minimal CI images.
  - plugins/memory/holographic/store.py: made `apply_wal_with_fallback` import tolerant (if `hermes_state` is unavailable, a best-effort no-op/wal-pragma helper is used). This avoids failing test collection when `hermes_state` is not installed.
- Added missing retrieval adapters and package marker to stabilize imports:
  - plugins/memory/adapters/__init__.py (package marker)
  - plugins/memory/adapters/holographic_adapter.py (HolographicAdapter wrapper)
  - plugins/memory/adapters/local_vector_adapter.py (LocalVectorAdapter wrapper)
- Added maya-dev/.hermes_shim/__init__.py to mirror the CI PYTHONPATH target and ensure repository root + plugins path are added to sys.path when CI sets PYTHONPATH to that shim.
- CI workflow edits (branch: fix/holographic-import-fallback-20260605): run-ingest-tests.yml and memory-ci.yml were patched to install `hermes_state` and to prepend the workspace root to PYTHONPATH in the test steps. NOTE: `hermes_state` is not published on PyPI — see "Known blockers" below.
- Committed and pushed the above changes to branch fix/holographic-import-fallback-20260605. The holographic adapter unit test (plugins/memory/ingest/tests/test_holographic_adapter.py) passes locally in a venv after adding the store fallback.

Update: the most recent PR was merged and CI on main ran green. Verified by the user and merged on 2026-06-05T21:55:03Z.

Known blockers & recommendations
- hermes_state is not available on PyPI (pip reports: "No matching distribution found for hermes_state"). Installing `hermes_state` in CI by name will fail on standard runners. Two recommended approaches:
  1) Preferred: remove `hermes_state` from the CI pip install list and rely on the `apply_wal_with_fallback` fallback in store.py (already committed). This avoids failing installs and keeps tests runnable in minimal runners.
  2) If `hermes_state` is required for production behavior, point CI at a concrete source (git URL or internal package index) and update the workflows to install from that source. Provide the URL if you want this option.

Status of local verification
- Verified locally (in this environment):
  - Created a venv, installed pytest and jsonschema, and ran the holographic adapter test file; the test passed: `.  [100%]`.
  - Attempted `pip install -e . pytest jsonschema hermes_state` — failed because `hermes_state` is not on PyPI.

Next recommended actions
1) Choose how CI should handle `hermes_state` (remove from installs, or provide an install source). If you prefer removal, I can update the workflows accordingly and push the change.
2) After CI install issues are resolved, re-run the failing workflows and fetch full logs for the most recent run to confirm no further import/runtime errors.
3) Consider keeping the `apply_wal_with_fallback` fallback (non-invasive, safe) to make test discovery more robust on minimal images, or replace it with the canonical `hermes_state` implementation when available.

Files touched in the current cycle
- plugins/memory/holographic/__init__.py (fallbacks added)
- plugins/memory/holographic/store.py (hermes_state import made tolerant)
- plugins/memory/adapters/__init__.py (added)
- plugins/memory/adapters/holographic_adapter.py (added)
- plugins/memory/adapters/local_vector_adapter.py (added)
- maya-dev/.hermes_shim/__init__.py (added)
- .github/workflows/run-ingest-tests.yml (patched to add hermes_state and PYTHONPATH changes)
- .github/workflows/memory-ci.yml (patched to add hermes_state)

End of snapshot.
