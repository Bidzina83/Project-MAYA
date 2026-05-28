# Temporary test-only shim to satisfy imports of maya_dev.plugins.memory.* during tests.
# This file will be committed to the repository as maya_dev/__init__.py by the GitHub App helper.
# It maps maya_dev.plugins.memory.* to existing hermes.plugins.memory.* modules at import time.
import importlib, sys

# Helper to map a source module into a target import path
def _map(src, target):
    try:
        m = importlib.import_module(src)
        sys.modules[target] = m
    except Exception:
        # best-effort; don't fail import of maya_dev
        pass

# Map the key modules used by tests to their hermes equivalents
_map('hermes.plugins.memory', 'maya_dev.plugins.memory')
_map('hermes.plugins.memory.ingest', 'maya_dev.plugins.memory.ingest')
_map('hermes.plugins.memory.ingest.backends.openai_backend', 'maya_dev.plugins.memory.ingest.backends.openai_backend')
_map('hermes.plugins.memory.ingest.backends.hf_backend', 'maya_dev.plugins.memory.ingest.backends.hf_backend')
_map('hermes.plugins.memory.ingest.embedder', 'maya_dev.plugins.memory.ingest.embedder')
_map('hermes.plugins.memory.ingest.chunker', 'maya_dev.plugins.memory.ingest.chunker')

# Provide a minimal package module for maya_dev and maya_dev.plugins
if 'maya_dev' not in sys.modules:
    import types
    pkg = types.ModuleType('maya_dev')
    pkg.__path__ = []
    sys.modules['maya_dev'] = pkg

if 'maya_dev.plugins' not in sys.modules:
    import types
    pmod = types.ModuleType('maya_dev.plugins')
    pmod.__path__ = []
    sys.modules['maya_dev.plugins'] = pmod

# If hermes.plugins.memory is present, expose it as attribute on maya_dev.plugins
try:
    if 'maya_dev.plugins.memory' in sys.modules:
        sys.modules['maya_dev.plugins'].memory = sys.modules['maya_dev.plugins.memory']
except Exception:
    pass

# End shim
