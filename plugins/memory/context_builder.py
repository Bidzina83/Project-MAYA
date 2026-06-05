"""Minimal ContextBuilder skeleton for Project-MAYA.

Produces an OperationalContext from a list of RetrievalResult dicts.
This is intentionally small and deterministic for unit testing and CI.
"""
from __future__ import annotations

from typing import List, Dict, Any, TypedDict, Optional


class OperationalContext(TypedDict):
    blocks: List[Dict[str, Any]]
    total_tokens: int
    token_budget: int
    truncated: bool
    governance_summary: Optional[Dict[str, int]]


def _estimate_tokens(text: str) -> int:
    """Very small-token estimator: approximate tokens by whitespace-separated words.

    Deterministic and cheap; replace with a tokenizer hook in future.
    """
    if not text:
        return 0
    return max(1, len(text.split()))


def build_context(retrievals: List[Dict[str, Any]], token_budget: int = 2048, governance: Optional[Dict[str, Any]] = None) -> OperationalContext:
    """Build an OperationalContext from normalized RetrievalResult dicts.

    Behavior (minimal, deterministic):
      - Filters out retrievals without content.
      - Sorts by 'score' desc then 'trust_score' desc then 'similarity' desc.
      - Deduplicates by 'chunk_id' keeping the highest-ranked entry.
      - Accumulates blocks until token_budget is exhausted (by _estimate_tokens), sets 'truncated' if not all deduped items fit.
      - Each block includes provenance and a conservative token estimate.
      - If governance is provided (GovernanceReportV2 as dict), attaches governance_summary and per-block gov_annotations.

    This is intentionally simple to provide a stable surface for higher-level logic
    and tests. Future iterations will add summarization hooks, smarter token
    budgeting, and chunk stitching.
    """
    # Normalize and filter
    candidates = [r for r in retrievals if r.get("content")]

    # Sorting keys: score (desc), trust_score (desc), similarity (desc)
    def _sort_key(r: Dict[str, Any]):
        return (
            -(r.get("score") or 0.0),
            -(r.get("trust_score") or 0.0),
            -(r.get("similarity") or 0.0),
        )

    candidates.sort(key=_sort_key)

    # Deduplicate by chunk_id, keeping first (highest-ranked) occurrence
    seen = set()
    deduped: List[Dict[str, Any]] = []
    for r in candidates:
        cid = r.get("chunk_id") or r.get("id")
        if cid in seen:
            continue
        seen.add(cid)
        deduped.append(r)

    blocks: List[Dict[str, Any]] = []
    total_tokens = 0
    truncated = False

    for r in deduped:
        content = r.get("content", "")
        est = _estimate_tokens(content)
        if total_tokens + est > token_budget:
            truncated = True
            break
        block = {
            "chunk_id": r.get("chunk_id") or r.get("id"),
            "content": content,
            "provider": r.get("provider"),
            "score": r.get("score"),
            "similarity": r.get("similarity"),
            "trust_score": r.get("trust_score"),
            "source_path": r.get("source_path"),
            "created_at": r.get("created_at"),
            "meta": r.get("meta", {}),
            "estimated_tokens": est,
        }
        blocks.append(block)
        total_tokens += est

    ctx: OperationalContext = OperationalContext(blocks=blocks, total_tokens=total_tokens, token_budget=token_budget, truncated=truncated, governance_summary=None)

    # Attach governance summary and per-block gov_annotations if provided
    if governance:
        # governance expected to be a dict like GovernanceReportV2.to_dict()
        gs = governance.get("summary") if isinstance(governance, dict) else None
        ctx["governance_summary"] = gs
        ann = governance.get("annotations") if isinstance(governance, dict) else None
        if ann:
            # index annotations by chunk_id
            idx = {a.get("chunk_id"): a for a in ann}
            for b in ctx["blocks"]:
                cid = b.get("chunk_id")
                a = idx.get(cid)
                if a:
                    # attach governance annotation
                    b["gov_annotations"] = a
                else:
                    b["gov_annotations"] = None

    return ctx
