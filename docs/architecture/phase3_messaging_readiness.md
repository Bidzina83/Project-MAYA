# Phase 3 Messaging Readiness

## Status

Messaging and connector readiness refinement slice for Phase 3 Capability
Dependency and Readiness Foundation.

## Decision

Maya reports messaging readiness through the existing Phase 2 connector
contracts and validators. The dependency layer does not create a second
connector health system.

The `maya-messaging` profile now reports, for Google, Slack, and Telegram:

- external-service readiness through `validate_configured_connectors()`;
- connector contract readiness, including credential mode, capabilities, and
  declared scopes;
- governance and allowlist readiness, including local policy requirement and
  allowlist configuration state.

Telegram remains customer-owned only. Maya does not provide or recommend a
shared Maya-managed Telegram bot.

## Doctor Behavior

`maya doctor` emits stable checks such as:

- `dependencies.profile.maya-messaging`
- `dependencies.service.google`
- `dependencies.connector.google-contract`
- `dependencies.connector.google-governance`
- `dependencies.service.slack`
- `dependencies.connector.slack-contract`
- `dependencies.connector.slack-governance`
- `dependencies.service.telegram`
- `dependencies.connector.telegram-contract`
- `dependencies.connector.telegram-governance`

Disabled connectors report `disabled` readiness and do not fail the profile.
Enabled connectors with valid static configuration report customer-managed
readiness and `network_used=false`. Invalid connector configuration remains a
required readiness failure.

Messages are redacted. They may include credential-reference state, credential
mode, capability names, declared scopes, allowlist categories, and health
state, but do not print `secret://` references, token values, webhook payloads,
messages, chat IDs, channel IDs, user IDs, or provider responses.

## Non-Goals

This slice does not:

- perform live OAuth;
- validate token freshness with Google, Slack, or Telegram;
- verify provider webhooks or events;
- send or receive messages;
- revoke OAuth grants or Telegram bot tokens;
- implement broker-assisted Standard OAuth.

Those capabilities belong to later connector adapter, broker protocol, and
provider-specific lifecycle work.
