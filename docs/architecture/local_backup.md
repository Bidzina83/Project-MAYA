# Local Backup

## Decision

Phase 1 introduces a minimal local backup command:

```text
maya backup --config <path>
```

The command validates the typed configuration, creates a ZIP archive under
`<deployment.data_dir>/backups/` by default, and reports only the archive path
and file count. Callers may provide an explicit destination with `--to`.

The archive contains:

- normalized `maya-config.json` with secret references, not secret values;
- files under the configured local Maya data directory.

The `backups/` directory itself is excluded so backup archives do not
recursively contain earlier backups.

Existing archive destinations are not overwritten. This keeps the command
idempotent and avoids destructive replacement until a fuller backup lifecycle
policy exists.

## Limits

This is not the final restore, retention, encryption, external storage, or
platform qualification flow. It is the Phase 1 local artifact needed to prove
that customer-controlled state can be captured without printing memory
contents, prompts, raw records, or secret values.
