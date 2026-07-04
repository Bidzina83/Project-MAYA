# Phase 5 Token Lifecycle

Phase 5 token handling is dry-run-first, secret-safe, and provider-specific.

- OAuth session creation, token completion, refresh, and revoke mutations
  require `--apply`.
- Raw access tokens, refresh tokens, authorization codes, and verifier values
  are never printed in CLI output, docs, tests, audit summaries, or config.
- Token metadata records provider, lifecycle state, scopes, expiry,
  refresh-owner, rotation count, revocation time, and a `secret://` reference.
- Slack refresh rotates the refresh-token envelope and increments rotation
  metadata.
- Revocation deletes the local token envelope and records redacted revoked
  state; provider revocation remains broker-mediated.
