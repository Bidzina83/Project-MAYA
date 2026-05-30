"""Test conftest that ensures our test support overrides are injected into
backend modules before tests run. This makes behavior deterministic when
monkeypatch ordering / multiple import aliases are present in the test run.
"""
import importlib
import importlib.util
import os

# Make spec_from_file_location resilient to absolute /opt/hermes paths used in some
# modules/tests. When the runner uses a workspace path (GITHUB_WORKSPACE) or the
# repo checkout, prefer that location if the /opt/hermes file is missing.
_orig_spec = importlib.util.spec_from_file_location
def _spec_from_file_location(name, location, *args, **kwargs):
    if isinstance(location, str) and location.startswith('/opt/hermes/'):
        rel = location[len('/opt/hermes/'):].lstrip('/')
        gw = os.environ.get('GITHUB_WORKSPACE')
        candidates = []
        if gw:
            candidates.append(os.path.join(gw, rel))
        # repo-relative candidate
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
        candidates.append(os.path.join(repo_root, rel))
        # cwd fallback
        candidates.append(os.path.join(os.getcwd(), rel))
        for alt in candidates:
            if os.path.exists(alt):
                location = alt
                break
    return _orig_spec(name, location, *args, **kwargs)
importlib.util.spec_from_file_location = _spec_from_file_location

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
