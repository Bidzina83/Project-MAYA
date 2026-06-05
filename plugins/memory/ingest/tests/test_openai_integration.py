import os
import importlib.util
import pytest

BACKEND_PATH = "/opt/hermes/plugins/memory/ingest/backends/openai_backend.py"

OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

pytestmark = pytest.mark.skipif(not OPENAI_KEY, reason="OPENAI_API_KEY not set; integration test skipped")


def load_backend():
    spec = importlib.util.spec_from_file_location("openai_backend", BACKEND_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.OpenAIBackend


def test_openai_embed_small():
    OpenAIBackend = load_backend()
    backend = OpenAIBackend(model=os.environ.get("OPENAI_EMBED_MODEL"))
    vecs = backend.embed_batch(["hello world"])
    assert isinstance(vecs, list)
    assert len(vecs) == 1
    # vector should be a sequence of floats
    v = vecs[0]
    assert hasattr(v, "__len__") and len(v) > 0
    assert all(isinstance(x, (float, int)) for x in v)
