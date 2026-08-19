---
name: information-manager/business-memory
origin: maya_trained
version: 0.1.0
capabilities:
  - memory.read
  - memory.write
---

# SMB Business Memory

Use Maya business memory for durable operational and business information about
the customer organization. Do not use it for Hermes conversation sessions,
agent operating notes, or user preferences; Hermes continues to own those in
its normal session store, `MEMORY.md`, and `USER.md`.

Use `maya_business_memory_search` to retrieve relevant customer-controlled
business records. Use `maya_business_memory_ingest` only for approved files
inside the configured Maya documents directory. Use
`maya_business_memory_rebuild_embeddings` after an approved local embedding
model update or when doctor reports stale or missing vectors.

Every read and write passes through Maya's local authorization gateway and
audit sink. Never bypass the tools with direct SQLite access. Do not place
credentials, tokens, passwords, or raw secret values in persistent memory.
