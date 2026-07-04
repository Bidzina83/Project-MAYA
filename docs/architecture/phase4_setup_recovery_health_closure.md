# Phase 4 Closure Audit

V2 Phase 4 is complete for the Setup, Recovery, Backup, and Health Experience
scope.

## Objective

```text
Maya can be initialized, inspected, repaired, backed up, restored, and checked
from the installed package through safe operator commands without silently
installing dependencies, contacting providers, exposing secrets, or claiming
production installer support.
```

## Approved Step Evidence

| Step | Evidence |
| --- | --- |
| 1. Scope gate | `docs/architecture/phase4_setup_recovery_health_scope.md` |
| 2. Edition-aware setup contract | `src/project_maya/setup.py`, `tests/test_phase4_setup_health.py` |
| 3. Setup CLI | `src/project_maya/cli.py`, `scripts/verify_phase1_package.py` |
| 4. Health summary | `src/project_maya/health.py`, `tests/test_phase4_setup_health.py` |
| 5. Recovery UX | `src/project_maya/repair.py`, `docs/architecture/phase4_recovery_operator_guide.md` |
| 6. Backup/restore hardening | `src/project_maya/backup.py`, `tests/test_phase1_backup.py`, `tests/test_phase4_setup_health.py` |
| 7. Migration and update readiness hardening | `src/project_maya/migration.py`, `src/project_maya/update.py`, `tests/test_phase1_update.py`, `scripts/verify_phase1_package.py` |
| 8. Windows installed-package smoke | `docs/examples/phase4_windows_operator_smoke.md` |
| 9. Package verification | `scripts/verify_phase1_package.py`, `tests/test_phase4_setup_recovery_health_package_verification.py` |
| 10. Closure | `docs/architecture/phase4_setup_recovery_health_closure.md`, `tests/test_phase4_setup_recovery_health_closure.py` |

## Completed Surfaces

- `maya setup plan` and `maya setup init` report edition-aware setup actions
  for Standard and Enterprise without creating OAuth grants, broker sessions,
  credentials, tenant resources, or hidden dependency installs.
- `maya health summary` provides an operator-oriented view over existing
  diagnostics, setup, recovery, backup, restore, migration, update, documents,
  Metabase, and packaged skill readiness.
- `maya repair` includes category, severity, and recovery hints.
- Backup archives include `maya-backup-manifest.json`.
- `maya backup inspect` reads manifests without extraction.
- Restore planning reports manifest status, file count, conflicts, and
  overwrite requirements before extraction.
- Migration remains dry-run by default and package verification proves the
  installed CLI does not write destinations in dry-run mode.
- Update and rollback checks remain local, non-mutating, and network-free.
- Clean package verification covers installed V2 Phase 4 CLI surfaces.

## Known Limits

V2 Phase 4 intentionally does not:

- create or sign a production installer;
- perform automatic update or rollback;
- install system dependencies;
- create credentials, OAuth grants, or broker setup sessions;
- create customer tenant resources;
- claim Windows, macOS, Linux, server, or container support.
