import types


def test_embedder_batching(monkeypatch):
    calls = []

    class FakeBackend:
        def __init__(self, model=None):
            self.model = model

        def embed_batch(self, texts):
            calls.append(list(texts))
            return [[len(t)] for t in texts]

    # Patch BackendFactory used inside Embedder to return our FakeBackend
    monkeypatch.setattr('hermes.plugins.memory.ingest.embedder.BackendFactory', lambda name, model: FakeBackend(model), raising=True)

    from hermes.plugins.memory.ingest.embedder_wrapper import EmbeddingClient

    client = EmbeddingClient(backend='mock', model='m', batch_size=2)
    docs = [str(i) * (i + 1) for i in range(5)]  # lengths 1..5
    out = client.embed_documents(docs)

    # Expect 3 backend embed_batch calls: batches of 2,2,1
    assert len(calls) == 3
    assert calls[0] == [docs[0], docs[1]]
    assert calls[1] == [docs[2], docs[3]]
    assert calls[2] == [docs[4]]

    # Returned vectors preserved in order
    assert [r['vector'][0] for r in out] == [1, 2, 3, 4, 5]
