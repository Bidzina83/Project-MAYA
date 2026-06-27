# Phase 1 Package Verification

## Decision

Phase 1 verifies that Project MAYA can be installed from a built wheel without
using editable installs, repository `PYTHONPATH`, or test-only path shims.

The verification script is:

```text
scripts/verify_phase1_package.py
```

It performs these checks in a temporary workspace:

- builds a wheel from the repository packaging metadata;
- verifies the wheel contains `project_maya` and excludes tests, caches, and
  legacy non-product package trees;
- creates a clean virtual environment;
- installs the wheel with `--no-deps`;
- imports the canonical `project_maya` package;
- verifies the packaged `maya` console entry point metadata;
- verifies the installed CLI module responds to `--help` and exposes the
  Phase 1 `doctor`, repair, integration reset, one-shot `run`, local API
  serve, secret rotation, config import/export, backup, restore, and migration
  commands.

## Scope

This is a Phase 1 artifact sanity check. It proves the minimal local product
API and CLI are present in the built package.

It does not claim:

- signed installer support;
- platform qualification;
- dependency locking;
- SBOM or release provenance;
- update or rollback support;
- full clean-machine product installation.

Those remain later release and distribution gates.
