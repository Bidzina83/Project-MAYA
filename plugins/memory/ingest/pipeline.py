"""Ingestion pipeline: chunk -> embed -> persist embedding metadata.

Exports:
- IngestionPipeline: process_file(path, storage_root, force=False)

Behavior:
- Uses chunker.chunk_file to produce chunks with provenance
- Uses embedder.Embedder to produce vectors (BackendFactory may be monkeypatched in tests)
- Writes per-chunk embedding JSON files to STORAGE_ROOT/embeddings/{chunk_id}.json
- Embedding file contains: chunk_id, embedding (list), model, extractor_version, source_path, source_hash, chunk_start, chunk_end, chunk_text (optionally truncated), embedding_timestamp
- Idempotent by default: if embedding file exists and force=False, skip generation
- Optionally dual-writes registry entries into both JSON (MemoryRegistry) and SQLite (SQLiteMemoryRegistry) when dual_write=True
"""
from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from typing import List

from .chunker import chunk_file
from .embedder import Embedder, compute_chunk_id, EmbedderError
from .registry import MemoryRegistry

# sqlite_registry is optional; import locally when needed


class IngestionPipeline:
    def __init__(self, backend: str = "mock", model: str | None = None, batch_size: int = 32, dual_write: bool = False):
        self.backend = backend
        self.model = model
        self.batch_size = int(batch_size)
        self.dual_write = bool(dual_write)

    def _ensure_dirs(self, root: str):
        embd = os.path.join(root, "embeddings")
        os.makedirs(embd, exist_ok=True)
        return embd

    def _normalize_reg_meta(self, cid: str, fname: str, c, vec, metadata_timestamp: str | None = None):
        provider = self.backend or "unknown"
        vector_dim = None
        try:
            if hasattr(vec, '__len__'):
                vector_dim = int(len(vec))
        except Exception:
            vector_dim = None
        reg_meta = {
            "chunk_id": cid,
            "embedding_path": fname,
            "source_path": c.metadata.get("source_path"),
            "source_hash": c.metadata.get("source_hash"),
            "model": self.model or "unknown",
            "provider": provider,
            "vector_dim": vector_dim,
            "extractor_version": c.metadata.get("extractor_version"),
            "embedding_timestamp": metadata_timestamp or datetime.now(timezone.utc).isoformat(),
        }
        return reg_meta

    def process_file(self, path: str, storage_root: str, force: bool = False, max_chars: int = 1000, extractor_version: str = "v0.1") -> List[str]:
        """Process a source file: chunk, embed, write embedding metadata files.

        Returns list of written embedding file paths.
        """
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        emb_dir = self._ensure_dirs(storage_root)
        registry = MemoryRegistry(storage_root)

        sqlite_registry = None
        if self.dual_write:
            try:
                from .sqlite_registry import SQLiteMemoryRegistry
                sqlite_registry = SQLiteMemoryRegistry(storage_root)
            except Exception:
                sqlite_registry = None

        chunks = chunk_file(path, max_chars=max_chars, extractor_version=extractor_version)
        texts = [c.text for c in chunks]
        chunk_ids = [compute_chunk_id(t) for t in texts]

        emb = Embedder(backend=self.backend, model=self.model, batch_size=self.batch_size)
        vectors = emb.embed(texts)
        if len(vectors) != len(chunks):
            raise EmbedderError("embedding count mismatch")

        written_paths: List[str] = []
        for c, cid, vec in zip(chunks, chunk_ids, vectors):
            fname = os.path.join(emb_dir, f"{cid}.json")
            metadata_timestamp = datetime.now(timezone.utc).isoformat()
            # compute normalized registry meta early
            reg_meta = self._normalize_reg_meta(cid, fname, c, vec, metadata_timestamp)

            if os.path.exists(fname) and not force:
                # ensure registry entry exists even if file already present
                registry.add_entry(reg_meta)
                if sqlite_registry is not None:
                    try:
                        sqlite_registry.add_entry(reg_meta)
                    except Exception:
                        # don't fail the whole run for sqlite write errors
                        pass
                written_paths.append(fname)
                continue
            metadata = {
                "chunk_id": cid,
                "embedding": vec,
                "model": self.model or "unknown",
                "provider": reg_meta["provider"],
                "vector_dim": reg_meta["vector_dim"],
                "extractor_version": c.metadata.get("extractor_version"),
                "source_path": c.metadata.get("source_path"),
                "source_hash": c.metadata.get("source_hash"),
                "chunk_start": c.start,
                "chunk_end": c.end,
                "chunk_text_snippet": c.text[:512],
                "embedding_timestamp": metadata_timestamp,
            }
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

            # record in JSON registry
            registry.add_entry(reg_meta)
            # optionally record in sqlite
            if sqlite_registry is not None:
                try:
                    sqlite_registry.add_entry(reg_meta)
                except Exception:
                    # ignore sqlite errors to keep pipeline resilient
                    pass
            written_paths.append(fname)
        return written_paths
