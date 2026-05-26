# Changelog (auto-generated)

## 2026-05-26
- Merged PR #24: feat/add-memory-schemas-20260526 — Align memory_record.schema.json with pipeline (embedding field + metadata fields). CI guards and workflow_call inputs added to avoid job-level secrets references.
- Merged PR #26: ci: rerun main workflows (retry) — Re-ran CI after workflow fixes.
- Merged PR #27: fix(ingest): align embedder_wrapper with hermes implementation for tests — Makes ingest client output stable {id, vector} shape and deterministic ids for string inputs.

Notes:
- Canonical SQLite vector store table name used by LocalVectorStore is `entries`. Registry monitor prefers `entries` when present; older components may reference `embeddings` — prefer `entries` going forward.
