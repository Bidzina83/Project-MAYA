"""Stable adapter over Project MAYA's canonical retrieval contract."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Retriever(Protocol):
    def upsert(self, doc: dict[str, Any]) -> None: ...

    def bulk_upsert(self, docs: list[dict[str, Any]]) -> None: ...

    def get(self, id: str) -> dict[str, Any] | None: ...

    def query_vector(
        self,
        vector: list[float],
        top_k: int = 10,
        metric: str = "cosine",
    ) -> list[dict[str, Any]]: ...

    def search(
        self,
        query: str,
        category: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]: ...

    def probe(
        self, entity: str, category: str | None = None, limit: int = 10
    ) -> list[dict[str, Any]]: ...

    def related(
        self, entity: str, category: str | None = None, limit: int = 10
    ) -> list[dict[str, Any]]: ...

    def reason(
        self,
        entities: list[str],
        category: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]: ...

    def contradict(
        self,
        category: str | None = None,
        threshold: float = 0.3,
        limit: int = 10,
    ) -> list[dict[str, Any]]: ...

    def stats(self) -> dict[str, Any]: ...


class MemoryRetriever:
    """Small public vocabulary backed by the existing Retriever contract."""

    def __init__(self, retriever: Retriever) -> None:
        if not isinstance(retriever, Retriever):
            raise TypeError("retriever does not implement the Retriever contract")
        self._retriever = retriever

    def remember(self, document: dict[str, Any]) -> None:
        identifiers = ("id", "chunk_id", "embedding_id")
        if not any(document.get(key) for key in identifiers):
            raise ValueError("document requires id, chunk_id, or embedding_id")
        self._retriever.upsert(document)

    def recall(self, memory_id: str) -> dict[str, Any] | None:
        return self._retriever.get(memory_id)

    def search(
        self,
        query: str,
        *,
        category: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        if limit < 1:
            raise ValueError("limit must be positive")
        return self._retriever.search(query, category=category, limit=limit)
