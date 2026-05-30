"""SQLite-backed Memory Registry for Project MAYA.

Provides a small SQLite wrapper suitable as a drop-in alternative to the JSON registry.

Usage:
    reg = SQLiteMemoryRegistry(storage_root)
    reg.add_entry(metadata)
    reg.get_entry(chunk_id)
    reg.list_entries()
    reg.bulk_import(dict_of_entries)

The SQLite DB is stored at STORAGE_ROOT/registry/memory_registry.sqlite
"""
from __future__ import annotations
import os
import sqlite3
import json
from typing import Dict, Any, Optional


class SQLiteMemoryRegistry:
    def __init__(self, storage_root: str):
        self.storage_root = storage_root
        self.registry_dir = os.path.join(storage_root, "registry")
        os.makedirs(self.registry_dir, exist_ok=True)
        self.db_path = os.path.join(self.registry_dir, "memory_registry.sqlite")
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        return conn

    def _init_db(self):
        conn = self._connect()
        try:
            cur = conn.cursor()
            # pragmas for WAL and reasonable durability
            cur.execute("PRAGMA journal_mode=WAL;")
            cur.execute("PRAGMA synchronous=NORMAL;")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS embeddings (
                    chunk_id TEXT PRIMARY KEY,
                    embedding_path TEXT,
                    source_path TEXT,
                    source_hash TEXT,
                    model TEXT,
                    extractor_version TEXT,
                    embedding_timestamp TEXT,
                    updated_at TEXT
                )
                """
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_source_hash ON embeddings(source_hash);")
            conn.commit()
        finally:
            conn.close()

    def add_entry(self, metadata: Dict[str, Any]):
        if "chunk_id" not in metadata:
            raise ValueError("metadata must include chunk_id")
        cid = metadata["chunk_id"]
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO embeddings(chunk_id, embedding_path, source_path, source_hash, model, extractor_version, embedding_timestamp, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(chunk_id) DO UPDATE SET
                    embedding_path=excluded.embedding_path,
                    source_path=excluded.source_path,
                    source_hash=excluded.source_hash,
                    model=excluded.model,
                    extractor_version=excluded.extractor_version,
                    embedding_timestamp=excluded.embedding_timestamp,
                    updated_at=datetime('now')
                """,
                (
                    cid,
                    metadata.get("embedding_path"),
                    metadata.get("source_path"),
                    metadata.get("source_hash"),
                    metadata.get("model"),
                    metadata.get("extractor_version"),
                    metadata.get("embedding_timestamp"),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get_entry(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT chunk_id, embedding_path, source_path, source_hash, model, extractor_version, embedding_timestamp, updated_at FROM embeddings WHERE chunk_id = ?", (chunk_id,))
            row = cur.fetchone()
            if not row:
                return None
            keys = ["chunk_id", "embedding_path", "source_path", "source_hash", "model", "extractor_version", "embedding_timestamp", "updated_at"]
            return dict(zip(keys, row))
        finally:
            conn.close()

    def list_entries(self, limit: int = 100, offset: int = 0) -> Dict[str, Dict[str, Any]]:
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT chunk_id, embedding_path, source_path, source_hash, model, extractor_version, embedding_timestamp, updated_at FROM embeddings ORDER BY updated_at DESC LIMIT ? OFFSET ?", (limit, offset))
            rows = cur.fetchall()
            keys = ["chunk_id", "embedding_path", "source_path", "source_hash", "model", "extractor_version", "embedding_timestamp", "updated_at"]
            return {r[0]: dict(zip(keys, r)) for r in rows}
        finally:
            conn.close()

    def bulk_import(self, data: Dict[str, Dict[str, Any]]):
        """Import many entries from a dict mapping chunk_id -> metadata"""
        conn = self._connect()
        try:
            cur = conn.cursor()
            for cid, meta in data.items():
                cur.execute(
                    """
                    INSERT INTO embeddings(chunk_id, embedding_path, source_path, source_hash, model, extractor_version, embedding_timestamp, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    ON CONFLICT(chunk_id) DO UPDATE SET
                        embedding_path=excluded.embedding_path,
                        source_path=excluded.source_path,
                        source_hash=excluded.source_hash,
                        model=excluded.model,
                        extractor_version=excluded.extractor_version,
                        embedding_timestamp=excluded.embedding_timestamp,
                        updated_at=datetime('now')
                    """,
                    (
                        cid,
                        meta.get("embedding_path"),
                        meta.get("source_path"),
                        meta.get("source_hash"),
                        meta.get("model"),
                        meta.get("extractor_version"),
                        meta.get("embedding_timestamp"),
                    ),
                )
            conn.commit()
        finally:
            conn.close()
