"""Local audit records for Project MAYA runtime decisions."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Mapping, Protocol, runtime_checkable


@dataclass(frozen=True)
class AuditRecord:
    event_type: str
    decision: str
    reason_code: str
    actor_id: str
    capability: str
    target: str
    operation: str
    data_classification: str
    idempotency_key: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat(timespec="seconds")
    )
    schema_version: int = 1

    def to_json(self) -> str:
        return json.dumps(
            {
                "schema_version": self.schema_version,
                "timestamp": self.timestamp,
                "event_type": self.event_type,
                "decision": self.decision,
                "reason_code": self.reason_code,
                "actor_id": self.actor_id,
                "capability": self.capability,
                "target": self.target,
                "operation": self.operation,
                "data_classification": self.data_classification,
                "idempotency_key": self.idempotency_key,
                "metadata": dict(self.metadata),
            },
            sort_keys=True,
        )


@runtime_checkable
class AuditSink(Protocol):
    def write(self, record: AuditRecord) -> None:
        """Persist an audit record without exposing secret or prompt contents."""


class NullAuditSink:
    def write(self, record: AuditRecord) -> None:
        return


class LocalJsonlAuditSink:
    """Append-only JSON Lines audit sink for local runtime decisions."""

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def write(self, record: AuditRecord) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(record.to_json())
            handle.write("\n")
