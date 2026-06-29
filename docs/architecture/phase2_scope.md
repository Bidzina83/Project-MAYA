# Phase 2 Scope Gate

## Status

Phase 2 started after the Phase 1 closure checkpoint. Its purpose was to prove
that Maya Enterprise can operate with customer-owned credentials and with Maya
cloud services disabled.

The Phase 2 objective is:

```text
Enterprise operates without Maya cloud services.
```

Phase 2 must build on the Phase 1 local runtime, governance, memory, secrets,
audit, local API, backup, restore, migration, repair, integration reset, and
update-status surfaces. It must not create a second runtime, bypass local
governance, or move authoritative state into Maya cloud services.

Phase 2 closure evidence is recorded in
`docs/architecture/phase2_closure.md`.

## Acceptance Criteria

Phase 2 is complete only when all of these are true:

1. An Enterprise configuration with `broker.mode=disabled` validates and
   assembles without requiring Maya cloud endpoints.
2. Customer-owned model credentials are represented as secret references and
   can be validated without exposing secret values.
3. Customer-owned or local model endpoints can be configured through the
   existing Hermes-compatible model adapter boundary.
4. Google, Slack, and Telegram connector credential modes are contractually
   represented as `customer_owned`, `broker`, `local_only`, or `disabled`.
5. Connector validation reports capabilities, scopes, credential-reference
   state, allowlist state, and redacted health without contacting unsupported
   provider flows.
6. Connector reset and revocation contracts distinguish local state reset from
   provider-token revocation and never claim revocation when it did not occur.
7. The local API, governed runtime, model egress policy, memory provider,
   audit sink, backup/restore, and diagnostics operate with the broker
   disabled.
8. Clean package verification covers the Enterprise BYO command/configuration
   surfaces without editable installs or repository path shims.
9. The Phase 2 closure audit maps each accepted capability to tests and docs.

## Non-Goals

Phase 2 does not implement:

- production Maya OAuth Broker protocol;
- broker-assisted Standard Google or Slack OAuth;
- Maya-managed model billing or model proxying;
- production provider token refresh;
- production connector webhooks or event ingestion;
- Metabase service packaging or dashboard provisioning;
- document processing, browser automation, or local model installation;
- signed installers, SBOMs, release provenance, or automatic updates;
- shared Maya-managed Telegram bots.

## Implementation Order

Work Phase 2 in this approved order unless a later approved architecture
decision changes it:

1. Phase 2 scope gate.
2. Model credential modes.
3. Connector credential contracts.
4. Connector validation.
5. Connector revocation and reset contracts.
6. Broker-disabled runtime path.
7. Enterprise config profiles.
8. Local model endpoint readiness.
9. Secret backend extension point.
10. Phase 2 package verification.
11. Phase 2 closure audit.

## Required Boundaries

- Configuration stores secret references, not raw credentials.
- External model calls remain governed data egress.
- Connector operations remain behind local authorization.
- Broker-disabled mode must not silently fall back to Maya cloud.
- Telegram remains customer-owned only.
- Local state remains authoritative for memory, governance, audit, operational
  state, and backups.
- Unsupported provider operations must report unavailable rather than healthy.
