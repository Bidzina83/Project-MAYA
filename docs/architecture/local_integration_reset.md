# Local Integration Reset CLI

## Decision

Phase 1 introduces a conservative local integration reset command:

```text
maya reset-integration <name> --config <maya-config.json>
maya reset-integration <name> --config <maya-config.json> --apply
```

The command is dry-run by default. It validates that `<name>` is present in the
typed integration configuration and plans removal of local connector state at:

```text
<deployment.data_dir>/integrations/<name>
```

When `--apply` is supplied, it deletes only that local integration state
directory. The command does not delete or print secret values, modify the
configuration file, contact external providers, revoke OAuth grants, revoke
Telegram bot tokens, or reset broker state.

The JSON result reports whether a credential reference is configured, but it
does not disclose the reference value.

## Scope

This is a Phase 1 local recovery surface. Full connector reset and revocation
requires provider-specific connector contracts, token ownership design,
allowlist reset behavior, audit records, and broker/customer-owned credential
mode handling.
