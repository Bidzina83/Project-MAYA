from __future__ import annotations
from typing import List, Dict, Any, Optional

from plugins.memory.retriever_api import Retriever, RetrievalResult, RetrieverError
from plugins.memory.utils.normalization import text_normalize, vector_normalize


try:
    from plugins.memory.holographic.retrieval import FactRetriever
except Exception:
    FactRetriever = None  # type: ignore


class HolographicAdapter(Retriever):
    """Adapter around the holographic FactRetriever.

    This adapter expects a `store` object exposing a `_conn` sqlite3 connection
    and the schema the holographic retriever uses (facts, facts_fts, memory_banks,
    entities, fact_entities). If the underlying store does not expose the required
    schema, methods will raise RetrieverError.
    """

    def __init__(self, store: Any, name: str = "holographic", **kwargs):
        if FactRetriever is None:
            raise RetrieverError("Holographic FactRetriever not available")
        self.name = name
        try:
            self.retriever = FactRetriever(store=store, **kwargs)
        except Exception as e:
            raise RetrieverError(f"failed to init FactRetriever: {e}")

    def upsert(self, doc: Dict[str, Any]) -> None:
        # Holographic retriever is read-oriented here; upsert not supported
        raise RetrieverError("holographic adapter does not support upsert")

    def bulk_upsert(self, docs: List[Dict[str, Any]]) -> None:
        raise RetrieverError("holographic adapter does not support upsert")

    def get(self, id: str) -> Optional[RetrievalResult]:
        # Not directly supported by FactRetriever; fallback to search by id
        try:
            res = self.retriever.search(id, limit=1)
            if not res:
                return None
            r = res[0]
            r["provider"] = self.name
            # normalize content if present
            if r.get("content"):
                r["content_normalized"] = text_normalize(r.get("content"))
            return r
        except Exception as e:
            raise RetrieverError(str(e))

    def query_vector(self, vector: List[float], top_k: int = 10, metric: str = "cosine") -> List[RetrievalResult]:
        try:
            qvec = vector_normalize(vector)
            res = self.retriever._score_facts_by_vector(qvec, limit=top_k)
            out = []
            for r in res:
                r["provider"] = self.name
                # normalize content if present
                if r.get("content"):
                    r["content_normalized"] = text_normalize(r.get("content"))
                # normalize embedding if present
                if r.get("embedding"):
                    r["embedding"] = vector_normalize(r.get("embedding"))
                out.append(r)
            return out
        except Exception as e:
            raise RetrieverError(str(e))

    def search(self, query: str, category: Optional[str] = None, limit: int = 10) -> List[RetrievalResult]:
        try:
            res = self.retriever.search(query, category=category, limit=limit)
            for r in res:
                r["provider"] = self.name
                if r.get("content"):
                    r["content_normalized"] = text_normalize(r.get("content"))
            return res
        except Exception as e:
            raise RetrieverError(str(e))

    def probe(self, entity: str, category: Optional[str] = None, limit: int = 10) -> List[RetrievalResult]:
        try:
            res = self.retriever.probe(entity, category=category, limit=limit)
            for r in res:
                r["provider"] = self.name
                if r.get("content"):
                    r["content_normalized"] = text_normalize(r.get("content"))
            return res
        except Exception as e:
            raise RetrieverError(str(e))

    def related(self, entity: str, category: Optional[str] = None, limit: int = 10) -> List[RetrievalResult]:
        try:
            res = self.retriever.related(entity, category=category, limit=limit)
            for r in res:
                r["provider"] = self.name
                if r.get("content"):
                    r["content_normalized"] = text_normalize(r.get("content"))
            return res
        except Exception as e:
            raise RetrieverError(str(e))

    def reason(self, entities: List[str], category: Optional[str] = None, limit: int = 10) -> List[RetrievalResult]:
        try:
            res = self.retriever.reason(entities, category=category, limit=limit)
            for r in res:
                r["provider"] = self.name
                if r.get("content"):
                    r["content_normalized"] = text_normalize(r.get("content"))
            return res
        except Exception as e:
            raise RetrieverError(str(e))

    def contradict(self, category: Optional[str] = None, threshold: float = 0.3, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            res = self.retriever.contradict(category=category, threshold=threshold, limit=limit)
            # results are pairs; attach provider hint
            for pair in res:
                pair.setdefault("provider", self.name)
            return res
        except Exception as e:
            raise RetrieverError(str(e))

    def stats(self) -> Dict[str, Any]:
        # best-effort: delegate to underlying store stats if available
        try:
            return {"provider": self.name}
        except Exception:
            return {"provider": self.name}
