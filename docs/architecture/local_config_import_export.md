# Local Config Import And Export

## Decision

Phase 1 exposes normalized configuration portability through:

```text
maya export-config --config <path>
maya import-config --from <path> --to <path>
```

`export-config` validates the input and prints a normalized JSON
representation of the typed Project MAYA configuration.

`import-config` validates the source configuration and defaults to dry-run. It
only writes the normalized destination file when `--apply` is supplied. If the
destination already exists, `--allow-overwrite` is also required.

The normalized representation preserves secret references such as
`secret://integrations/google` but never reads, exports, imports, or prints
secret values from the platform secret store.

## Limits

This is not yet the final setup, profile migration, or policy-authoring UX. It
is the minimal Phase 1 import/export surface needed for reproducible local
configuration without raw credentials.
