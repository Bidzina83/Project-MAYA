"""Hermes-facing memory provider backed by governed Maya memory."""

from __future__ import annotations

from typing import Any

from .retriever import GovernedMemoryRetriever


class HermesMemoryProvider:
    """Runtime memory adapter that preserves Maya's governed retriever boundary."""

    def __init__(self, memory: GovernedMemoryRetriever) -> None:
        self._memory = memory
        self._session_id: str | None = None

    @property
    def session_id(self) -> str | None:
        return self._session_id

    def begin_session(
        self,
        session_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        if not session_id or not session_id.strip():
            raise ValueError("session_id is required")
        self._session_id = session_id
        return {"session_id": session_id, "status": "started"}

    def end_session(self, session_id: str | None = None) -> dict[str, str]:
        ended = session_id or self._session_id
        self._session_id = None
        return {"session_id": ended or "", "status": "ended"}

    def prefetch(
        self,
        query: str,
        *,
        category: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        return self._memory.search(query, category=category, limit=limit)

    def recall(self, memory_id: str) -> dict[str, Any] | None:
        return self._memory.recall(memory_id)

    def remember(self, document: dict[str, Any]) -> None:
        self._memory.remember(document)

    def synchronize_turn(
        self,
        records: list[dict[str, Any]] | None = None,
    ) -> dict[str, int]:
        stored = 0
        for record in records or []:
            self._memory.remember(record)
            stored += 1
        return {"stored": stored}
