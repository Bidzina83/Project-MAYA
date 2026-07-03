# Phase 4 Metabase Capability Hardening

## Status

Incremental hardening after the initial Phase 4 Metabase foundation.

## Decision

Metabase integration now reports lifecycle state separately from health and
provisioning.

The hardening keeps Metabase non-live by default:

- `customer_managed` deployments report that lifecycle ownership remains with
  the customer.
- `managed_local` deployments report whether the expected local service
  artifact is present without claiming Maya can start or upgrade Metabase.
- provisioning plans can be persisted as redacted JSON under
  `maya-data/metabase/provisioning`.
- `apply-provision` writes a redacted `last-applied-plan.json` only after
  local governance authorization succeeds.

## CLI Surface

```text
maya metabase lifecycle --config maya-config.json
maya metabase plan-provision --config maya-config.json --write
maya metabase apply-provision --config maya-config.json --apply
```

## Doctor Checks

`maya doctor` reports:

- `metabase.health`
- `metabase.lifecycle`
- `metabase.provisioning`

Managed-local missing artifacts are warnings, not false success claims.

## Boundaries

This hardening step does not:

- perform live HTTP Metabase checks;
- start, stop, install, upgrade, or back up Metabase;
- create live dashboards, users, collections, or permissions;
- expose Maya memory, prompts, secrets, files, or raw customer records.
