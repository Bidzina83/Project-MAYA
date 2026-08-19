# Governed Memory

## Decision

Phase 1 assembled Maya products use `GovernedMemoryRetriever` for public
memory operations.

The underlying `Retriever` remains provider-agnostic storage and search.
Governance is applied by the product-facing memory facade before:

- `remember`
- `recall`
- `search`

Hermes retains its built-in conversation sessions, `MEMORY.md`, and `USER.md`.
Those records support Hermes operation and user preferences and are not moved
into Maya persistent memory. The installed external `maya` provider exposes
governed retrieval and explicit ingestion for SMB operational and business
information. Its turn synchronization hook is intentionally a no-op.

The Standard installer additionally configures the public Hermes memory-plugin
loader with provider `maya`. The installed provider uses
`LocalSQLiteVectorRetriever` and the configured Maya authorization policy and
audit sink. It does not create a Hermes-owned database or cloud memory account.

The first capabilities are:

- `memory.write`
- `memory.read`
- `memory.ingest`

Memory authorization decisions are written to the local runtime audit sink as:

```text
authorization.memory
```

Phase 1 configuration rejects `memory.governance_enabled: false`. The flag is
reserved for future policy design and is not an escape hatch around governed
retrieval in the minimal local product.

## Privacy

Memory audit records include decision metadata such as actor, capability,
operation, target, reason code, and stable memory identifiers. They must not
include memory record bodies, prompt text, completion text, raw files, secret
values, or connector payloads.

## Limits

Authorization and secret-safe audit are active for memory reads, ingestion,
embedding rebuilds, and writes.
The SQLite store persists trust and provenance fields, validates vector
dimensions, and supports governed full-text, vector, and hybrid retrieval. A
pinned offline ONNX model performs embedding generation when its disclosed and
hashed artifact is installed. Missing semantic artifacts leave lexical search
available but block semantic readiness. Richer classification, retention
enforcement, contradiction resolution, and a benchmarked large-collection
vector index remain follow-on work.
