"""Canonical retrieval interface for Project-MAYA persistent memory.

This module defines the provider-agnostic Retriever interface and related
exceptions / types that all retrieval providers (local, holographic, remote
vector DBs) should implement or adapt to.

Guiding principles:
- Keep the API small and synchronous (test-friendly).
- Results are provider-agnostic dicts that conform to the agreed "result schema".
- Providers should NOT raise for normal empty results; raise RetrieverError for
  operational failures only.

"""
from __future__ import annotations

from typing import Protocol, List, Dict, Any, Optional, TypedDict
from dataclasses import dataclass


class RetrieverError(Exception):
    """Operational error from a retriever (network/db/unavailability).

    Providers should raise this on transient or permanent operational failures.
    """


class RetrievalResult(TypedDict, total=False):
    """Normalized retrieval result schema (partial  providers may omit None fields).

    Notes:
      - similarity and score are normalized floats where higher==better and
        score is the final relevance after governance adjustments.
      - provider is required so callers know which provider produced the result.
    """
    id: str
    embedding_id: str
    chunk_id: str
    content: str
    embedding: List[float]
    vector_dim: int
    similarity: float
    score: float
    trust_score: float
    model: str
    provider: str
    source_path: str
    embedding_path: str
    created_at: str
    updated_at: str
    category: str
    tags: List[str]
    meta: Dict[str, Any]


class Retriever(Protocol):
    """Provider-agnostic retrieval interface.

    Implementations must be synchronous and side-effect free for read ops.
    Write ops (upsert/bulk_upsert) may persist data; callers can choose
    to use dual-write semantics via a higher-level service.
    """

    def upsert(self, doc: Dict[str, Any]) -> None:
        """Upsert a single document into the provider.

        doc should include at minimum a stable id and any metadata the provider
        expects (embedding optional). Providers SHOULD persist enough metadata
        for subsequent retrieval and provenance (provider, model, created_at).
        """

    def bulk_upsert(self, docs: List[Dict[str, Any]]) -> None:
        """Bulk upsert many documents. Implementations should use efficient
        batch semantics when available and guarantee atomicity when possible.
        """

    def get(self, id: str) -> Optional[RetrievalResult]:
        """Return a single normalized result for the given id, or None if missing."""

    def query_vector(self, vector: List[float], top_k: int = 10, metric: str = "cosine") -> List[RetrievalResult]:
        """Query by numeric vector and return top_k results.

        Results must have 'similarity' and optionally 'score'. Similarity should
        be normalized to a [0,1] range where higher is better when possible.
        """

    def search(self, query: str, category: Optional[str] = None, limit: int = 10) -> List[RetrievalResult]:
        """Keyword search / text search returning ranked results."""

    def probe(self, entity: str, category: Optional[str] = None, limit: int = 10) -> List[RetrievalResult]:
        """Provider-level compositional query (optional). Fall back to search when
        unavailable. Example: holographic probe using structural vectors."""

    def related(self, entity: str, category: Optional[str] = None, limit: int = 10) -> List[RetrievalResult]:
        """Discover related facts for an entity. Optional; providers may fall back
        to search if not supported."""

    def reason(self, entities: List[str], category: Optional[str] = None, limit: int = 10) -> List[RetrievalResult]:
        """Multi-entity compositional query. Optional; providers may fall back.
        """

    def contradict(self, category: Optional[str] = None, threshold: float = 0.3, limit: int = 10) -> List[Dict[str, Any]]:
        """Find contradictory fact-pairs. Returns provider-specific dicts with at
        least 'fact_a', 'fact_b', and 'contradiction_score'. Optional.
        """

    def stats(self) -> Dict[str, Any]:
        """Return provider health / capability metrics (counts, last_updated).

        This is read-only and used for routing and monitoring.
        """


# Small helper dataclass for provider registration metadata
@dataclass
class ProviderInfo:
    name: str
    read: bool = True
    write: bool = True
    capabilities: List[str] = None


__all__ = [
    "Retriever",
    "RetrieverError",
    "RetrievalResult",
    "ProviderInfo",
]
