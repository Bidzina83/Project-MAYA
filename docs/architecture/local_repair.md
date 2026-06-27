# Local Repair CLI

## Decision

Phase 1 introduces a conservative local repair command:

```text
maya repair --config <maya-config.json>
maya repair --config <maya-config.json> --apply
```

The command plans missing local state directories by default. It only writes
when `--apply` is supplied, and its Phase 1 write surface is limited to
creating missing directories under the configured `deployment.data_dir`.

The command does not modify memory records, governance policies, audit logs,
secrets, backups, migrations, connector credentials, or runtime state. If a
target path already exists as a file, or if the configured data-directory
parent does not exist, repair fails with a generic secret-safe error.

## Scope

This is not the final interactive recovery UX. It is the first installable
repair surface needed to turn first-run `maya doctor` warnings about missing
local state directories into an explicit, dry-run-first recovery plan.
