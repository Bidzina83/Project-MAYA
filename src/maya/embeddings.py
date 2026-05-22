from typing import List
import os

from . import config

# Try to import the OpenAI adapter lazily; keep a local fallback implementation
_adapter = None


def _load_adapter():
    global _adapter
    if _adapter is not None:
        return _adapter

    provider = os.getenv("MAYA_EMBEDDING_PROVIDER", config.MAYA_EMBEDDING_PROVIDER).lower()
    if provider in ("openai", "azure", "openai-azure"):
        try:
            from .adapters.openai_provider import embed_text_openai
            _adapter = embed_text_openai
            return _adapter
        except Exception as e:
            # Adapter import failed; fall back to local placeholder but raise when used
            _adapter = None
            return None
    else:
        return None


def embed_text(text: str) -> List[float]:
    """Public entrypoint for embedding text.

    Behavior:
    - If MAYA_EMBEDDING_PROVIDER is 'openai' (or 'azure'), try to call the OpenAI adapter.
    - If the OpenAI adapter is unavailable or raises configuration errors, raise RuntimeError so callers/tests see the issue.
    - Otherwise, use a deterministic local placeholder embedding (skeleton) suitable for tests.
    """
    provider = os.getenv("MAYA_EMBEDDING_PROVIDER", config.MAYA_EMBEDDING_PROVIDER).lower()
    adapter = _load_adapter()

    if provider in ("openai", "azure"):
        if adapter is None:
            raise RuntimeError("OpenAI adapter is not available; ensure the openai package is installed and adapter import succeeds")
        return adapter(text)

    # Local deterministic placeholder (previous skeleton)
    if not text:
        return [0.0]
    vec = [float(ord(c) % 256) / 255.0 for c in text[: config.FALLBACK_DIM]]
    return vec
