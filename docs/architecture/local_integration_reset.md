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

Phase 2 makes the reset/revocation boundary explicit. `reset-integration`
reports:

- whether local state would be or was removed;
- whether a credential reference is configured;
- whether provider-token revocation was requested;
- provider revocation status;
- the reason provider revocation did or did not happen.

Local reset does not revoke OAuth grants, Telegram bot tokens, broker
sessions, or customer-owned provider credentials. If provider revocation is
requested before a provider-specific revoker exists, Maya reports
`provider_revocation_status=unavailable` and
`external_revocation_performed=false`.
