from hermes.plugins.memory.ingest.embedder import Embedder

class EmbeddingClient:
    def __init__(self, backend=None, model=None, batch_size=32):
        self.backend = backend
        self.model = model
        self.batch_size = batch_size
        self.embedder = Embedder(backend=backend, model=model, batch_size=batch_size)

    def embed_documents(self, docs):
        """
        Embed a list of documents using batching.
        Returns list of dicts with 'vector' key.
        """
        try:
            out = self.embedder.embed_with_provenance(docs, source_texts=None)
            if out and isinstance(out[0], dict) and 'vector' in out[0]:
                return out
        except Exception:
            out = None
        vecs = self.embedder.embed(docs)
        return [{'vector': v} for v in vecs]
