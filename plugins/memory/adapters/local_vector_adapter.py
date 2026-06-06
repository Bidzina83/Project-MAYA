from __future__ import annotations
from typing import List, Dict, Any, Optional
import json
import math

from plugins.memory.retriever_api import Retriever, RetrievalResult, RetrieverError
from plugins.memory.indexer import LocalVectorStore
from plugins.memory.utils.normalization import text_normalize, vector_normalize


class LocalVectorAdapter(Retriever):
    """Adapter that exposes LocalVectorStore with the canonical Retriever API.

    Notes:
    - Stores free-form doc metadata inside score_meta so simple text search can
      inspect content when present.
    - query_vector performs an exact scan over the SQLite entries and computes
      cosine similarity in Python. This is O(N) and intended for testing/local use.
    """

    def __init__(self, store: LocalVectorStore, name: str = "local_vector_store"):
        self.store = store
        self.name = name

    def upsert(self, doc: Dict[str, Any]) -> None:
        try:
            # preserve original embedding for auditability
            original_embedding = doc.get("embedding") or []
            # compute normalized vector but do NOT overwrite the original embedding
            normalized_vec = vector_normalize(original_embedding) if original_embedding else []
            embedding_id = doc.get("embedding_id") or doc.get("chunk_id") or ""
            chunk_id = doc.get("chunk_id") or embedding_id or ""
            score_meta = doc.get("meta") or {}
            # Keep content in score_meta for simple keyword search
            if doc.get("content"):
                # store normalized content for search while preserving original in meta
                score_meta.setdefault("content", doc.get("content"))
                score_meta.setdefault("content_normalized", text_normalize(doc.get("content")))
            # normalized vector metadata
            from datetime import datetime
            now = datetime.utcnow().isoformat() + "Z"
            normalized_algo = "l2-v1"
            normalized_version = 1
            # store entry: original embedding preserved, normalized vector and metadata stored as first-class fields
            self.store.add_entry(
                str(embedding_id),
                str(chunk_id),
                original_embedding,
                normalized_vector=normalized_vec,
                normalized_vector_algo=normalized_algo,
                normalized_vector_dim=len(normalized_vec),
                normalized_at=now,
                normalized_version=normalized_version,
                created_at=doc.get("created_at"),
                source_path=doc.get("source_path"),
                score_meta=score_meta,
            )
        except Exception as e:
            raise RetrieverError(str(e))

    def bulk_upsert(self, docs: List[Dict[str, Any]]) -> None:
        for d in docs:
            self.upsert(d)

    def get(self, id: str) -> Optional[RetrievalResult]:
        try:
            row = self.store.get_by_chunk_id(id)
            if not row:
                return None
            return self._normalize_row(row)
        except Exception as e:
            raise RetrieverError(str(e))

    def query_vector(self, vector: List[float], top_k: int = 10, metric: str = "cosine") -> List[RetrievalResult]:
        try:
            # normalize input vector
            qvec = vector_normalize(vector)
            cur = self.store.conn.cursor()
            # detect whether normalized_vector column exists in this SQLite table at runtime
            try:
                cur.execute("PRAGMA table_info(entries)")
                cols = [r[1] for r in cur.fetchall()]
            except Exception:
                cols = []
            extra_columns = ", normalized_vector" if "normalized_vector" in cols else ""
            cur.execute("SELECT embedding_id, chunk_id, vector, vector_dim, created_at, source_path, score_meta{extra} FROM entries".format(extra=extra_columns))
            rows = cur.fetchall()
            parsed = []
            for row in rows:
                embedding_id = row[0]
                chunk_id = row[1]
                # columns: embedding_id, chunk_id, vector, vector_dim, created_at, source_path, score_meta [, normalized_vector]
                vec_json = row[2] if len(row) > 2 else None
                vector_dim = row[3] if len(row) > 3 else None
                created_at = row[4] if len(row) > 4 else None
                source_path = row[5] if len(row) > 5 else None
                score_meta_json = row[6] if len(row) > 6 else None
                normalized_json = row[7] if len(row) > 7 else None
                # prefer precomputed normalized_vector if available (new schema)
                nvec = []
                try:
                    if normalized_json:
                        nvec = json.loads(normalized_json)
                    else:
                        vec = json.loads(vec_json) if vec_json else []
                        nvec = vector_normalize(vec)
                except Exception:
                    # fallback to empty normalized vector on parse errors
                    nvec = []
                sim = self._cosine_similarity(qvec, nvec)
                parsed.append((sim, {
                    "embedding_id": embedding_id,
                    "chunk_id": chunk_id,
                    "vector": nvec,
                    "vector_dim": row[3],
                    "created_at": row[4],
                    "source_path": row[5],
                    "score_meta": json.loads(row[6] or "{}") if row[6] else {},
                    "similarity": sim,
                }))
            parsed.sort(key=lambda t: t[0], reverse=True)
            out = []
            for sim, r in parsed[:top_k]:
                rr = self._normalize_row(r)
                # convert cosine [-1,1] to [0,1]
                try:
                    rr["similarity"] = (sim + 1.0) / 2.0
                except Exception:
                    rr["similarity"] = 0.0
                rr.setdefault("score", rr["similarity"])
                out.append(rr)
            return out
        except Exception as e:
            raise RetrieverError(str(e))

    def search(self, query: str, category: Optional[str] = None, limit: int = 10) -> List[RetrievalResult]:
        try:
            cur = self.store.conn.cursor()
            cur.execute("SELECT embedding_id, chunk_id, vector, vector_dim, created_at, source_path, score_meta FROM entries")
            rows = cur.fetchall()
            matches = []
            q_norm = text_normalize(query)
            for row in rows:
                score_meta = json.loads(row[6] or "{}") if row[6] else {}
                content_norm = text_normalize(score_meta.get("content") or "")
                if q_norm in content_norm:
                    r = {
                        "embedding_id": row[0],
                        "chunk_id": row[1],
                        "vector": json.loads(row[2]) if row[2] else [],
                        "vector_dim": row[3],
                        "created_at": row[4],
                        "source_path": row[5],
                        "score_meta": score_meta,
                        "similarity": 1.0,
                    }
                    matches.append(self._normalize_row(r))
            return matches[:limit]
        except Exception as e:
            raise RetrieverError(str(e))

    def probe(self, entity: str, category: Optional[str] = None, limit: int = 10) -> List[RetrievalResult]:
        return self.search(entity, category=category, limit=limit)

    def related(self, entity: str, category: Optional[str] = None, limit: int = 10) -> List[RetrievalResult]:
        return self.search(entity, category=category, limit=limit)

    def reason(self, entities: List[str], category: Optional[str] = None, limit: int = 10) -> List[RetrievalResult]:
        try:
            tokens = [text_normalize(e) for e in entities]
            cur = self.store.conn.cursor()
            cur.execute("SELECT embedding_id, chunk_id, vector, vector_dim, created_at, source_path, score_meta FROM entries")
            rows = cur.fetchall()
            matches = []
            for row in rows:
                score_meta = json.loads(row[6] or "{}") if row[6] else {}
                content_norm = text_normalize(score_meta.get("content") or "")
                if all(t in content_norm for t in tokens):
                    matches.append(self._normalize_row({
                        "embedding_id": row[0],
                        "chunk_id": row[1],
                        "vector": json.loads(row[2]) if row[2] else [],
                        "vector_dim": row[3],
                        "created_at": row[4],
                        "source_path": row[5],
                        "score_meta": score_meta,
                        "similarity": 1.0,
                    }))
            return matches[:limit]
        except Exception as e:
            raise RetrieverError(str(e))

    def contradict(self, category: Optional[str] = None, threshold: float = 0.3, limit: int = 10) -> List[Dict[str, Any]]:
        return []

    def stats(self) -> Dict[str, Any]:
        cur = self.store.conn.cursor()
        cur.execute("SELECT COUNT(1) as c FROM entries")
        row = cur.fetchone()
        return {"count": row[0] if row else 0}

    def _normalize_row(self, row: Dict[str, Any]) -> RetrievalResult:
        if isinstance(row, dict):
            embedding = row.get("vector") or []
            score_meta = row.get("score_meta") or {}
            return RetrievalResult(
                {
                    "id": row.get("chunk_id") or row.get("embedding_id"),
                    "embedding_id": row.get("embedding_id"),
                    "chunk_id": row.get("chunk_id"),
                    "content": score_meta.get("content") if isinstance(score_meta, dict) else None,
                    "embedding": embedding,
                    "vector_dim": row.get("vector_dim") or (len(embedding) if embedding else None),
                    "similarity": row.get("similarity"),
                    "score": row.get("score"),
                    "trust_score": score_meta.get("trust_score", 1.0) if isinstance(score_meta, dict) else 1.0,
                    "model": score_meta.get("model"),
                    "provider": self.name,
                    "source_path": row.get("source_path"),
                    "embedding_path": score_meta.get("embedding_path"),
                    "created_at": row.get("created_at"),
                    "updated_at": None,
                    "category": score_meta.get("category") if isinstance(score_meta, dict) else None,
                    "tags": score_meta.get("tags") if isinstance(score_meta, dict) else None,
                    "meta": score_meta if isinstance(score_meta, dict) else {},
                }
            )
        else:
            r = dict(row)
            vec = json.loads(r.get("vector") or "[]") if r.get("vector") is not None else []
            score_meta = json.loads(r.get("score_meta") or "{}") if r.get("score_meta") else {}
            return RetrievalResult(
                {
                    "id": r.get("chunk_id") or r.get("embedding_id"),
                    "embedding_id": r.get("embedding_id"),
                    "chunk_id": r.get("chunk_id"),
                    "content": score_meta.get("content") if isinstance(score_meta, dict) else None,
                    "embedding": vec,
                    "vector_dim": r.get("vector_dim") or (len(vec) if vec else None),
                    "similarity": None,
                    "score": None,
                    "trust_score": score_meta.get("trust_score", 1.0) if isinstance(score_meta, dict) else 1.0,
                    "model": score_meta.get("model"),
                    "provider": self.name,
                    "source_path": r.get("source_path"),
                    "embedding_path": score_meta.get("embedding_path"),
                    "created_at": r.get("created_at"),
                    "updated_at": None,
                    "category": score_meta.get("category") if isinstance(score_meta, dict) else None,
                    "tags": score_meta.get("tags") if isinstance(score_meta, dict) else None,
                    "meta": score_meta if isinstance(score_meta, dict) else {},
                }
            )

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
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