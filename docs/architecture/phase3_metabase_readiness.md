# Phase 3 Metabase Readiness

## Status

Metabase readiness hardening slice for Phase 3 Capability Dependency and
Readiness Foundation.

## Decision

Maya reports Metabase readiness through deterministic local checks before
Metabase lifecycle management is treated as product-complete.

The `maya-metabase` profile now reports:

- Java runtime availability through the local `java` command.
- Metabase service configuration state without live network probing.
- Metabase application database configuration as a separate readiness surface.
- Approved analytics-source configuration as a separate readiness surface.

The readiness layer keeps the Product Specification V2 storage boundary:

1. Metabase application database.
2. Maya analytics data sources.
3. Maya persistent memory.

Maya persistent memory is not reported as an analytics source, and raw memory,
prompts, files, secrets, or customer records are not exposed to Metabase by
default.

## Readiness Behavior

`maya doctor` emits stable checks such as:

- `dependencies.profile.maya-metabase`
- `dependencies.runtime.java`
- `dependencies.service.metabase`
- `dependencies.database.metabase-application`
- `dependencies.database.metabase-analytics-sources`

Missing Java is a required dependency failure when `maya-metabase` is enabled.
Missing analytics sources are reported as optional readiness warnings because
Metabase can start before dashboards are provisioned. Missing Metabase service
configuration or application database configuration is treated as a required
readiness failure.

Messages are redacted. They report whether credential references are
configured, but do not print `secret://` values or database contents.

## Non-Goals

This slice does not:

- package Metabase;
- install Java;
- start, stop, migrate, back up, or upgrade Metabase;
- perform live HTTP health checks against a Metabase endpoint;
- provision dashboards, users, permissions, or analytics databases;
- expose Maya persistent memory as a Metabase source.

Those lifecycle and provisioning capabilities belong to later Metabase
integration work.
