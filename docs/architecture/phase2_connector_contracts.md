# Phase 2 Connector Credential Contracts

Phase 2 adds static credential contracts for Google, Slack, and Telegram.
These contracts define which credential modes are allowed, whether a secret
reference is required, the connector capabilities, minimal initial scopes, and
the allowlist categories Maya must reason about.

The contract layer is deliberately not a live provider health check. It does
not perform OAuth, refresh tokens, call provider APIs, verify webhooks, or
claim revocation. Those belong to later connector validation and revocation
work.

## Supported Modes

Google supports:

- `broker`
- `customer_owned`
- `disabled`

Slack supports:

- `broker`
- `customer_owned`
- `disabled`

Telegram supports:

- `customer_owned`
- `disabled`

Telegram does not support broker credentials or a shared Maya-managed bot.

When `broker.mode=disabled`, Google and Slack configurations may not use
`credential_mode=broker`. Enabled connectors may not use
`credential_mode=disabled`. Credential-bearing modes require a
`secret://...` reference and validation reports only whether that reference is
present, never the value behind it.

## Boundary

The contract layer feeds typed configuration validation and connector
manifests. Connector operations still remain behind the local authorization
gateway, and unsupported provider operations must report unavailable rather
than healthy.
