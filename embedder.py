"""Embedding wrapper for Project MAYA persistent memory.

Provides:
- Embedder class with simple batching and backend factory hook
- compute_chunk_id(text) -> sha256 hex
- EmbedderError exception

This module keeps the implementation minimal and pluggable for tests.
"""
from __future__ import annotations
import hashlib
from typing import List, Any

__version__ = "0.1.0"


class EmbedderError(Exception):
    pass


def compute_chunk_id(text: str) -> str:
    """Deterministic sha256 chunk id for a piece of text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# Default BackendFactory; test harnesses may monkeypatch this name on the module.
def BackendFactory(name: str, model: str):
    """Create and return a backend instance.

    Tests may monkeypatch this symbol to return a mock backend.
    The default behavior supports an in-module MockBackend if present.
    """
    if name == "mock" and "MockBackend" in globals():
        return globals()["MockBackend"](model=model)
    raise NotImplementedError("no backend factory for %s" % name)


class Embedder:
    """Simple embedder wrapper.

    Args:
        backend: backend name passed to BackendFactory
        model: model identifier
        batch_size: number of items per backend.batch call
    """

    def __init__(self, backend: str = "mock", model: str | None = None, batch_size: int = 32):
        self.backend = backend
        self.model = model
        self.batch_size = int(batch_size)

    def embed(self, texts: List[str]) -> List[Any]:
        """Return list of vectors, preserving input order.

        Uses BackendFactory(module-level) so tests can monkeypatch BackendFactory.
        """
        if not texts:
            return []
        try:
            backend_inst = BackendFactory(self.backend, self.model)
        except Exception as e:
            raise EmbedderError(f"backend init failed: {e}")

        out = []
        try:
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i : i + self.batch_size]
                vecs = backend_inst.embed_batch(batch)
                out.extend(vecs)
        except Exception as e:
            # wrap backend errors
            raise EmbedderError(f"backend error: {e}")
        return out
