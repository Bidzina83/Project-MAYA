import hashlib
import importlib
import types

import pytest

from hermes.plugins.memory.ingest import embedder


def test_compute_chunk_id_known():
    text = "hello world"
    expected = hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert embedder.compute_chunk_id(text) == expected


def test_embedder_empty_returns_empty_list():
    e = embedder.Embedder(backend="mock", model="m1", batch_size=4)
    assert e.embed([]) == []


class FakeBackend:
    def __init__(self, model=None):
        self.model = model

    def embed_batch(self, texts):
        # return deterministic vectors: each vector is list of char codes of first char
        out = []
        for t in texts:
            if t == "__raise__":
                raise RuntimeError("backend fail")
            v = [ord(t[0]) if t else 0]
            out.append(v)
        return out


def test_embedder_preserves_order_and_batching(monkeypatch):
    # Monkeypatch BackendFactory to return our FakeBackend
    def factory(name, model):
        return FakeBackend(model=model)

    monkeypatch.setattr(embedder, "BackendFactory", factory)

    e = embedder.Embedder(backend="mock", model="m1", batch_size=2)
    inputs = ["a", "b", "c", "d"]
    out = e.embed(inputs)
    assert out == [[97], [98], [99], [100]]


def test_embedder_wraps_backend_exceptions(monkeypatch):
    # factory that returns backend which raises
    def factory(name, model):
        return FakeBackend(model=model)

    monkeypatch.setattr(embedder, "BackendFactory", factory)
    e = embedder.Embedder(backend="mock", model="m1", batch_size=2)
    with pytest.raises(embedder.EmbedderError):
        e.embed(["ok", "__raise__", "ok2"])
