import hashlib

import pytest

from plugins.memory.ingest import embedder


def test_compute_source_hash_and_provenance(monkeypatch):
    texts = ["alpha", "beta"]
    sources = ["full content alpha", "full content beta"]

    class FakeBackend:
        def __init__(self, model=None):
            self.model = model

        def embed_batch(self, texts):
            return [[len(t)] for t in texts]

    def factory(name, model):
        return FakeBackend(model=model)

    monkeypatch.setattr(embedder, "BackendFactory", factory)

    e = embedder.Embedder(backend="mock", model="m1", batch_size=2)
    res = e.embed_with_provenance(texts, source_texts=sources, extractor_version="v0.1")
    assert isinstance(res, list)
    assert len(res) == 2
    for t, s, item in zip(texts, sources, res):
        assert item["chunk_id"] == hashlib.sha256(t.encode("utf-8")).hexdigest()
        assert item["source_hash"] == hashlib.sha256(s.encode("utf-8")).hexdigest()
        assert item["extractor_version"] == "v0.1"
        assert isinstance(item["vector"], list)
