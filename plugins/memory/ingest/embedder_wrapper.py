"""Embedding client wrapper (T1.1) - extended implementation

Provides EmbeddingClient with simple input normalization and output shaping.
Supports inputs:
 - list[str]
 - list[dict] where dict must contain 'text' and optional 'id'

Returns list[dict] with keys: id, vector
"""
from typing import List, Any, Union

from .embedder import Embedder, compute_chunk_id, EmbedderError


class EmbeddingClient:
    """Thin wrapper providing convenience methods around Embedder.

    Args:
        backend: backend name (default: 'mock')
        model: model identifier passed through to the backend
        batch_size: backend batch size
    """

    def __init__(self, backend: str = "mock", model: str | None = None, batch_size: int = 32):
        self.embedder = Embedder(backend=backend, model=model, batch_size=batch_size)
        self.batch_size = int(batch_size)

    def _normalize_inputs(self, docs: List[Union[str, dict]]) -> List[dict]:
        out = []
        for item in docs:
            if isinstance(item, str):
                out.append({"text": item, "id": compute_chunk_id(item)})
            elif isinstance(item, dict):
                if "text" not in item:
                    raise EmbedderError("dict input must contain 'text' key")
                entry = dict(item)
                if "id" not in entry or not entry["id"]:
                    entry["id"] = compute_chunk_id(entry["text"])
                out.append(entry)
            else:
                raise EmbedderError("unsupported input type for embedding")
        return out

    def embed_documents(self, docs: List[Union[str, dict]]) -> List[dict]:
        """Embed documents and return list of dicts {id, vector} preserving order.
        """
        if not docs:
            return []
        normalized = self._normalize_inputs(docs)
        texts = [d["text"] for d in normalized]
        try:
            vecs = self.embedder.embed(texts)
        except EmbedderError:
            raise
        except Exception as e:
            raise EmbedderError(f"embedding failed: {e}")
        if len(vecs) != len(normalized):
            raise EmbedderError("backend returned mismatched vector count")
        result = []
        for meta, vec in zip(normalized, vecs):
            result.append({"id": meta["id"], "vector": vec})
        return result

    def compute_id(self, text: str) -> str:
        """Compute deterministic id for a chunk of text."""
        return compute_chunk_id(text)
