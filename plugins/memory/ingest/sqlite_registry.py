import os
import sqlite3
import json
from typing import Dict, Any, List, Optional

class SQLiteMemoryRegistry:
    """SQLite-backed registry used in tests. Stores JSON-serialized meta per chunk_id.

    Schema:
      registry(chunk_id TEXT PRIMARY KEY, meta TEXT NOT NULL)
    """

    def __init__(self, storage_root: str):
        self.db_path = os.path.join(storage_root, 'registry', 'memory_registry.db')
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        # sqlite3 connection with check_same_thread=False to be flexible in tests
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS registry (
                chunk_id TEXT PRIMARY KEY,
                meta TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def add_entry(self, meta: Dict[str, Any]):
        chunk_id = meta.get('chunk_id')
        if chunk_id is None:
            raise ValueError('meta must include chunk_id')
        self.conn.execute('INSERT OR REPLACE INTO registry (chunk_id, meta) VALUES (?, ?)', (chunk_id, json.dumps(meta)))
        self.conn.commit()

    def get_entry(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        cur = self.conn.execute('SELECT meta FROM registry WHERE chunk_id = ?', (chunk_id,))
        row = cur.fetchone()
        if not row:
            return None
        return json.loads(row[0])

    def list_entries(self, limit: Optional[int] = None) -> Any:
        """If limit is None, return a dict mapping chunk_id -> meta.
        If limit is provided, return a list of meta dicts up to the limit (most-recent insertion order unspecified).
        """
        cur = self.conn.cursor()
        if limit is None:
            cur.execute('SELECT chunk_id, meta FROM registry')
            rows = cur.fetchall()
            return {r[0]: json.loads(r[1]) for r in rows}
        else:
            cur.execute('SELECT meta FROM registry LIMIT ?', (limit,))
            rows = cur.fetchall()
            return [json.loads(r[0]) for r in rows]

    def bulk_import(self, entries: Any) -> None:
        """Bulk import entries. Accepts either a dict mapping chunk_id->meta or an iterable/list of meta dicts.
        Upserts entries into the sqlite registry.
        """
        if entries is None:
            return
        cur = self.conn.cursor()
        if isinstance(entries, dict):
            items = entries.items()
        else:
            # assume iterable of meta dicts
            items = ((m.get('chunk_id'), m) for m in entries)
        for cid, meta in items:
            if cid is None:
                # try to find chunk_id inside meta
                cid = meta.get('chunk_id') if isinstance(meta, dict) else None
            if cid is None:
                # skip malformed
                continue
            cur.execute('INSERT OR REPLACE INTO registry (chunk_id, meta) VALUES (?, ?)', (cid, json.dumps(meta)))
        self.conn.commit()

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass
