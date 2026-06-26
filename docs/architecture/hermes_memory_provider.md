# Hermes Memory Provider

## Decision

Phase 1 uses `HermesMemoryProvider` as the runtime-facing memory adapter
attached to the Maya `Agent` before Hermes startup.

The provider does not own a separate store. It delegates persistence and
search to `GovernedMemoryRetriever`, which in turn applies local authorization
before using the configured `Retriever`.

```text
Hermes runtime
  -> HermesMemoryProvider
    -> GovernedMemoryRetriever
      -> MemoryRetriever
        -> configured Retriever
```

## Supported Phase 1 Hooks

The provider exposes the first Hermes-facing memory hooks:

- `begin_session(session_id)`
- `end_session(session_id=None)`
- `prefetch(query, category=None, limit=5)`
- `recall(memory_id)`
- `remember(document)`
- `synchronize_turn(records=None)`

`prefetch` and `recall` are governed memory reads. `remember` and
`synchronize_turn` are governed memory writes. Denied decisions stop the memory
operation before records are returned or persisted.

## Privacy

The provider never writes prompt bodies or memory document bodies to audit
records. Audit events are produced by `GovernedMemoryRetriever` and contain
authorization facts such as capability, operation, target, reason code, and
stable memory identifiers.

## Limits

This is the first local MemoryProvider adapter. It does not yet implement
vector prefetch ranking, provider-specific Hermes session objects, retention
policy, migration, conflict handling, or shutdown compaction. Those later
features must preserve this dependency direction and continue using governed
retrieval as the control point.
