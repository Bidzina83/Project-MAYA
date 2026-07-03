# Phase 4 Metabase Capability

## Status

Initial Metabase integration and provisioning foundation.

## Decision

Project MAYA now owns a `project_maya.metabase` capability layer for
Metabase health and provisioning plans.

The layer supports two deployment modes:

- `customer_managed`: Maya validates and plans against a customer-operated
  Metabase endpoint.
- `managed_local`: Maya reports local lifecycle/provisioning contracts, but
  only runs lifecycle actions when required runtime artifacts and
  configuration exist.

## Store Separation

The Phase 4 Metabase capability preserves the Product Specification V2
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

Lifecycle reporting is separate from health. Customer-managed deployments
report customer ownership. Managed-local deployments report whether the local
service artifact is present without claiming start/stop support.

Provisioning is plan-first. Redacted plans may be written under:

```text
maya-data/metabase/provisioning/
```

`apply-provision` requires local governance authorization and currently records
the governed apply event plus a redacted applied-plan file without live
Metabase mutations.

## Deferred Work

- live HTTP Metabase health checks;
- dashboard, user, collection, and permission creation;
- managed-local Metabase start/stop/upgrade/backup lifecycle;
- bundled Metabase runtime artifacts;
- analytics database migrations;
- production installer qualification.
