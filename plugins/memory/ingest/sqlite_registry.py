"""SQLite-backed MemoryRegistry implementation.

Provides a simple transactional registry using SQLite with WAL mode to support
concurrent writers safely and efficiently. This is intended as a replacement
for the JSON file-backed MemoryRegistry for higher-concurrency workloads.
"""
from __future__ import annotations
import os
import sqlite3
from typing import Dict, Any, Optional

class SQLiteMemoryRegistry:
    def __init__(self, storage_root: str, db_name: str = 'memory_registry.db'):
        self.storage_root = storage_root
        self.db_path = os.path.join(storage_root, 'registry', db_name)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._ensure_db()

    def _conn(self):
        conn = sqlite3.connect(self.db_path, timeout=30, isolation_level=None)
        # use WAL for concurrent readers/writers
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.execute('PRAGMA synchronous=NORMAL;')
        return conn

    def _ensure_db(self):
        with self._conn() as c:
            c.execute("CREATE TABLE IF NOT EXISTS registry (chunk_id TEXT PRIMARY KEY, metadata_json TEXT NOT NULL)")

    def add_entry(self, metadata: Dict[str, Any]) -> None:
        import json
        if 'chunk_id' not in metadata:
            raise ValueError('metadata must include chunk_id')
        cid = metadata['chunk_id']
        meta_json = json.dumps(metadata, separators=(',', ':'), ensure_ascii=False)
        with self._conn() as c:
            c.execute('BEGIN IMMEDIATE')
            try:
                c.execute('INSERT OR REPLACE INTO registry(chunk_id, metadata_json) VALUES (?, ?)', (cid, meta_json))
                c.execute('COMMIT')
            except Exception:
                c.execute('ROLLBACK')
                raise

    def get_entry(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        import json
        with self._conn() as c:
            cur = c.execute('SELECT metadata_json FROM registry WHERE chunk_id = ?', (chunk_id,))
            row = cur.fetchone()
            if not row:
                return None
            return json.loads(row[0])

    def list_entries(self) -> Dict[str, Dict[str, Any]]:
        import json
        with self._conn() as c:
            cur = c.execute('SELECT chunk_id, metadata_json FROM registry')
            return {row[0]: json.loads(row[1]) for row in cur.fetchall()}

    def exists(self, chunk_id: str) -> bool:
        with self._conn() as c:
            cur = c.execute('SELECT 1 FROM registry WHERE chunk_id = ? LIMIT 1', (chunk_id,))
            return cur.fetchone() is not None