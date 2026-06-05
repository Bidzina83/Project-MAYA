# Persistent Memory Subsystem - Current State Snapshot

Last updated: 2026-05-28T13:51:23.640597+00:00 (UTC)

Purpose
- Snapshot the current architecture and operational state for the persistent-memory (ingest) subsystem so the assistant can resume work next session without re-discovery.

High-level summary
- Root cause of recent CI failures: pytest collection imports test modules as top-level files; tests use relative imports (e.g., from ..chunker) which raise "attempted relative import with no known parent package" during collection.
- Local tests pass when the package is installed (pip install -e .) and when tests are run in package context.

Repository state (confirmed)
- PRs/Branches created or handled by agent during troubleshooting:
  - PR #35: test(ci): add init files so ingest package imports work in CI — MERGED (2026-05-27T19:22:01Z). This added __init__.py to plugins, plugins/memory, plugins/memory/ingest.
  - PR #45: fix: prefer legacy openai module for test compatibility — MERGED (2026-05-28).
  - PR #46: test: combined verification for PR36 + PR31 + fix — MERGED (2026-05-28).
  - PR #31, PR #36: merged into main.
  - PR #33: had merge conflicts; resolved and merged by the assistant — MERGED (2026-05-28).
- Workflow files inspected/modified during session:
  - .github/workflows/run-ingest-tests.yml (merged CI steps, added basetemp handling and smoke import checks).
- Local test result (host environment): full suite run with repo-local basetemp -> 32 passed, 1 skipped, 2 warnings (final run on main after merges).
- Recent remote branch cleanup: 13 merged branches were deleted remotely and corresponding local branches pruned where present.

Branch / PR housekeeping (current)
- Current local branch during investigation: tmp/inv-move-maya-dev-into-tools (inspection only).
- Notable remaining branches for review: ci/add-ingest-test-shims-resolved, combined/pr36, add/registry-concurrency-1, example/call-ingest-20260526, feat/ci-memory-20260525..., ci/patch-install-pypath-20260527, test/add-ingest-test-shims, ci/add-github-actions, feature/memory-registry-cli, fix/packaging-pyproject-20260526, etc.

Fixes applied so far
- Added package __init__.py files to plugins, plugins/memory, plugins/memory/ingest (PR #35) to make package parents explicit.
- Created and merged small focused PRs for test-compat fixes (PR #45), combined verification (PR #46), and merged multiple supporting PRs into main.
- Updated run-ingest-tests workflow to include install step and PYTHONPATH; smoke import step added for early failure detection.

Remaining issues and investigation notes
- Some branches remain unreviewed and contain CI/packaging changes; investigate high-ahead branches (test/add-ingest-test-shims, combined/pr36, ci/patch-install-pypath-20260527) before bulk deletion.
- move-maya-dev-into-tools branch restructures maya_dev and tools/ layout; it requires decision whether to keep maya_dev at top-level or adopt the tools/ layout and update packaging/CI accordingly. Agent ran focused tests with PYTHONPATH set and validated at least one config test.

Immediate next actions recommended (persisted)
1) Continue manual review of the top remaining branches and run full test suite with repo-local basetemp on branches of interest (agent can run and report).  
2) For move-maya-dev-into-tools: decide repo layout (keep maya_dev at top-level or move into tools/) and either (a) add packaging to expose maya_dev via pip install -e ., or (b) add CI steps to set PYTHONPATH for package imports.  
3) Add small follow-up PR to address datetime deprecation warnings (non-blocking).

Notes about agent actions and CI credentials
- The agent used the GitHub App installation flow to create branches and PRs and to update branch refs when necessary. Installation tokens were short-lived and not stored in this file.

End of snapshot.
