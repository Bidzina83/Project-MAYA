# Retrieval Normalization Migration Playbook

This playbook describes staging and production steps to backfill normalized vectors, verify retrieval correctness, and roll out retrieval preference to use normalized vectors.

Prerequisites
- Ensure backups of the target DB are taken and accessible.
- Operator has read/write access to DB file or DB connection string.
- CI/test runner with same schema available for dry runs.

High-level steps
1. Prepare: create feature branch, add migration scripts, add metrics and diagnostics (already merged to main).
2. Dry-run on staging: run backfill script with --dry-run to estimate rows and time.
3. Validate: run verification queries and ranking-consistency checks.
4. Backfill staging (non-dry-run) in a maintenance window if needed.
5. Monitor metrics and run acceptance tests.
6. Roll out to production with appropriate maintenance window and rollback plan.

Dry-run command (local/staging):

  python plugins/memory/scripts/backfill_normalize_entries.py --db /path/to/staging.db --chunk 500 --dry-run --metrics-output /tmp/backfill_metrics.json

Real run (staging):

  python plugins/memory/scripts/backfill_normalize_entries.py --db /path/to/staging.db --chunk 500 --metrics-output /tmp/backfill_metrics.json

Verification checks
- Confirm updated count: check printed summary or metrics JSON ("updated").
- Run ranking-consistency smoke tests (re-using test_backfill_and_ranking.py utilities):
  - Before backfill: sample N queries, record ranked ids.
  - After backfill: rerun queries and assert ranking unchanged (within tolerance).
- Spot-check rows: SELECT embedding_id, normalized_vector, normalized_vector_dim, normalized_vector_algo FROM entries WHERE embedding_id IN (...)

Metrics to collect
- rows_examined, rows_updated, total_time_seconds, avg_time_per_row_ms, rows_per_second.
- Per-query metrics: rows_scanned, used_precomputed_normalized (boolean), query_time_ms, top_k_returned.

Rollback plan
- Keep DB backup; if retrieval correctness degrades or corruption occurs, restore backup and stop rollout.
- Alternatively, clear normalized_* columns (if necessary) via scripted UPDATE ... SET normalized_vector=NULL, normalized_vector_dim=NULL, normalized_vector_algo=NULL, normalized_at=NULL, normalized_version=NULL

Notes and pitfalls
- ALTER TABLE ADD COLUMN is cheap for SQLite but may vary on other DB engines.
- For very large DBs, perform backfill in batches and during low-traffic windows.
