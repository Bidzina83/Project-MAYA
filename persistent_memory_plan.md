Persistent Memory Implementation Plan — Project MAYA

Goal
Build a filesystem-first persistent semantic memory subsystem for Project MAYA that is reproducible, provenance-rich, test-driven, and discoverable by auto-resume and developer tooling.

Canonical references
- Spec path (canonical): /opt/hermes/plugins/memory/docs/persistent-memory-subsystem-spec.md
- Repo plugin path: /opt/hermes/plugins/memory/
- Ops lookup symlink: /opt/data/docs/persistent-memory-subsystem-spec.md

Constraints
- Filesystem-first: all source artifacts remain on disk with provenance (path, source_hash, extractor_version, timestamp).
- Use existing Google Workspace/Drive connectors for ingestion (do not rebuild connectors).
- Co-locate docs, JSON schemas, and tests under /opt/hermes/plugins/memory/docs and /opt/hermes/plugins/memory/schemas.
- TDD: write failing tests first, implement, then verify.
- No secrets in docs.

Deliverables
1. JSON schemas for memory records, provenance and index metadata (stored under docs/schemas/).
2. Deterministic ingestion pipeline: chunker → extractor → embedder → indexer (with config and versions recorded).
3. Embedding client wrapper + tests (T1.1 already started: embedder.py skeleton).
4. Chunker tests (existing) executed, fixed if failing.
5. CI task(s) to run tests and lint on PRs.
6. Persistent pointer recorded in assistant memory and a git commit in a durable repo.
7. A Google Drive document copy of this plan at: MyHermes/Project MAYA/Persistent Memory (this document).

Implementation tasks (bite-sized, ordered)
T0 — Verify environment (pre-reqs)
  - T0.1: Confirm google-workspace auth (run /opt/data/skills/productivity/google-workspace/run_setup --check). If not authenticated, run setup flow with user.
  - T0.2: Ensure python venv available at /opt/data/google_workspace_venv.
  - T0.3: Confirm write permission to /opt/hermes or plan alternate commit location (/opt/data/maya-memory-repo).

T1 — Embedding client (skeleton present)
  - T1.1: Write unit tests for embedder wrapper (tests/test_embedder.py). Fail first.
  - T1.2: Implement embedder to support pluggable backends (openai, local-gguf, hf). Use config: EMBED_BACKEND, EMBED_MODEL, BATCH_SIZE.
  - T1.3: Add deterministic hashing of input chunk to record provenance (sha256) and extractor_version.
  - T1.4: Run tests, iterate until green.

T2 — Chunker & extractor
  - T2.1: Run existing chunker tests (pytest -q plugins/memory/ingest/tests/test_chunker.py).
  - T2.2: Fix chunker edge-cases: unicode, long URLs, code blocks, PDF text noise.
  - T2.3: Add provenance metadata per chunk: source_path, source_hash, extractor_version, extracted_at.
  - T2.4: Add tests to assert provenance fields exist and stable hashing across runs.

T3 — Schema & storage layout
  - T3.1: Create JSON schemas under /opt/hermes/plugins/memory/docs/schemas/
    - memory_record.schema.json
    - provenance.schema.json
    - index_entry.schema.json
  - T3.2: Add schema validation tests using jsonschema.
  - T3.3: Document storage layout: /opt/hermes/data/memory/{year}/{month}/{sha256}.json (example layout in spec).

T4 — Indexer & retrieval metadata
  - T4.1: Define index entry fields (embedding_id, chunk_id, vector_dim, created_at, source_path, score_meta).
  - T4.2: Implement index writer with atomic commits (write to tmp then move) and tests.
  - T4.3: Add small local vector store adapter for CI tests (in-memory or sqlite-backed).

T5 — Ingestion pipeline orchestration
  - T5.1: Compose pipeline CLI: ingest --source /path --config /opt/hermes/plugins/memory/ingest/config.yaml
  - T5.2: Ensure idempotence: pipeline should skip already-ingested files using stable source_hash.
  - T5.3: Add logging and per-file ingestion report (counts, durations, errors).

T6 — CI and repo durability
  - T6.1: Create repo or commit into existing repo: add docs/schemas and tests; commit message: "chore(memory): add persistent memory schemas and tests"
  - T6.2: Add GitHub Actions job: memory/ci.yml to run pytest and jsonschema validation on commits.
  - T6.3: Push to remote (requires remote URL and auth) and tag a release v0.1-memory-spec.

T7 — Operationalization and pointer
  - T7.1: Add persistent assistant memory pointer to canonical spec path (if capacity allows). If memory full, replace older less-useful entry explicitly.
  - T7.2: Maintain symlink in /opt/data/docs pointing to canonical path (done).
  - T7.3: Add README with quick-start and auto_resume instructions under /opt/hermes/plugins/memory/docs/README.md.

Verification & acceptance
- For each T# task, write unit tests first and ensure they fail; implement minimal code to pass tests.
- After creation actions in Drive or repository, run a separate read/get to verify and include webViewLink and fileId in the verification report.
- CI passes on main branch for all tests and lint checks.
- auto_resume.py should validate the spec path without needing a repo search.

Estimated effort (rough)
- T0: 0.5 day
- T1: 1-2 days
- T2: 1-2 days
- T3: 0.5-1 day
- T4: 1-2 days
- T5: 1-2 days
- T6: 0.5-1 day (excluding remote push time)
- T7: 0.5 day

Next immediate actions I will perform now (with your approval already given):
1) Create a Google Doc titled "Persistent Memory Implementation Plan (Project MAYA)" in MyHermes/Project MAYA/Persistent Memory and verify its creation.
2) If you want, also create a local copy at /opt/hermes/plugins/memory/docs/implementation-plan.md and/or commit into a repo under /opt/data/maya-memory-repo.
