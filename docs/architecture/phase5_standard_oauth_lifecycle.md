# Phase 5 Standard OAuth Lifecycle

Standard Google and Slack OAuth is broker-assisted but locally governed.
Configuration stores only secret references and redacted lifecycle metadata.

## Google

Google OAuth sessions use PKCE S256, state, nonce, short expiry, provider
binding, and loopback/manual callback completion. The local deployment stores
the resulting token envelope only through the approved `SecretStore`.

Google refresh ownership is local where technically possible. The broker helps
with setup and signed credential handoff; it is not persistent memory or a
governance authority.

## Slack

Slack OAuth uses the same local session controls and records refresh ownership
as `broker_assisted`, matching Slack token rotation where the distributed app
secret remains broker-controlled. Local Maya stores redacted lifecycle
metadata and encrypted token material only through the approved `SecretStore`.

## Exclusions

Telegram is not broker-assisted. Enterprise deployments use customer-owned
Google and Slack applications unless policy explicitly chooses broker
participation.
