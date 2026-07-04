# Local Backup

## Decision

Phase 1 introduces a minimal local backup command:

```text
maya backup --config <path>
maya restore --from <archive> --to <data-dir>
```

The command validates the typed configuration, creates a ZIP archive under
`<deployment.data_dir>/backups/` by default, and reports only the archive path
and file count. Callers may provide an explicit destination with `--to`.

The archive contains:

- normalized `maya-config.json` with secret references, not secret values;
- `maya-backup-manifest.json` with schema version, created time, instance id,
  file count, included roots, excluded roots, and runtime/package version
  metadata when available;
- Maya-owned files under the configured local Maya data directory.

The `backups/` directory itself is excluded so backup archives do not
recursively contain earlier backups.

V2 Phase 3 narrows the default archive boundary for document and Metabase
capability state. The archive includes Maya document outputs/caches and
Metabase provisioning metadata, but excludes customer analytics sources and
Metabase application database state unless a future explicit contract opts
them in.

Existing archive destinations are not overwritten. This keeps the command
idempotent and avoids destructive replacement until a fuller backup lifecycle
policy exists.

`restore` validates an archive and reports the restore plan by default. It only
writes files when `--apply` is supplied. If a destination file already exists,
`--allow-overwrite` is also required. Archive paths are checked before restore
so entries cannot escape the destination directory.

The top-level `maya-config.json` backup entry restores to
`<data-dir>/config/maya-config.json`; data files under `maya-data/` restore to
their relative paths under the destination data directory.

## Limits

This is not the final retention, encryption, external storage, or platform
qualification flow. It is the Phase 1 local artifact needed to prove that
customer-controlled state can be captured and restored without printing memory
contents, prompts, raw records, or secret values.
