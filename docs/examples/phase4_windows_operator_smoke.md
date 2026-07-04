# Phase 4 Windows Operator Smoke

Run these commands from a PowerShell prompt after installing the built
`project-maya` wheel into a virtual environment.

```powershell
maya setup plan --config maya-config.json --format text
maya setup init --config maya-config.json
maya setup init --config maya-config.json --apply
maya health summary --config maya-config.json --format text
maya doctor --config maya-config.json
maya backup --config maya-config.json --to .\maya-smoke-backup.zip
maya backup inspect --from .\maya-smoke-backup.zip
maya restore --from .\maya-smoke-backup.zip --to .\maya-restore-smoke
maya migrate --from .\legacy-memory.sqlite --to .\maya-memory.sqlite --dry-run
maya update --config maya-config.json --check
maya update --config maya-config.json --rollback
```

Expected behavior:

- setup and restore are dry-run unless `--apply` is supplied;
- restore conflicts fail safely unless `--apply --allow-overwrite` is supplied;
- migration is dry-run unless `--apply --allow-modify` is supplied;
- health and doctor may report warnings for missing optional dependencies;
- update and rollback checks do not use the network;
- output must not include secret values, prompt contents, document contents, or
  customer records.

This smoke does not claim Windows platform support or create a production
installer. It validates installed-package operator surfaces only.
