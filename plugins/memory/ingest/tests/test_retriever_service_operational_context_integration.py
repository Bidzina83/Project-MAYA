from plugins.memory.retriever_api import Retriever
from plugins.memory.retriever_service import RetrieverService


class FakeRetriever(Retriever):
    def __init__(self, name="fake"):
        self.name = name

    def upsert(self, doc):
        raise NotImplementedError

    def bulk_upsert(self, docs):
        raise NotImplementedError

    def get(self, id: str):
        return None

    def query_vector(self, vector, top_k: int = 10, metric: str = "cosine"):
        # Return two mock retrieval results
        return [
            {
                "id": "id-a",
                "chunk_id": "c-a",
                "content": "alpha beta gamma",
                "embedding": [0.1, 0.2],
                "vector_dim": 2,
                "similarity": 0.9,
                "score": 0.9,
                "trust_score": 1.0,
                "model": "embedder-v1",
                "provider": self.name,
                "source_path": "/data/c-a.txt",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
                "category": "note",
                "tags": ["t1"],
                "meta": {"example": True},
            },
            {
                "id": "id-b",
                "chunk_id": "c-b",
                "content": "delta epsilon",
                "embedding": [0.3, 0.4],
                "vector_dim": 2,
                "similarity": 0.85,
                "score": 0.85,
                "trust_score": 1.0,
                "model": "embedder-v1",
                "provider": self.name,
                "source_path": "/data/c-b.txt",
                "created_at": "2026-01-02T00:00:00Z",
                "updated_at": "2026-01-02T00:00:00Z",
                "category": "note",
                "tags": ["t2"],
                "meta": {"example": True},
            },
        ]

    def search(self, query, category=None, limit: int = 10):
        return []

    def probe(self, entity, category=None, limit: int = 10):
        return []

    def related(self, entity, category=None, limit: int = 10):
        return []

    def reason(self, entities, category=None, limit: int = 10):
        return []

    def contradict(self, category: None, threshold: float = 0.3, limit: int = 10):
        return []

    def stats(self):
        return {"count": 2}


def test_retriever_service_builds_operational_context_after_query():
    svc = RetrieverService(primary_local="fake")
    fake = FakeRetriever(name="fake")
    svc.register_provider("fake", fake)

    results = svc.query_vector([0.0, 0.0], top_k=2)
    # Ensure the query returned results
    assert len(results) == 2

    # Ensure last_operational_context was populated
    ctx = svc.last_operational_context
    assert ctx is not None
    assert isinstance(ctx, dict)
    assert "blocks" in ctx
    assert isinstance(ctx["blocks"], list)
    assert len(ctx["blocks"]) == 2

    # Check block fields
    b0 = ctx["blocks"][0]
    assert b0["chunk_id"] == "c-a"
    assert b0["content"].startswith("alpha")
    assert b0["provider"] == "fake"
    assert "estimated_tokens" in b0 and b0["estimated_tokens"] > 0

    # Check totals
    assert ctx["total_tokens"] > 0
    assert ctx["token_budget"] == 2048
    assert "truncated" in ctx
