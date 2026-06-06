Retrieval normalization migration - design and runbook

Overview
--------
This document describes the safe migration approach for computing and storing
L2-normalized embedding vectors alongside the original vectors. The goal is to
preserve original embeddings for audit/reindexing while enabling fast retrieval
using a precomputed normalized vector.

Schema changes
--------------
Table: entries
Add columns (ALTER TABLE):
- normalized_vector TEXT           -- JSON array of floats (L2-normalized)
- normalized_vector_dim INTEGER    -- number of floats in normalized_vector
- normalized_vector_algo TEXT     -- e.g. "l2-v1"
- normalized_at TEXT               -- ISO8601 UTC timestamp when normalized
- normalized_version INTEGER       -- integer version so future algorithm changes can be detected

Principles
----------
- Original `vector` column is never overwritten.
- Normalized vectors are stored in `normalized_vector` and associated metadata columns.
- Backfill is idempotent and parameterized by `algo` and `version`.
- Retrieval logic prefers `normalized_vector` when present, and falls back to normalizing `vector` in-memory when absent.

Backfill script
----------------
Location: plugins/memory/scripts/backfill_normalize_entries.py
- Adds normalized columns if missing.
- Selects rows needing normalization (normalized_vector IS NULL OR algo/version mismatch).
- Computes normalized_vector = vector_normalize(original_vector) and writes normalized fields.
- Commits in batches (default chunk=1000).
- Supports --dry-run for validation.

Retrieval changes
-----------------
Location: plugins/memory/adapters/local_vector_adapter.py
- When reading rows, prefer normalized_vector if present.
- If normalized_vector missing, load original `vector` and normalize it in-memory.
- Use normalized vectors for similarity computations; convert cosine [-1,1] to [0,1] as before.

Tests
-----
New tests: plugins/memory/ingest/tests/test_backfill_and_ranking.py
- test_ranking_consistency_before_after_normalization: builds a small LocalVectorStore, verifies the top-k order is identical before and after writing normalized_vector (simulating backfill).
- test_backfill_idempotent: runs the backfill twice (via import) against a test DB and asserts the second run produces no additional updates.

Docs & runbook
---------------
This file (docs/retrieval_normalization_migration.md) is the migration runbook:
- Backup DB first: cp /path/to/store.db /path/to/store.db.bak
- Run a staging backfill: cp store.db /tmp/store.stage.db; python3 plugins/memory/scripts/backfill_normalize_entries.py --db /tmp/store.stage.db --dry-run; inspect; then run without --dry-run
- Verification queries provided below (count needing normalization, sample rows, etc.)

Rollback
--------
- Restore DB from the backup if any issue: cp /path/to/store.db.bak /path/to/store.db

Approval
--------
Do NOT run the backfill until this implementation and tests are reviewed and the DB path and staging plan are provided.

