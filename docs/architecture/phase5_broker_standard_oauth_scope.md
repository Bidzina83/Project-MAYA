# Phase 5 Scope: Broker and Standard OAuth

## Status

Implementation-ready Product Spec V2 Phase 5 scope. Final closure remains
review-ready until an independent security review artifact is recorded.

## Objective

Product Spec V2 Phase 5 is reserved for the broker and Standard OAuth work:
mock broker conformance, cryptographic instance protocol, approved token
lifecycle, production Google and Slack OAuth, and optional Maya-managed model billing.

## Boundary

Setup, recovery, backup, restore, health, and update-readiness operator
surfaces are V2 Phase 4 work. They must not be used as evidence that V2 Phase
5 is complete.

Phase 5 is not complete until independent security review and
credential-lifecycle tests pass.

## Product Surfaces

- `project_maya.broker` exports the broker protocol, OAuth session, token
  lifecycle, conformance, and model-proxy readiness contracts.
- `maya broker status`, `register`, `oauth-start`, `oauth-complete`,
  `token-status`, `token-refresh`, `token-revoke`, `conformance`, and
  `model-proxy-status` expose the operator CLI.
- Google and Slack are the only broker-assisted OAuth providers in Phase 5.
- Telegram remains customer-owned only.
