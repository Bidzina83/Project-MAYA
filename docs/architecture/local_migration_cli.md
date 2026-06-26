# Local Migration CLI

## Decision

Phase 1 exposes the legacy memory migration safety contract through the
installed product CLI:

```text
maya migrate --from <legacy.sqlite> --to <destination.sqlite>
```

The command delegates to the packaged migration implementation and preserves
the existing safety defaults:

- dry-run is the default;
- `--apply` is required before any destination write;
- `--allow-modify` is required with `--apply`;
- applying to an existing destination requires `--backup`;
- applied migrations produce a JSON report.

The command prints a JSON summary. Failure output is generic and does not echo
source paths, destination paths, migrated values, memory contents, or secret
references.

## Limits

This command covers legacy `memory_kv` SQLite migration only. It is not the
final memory schema evolution framework, vector-index rebuild pipeline, or
cross-version product migration UX.
