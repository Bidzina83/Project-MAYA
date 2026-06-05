import pytest

from plugins.memory.context_builder import build_context


def _make_retrieval(chunk_id: str, content: str, score: float = 1.0, trust: float = 1.0, similarity: float = 1.0, provider: str = "local"):
    return {
        "id": f"id-{chunk_id}",
        "chunk_id": chunk_id,
        "content": content,
        "score": score,
        "trust_score": trust,
        "similarity": similarity,
        "provider": provider,
        "source_path": f"/data/{chunk_id}.txt",
        "created_at": "2026-01-01T00:00:00Z",
        "meta": {"example": True},
    }


def test_build_context_basic_order_and_dedupe():
    r1 = _make_retrieval("c1", "alpha beta gamma", score=0.9, trust=0.9)
    r2 = _make_retrieval("c2", "delta epsilon", score=0.8, trust=0.8)
    r3 = _make_retrieval("c1", "alpha beta gamma DUP", score=0.5, trust=0.5)  # duplicate chunk_id, lower score

    ctx = build_context([r2, r3, r1], token_budget=100)

    # Deduped should keep the highest-scoring c1 and c2 => two blocks
    assert len(ctx["blocks"]) == 2
    # Order should be by score desc: c1 then c2
    assert ctx["blocks"][0]["chunk_id"] == "c1"
    assert ctx["blocks"][1]["chunk_id"] == "c2"
    assert ctx["truncated"] is False


def test_build_context_respects_token_budget_and_truncation():
    long_text = "word " * 50  # 50 tokens
    r1 = _make_retrieval("a", long_text, score=1.0)
    r2 = _make_retrieval("b", long_text, score=0.9)
    r3 = _make_retrieval("c", long_text, score=0.8)

    # token_budget smaller than total tokens for all three (150); set budget=110 to allow only two
    ctx = build_context([r1, r2, r3], token_budget=110)
    assert len(ctx["blocks"]) == 2
    assert ctx["truncated"] is True
    assert ctx["total_tokens"] <= 110


def test_build_context_filters_empty_content():
    r1 = _make_retrieval("x", "", score=1.0)
    r2 = _make_retrieval("y", "some content", score=0.5)
    ctx = build_context([r1, r2], token_budget=100)
    assert len(ctx["blocks"]) == 1
    assert ctx["blocks"][0]["chunk_id"] == "y"
