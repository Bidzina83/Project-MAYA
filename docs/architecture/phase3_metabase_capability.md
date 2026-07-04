# Phase 3 Metabase Capability

## Status

Final V2 Phase 3 Metabase integration and dashboard provisioning capability.

## Decision

Project MAYA now owns a `project_maya.metabase` capability layer for
Metabase health, governed views, dashboard specifications, and provisioning
plans.

The layer supports two deployment modes:

- `customer_managed`: Maya validates and plans against a customer-operated
  Metabase endpoint.
- `managed_local`: Maya reports local lifecycle/provisioning contracts, but
  only runs lifecycle actions when required runtime artifacts and
  configuration exist.

## Store Separation

The Product Spec V2 Phase 3 Metabase capability preserves the Product Specification V2
boundary between:

1. Metabase application database;
2. Maya analytics data sources;
3. Maya persistent memory.

Provisioning plans exclude raw memory, prompts, secrets, files, and
unapproved customer records by default.

## Health And Provisioning

Metabase health validation is secret-safe and local by default. It validates:

- deployment mode;
- endpoint shape;
- application database configuration;
- credential-reference presence;
- analytics source declaration count.

Opt-in live health checks are timeout-bounded and redact endpoint and
credential details. Unreachable endpoints report `live_unavailable` rather
than leaking network or credential state.

Lifecycle reporting is separate from health. Customer-managed deployments
report customer ownership. Managed-local deployments report whether the local
service artifact is present without claiming start/stop support.

Provisioning is plan-first. Plans include governed views, cards, and dashboard
specifications for approved analytics sources. Redacted plans may be written
under:

```text
maya-data/metabase/provisioning/
```

`apply-provision` requires local governance authorization and records the
governed apply event plus redacted applied-plan and dashboard files. These
artifacts prove the approved dashboard/view boundary without exposing memory,
prompts, files, secrets, or unapproved records.

## Deferred Work

- live Metabase user, collection, and permission creation;
- managed-local Metabase start/stop/upgrade/backup lifecycle;
- bundled Metabase runtime artifacts;
- analytics database migrations;
- production installer qualification.
