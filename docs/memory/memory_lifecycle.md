# Memory Lifecycle (Project-MAYA)

This document traces the end-to-end lifecycle for persistent memory entries (embeddings, registry, and vector store) in the Project-MAYA runtime.

1) Ingest / Embed
- Source: document/text/asset is submitted to the ingest pipeline (plugins/memory/ingest/pipeline.py).
- Chunking: text is chunked, metadata prepared (chunk_id, source_path, source_hash).
- Embedding: embedder (plugins/memory/ingest/embedder.py) produces an embedding vector (list of floats) and writes an embedding file under STORAGE_ROOT/embeddings/{chunk_id}.json using atomic write.
- Registry write: MemoryRegistry.add_entry writes a JSON entry under STORAGE_ROOT/registry/memory_registry.json mapping chunk_id -> metadata (embedding_path, provider, model, vector_dim, extractor_version, embedding_timestamp, etc.).
- LocalVectorStore write: LocalVectorStore.add_entry (sqlite) inserts a row into the SQLite registry (default path STORAGE_ROOT/registry/memory_registry.sqlite) in the `entries` table with columns: embedding_id, chunk_id, vector (JSON text), vector_dim, created_at, source_path, score_meta.

2) Monitoring and Duplication
- The registry monitor (plugins/memory/ingest/bin/registry_monitor.py) reports counts by checking both the JSON registry and the SQLite registry. Historically it checked the `embeddings` table; LocalVectorStore uses `entries`, so monitor now checks `entries` first then `embeddings`.

3) Retrieval
- The retrieval layer reads the LocalVectorStore `entries` table (or remote vector providers) and uses the stored `vector` for similarity search. After normalization migration, the store may also contain `normalized_vector*` columns which retrieval prefers.

4) Normalization / Backfill
- A backfill script (plugins/memory/scripts/backfill_normalize_entries.py) can add the normalized_* columns and populate them with L2-normalized vectors. The script is idempotent and supports --dry-run (non-mutating) and --chunk for batching.

5) Post-migration
- Retrieval should prefer normalized_vector when present; otherwise compute normalization on-the-fly (adapter fallback).
- Metadata: normalized_vector_algo and normalized_version allow rolling upgrades of normalization algorithm and controlled re-normalization.

Operator notes
- Always backup DB before applying schema updates or backfills.
- Dry-run should never mutate schema or write data.
- Use registry_monitor to verify both JSON and SQLite representations.

Verification checklist
- After ingest: ensure embedding file exists and JSON registry contains mapping for chunk_id.
- Ensure the SQLite `entries` table has a row with that chunk_id and vector content.
- For migration: dry-run reports expected updates without altering schema; real run populates normalized_* fields.

