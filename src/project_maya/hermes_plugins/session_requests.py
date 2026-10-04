"""Source-candidate Local API binding, not production runtime activation."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
import hashlib
from importlib import import_module
from pathlib import Path
from threading import Lock
from typing import Iterator
from uuid import uuid4

from ..audit import AuditRecord, AuditSink, NullAuditSink

from .governance import (
    GovernanceBoundaryError, RequestIdentity, SESSION_WRITE_CONTRACT,
    bind_request_identity, bind_session_write,
)

ACKNOWLEDGEMENT = "session-write-source-candidate-only"
REQUEST_BINDING_CONTRACT = "project-maya.authenticated-session-request.v1"


@dataclass(frozen=True)
class CandidateSessionRequestBinding:
    """Host-selected single-owner session; request bodies cannot select authority.

    Authentication happens at the Local API before this scope is entered. This
    binds authority, not a policy grant: each native write still uses the gateway.
    Setup, maintenance, session rotation and multi-user routing are not enabled.
    """

    owner: RequestIdentity
    session_id: str
    database: Path
    operations: frozenset[str]
    acknowledgement: str = field(repr=False)
    audit_sink: AuditSink = field(repr=False, kw_only=True)
    timeout_seconds: float = field(default=120.0, kw_only=True)
    _lock: object = field(default_factory=Lock, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if (self.acknowledgement != ACKNOWLEDGEMENT or not isinstance(self.owner, RequestIdentity)
                or not isinstance(self.audit_sink, AuditSink) or isinstance(self.audit_sink, NullAuditSink)
                or self.timeout_seconds is None):
            raise GovernanceBoundaryError("governance.session_context_invalid")
        try:
            database = Path(self.database).resolve(strict=True)
            if not database.is_file():
                raise ValueError
            with bind_request_identity(self.owner.actor_id, self.owner.data_classification):
                with bind_session_write("binding-validation", self.session_id, database, self.operations,
                                        timeout_seconds=self.timeout_seconds):
                    pass
        except Exception:
            raise GovernanceBoundaryError("governance.session_context_invalid") from None
        object.__setattr__(self, "database", database)

    @contextmanager
    def authenticated_request(self, identity: RequestIdentity) -> Iterator[None]:
        if identity != self.owner:
            raise GovernanceBoundaryError("governance.session_owner_mismatch")
        try:
            middleware = import_module("hermes_cli.middleware")
            if (getattr(middleware, "SESSION_WRITE_CONTRACT", None) != SESSION_WRITE_CONTRACT
                    or middleware.mandatory_middleware_enabled() is not True
                    or middleware.validate_mandatory_middleware() is not True):
                raise ValueError
        except Exception:
            raise GovernanceBoundaryError("governance.session_contract_unavailable") from None
        if not self._lock.acquire(blocking=False):
            raise GovernanceBoundaryError("governance.session_request_busy")
        try:
            request_id = uuid4().hex
            try:
                self.audit_sink.write(AuditRecord(
                    event_type="authentication.local_api_session", decision="allow",
                    reason_code="authentication.identity_bound", actor_id=identity.actor_id,
                    capability="local_api.request", target="sha256:" + hashlib.sha256(self.session_id.encode()).hexdigest(),
                    operation="bind", data_classification=identity.data_classification,
                    idempotency_key="sha256:" + hashlib.sha256(request_id.encode()).hexdigest(),
                ))
            except Exception:
                raise GovernanceBoundaryError("governance.audit_unavailable") from None
            with bind_request_identity(identity.actor_id, identity.data_classification):
                with bind_session_write(request_id, self.session_id, self.database, self.operations,
                                        timeout_seconds=self.timeout_seconds):
                    yield
        finally:
            self._lock.release()
