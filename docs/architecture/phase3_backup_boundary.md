# Phase 3 Backup Boundary

## Status

Accepted Product Spec V2 Phase 3 boundary for document and Metabase capability integration.

## Decision

Maya's default local backup captures Maya-owned runtime state and V2 Phase 3
capability artifacts, while keeping customer-managed analytics databases and
Metabase application state outside the archive unless a future explicit backup
contract opts them in.

Default backup includes:

- normalized `maya-config.json` with secret references only;
- governed audit and local runtime state already covered by Phase 1 backup;
- document outputs and caches under `maya-data/documents`;
- Metabase provisioning metadata under `maya-data/metabase/provisioning`.

Default backup excludes:

- customer analytics sources under `maya-data/analytics/sources`;
- Metabase application database state under `maya-data/metabase/application`;
- prior backup archives under `maya-data/backups`.

This preserves the V2 Phase 3 separation between:

1. Maya persistent memory and runtime state;
2. approved analytics source declarations and provisioning metadata;
3. customer-owned analytics databases;
4. Metabase's own application database.

## Rationale

Document outputs and Metabase provisioning plans are Maya-produced artifacts.
They are safe to include in the local Maya archive when the archive remains
customer-controlled and secret-safe.

Analytics databases and Metabase application databases may be large,
externally governed, separately backed up, licensed, encrypted, or managed by
customer infrastructure. Maya should not silently copy them into product
backups in V2 Phase 3.

## Future Work

A later backup phase may add explicit, customer-approved backup contracts for
selected analytics sources or managed-local Metabase application state. That
work needs its own retention, encryption, restore, size, locking, and platform
qualification rules.
