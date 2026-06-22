Migration specification — legacy memory_kv → Project-MAYA registry

Overview

Purpose
- Convert legacy key/value persistence (table `memory_kv`) into the canonical Project-MAYA registry schema so migrated data is immediately usable by downstream consumers without code changes.
- Record provenance and fail-safe behavior; enable future schema evolution via Alembic-managed revisions.

Scope
- Source: legacy SQLite DB with table `memory_kv(key TEXT PRIMARY KEY, value TEXT)`.
- Destination: Project-MAYA registry schema (tables `entries` + `embeddings`) OR the legacy `memory_entries` prototype table (optional).

High-level rules
1) Target selection
   - Default target: `registry` (entries + embeddings).
   - Optional target: `memory_entries` (keeps earlier simple schema). Use `--target-schema` to override.

2) Row transformation
   - For each (key, value) in `memory_kv`:
     a) If `value` parses as a JSON array of numbers (numeric vector):
        - entries.embedding_id = key (string)
        - entries.chunk_id = key
        - entries.vector = canonical JSON string of the numeric array (compact)
        - entries.vector_dim = length(array)
        - entries.created_at = original timestamp if present else current UTC ISO timestamp
        - entries.source_path = "legacy_kv"
        - entries.score_meta = JSON({"migrated_from": <src_path>, "original_sha256": <sha256_of_value>})
        - Upsert embeddings row with chunk_id=key, source_path="legacy_kv", source_hash=<sha256>, extractor_version="legacy-migration", embedding_timestamp=entries.created_at, updated_at=now
     b) If `value` does NOT parse as numeric vector:
        - entries.embedding_id = key
        - entries.chunk_id = NULL
        - entries.vector = NULL
        - entries.vector_dim = NULL
        - entries.created_at = now
        - entries.source_path = "legacy_kv"
        - entries.score_meta = JSON({"migrated_from": <src_path>, "legacy_value_sha256": <sha256_of_value>})
        - Optionally create embeddings row with chunk_id=NULL and source_hash recorded (recommended for provenance)

3) Conflict policy
   - Default behavior: SKIP migration for keys where entries.embedding_id already exists in destination. Record skipped keys in the migration report.
   - Optional flags:
     --overwrite: replace existing destination rows (dangerous; requires explicit consent and backup)
     --report-only: collect a full report of conflicts and proposed actions and exit (equivalent to dry-run + conflict log)

4) Validation and post-checks
   - Verify migrated_count == number of source rows minus skipped due to conflicts.
   - For numeric-vector rows: parse entries.vector and assert vector_dim == len(parsed_vector).
   - Sample N rows (default N=5) and validate parseability and value ranges.
   - Produce a migration report (JSON) with: source_rows, migrated, skipped_keys, samples, validation_errors, duration, to_path.

5) Provenance & audit
   - Every migrated row must include in entries.score_meta a JSON object containing at least {"migrated_from": <abs_source_path>, "original_sha256": <hex>}.
   - Keep a migration log file alongside the destination DB (destination_path + ".migration.log.json").

6) Safety and backups
   - DO NOT run in-place migration against a live registry without a backup.
   - Default operation is dry-run; operator must pass --apply (or dry_run=False) plus explicit --allow-modify to perform writes.
   - Before a non-dry-run in-place migration: create a backup copy of the live DB and verify the backup is restorable.

7) Tests to include (unit + integration)
   - Unit: numeric vector migration -> entries.vector + vector_dim populated and embeddings upserted.
   - Unit: non-numeric value -> entries.vector NULL and score_meta contains original hash.
   - Unit: conflict handling -> ensure skip vs overwrite behavior works.
   - Integration: migrate a sample legacy DB into a fresh alembic-upgraded registry DB; run validation and assert counts.

8) Runtime and ops notes
   - The migrate() function exposes a target_schema parameter ("registry" | "memory_entries") and supports dry_run and apply modes.
   - The migration creates/ensures the destination schema when targeting the registry (idempotent CREATE TABLE IF NOT EXISTS statements), but Alembic must be used to record schema versions and evolve the canonical schema going forward.

9) Alembic and schema evolution
   - Add Alembic to project dependencies (pyproject/requirements).
   - Create alembic.ini and env.py configured for the project's SQLAlchemy models and set target_metadata to the model metadata for autogenerate.
   - Initial revision: create a baseline revision that captures the current canonical schema (entries + embeddings). This file is in alembic/versions/0001_initial_registry_schema.py in the workspace.
   - Workflow: for future schema changes, create incremental alembic revisions and run alembic upgrade/downgrade under CI.

10) Rollback plan
   - If --overwrite is used, the only safe rollback is to restore the pre-migration backup. Document restore steps in the migration report.

Operational commands (examples)
- Dry-run targeting registry:
  python3 scripts/migrate.py --from /path/to/legacy.db --to /tmp/out.db --target-schema registry --dry-run

- Apply into a new destination DB (safe, not in-place):
  python3 scripts/migrate.py --from /path/to/legacy.db --to /tmp/new_registry.db --target-schema registry

- Apply in-place (NOT recommended) with explicit allow flags (operator must confirm):
  python3 scripts/migrate.py --from /path/to/legacy.db --to /opt/data/Project-MAYA/registry/memory_registry.sqlite --target-schema registry --allow-modify --backup /opt/data/Project-MAYA/registry/memory_registry.sqlite.bak

Reporting
- The migration run will write a JSON report to <to_dest>.migration.report.json containing counts, lists of skipped keys, sample mappings, and validation status.

Appendix: sample JSON for score_meta
- {"migrated_from": "/path/to/legacy.db", "original_sha256": "<hex>", "note": "migrated by scripts/migrate.py v1"}

