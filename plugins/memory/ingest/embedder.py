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
try:
    from . import config
except Exception:
    # When the module is loaded standalone (tests using importlib.exec_module) the
    # package-relative import may fail. Try absolute import, then fall back to a
    # minimal env-based config shim.
    try:
        import importlib

        config = importlib.import_module("hermes.plugins.memory.ingest.config")
    except Exception:
        import os
        class _FallbackConfig:
            def get_default_backend(self):
                return os.environ.get("MAYA_DEFAULT_BACKEND", "openai")

            def get_default_model(self):
                return os.environ.get("MAYA_DEFAULT_MODEL", "text-embedding-3-small")

        config = _FallbackConfig()

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
    # Known built-in backends (real provider implementations live under backends/)
    if name in ("openai", "openai_api"):
        try:
            from .backends.openai_backend import OpenAIBackend

            return OpenAIBackend(model)
        except Exception as e:
            raise NotImplementedError(f"OpenAI backend not available: {e}")

    if name in ("hf", "huggingface"):
        try:
            from .backends.hf_backend import HFBackend

            return HFBackend(model)
        except Exception as e:
            raise NotImplementedError(f"HuggingFace backend not available: {e}")

    if name == "mock":
        try:
            from .backends.mock_backend import MockBackend as _MockBackend
            return _MockBackend(model)
        except Exception:
            # fallback to legacy global MockBackend if tests injected it
            if "MockBackend" in globals():
                return globals()["MockBackend"](model=model)
            raise NotImplementedError("mock backend not available; please install or provide MockBackend")
    raise NotImplementedError("no backend factory for %s" % name)


class Embedder:
    """Simple embedder wrapper.

    Args:
        backend: backend name passed to BackendFactory
        model: model identifier
        batch_size: number of items per backend.batch call
    """

    def __init__(self, backend: str | None = "mock", model: str | None = None, batch_size: int = 32):
        # If backend is None or "auto", consult config defaults
        if backend in (None, "auto"):
            backend = config.get_default_backend()
        self.backend = backend
        # model preference: explicit argument > env/config default
        if model is None:
            model = config.get_default_model()
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

    # Provenance helpers
    def compute_source_hash(self, source_text: str) -> str:
        """Compute sha256 of the full source (useful as source_hash)."""
        return hashlib.sha256(source_text.encode("utf-8")).hexdigest()

    def embed_with_provenance(self, texts: List[str], source_texts: List[str] | None = None, extractor_version: str | None = None) -> List[dict]:
        """Embed texts and return list of dicts: {chunk_id, source_hash, extractor_version, vector}.

        - source_texts: optional parallel array providing the source content for each text (used to compute source_hash).
        - extractor_version: string describing extractor version to record.
        """
        if not texts:
            return []
        if source_texts is None:
            source_texts = [None] * len(texts)
        if len(source_texts) != len(texts):
            raise EmbedderError("source_texts length must match texts length")
        try:
            backend_inst = BackendFactory(self.backend, self.model)
        except Exception as e:
            raise EmbedderError(f"backend init failed: {e}")

        out = []
        try:
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i : i + self.batch_size]
                batch_source = source_texts[i : i + self.batch_size]
                vecs = backend_inst.embed_batch(batch)
                for t, s, v in zip(batch, batch_source, vecs):
                    chunk_id = compute_chunk_id(t)
                    source_hash = self.compute_source_hash(s) if s is not None else None
                    out.append({
                        "chunk_id": chunk_id,
                        "source_hash": source_hash,
                        "extractor_version": extractor_version,
                        "vector": v,
                    })
        except Exception as e:
            raise EmbedderError(f"backend error: {e}")
        return out
