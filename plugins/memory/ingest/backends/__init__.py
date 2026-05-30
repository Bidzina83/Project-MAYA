# Make backends a regular package namespace exposing known backend modules as attributes
# This helps attribute-based monkeypatching used in tests (monkeypatch.setattr('...backends.openai_backend.openai', ...)).
try:
    from . import openai_backend  # type: ignore
    from . import hf_backend  # type: ignore
    from . import mock_backend  # type: ignore
except Exception:
    # best-effort: backends may be absent in some environments
    pass

# Expose names in module namespace if imported
try:
    globals().setdefault('openai_backend', openai_backend)
except NameError:
    pass
try:
    globals().setdefault('hf_backend', hf_backend)
except NameError:
    pass
try:
    globals().setdefault('mock_backend', mock_backend)
except NameError:
    pass
