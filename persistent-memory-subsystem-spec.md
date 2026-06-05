# Persistent Memory Subsystem — Formal Implementation Spec

Status: Draft for implementation
Last updated: 2026-06-05T21:55:03+00:00 (UTC)
Scope: filesystem-first persistent memory for organizational intelligence (Project: Maya — Information Manager AI Employee)
Canonical path: /opt/hermes/plugins/memory/docs/persistent-memory-subsystem-spec.md

---

## 1. Purpose and constraints

This subsystem provides persistent organizational memory for Project Maya by deriving semantic state from authoritative filesystem sources. It is a filesystem-first design: the filesystem is the source of truth and all derived semantic artifacts are augmentative, reproducible, and traceable back to source files.

Core constraints:
- The filesystem is authoritative. Do not mutate or replace source files from the semantic layer.
- Derived state (chunks, embeddings, entities, relations, timelines) is non-authoritative and must carry provenance back to the source (path, source_hash, extractor_version, timestamp).
- Storage must persist across process/container restarts and be reconstructable from sources.
- Governance and validators must run on every ingest and on retrieval-time decisions (privacy, retention, permissions).
- Prefer reusing existing upstream connectors (Google Workspace / Drive) as ingestion sources rather than rebuilding connectors.

Authoritative sources examples:
- Markdown documents, RFCs, policies
- Runtime logs and telemetry
- Documents, spreadsheets, PDFs (after extraction)
- Google Workspace artifacts accessed through existing connectors

Non-goals:
- This subsystem is not a general-purpose knowledge graph service for external consumers.
- It is not intended to replace upstream data stores nor to perform heavy-weight ML training.

---

## 2. Architecture overview (layers)

Layer 1 — Authoritative filesystem layer
- Immutable or versioned source files (or snapshots)
- Human-authored and system-generated documents
- Files are the canonical runtime artifacts

Layer 2 — Derived semantic layer
- Deterministic deterministic chunking of text into character-anchored chunks
- Embeddings (provider-abstracted)
- Entities and relationships (lightweight, provenance-aware)
- Timelines and event traces
- Local vector/index caches for retrieval speed

Layer 3 — Retrieval & context assembly layer
- Hybrid retrieval: metadata-first (filters) then vector fallback
- Context bundle construction (result list + provenance + confidence + gap notes)
- Permission-aware assembly and masking

Layer 4 — Governance & validators
- Schema validation, provenance checks, permission checks, retention enforcement, duplication detection
- Audit trail and telemetry for all mutations to derived state

Principles:
- Deterministic and reproducible indexing / chunking
- Always return provenance and confidence statements alongside semantic results
- Minimal surprises: never expose derived state without the source link(s)

---

## 1.x Recent operational changes (summary)

- 2026-06-05: Defensive hardening and CI/test compatibility updates were applied to the repository to address import-time failures observed on minimal CI runners. Changes included:
  - Added fallbacks in plugins/memory/holographic to tolerate missing runtime packages (agent, tools.registry, hermes_state) during test collection.
  - Made the MemoryStore initialization tolerant to a missing `hermes_state` by providing a best-effort fallback for apply_wal_with_fallback (no-op/WAL PRAGMA). This allows unit tests to run on runners where hermes_state is not installed.
  - Added missing adapter files and package markers (plugins/memory/adapters/*) and a maya-dev/.hermes_shim to mirror CI PYTHONPATH expectations.
  - CI workflow edits (branch fix/holographic-import-fallback-20260605) attempted to install `hermes_state` in test jobs, but `hermes_state` is not available on PyPI (pip reports no matching distribution). See "Known blockers" below.

Update: the most recent PR was merged by the user and CI on main ran green (verified 2026-06-05T21:55:03Z).

Known blocker and guidance

- `hermes_state` is not published to PyPI; installing it by name in CI will fail. Options:
  1) Remove hermes_state from the CI install list and rely on the `apply_wal_with_fallback` fallback in store.py (already committed). This avoids failing installs and keeps tests runnable in minimal runners.
  2) If `hermes_state` is required for production behavior, point CI at a concrete source (git URL or internal package index) and update the workflows to install from that source. Provide the URL if you want this option.

Local verification

- The holographic adapter unit test (plugins/memory/ingest/tests/test_holographic_adapter.py) passes locally in a virtualenv after adding the store fallback.
- Attempting `pip install -e . pytest jsonschema hermes_state` failed locally because `hermes_state` is not on PyPI.

Recommended immediate actions

1) Decide how CI should handle `hermes_state` (remove from installs, or provide an install source). If you prefer removal, I can update the workflows accordingly and push the change.
2) After CI install issues are resolved, re-run the failing workflows and fetch full logs for the most recent run to confirm no further import/runtime issues.
3) Consider keeping the `apply_wal_with_fallback` fallback (non-invasive, safe) to make test discovery more robust on minimal images, or replace it with the canonical `hermes_state` implementation when available.

---

## 3. Storage layout (recommended)

All persistent artifacts live under a single STORAGE_ROOT. Example:

STORAGE_ROOT/
  sources/               # read-only copies or canonical pointers to source artifacts (mirrors or references)
  registry/              # compact registry JSON (memory_registry.json) mapping sources -> derived objects
  chunks/                # per-source chunk files (JSONL) or uid.json
  embeddings/            # vector files (per-chunk) or vector DB pointers
  entities/              # entity records (JSON/JSONL)
  relations/             # relation records
  timelines/             # timeline/event records
  audit/                 # append-only audit logs and mutation records
  schemas/               # JSON schema files for chunk, entity, relation, registry
  cache/                 # transient caches (rebuildable)
  tmp/                   # short-lived staging

File responsibilities:
- registry/memory_registry.json: canonical registry (compact index) with counts and last_indexed timestamps
- chunks/*.jsonl: append-only chunk entries with fields {id, start, end, text, metadata}
- embeddings/*: provider-agnostic pointers or local vector files (persistable)
- audit/*: immutable audit lines (ISO timestamp, actor, operation, target, details)

Always include source_path, source_hash, extractor_version, and timestamp in derived records.

---

## 4. Data models & JSON schemas (summary)

Minimum JSON schemas to create under docs/schemas/:
- registry.schema.json — memory_registry entry shape
- chunk.schema.json — chunk record with provenance
- embedding.schema.json — embedding record (id, vector_length, provider, pointer)
- entity.schema.json — entity record (id, type, canonical_mentions, provenance)
- relation.schema.json — relation record (subject_id, object_id, predicate, provenance)

Each schema must declare required fields and validation rules used by validators. Keep schemas small and strict for Phase 1.

Example chunk record (conceptual):
{
  "id": "uuid4",
  "source_path": "/abs/path/to/source.md",
  "source_hash": "sha256hex",
  "extractor_version": "v0.1",
  "start": 102,
  "end": 478,
  "text": "...",
  "created_at": "2026-05-20T19:00:00Z"
}

---

## 5. Ingestion & indexing APIs (CLI + programmatic)

Provide two primary interfaces:

1) CLI (bin/memoryctl)
- bin/memoryctl validate-config --config /path/to/config.yaml
- bin/memoryctl ingest --source /path/to/file --dry-run --extractor-version v0.1
- bin/memoryctl rebuild-registry --force
- bin/memoryctl health

2) Programmatic API (Python)
- ingest.file(path: str, extractor_version: str = 'v0.1', dry_run: bool=False) -> IngestReport
- index.chunks(chunks: List[Chunk]) -> IndexReport
- registry.query(filters: dict) -> list
- retrieve(query: str, metadata_filters: dict, top_k: int=5) -> RetrievalBundle

All ingest operations must:
- validate source (permissions, allowed MIME)
- compute source_hash (sha256) of text bytes
- produce character-anchored chunks
- run validators before writing derived artifacts
- append audit records

---

## 6. Chunking & embedding strategy (deterministic)

Chunking rules (Phase 1):
- Chunk on paragraph boundaries where possible
- Max chunk size configurable (default 1000 chars)
- If paragraph exceeds max_chars, split by sentence-like boundaries
- Persist chunk start/end offsets and provenance

Embedding rules:
- Use an embedding client abstraction (provider-agnostic wrapper)
- Record embedding metadata: model, dim, provider, provider_version, created_at
- Store vectors either as files under embeddings/ or as pointers to a local vector DB (Chroma/SQLite combo)

---

## 7. Validators & governance

Validators run at ingest and on-demand:
- Schema validator (strict JSON schema checks against schemas/)
- Provenance validator (requires source_path, source_hash, extractor_version, timestamp)
- Permission validator (enforces that derived exposure honors source permissions)
- Retention validator (checks file age/retention tags)
- Duplication validator (detect same source_hash pre-indexed)

Failure modes:
- On critical validation failure: abort ingest, preserve original source, append audit entry, surface error for human review.
- On non-critical (warning) failure: index with warning flag and include in registry; schedule human review.

Governance hooks:
- Admin endpoint to approve or reject flagged derived artifacts
- Periodic audit job to re-run validators across registry

---

## 8. Retrieval semantics

Hybrid retrieval pipeline:
1. Metadata filter stage (date ranges, author, source_path prefixes, entity filters)
2. Vector-based fallback (embedding similarity) scoped by metadata results
3. Deterministic scoring + explainability layer (explain why each item matched)
4. Context assembly: bundle selected chunks, attach citations (source_path + char range), attach provenance, and produce confidence/gap notes

Always include the following in responses:
- citations: list of {source_path, start, end, snippet}
- registry_ids/record ids
- extractor_version and timestamp
- short statement of confidence and any missing-sources note

---

## 9. Phased implementation plan (T0 → T4)

T0 — Project scaffolding (1-2 days)
- Create docs/ and docs/schemas/ and add canonical spec
- Create STORAGE_ROOT directory layout (empty placeholders)
- Add README pointing to canonical path
- Create minimal tests folder structure

T1 — Storage & ingestion pipeline (Phase 1) (3-5 days)
T1.0: Chunker implementation (deterministic, tested)
- Implement ingest/chunker.py (chunk_text, chunk_file)
- Unit tests ensuring round-trip reconstruction and provenance

T1.1: Embedding wrapper (provider-agnostic) — minimal skeleton
- Implement ingest/embedder.py with dummy vector backend for tests
- Unit tests for embedder API

T1.2: Registry writer & schema files
- Implement registry writer that writes registry/memory_registry.json
- Add JSON schemas under docs/schemas/
- Unit tests for registry consistency

T1.3: CLI glue (memoryctl ingest --dry-run)
- Implement CLI entrypoints and dry-run mode
- Hook chunker -> embedder (dry-run uses dummy embedder)

T2 — Persistence & vector store integration (2-3 days)
- Optionally integrate lightweight local vector store (Chroma/SQLite) with file pointers
- Add embedding persistence and retrieval adapters

T3 — Retrieval + governance (3-5 days)
- Implement retrieval pipeline, metadata filters, explainability
- Implement validators (permission/retention/duplication)
- Add audit trail integration

T4 — Hardening, tests, and CI (2-4 days)
- Add end-to-end integration tests using small sample dataset
- Add CI job to validate schemas and run tests
- Add documentation and operational playbook (backup, restore, rebuild)

Each task must follow TDD: write failing test, run to fail, implement minimal code, run to pass, commit.

---

## 10. Verification & acceptance criteria

- Source files remain unchanged after indexing (checksum check)
- Every derived record contains provenance and a valid source_hash
- Registry survives restart and matches derived counts
- Retrieval returns provenance with each result
- Validators block invalid or unauthorized operations
- Tests: unit tests for chunker/embedder/registry + integration test that runs ingest --dry-run and validates outputs

---

## 11. Operational notes & automation hooks

- auto_resume.py should reference the spec path (already configured). Use auto_resume for resuming tasks.
- Use a lockfile for ingest operations to enforce single-writer principle.
- Provide "--dry-run" flags widely for safe iteration.

---

## 12. Next steps (immediate)

1. Recreate this spec file at the canonical path (done)
2. Add docs/schemas/ with minimal schemas for chunk and registry
3. Implement and test chunker (ingest/chunker.py) — unit tests exist under plugins/memory/ingest/tests/
4. Implement embedder skeleton (ingest/embedder.py) — test and replace with real provider later
5. Add registry writer and CLI entrypoints
6. Save canonical path into persistent memory (optional) so Project Maya always finds it without repo-wide search

---

## 13. Appendix: canonical paths & pointers

- Spec (canonical): /opt/hermes/plugins/memory/docs/persistent-memory-subsystem-spec.md
- Implementation plugin root: /opt/hermes/plugins/memory/
- Ingest code: /opt/hermes/plugins/memory/ingest/
- Tests: /opt/hermes/plugins/memory/ingest/tests/
- Session-derived notes: /opt/data/skills/software-development/writing-plans/references/persistent-memory-subsystem-notes.md

---

(End of spec draft)
