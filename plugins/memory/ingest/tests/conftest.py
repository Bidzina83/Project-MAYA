"""Test conftest that ensures our test support overrides are injected into
backend modules before tests run. This makes behavior deterministic when
monkeypatch ordering / multiple import aliases are present in the test run.
"""
import importlib

try:
    overrides = importlib.import_module("hermes.plugins.memory.ingest.tests.support.overrides")
except Exception:
    overrides = None

candidates = [
    'hermes.plugins.memory.ingest.backends.openai_backend',
    'maya_dev.plugins.memory.ingest.backends.openai_backend',
    'plugins.memory.ingest.backends.openai_backend',
]

for name in candidates:
    try:
        m = importlib.import_module(name)
        if overrides:
            # only set defaults if not already present
            if not getattr(m, 'openai', None):
                setattr(m, 'openai', overrides.openai)
            if not getattr(m, 'openai_error', None):
                setattr(m, 'openai_error', overrides.openai_error)
    except Exception:
        pass

# HF requests candidate modules
hf_candidates = [
    'hermes.plugins.memory.ingest.backends.hf_backend',
    'maya_dev.plugins.memory.ingest.backends.hf_backend',
    'plugins.memory.ingest.backends.hf_backend',
]
for name in hf_candidates:
    try:
        m = importlib.import_module(name)
        if overrides and not getattr(m, 'requests', None):
            setattr(m, 'requests', overrides.requests)
    except Exception:
        pass
