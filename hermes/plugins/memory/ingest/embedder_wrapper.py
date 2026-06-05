from plugins.memory.ingest.embedder import Embedder

class EmbeddingClient:
    """Lightweight proxy embedding client that delegates to the repo Embedder implementation.
    This satisfies tests importing hermes.plugins.memory.ingest.embedder_wrapper.
    """
    def __init__(self, backend=None, model=None, batch_size=32):
        self.embedder = Embedder(backend=backend, model=model, batch_size=batch_size)

    def embed_batch(self, texts):
        return self.embedder.embed(texts)
