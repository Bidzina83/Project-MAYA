"""Indexer and local vector store adapter for Project MAYA persistent memory.

Provides:
- atomic_write_json(obj, path)
- Indexer class: write_index_entry(entry, base_dir=...)
- LocalVectorStore: sqlite-backed adapter for tests/CI with add/query operations

Design notes:
- Indexer writes per-entry JSON files under base_dir/YYYY/MM/{chunk_id}.json using os.replace for atomic commit
- LocalVectorStore stores vectors and metadata in a local sqlite DB for quick CI verification
"""
from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import math
from datetime import datetime
from typing import Any, Dict, Optional, List, Tuple


def atomic_write_json(obj: Dict[str, Any], path: str) -> None:
    """Write JSON to a temporary file in the target directory then atomically replace.

    Ensures the write is atomic on POSIX by writing to the same filesystem and using os.replace.
    """
    dirpath = os.path.dirname(path)
    os.makedirs(dirpath, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp_index_", dir=dirpath)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        # If replace failed and tmp still exists, remove it
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass


class Indexer:
    """Index writer that creates one file per index entry.

    Example entry shape:
      {"embedding_id": "emb-...", "chunk_id": "<sha256>", "vector_dim": 1536, "created_at": "...", "source_path": "/abs/path", "score_meta": {...}}
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or "/opt/hermes/data/memory/index"

    def write_index_entry(self, entry: Dict[str, Any]) -> str:
        """Write entry JSON atomically and return the final path."""
        created_at = entry.get("created_at") or datetime.utcnow().isoformat() + "Z"
        entry["created_at"] = created_at

        # path layout: base_dir/YYYY/MM/{chunk_id}.json
        dt = datetime.fromisoformat(created_at.replace("Z", ""))
        year = dt.year
        month = f"{dt.month:02d}"
        chunk_id = entry.get("chunk_id") or entry.get("embedding_id")
        if not chunk_id:
            raise ValueError("entry must contain chunk_id or embedding_id")
        final_dir = os.path.join(self.base_dir, str(year), month)
        final_path = os.path.join(final_dir, f"{chunk_id}.json")
        atomic_write_json(entry, final_path)
        return final_path


class LocalVectorStore:
    """SQLite-backed vector store used for tests/CI.

    Schema:
      entries(id INTEGER PRIMARY KEY, embedding_id TEXT UNIQUE, chunk_id TEXT, vector TEXT (JSON), vector_dim INTEGER, created_at TEXT, source_path TEXT, score_meta TEXT (JSON))
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        # Return rows as dict-like when using row factory
        self.conn.row_factory = sqlite3.Row
        self._ensure_table()

    def _ensure_table(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY,
                embedding_id TEXT UNIQUE,
                chunk_id TEXT,
                vector TEXT,
                vector_dim INTEGER,
                created_at TEXT,
                source_path TEXT,
                score_meta TEXT
            )"""
        )
        self.conn.commit()

    def add_entry(self, embedding_id: str, chunk_id: str, vector: List[float], created_at: Optional[str] = None, source_path: Optional[str] = None, score_meta: Optional[Dict[str, Any]] = None) -> None:
        cur = self.conn.cursor()
        vec_json = json.dumps(vector)
        score_json = json.dumps(score_meta or {})
        created_at = created_at or datetime.utcnow().isoformat() + "Z"
        cur.execute(
            "INSERT INTO entries (embedding_id, chunk_id, vector, vector_dim, created_at, source_path, score_meta) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (embedding_id, chunk_id, vec_json, len(vector), created_at, source_path, score_json),
        )
        self.conn.commit()

    def get_by_chunk_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT embedding_id, chunk_id, vector, vector_dim, created_at, source_path, score_meta FROM entries WHERE chunk_id = ?", (chunk_id,))
        row = cur.fetchone()
        if not row:
            return None
        return {
            "embedding_id": row[0],
            "chunk_id": row[1],
            "vector": json.loads(row[2]),
            "vector_dim": row[3],
            "created_at": row[4],
            "source_path": row[5],
            "score_meta": json.loads(row[6] or "{}"),
        }

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two equal-length vectors.

        Returns a float in [-1.0, 1.0]. If either vector is zero, returns 0.0.
        """
        if not a or not b or len(a) != len(b):
            return 0.0
        # compute dot and norms
        dot = 0.0
        na = 0.0
        nb = 0.0
        for x, y in zip(a, b):
            dot += float(x) * float(y)
            na += float(x) * float(x)
            nb += float(y) * float(y)
        if na == 0.0 or nb == 0.0:
            return 0.0
        return dot / (math.sqrt(na) * math.sqrt(nb))

    def query_by_vector(self, vector: List[float], top_k: int = 5, metric: str = "cosine") -> List[Dict[str, Any]]:
        """Query the local vector store by a numeric vector and return the top_k matches.

        Returns a list of dicts with keys: embedding_id, chunk_id, vector, vector_dim, created_at, source_path, score_meta, similarity
        Similarity is in [-1,1] for cosine; for other metrics adapt accordingly.
        """
        cur = self.conn.cursor()
        cur.execute("SELECT embedding_id, chunk_id, vector, vector_dim, created_at, source_path, score_meta FROM entries")
        rows = cur.fetchall()
        parsed: List[Tuple[float, Dict[str, Any]]] = []
        for row in rows:
            try:
                vec = json.loads(row[2]) if row[2] else []
            except Exception:
                vec = []
            if metric == "cosine":
                sim = self._cosine_similarity(vector, vec)
            else:
                # fallback to cosine
                sim = self._cosine_similarity(vector, vec)
            entry = {
                "embedding_id": row[0],
                "chunk_id": row[1],
                "vector": vec,
                "vector_dim": row[3],
                "created_at": row[4],
                "source_path": row[5],
                "score_meta": json.loads(row[6] or "{}"),
                "similarity": sim,
            }
            parsed.append((sim, entry))

        # sort by similarity descending
        parsed.sort(key=lambda t: t[0], reverse=True)
        results = [t[1] for t in parsed[:top_k]]
        return results

    def close(self) -> None:
        self.conn.close()
