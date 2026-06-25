# Governed Memory

## Decision

Phase 1 assembled Maya products use `GovernedMemoryRetriever` for public
memory operations.

The underlying `Retriever` remains provider-agnostic storage and search.
Governance is applied by the product-facing memory facade before:

- `remember`
- `recall`
- `search`

The first capabilities are:

- `memory.write`
- `memory.read`

Memory authorization decisions are written to the local runtime audit sink as:

```text
authorization.memory
```

## Privacy

Memory audit records include decision metadata such as actor, capability,
operation, target, reason code, and stable memory identifiers. They must not
include memory record bodies, prompt text, completion text, raw files, secret
values, or connector payloads.

## Limits

This is a minimal Phase 1 guard. Future work should add richer memory
classification, retention policy, trust metadata checks, provenance-aware
read policy, and governed vector retrieval.
