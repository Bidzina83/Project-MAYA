import os
import sqlite3
import json

class SQLiteMemoryRegistry:
    """Minimal SQLite-backed registry used in tests. Stores JSON-serialized meta per chunk_id.
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

    def add_entry(self, meta: dict):
        chunk_id = meta.get('chunk_id')
        if chunk_id is None:
            raise ValueError('meta must include chunk_id')
        self.conn.execute('INSERT OR REPLACE INTO registry (chunk_id, meta) VALUES (?, ?)', (chunk_id, json.dumps(meta)))
        self.conn.commit()

    def list_entries(self):
        cur = self.conn.execute('SELECT meta FROM registry')
        return [json.loads(row[0]) for row in cur.fetchall()]
