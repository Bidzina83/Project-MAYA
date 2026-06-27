# Phase 1 Closure Audit

## Status

Phase 1 is implementation-complete for the minimal local product checkpoint.
The repository now has a clean installable package surface, a concrete Hermes
adapter boundary, governed memory, local authorization, local API entrypoints,
secret-safe diagnostics, and conservative recovery/status commands.

This is not a production distribution claim. Signed installers, production
updates, provider-specific connector revocation, broker OAuth, Metabase
service management, Enterprise BYO operation, and platform qualification remain
later phases.

## Exit Criteria Evidence

| Phase 1 exit criterion | Evidence |
| --- | --- |
| Installs from a clean artifact | `scripts/verify_phase1_package.py`, `docs/architecture/phase1_package_verification.md`, `tests/test_phase1_package_install.py` |
| Public execution delegates through Hermes adapter | `docs/architecture/hermes_runtime_binding.md`, `tests/test_phase1_runtime.py`, `tests/test_agent_public_api.py` |
| Governed memory retrieval and writes work locally | `docs/architecture/governed_memory.md`, `docs/architecture/hermes_memory_provider.md`, `tests/test_phase1_governed_memory.py`, `tests/test_phase1_memory_provider.py`, `tests/test_memory_interface.py` |
| Consequential runtime actions pass through local authorization | `docs/architecture/local_authorization_policy.md`, `tests/test_phase1_policy.py`, `tests/test_phase1_audit.py` |
| External model egress is governed and audited | `docs/architecture/model_egress_governance.md`, `tests/test_phase1_audit.py`, `tests/test_phase1_local_api.py` |
| Local API is authenticated and loopback-only in Phase 1 | `docs/architecture/local_api_boundary.md`, `tests/test_phase1_local_api.py` |
| Secrets use an approved local backend or honestly report unavailable | `docs/architecture/local_secret_store.md`, `tests/test_phase1_secrets.py` |
| Local diagnostics and recovery commands exist | `docs/architecture/local_doctor_checks.md`, `docs/architecture/local_repair.md`, `docs/architecture/local_integration_reset.md`, `tests/test_phase1_doctor_local_state.py`, `tests/test_phase1_repair.py`, `tests/test_phase1_integration_reset.py` |
| Backup, restore, and migration are dry-run/safety oriented | `docs/architecture/local_backup.md`, `docs/architecture/local_migration_cli.md`, `tests/test_phase1_backup.py`, `tests/test_migration.py` |
| Update and rollback command surface is honest and non-mutating | `docs/architecture/local_update_status.md`, `tests/test_phase1_update.py` |
| Product context remains aligned with V2 | `scripts/validate_project_maya_context.py`, `tests/test_project_context_guard.py` |

## Required Command Surface

The installed `maya` command exposes the V2 local operations surface:

```text
maya doctor
maya repair
maya reset-integration <name>
maya rotate-secret <name>
maya export-config
maya import-config
maya backup
maya restore
maya migrate --dry-run
maya update --check
maya update --rollback
```

The package verifier builds a wheel, installs it into a clean virtual
environment, checks the console entrypoint, and smoke-tests the conservative
installed command behavior for repair, integration reset, update status, and
migration.

## Known Limits

- `maya update` is status-only in Phase 1. It does not download, install, or
  roll back artifacts.
- `maya reset-integration` clears local integration state only. It does not
  revoke OAuth grants, Telegram bot tokens, broker sessions, or external
  provider credentials.
- `maya repair` creates missing local directories only. It does not repair
  memory contents, policies, audit records, secrets, connector state, or
  runtime failures.
- Metabase, document processing, browser automation, connector runtime
  revocation, Enterprise BYO operation, broker OAuth, signed installers,
  SBOMs, and platform qualification remain downstream phases.
- On Windows, the non-Windows secret-store fallback test is intentionally
  skipped because Windows uses DPAPI rather than the unavailable fallback.

## Next Phase

After this checkpoint, the next product phase should begin with Enterprise BYO
and broker-disabled operation contracts. That means customer-owned model and
connector credentials, connector validation/revocation contracts, local model
configuration, and end-to-end operation without Maya cloud services.
