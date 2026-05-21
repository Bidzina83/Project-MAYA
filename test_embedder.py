import importlib.util
import hashlib
import pytest

EMBEDDER_PATH = "/opt/hermes/plugins/memory/ingest/embedder.py"


def load_embedder_module():
    spec = importlib.util.spec_from_file_location("m_embedder", EMBEDDER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_module_has_embedder_class():
    """The embedder module should expose an Embedder class."""
    m = load_embedder_module()
    assert hasattr(m, "Embedder"), "embedder.Embedder class missing"


def test_deterministic_hashing():
    """Same input text must produce the same sha256 chunk id."""
    m = load_embedder_module()
    text = "The quick brown fox jumps over the lazy dog"
    # Expect the module to provide a helper for chunk id generation.
    assert hasattr(m, "compute_chunk_id") or hasattr(m, "chunk_id"), "no chunk id helper found"
    fn = getattr(m, "compute_chunk_id", None) or getattr(m, "chunk_id", None)
    h1 = fn(text)
    h2 = fn(text)
    assert isinstance(h1, str)
    assert h1 == h2
    # compare to direct sha256 if possible
    expected = hashlib.sha256(text.encode("utf-8")).hexdigest()
    # allow implementations that prefix/suffix versioning; require contains expected or equals
    assert expected in h1 or h1 == expected


def test_batches_inputs_correctly(monkeypatch):
    """Embedder should batch inputs according to batch_size and call backend accordingly.

    We mock a backend that records calls.
    """
    m = load_embedder_module()
    # require Embedder class
    assert hasattr(m, "Embedder"), "Embedder class missing"
    calls = []

    class MockBackend:
        def __init__(self, model=None):
            self.model = model

        def embed_batch(self, texts):
            calls.append(list(texts))
            # return dummy vectors
            return [[0.1] * 8 for _ in texts]

    # Monkeypatch the backend factory or class on the module if present
    if hasattr(m, "BackendFactory"):
        monkeypatch.setattr(m, "BackendFactory", lambda name, model: MockBackend(model=model))
    else:
        # set attribute used by Embedder constructor if exists
        monkeypatch.setattr(m, "MockBackend", MockBackend, raising=False)

    # Construct embedder with batch_size 3
    Embedder = m.Embedder
    emb = Embedder(backend="mock", model="m", batch_size=3)

    texts = [f"text-{i}" for i in range(7)]
    result = emb.embed(texts)
    # verify backend was called in batches [3,3,1]
    assert calls == [texts[0:3], texts[3:6], texts[6:7]]
    # result should be a list of embeddings matching input length
    assert isinstance(result, list)
    assert len(result) == len(texts)


def test_handles_backend_errors_gracefully(monkeypatch):
    """If backend raises, embedder should raise a defined EmbedderError (or re-raise with context)."""
    m = load_embedder_module()
    class FailingBackend:
        def __init__(self, model=None):
            pass
        def embed_batch(self, texts):
            raise RuntimeError("backend fail")

    if hasattr(m, "BackendFactory"):
        monkeypatch.setattr(m, "BackendFactory", lambda name, model: FailingBackend(model=model))
    else:
        monkeypatch.setattr(m, "FailingBackend", FailingBackend, raising=False)

    Embedder = getattr(m, "Embedder")
    emb = Embedder(backend="fail", model="m", batch_size=2)
    with pytest.raises(Exception) as exc:
        emb.embed(["a","b"])
    # ensure original message is accessible
    assert "backend" in str(exc.value) or "fail" in str(exc.value)
