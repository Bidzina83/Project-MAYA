class MockBackend:
    def __init__(self, model=None):
        self.model = model
    def embed_batch(self, texts):
        return [[float(len(t)), 0.0, 0.0] for t in texts]
