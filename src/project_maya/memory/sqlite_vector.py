"""SQLite-backed local vector retrieval for Maya Standard."""

from __future__ import annotations

import json
import math
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = 1


class LocalSQLiteVectorRetriever:
    """Durable local retriever with full-text and exact vector search.

    SQLite remains the customer-controlled system of record for memory records.
    Vector indexes are derived data and can be rebuilt from stored embeddings.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.RLock()
        self._connection: sqlite3.Connection | None = None
        self._open()

    @property
    def path(self) -> Path:
        return self._path

    def upsert(self, doc: dict[str, Any]) -> None:
        self._upsert_many((doc,))

    def bulk_upsert(self, docs: list[dict[str, Any]]) -> None:
        self._upsert_many(docs)

    def get(self, id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._execute(
                "SELECT document_json FROM memory_records WHERE record_id = ?",
                (id,),
            ).fetchone()
        return _decode_document(row[0]) if row is not None else None

    def query_vector(
        self,
        vector: list[float],
        top_k: int = 10,
        metric: str = "cosine",
    ) -> list[dict[str, Any]]:
        if top_k < 1:
            raise ValueError("top_k must be positive")
        if metric != "cosine":
            raise ValueError("local_vector supports only cosine similarity")
        query = _validated_vector(vector)
        if not query:
            return []
        with self._lock:
            expected_dimension = self._embedding_dimension()
            if expected_dimension is not None and len(query) != expected_dimension:
                raise ValueError(
                    f"embedding dimension must be {expected_dimension}"
                )
            rows = self._execute(
                "SELECT document_json, embedding_json FROM memory_records "
                "WHERE embedding_json IS NOT NULL"
            ).fetchall()
        ranked: list[tuple[float, dict[str, Any]]] = []
        for row in rows:
            candidate = _validated_vector(json.loads(row[1]))
            if len(candidate) != len(query):
                continue
            document = _decode_document(row[0])
            similarity = _cosine_similarity(query, candidate)
            document["similarity"] = similarity
            document["score"] = similarity
            ranked.append((similarity, document))
        ranked.sort(key=lambda item: (-item[0], _document_id(item[1])))
        return [document for _, document in ranked[:top_k]]

    def search(
        self,
        query: str,
        category: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        if limit < 1:
            raise ValueError("limit must be positive")
        terms = _search_terms(query)
        if not terms:
            return []
        match = " AND ".join(f'"{term}"' for term in terms)
        statement = (
            "SELECT r.document_json, bm25(memory_records_fts) AS rank "
            "FROM memory_records_fts "
            "JOIN memory_records r ON r.record_id = memory_records_fts.record_id "
            "WHERE memory_records_fts MATCH ?"
        )
        parameters: list[Any] = [match]
        if category is not None:
            statement += " AND r.category = ?"
            parameters.append(category)
        statement += " ORDER BY rank, r.record_id LIMIT ?"
        parameters.append(limit)
        with self._lock:
            rows = self._execute(statement, tuple(parameters)).fetchall()
        return [_decode_document(row[0]) for row in rows]

    def probe(
        self, entity: str, category: str | None = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        return self.search(entity, category=category, limit=limit)

    def related(
        self, entity: str, category: str | None = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        return self.search(entity, category=category, limit=limit)

    def reason(
        self,
        entities: list[str],
        category: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        return self.search(" ".join(entities), category=category, limit=limit)

    def contradict(
        self,
        category: str | None = None,
        threshold: float = 0.3,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        return []

    def documents(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._execute(
                "SELECT document_json FROM memory_records ORDER BY record_id"
            ).fetchall()
        return [_decode_document(row[0]) for row in rows]

    def replace_embeddings(self, embeddings: dict[str, list[float]]) -> None:
        """Atomically replace every stored embedding with one model generation."""

        prepared = {
            str(record_id): _validated_vector(vector)
            for record_id, vector in embeddings.items()
        }
        dimensions = {len(vector) for vector in prepared.values() if vector}
        if len(dimensions) > 1:
            raise ValueError("all embeddings must use one dimension")
        with self._lock:
            connection = self._require_connection()
            with connection:
                rows = connection.execute(
                    "SELECT record_id, document_json FROM memory_records "
                    "ORDER BY record_id"
                ).fetchall()
                stored_ids = {str(row[0]) for row in rows}
                if set(prepared) != stored_ids:
                    raise ValueError("embedding rebuild must cover every memory record")
                now = datetime.now(timezone.utc).isoformat()
                for record_id, document_json in rows:
                    vector = prepared[str(record_id)]
                    document = _decode_document(document_json)
                    if vector:
                        document["embedding"] = vector
                    else:
                        document.pop("embedding", None)
                        document.pop("vector", None)
                    connection.execute(
                        "UPDATE memory_records SET document_json = ?, "
                        "embedding_json = ?, vector_dim = ?, updated_at = ? "
                        "WHERE record_id = ?",
                        (
                            json.dumps(document, ensure_ascii=True, sort_keys=True),
                            json.dumps(vector) if vector else None,
                            len(vector) if vector else None,
                            now,
                            record_id,
                        ),
                    )
                connection.execute(
                    "DELETE FROM memory_metadata WHERE key='embedding_dimension'"
                )
                if dimensions:
                    connection.execute(
                        "INSERT INTO memory_metadata(key, value) "
                        "VALUES('embedding_dimension', ?)",
                        (str(dimensions.pop()),),
                    )

    def search_hybrid(
        self,
        query: str,
        *,
        query_vector: list[float] | None = None,
        category: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        lexical = self.search(query, category=category, limit=max(limit * 3, 20))
        semantic = (
            self.query_vector(query_vector, top_k=max(limit * 3, 20))
            if query_vector
            else []
        )
        if category is not None:
            semantic = [item for item in semantic if item.get("category") == category]
        ranked: dict[str, tuple[float, dict[str, Any]]] = {}
        for results, weight in ((lexical, 0.45), (semantic, 0.55)):
            for rank, document in enumerate(results, start=1):
                record_id = _document_id(document)
                score = weight / (60.0 + rank)
                previous = ranked.get(record_id, (0.0, document))[0]
                ranked[record_id] = (previous + score, document)
        ordered = sorted(ranked.values(), key=lambda item: (-item[0], _document_id(item[1])))
        output = []
        for score, document in ordered[:limit]:
            item = dict(document)
            item["hybrid_score"] = score
            output.append(item)
        return output

    def stats(self) -> dict[str, Any]:
        with self._lock:
            row = self._execute(
                "SELECT COUNT(*), "
                "SUM(CASE WHEN embedding_json IS NOT NULL THEN 1 ELSE 0 END) "
                "FROM memory_records"
            ).fetchone()
            journal = self._execute("PRAGMA journal_mode").fetchone()[0]
        return {
            "backend": "local_vector",
            "path": str(self._path),
            "records": int(row[0]),
            "vectors": int(row[1] or 0),
            "schema_version": SCHEMA_VERSION,
            "journal_mode": str(journal).lower(),
        }

    def integrity_check(self) -> str:
        with self._lock:
            return str(self._execute("PRAGMA integrity_check").fetchone()[0])

    def close(self) -> None:
        with self._lock:
            if self._connection is not None:
                self._connection.close()
                self._connection = None

    def _open(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(
            self._path,
            timeout=30.0,
            check_same_thread=False,
        )
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = NORMAL")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS memory_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS memory_records (
                record_id TEXT PRIMARY KEY,
                document_json TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT,
                trust_score REAL NOT NULL DEFAULT 0.5
                    CHECK (trust_score >= 0.0 AND trust_score <= 1.0),
                embedding_json TEXT,
                vector_dim INTEGER,
                source_path TEXT,
                source_hash TEXT,
                extractor_version TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_memory_records_category
                ON memory_records(category);
            CREATE INDEX IF NOT EXISTS idx_memory_records_trust
                ON memory_records(trust_score DESC);
            CREATE VIRTUAL TABLE IF NOT EXISTS memory_records_fts USING fts5(
                record_id UNINDEXED,
                content,
                tokenize = 'unicode61'
            );
            """
        )
        connection.execute(
            "INSERT INTO memory_metadata(key, value) VALUES('schema_version', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (str(SCHEMA_VERSION),),
        )
        connection.commit()
        self._connection = connection

    def _upsert_many(self, docs: Iterable[dict[str, Any]]) -> None:
        prepared = [_prepare_document(document) for document in docs]
        if not prepared:
            return
        with self._lock:
            connection = self._require_connection()
            with connection:
                self._validate_embedding_dimensions(connection, prepared)
                for values in prepared:
                    connection.execute(
                        """
                        INSERT INTO memory_records(
                            record_id, document_json, content, category,
                            trust_score, embedding_json, vector_dim,
                            source_path, source_hash, extractor_version,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(record_id) DO UPDATE SET
                            document_json=excluded.document_json,
                            content=excluded.content,
                            category=excluded.category,
                            trust_score=excluded.trust_score,
                            embedding_json=excluded.embedding_json,
                            vector_dim=excluded.vector_dim,
                            source_path=excluded.source_path,
                            source_hash=excluded.source_hash,
                            extractor_version=excluded.extractor_version,
                            updated_at=excluded.updated_at
                        """,
                        values,
                    )
                    connection.execute(
                        "DELETE FROM memory_records_fts WHERE record_id = ?",
                        (values[0],),
                    )
                    connection.execute(
                        "INSERT INTO memory_records_fts(record_id, content) "
                        "VALUES (?, ?)",
                        (values[0], values[2]),
                    )

    def _embedding_dimension(self) -> int | None:
        row = self._execute(
            "SELECT value FROM memory_metadata WHERE key='embedding_dimension'"
        ).fetchone()
        return int(row[0]) if row is not None else None

    def _validate_embedding_dimensions(
        self,
        connection: sqlite3.Connection,
        prepared: list[tuple[Any, ...]],
    ) -> None:
        incoming = {int(values[6]) for values in prepared if values[6] is not None}
        if len(incoming) > 1:
            raise ValueError("all embeddings must use one dimension")
        if not incoming:
            return
        incoming_dimension = incoming.pop()
        stored = self._embedding_dimension()
        if stored is None:
            existing = {
                int(row[0])
                for row in connection.execute(
                    "SELECT DISTINCT vector_dim FROM memory_records "
                    "WHERE vector_dim IS NOT NULL"
                ).fetchall()
            }
            if len(existing) > 1:
                raise ValueError("stored embeddings use inconsistent dimensions")
            stored = existing.pop() if existing else incoming_dimension
            connection.execute(
                "INSERT INTO memory_metadata(key, value) "
                "VALUES('embedding_dimension', ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (str(stored),),
            )
        if incoming_dimension != stored:
            raise ValueError(f"embedding dimension must be {stored}")

    def _execute(
        self, statement: str, parameters: tuple[Any, ...] = ()
    ) -> sqlite3.Cursor:
        return self._require_connection().execute(statement, parameters)

    def _require_connection(self) -> sqlite3.Connection:
        if self._connection is None:
            raise RuntimeError("local_vector retriever is closed")
        return self._connection


def inspect_local_vector_store(path: Path) -> dict[str, Any]:
    """Return a redacted health summary without creating a missing database."""

    if not path.is_file():
        return {"status": "missing", "records": 0, "vectors": 0}
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
        version_row = connection.execute(
            "SELECT value FROM memory_metadata WHERE key='schema_version'"
        ).fetchone()
        count_row = connection.execute(
            "SELECT COUNT(*), "
            "SUM(CASE WHEN embedding_json IS NOT NULL THEN 1 ELSE 0 END) "
            "FROM memory_records"
        ).fetchone()
        return {
            "status": "ready" if integrity == "ok" else "corrupt",
            "integrity": integrity,
            "schema_version": int(version_row[0]),
            "records": int(count_row[0]),
            "vectors": int(count_row[1] or 0),
        }
    finally:
        connection.close()


def _prepare_document(document: dict[str, Any]) -> tuple[Any, ...]:
    doc = dict(document)
    record_id = _document_id(doc)
    content = _document_content(doc)
    embedding = _validated_vector(doc.get("embedding") or doc.get("vector") or [])
    trust_score = float(doc.get("trust_score", 0.5))
    if not 0.0 <= trust_score <= 1.0:
        raise ValueError("trust_score must be between 0 and 1")
    now = datetime.now(timezone.utc).isoformat()
    created_at = str(doc.get("created_at") or now)
    doc.setdefault("id", record_id)
    doc.setdefault("created_at", created_at)
    doc.setdefault("trust_score", trust_score)
    metadata = doc.get("meta") if isinstance(doc.get("meta"), dict) else {}
    return (
        record_id,
        json.dumps(doc, ensure_ascii=True, sort_keys=True),
        content,
        doc.get("category") or metadata.get("category"),
        trust_score,
        json.dumps(embedding) if embedding else None,
        len(embedding) if embedding else None,
        doc.get("source_path") or metadata.get("source_path"),
        doc.get("source_hash") or metadata.get("source_hash"),
        doc.get("extractor_version") or metadata.get("extractor_version"),
        created_at,
        now,
    )


def _document_id(document: dict[str, Any]) -> str:
    for key in ("id", "chunk_id", "embedding_id"):
        value = document.get(key)
        if value:
            return str(value)
    raise ValueError("document requires id, chunk_id, or embedding_id")


def _document_content(document: dict[str, Any]) -> str:
    for key in ("content", "text"):
        value = document.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    turn_parts = []
    for label, key in (("User", "user_content"), ("Assistant", "assistant_content")):
        value = document.get(key)
        if isinstance(value, str) and value.strip():
            turn_parts.append(f"{label}: {value.strip()}")
    if turn_parts:
        return "\n".join(turn_parts)
    return ""


def _validated_vector(value: Any) -> list[float]:
    if value in (None, []):
        return []
    if not isinstance(value, (list, tuple)):
        raise ValueError("embedding must be a numeric list")
    vector = [float(item) for item in value]
    if not all(math.isfinite(item) for item in vector):
        raise ValueError("embedding values must be finite")
    return vector


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)


def _search_terms(query: str) -> list[str]:
    return [
        term.replace('"', '""')
        for term in query.split()
        if term.strip()
    ]


def _decode_document(value: str) -> dict[str, Any]:
    document = json.loads(value)
    if not isinstance(document, dict):
        raise ValueError("stored memory document must be an object")
    return document
