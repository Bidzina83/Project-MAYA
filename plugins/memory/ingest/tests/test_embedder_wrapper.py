import hashlib
from typing import List

import pytest

from plugins.memory.ingest import embedder_wrapper as ew
from plugins.memory.ingest import embedder


class FakeBackend:
    def __init__(self, model=None):
        self.model = model

    def embed_batch(self, texts: List[str]):
        # return a vector with length = len(text) for deterministic assertion
        return [[len(t)] for t in texts]


def test_embed_documents_with_strings(monkeypatch):
    # monkeypatch BackendFactory to return our FakeBackend
    monkeypatch.setattr(embedder, "BackendFactory", lambda name, model: FakeBackend(model))

    client = ew.EmbeddingClient(backend="mock", model="mymodel", batch_size=2)
    docs = ["a", "bb", "ccc"]
    out = client.embed_documents(docs)
    assert isinstance(out, list)
    assert len(out) == 3
    # vectors should match lengths
    assert out[0]["vector"] == [1]
    assert out[1]["vector"] == [2]
    assert out[2]["vector"] == [3]
    # ids should be deterministic sha256
    assert out[0]["id"] == hashlib.sha256(b"a").hexdigest()


def test_embed_documents_with_dicts_and_ids(monkeypatch):
    monkeypatch.setattr(embedder, "BackendFactory", lambda name, model: FakeBackend(model))
    client = ew.EmbeddingClient(backend="mock", model=None, batch_size=10)
    docs = [{"text": "hello", "id": "custom-id-1"}, {"text": "yo"}]
    out = client.embed_documents(docs)
    assert out[0]["id"] == "custom-id-1"
    assert out[0]["vector"] == [5]
    # second id computed
    assert out[1]["id"] == hashlib.sha256(b"yo").hexdigest()
    assert out[1]["vector"] == [2]
