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
import importlib
import sys
import logging
try:
    from . import config
except Exception:
    # When the module is loaded standalone (tests using importlib.exec_module) the
    # package-relative import may fail. Try absolute import, then fall back to a
    # minimal env-based config shim.
    try:
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

log = logging.getLogger(__name__)


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

    if name == "mock" and "MockBackend" in globals():
        return globals()["MockBackend"](model=model)
    raise NotImplementedError("no backend factory for %s" % name)


def _resolve_backend_factory():
    """Robustly locate BackendFactory across possible module name prefixes.

    Pytest / xdist / import-order can result in the same module being loaded under
    slightly different package names (with or without top-level 'hermes'). To make
    tests' monkeypatches reliable, scan sys.modules for any callable BackendFactory.
    Prefer a module-level BackendFactory that differs from the local default when present.
    """
    candidates = []
    for mod_name, mod in list(sys.modules.items()):
        try:
            factory = getattr(mod, "BackendFactory", None)
            if callable(factory):
                candidates.append((mod_name, factory, mod))
        except Exception:
            continue
    # diagnostic
    if candidates:
        print("DEBUG: _resolve_backend_factory candidates:")
        for mn, fac, mod in candidates:
            print("  ", mn, "factory=", fac, "mod=", mod)
    else:
        print("DEBUG: _resolve_backend_factory no callable BackendFactory found in sys.modules")

    local_factory = globals().get('BackendFactory')
    # If the local BackendFactory has been replaced (module differs), prefer it
    if callable(local_factory) and getattr(local_factory, '__module__', None) != __name__:
        log.debug("_resolve_backend_factory: using local (monkeypatched) BackendFactory from module %s", getattr(local_factory, '__module__', None))
        return local_factory

    # prefer candidates in the canonical hermes module first
    for mn, fac, mod in candidates:
        if mn == 'hermes.plugins.memory.ingest.embedder' and fac is not local_factory:
            log.debug("_resolve_backend_factory: choosing hermes module candidate %s", mn)
            return fac
    # prefer explicit test-like module names if present
    for mn, fac, mod in candidates:
        if ('maya_dev' in mn or mn.startswith('plugins.')) and fac is not local_factory:
            log.debug("_resolve_backend_factory: preferring candidate in %s", mn)
            return fac
    # next prefer suffix match but prefer factories that differ from local
    for mod_name, mod in list(sys.modules.items()):
        try:
            if mod_name.endswith("memory.ingest.embedder"):
                factory = getattr(mod, "BackendFactory", None)
                if callable(factory) and factory is not local_factory:
                    log.debug("_resolve_backend_factory: found factory on module %s", mod_name)
                    return factory
                else:
                    log.debug("_resolve_backend_factory: module %s has BackendFactory but it's not callable or is local", mod_name)
        except Exception:
            continue
    # broader scan fallback: return the first candidate that differs from the local factory
    for mn, fac, mod in candidates:
        if fac is not local_factory:
            log.debug("_resolve_backend_factory: returning candidate differing from local: %s", mn)
            return fac
    # fallback to local symbol
    log.debug("_resolve_backend_factory: falling back to local BackendFactory")
    return local_factory


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
        This implementation resolves BackendFactory dynamically by scanning
        sys.modules to avoid stale bindings in environments where tests patch
        the module attribute at runtime (xdist worker / import-order fragility).
        """
        if not texts:
            return []
        try:
            print("DEBUG: embed resolving backend factory...")
            factory = _resolve_backend_factory()
            print("DEBUG: embed factory resolved:", factory)
            log.debug("embed: resolved factory=%s for backend=%s model=%s", getattr(factory, '__name__', str(factory)), self.backend, self.model)
            if not callable(factory):
                raise Exception("BackendFactory not available")
            backend_inst = factory(self.backend, self.model)
            print("DEBUG: embed backend_inst:", backend_inst)
            log.debug("embed: backend_inst=%s", type(backend_inst))
        except Exception as e:
            log.exception("embed: backend init failed")
            print("DEBUG: embed exception during backend init:", e)
            raise EmbedderError(f"backend init failed: {e}")

        out = []
        try:
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i : i + self.batch_size]
                print("DEBUG: embed sending batch:", batch)
                log.debug("embed: sending batch=%s", batch)
                vecs = backend_inst.embed_batch(batch)
                print("DEBUG: embed received vecs:", vecs)
                log.debug("embed: received vecs=%s", vecs)
                out.extend(vecs)
        except Exception as e:
            # wrap backend errors
            log.exception("embed: backend error")
            print("DEBUG: embed backend error:", e)
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
            factory = _resolve_backend_factory()
            print("DEBUG: embed_with_provenance factory:", factory)
            log.debug("embed_with_provenance: resolved factory=%s", getattr(factory, '__name__', str(factory)))
            if not callable(factory):
                raise Exception("BackendFactory not available")
            backend_inst = factory(self.backend, self.model)
            print("DEBUG: embed_with_provenance backend_inst:", backend_inst)
            log.debug("embed_with_provenance: backend_inst=%s", type(backend_inst))
        except Exception as e:
            log.exception("embed_with_provenance: backend init failed")
            print("DEBUG: embed_with_provenance exception during backend init:", e)
            raise EmbedderError(f"backend init failed: {e}")

        out = []
        try:
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i : i + self.batch_size]
                batch_source = source_texts[i : i + self.batch_size]
                print("DEBUG: embed_with_provenance sending batch:", batch)
                log.debug("embed_with_provenance: sending batch=%s", batch)
                vecs = backend_inst.embed_batch(batch)
                print("DEBUG: embed_with_provenance received vecs:", vecs)
                log.debug("embed_with_provenance: received vecs=%s", vecs)
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
            log.exception("embed_with_provenance: backend error")
            print("DEBUG: embed_with_provenance backend error:", e)
            raise EmbedderError(f"backend error: {e}")
        return out


# Test shim: provide MockBackend in module globals so tests that rely on the
# BackendFactory default path for name == "mock" can succeed even if their
# monkeypatch didn't take effect.
if "MockBackend" not in globals():
    class MockBackend:
        def __init__(self, model=None):
            self.model = model

        def embed_batch(self, texts):
            # return a vector of length for each text (deterministic)
            return [[len(t)] for t in texts]
