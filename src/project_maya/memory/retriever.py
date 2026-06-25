"""Stable adapter over Project MAYA's canonical retrieval contract."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from ..audit import AuditRecord, AuditSink, NullAuditSink
from ..governance import (
    ActionAuthorizationGateway,
    ActionDeniedError,
    ActionRequest,
)


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


class GovernedMemoryRetriever:
    """Governed public memory facade for assembled Maya products."""

    def __init__(
        self,
        memory: MemoryRetriever,
        gateway: ActionAuthorizationGateway,
        *,
        actor_id: str,
        audit_sink: AuditSink | None = None,
    ) -> None:
        if not isinstance(gateway, ActionAuthorizationGateway):
            raise TypeError("gateway does not implement ActionAuthorizationGateway")
        if audit_sink is not None and not isinstance(audit_sink, AuditSink):
            raise TypeError("audit_sink does not implement the AuditSink contract")
        self._memory = memory
        self._gateway = gateway
        self._actor_id = actor_id
        self._audit_sink = audit_sink or NullAuditSink()

    def remember(self, document: dict[str, Any]) -> None:
        memory_id = _memory_id(document)
        self._authorize(
            capability="memory.write",
            target=memory_id,
            operation="remember",
            metadata={"memory_id": memory_id},
        )
        self._memory.remember(document)

    def recall(self, memory_id: str) -> dict[str, Any] | None:
        self._authorize(
            capability="memory.read",
            target=memory_id,
            operation="recall",
            metadata={"memory_id": memory_id},
        )
        return self._memory.recall(memory_id)

    def search(
        self,
        query: str,
        *,
        category: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        self._authorize(
            capability="memory.read",
            target=category or "*",
            operation="search",
            metadata={"category": category or "*"},
        )
        return self._memory.search(query, category=category, limit=limit)

    def _authorize(
        self,
        *,
        capability: str,
        target: str,
        operation: str,
        metadata: dict[str, str],
    ) -> None:
        action = ActionRequest(
            actor_id=self._actor_id,
            capability=capability,
            target=target,
            operation=operation,
            data_classification="internal",
            metadata=metadata,
        )
        result = self._gateway.authorize(action)
        if result.audit_required:
            self._audit_sink.write(
                AuditRecord(
                    event_type="authorization.memory",
                    decision=result.decision.value,
                    reason_code=result.reason_code,
                    actor_id=action.actor_id,
                    capability=action.capability,
                    target=action.target,
                    operation=action.operation,
                    data_classification=action.data_classification,
                    idempotency_key=action.idempotency_key,
                    metadata=action.metadata,
                )
            )
        if not result.allowed:
            raise ActionDeniedError(result.reason_code)


def _memory_id(document: dict[str, Any]) -> str:
    for key in ("id", "chunk_id", "embedding_id"):
        value = document.get(key)
        if value:
            return str(value)
    return "*"
