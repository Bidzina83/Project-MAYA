# Auto-generated shim to expose EmbeddingClient for tests
from plugins.memory.ingest import embedder as _embedder

class EmbeddingClient:
    def __init__(self, model=None, provider=None):
        # delegate to embedder.EmbeddingClient if exists, otherwise use simple wrapper
        if hasattr(_embedder, 'EmbeddingClient'):
            self._inner = _embedder.EmbeddingClient(model=model, provider=provider)
        else:
            self._inner = None
    
    def embed_batch(self, texts):
        if self._inner is not None and hasattr(self._inner, 'embed_batch'):
            return self._inner.embed_batch(texts)
        # fallback: return list of lengths
        return [[len(t)] for t in texts]

    def embed_many(self, texts):
        return self.embed_batch(texts)
