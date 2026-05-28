# Package plugins.memory.ingest package for Project-MAYA

# Minimal package initializer to expose submodules as attributes for test monkeypatch resolution.
__all__ = [
    "chunker",
    "embedder",
    "embedder_wrapper",
    "pipeline",
    "registry",
    "sqlite_registry",
    "backends",
]

# Import submodules so they are available as attributes on the package module object.
# This is a small, backwards-compatible change to make attribute-based lookup (e.g. monkeypatch.setattr('hermes.plugins.memory.ingest.backends...')) work.
try:
    from . import chunker, embedder, embedder_wrapper, pipeline, registry, sqlite_registry, backends  # type: ignore
except Exception:
    # best-effort import; tests that rely on these modules will trigger their own imports if needed
    pass
