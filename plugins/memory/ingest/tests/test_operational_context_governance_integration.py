from plugins.memory.retriever_api import Retriever
from plugins.memory.retriever_service import RetrieverService
from plugins.memory.governance_validator import GovernanceValidator, GovernancePolicy


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
                "trust_score": 0.1,
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


def test_retriever_service_includes_governance_in_operational_context():
    policy = GovernancePolicy(min_trust=0.5)
    gv = GovernanceValidator(policy=policy)

    svc = RetrieverService(primary_local="fake", governance_validator=gv)
    fake = FakeRetriever(name="fake")
    svc.register_provider("fake", fake)

    results = svc.query_vector([0.0, 0.0], top_k=2)
    assert len(results) == 2

    ctx = svc.last_operational_context
    assert ctx is not None
    # governance_summary should be present and indicate low_trust for c-a
    assert "governance_summary" in ctx
    gs = ctx["governance_summary"]
    assert isinstance(gs, dict)
    # find block c-a and check gov_annotations
    blocks = {b["chunk_id"]: b for b in ctx["blocks"]}
    assert "c-a" in blocks
    b_a = blocks["c-a"]
    assert "gov_annotations" in b_a
    ann = b_a["gov_annotations"]
    assert ann is not None
    # enforcement_hints should be present for low_trust
    hints = ann.get("enforcement_hints")
    assert hints is not None
    assert "score_adjust" in hints or "block_flag" in hints
