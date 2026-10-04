"""Create-only source-candidate authority; no native persistence activation."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import re
from threading import Lock, RLock, get_ident
from time import monotonic
from uuid import uuid4

from ..audit import AuditRecord, AuditSink, NullAuditSink
from ..governance import ActionAuthorizationGateway, ActionRequest, AuthorizationResult
from .governance import GovernanceBoundaryError, RequestIdentity, _current_task
from .session_requests import ACKNOWLEDGEMENT

TRANSITION_CONTRACT = "project-maya.session-transition.v1"
_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:@-]{1,128}")
_CLASSIFICATIONS = frozenset({"public", "internal", "confidential", "restricted"})


def _identifier(value):
    return isinstance(value, str) and _IDENTIFIER.fullmatch(value) is not None


def _hash(value):
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CreateSessionDescriptor:
    """Host-prepared selector, not a bearer grant or a session-write scope."""

    contract: str
    instance_id: str
    database: str
    principal: str
    classification: str
    binding_version: int
    route_slot: str
    expected_route_version: int
    target_session: str
    request_id: str
    correlation_id: str
    operation: str = "create"

    @property
    def digest(self):
        raw = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return _hash(raw)


class CandidateCreateSessionAuthority:
    """One host-owned create descriptor with bounded, synchronous revocation.

    Native commit integration must enter commit_guard after acquiring its SQLite
    transaction and checking durable versions. This class never opens a database,
    grants append/model/tool permissions or marks a transition published.
    """

    def __init__(self, host, descriptor, timeout):
        self._descriptor = descriptor
        self._host = host
        self._deadline = monotonic() + timeout
        self._thread = get_ident()
        self._task = _current_task()
        self._lock = RLock()
        self._active = True
        self._consumed = False
        self._attempted = False

    @property
    def descriptor(self):
        return self._descriptor

    def revoke(self):
        # May be called from another thread. It serializes with commit_guard;
        # already committed effects must not be falsely reported as rolled back.
        with self._lock:
            self._active = False

    def _check(self, identity, descriptor):
        if (not self._active or monotonic() >= self._deadline
                or get_ident() != self._thread or _current_task() is not self._task
                or (self._task is not None and self._task.cancelling())
                or identity != self._host.owner or descriptor is not self.descriptor
                or descriptor.contract != TRANSITION_CONTRACT or descriptor.operation != "create"
                or type(descriptor.expected_route_version) is not int or descriptor.expected_route_version != 0
                or not all(_identifier(value) for value in
                           (descriptor.target_session, descriptor.request_id, descriptor.correlation_id))
                or descriptor.principal != identity.actor_id
                or descriptor.classification != identity.data_classification
                or descriptor.instance_id != self._host.instance_id
                or descriptor.database != str(self._host.database)
                or descriptor.route_slot != self._host.route_slot
                or descriptor.binding_version != self._host.binding_version):
            raise GovernanceBoundaryError("governance.transition_context_invalid")

    def authorize(self, identity, descriptor):
        """Policy preflight only. Durable owner/route checks are not replaced."""
        with self._lock:
            self._check(identity, descriptor)
            if self._consumed:
                raise GovernanceBoundaryError("governance.transition_consumed")
            for capability, operation, target in (
                ("session.read", "route_state", descriptor.route_slot),
                ("session.transition", "create", descriptor.route_slot),
                ("session.write", "create", descriptor.target_session),
            ):
                action = ActionRequest(
                    actor_id=identity.actor_id, capability=capability,
                    operation=operation, target=target,
                    data_classification=identity.data_classification,
                    idempotency_key=descriptor.correlation_id,
                    metadata={"contract": TRANSITION_CONTRACT,
                              "descriptor_digest": descriptor.digest},
                )
                try:
                    result = self._host.gateway.authorize(action)
                    allowed = (isinstance(result, AuthorizationResult) and result.allowed
                               and not result.constraints and not result.redactions)
                except Exception:
                    raise GovernanceBoundaryError("governance.authorization_unavailable") from None
                self._check(identity, descriptor)
                self._host._audit(descriptor, capability, operation, "allow" if allowed else "deny")
                if not allowed:
                    raise GovernanceBoundaryError("governance.transition_denied")
            self._check(identity, descriptor)

    def begin_attempt(self, identity, descriptor):
        """A failed allocation/lock/storage attempt cannot replay this authority."""
        with self._lock:
            self._check(identity, descriptor)
            if self._attempted:
                raise GovernanceBoundaryError("governance.transition_consumed")
            self._attempted = True

    @contextmanager
    def commit_guard(self, identity, descriptor):
        """Consume once, reauthorize, then serialize revocation with sync commit.

        Caller must not await, hand off execution or call revoke reentrantly here.
        Entering this guard alone does not implement or qualify native commit.
        Failed attempts also consume authority; status/recovery uses new authority.
        """
        with self._lock:
            self.authorize(identity, descriptor)
            self._consumed = True
            try:
                yield
            except BaseException:
                self._active = False
                raise

    @contextmanager
    def publication_guard(self, identity, descriptor):
        """Finish only the consumed transition; never authorize another commit."""
        with self._lock:
            self._check(identity, descriptor)
            if not self._consumed:
                raise GovernanceBoundaryError("governance.transition_context_invalid")
            yield


class CandidateCreateSessionBinding:
    """Trusted host configuration, never constructed from a request payload.

    Host authenticates before authenticated_create; the supplied identity must
    equal its explicit owner. No product frontend registers this candidate yet.
    """

    def __init__(self, *, owner: RequestIdentity, instance_id: str, database: Path,
                 route_slot: str, binding_version: int, gateway: ActionAuthorizationGateway,
                 audit_sink: AuditSink, acknowledgement: str, timeout_seconds=120.0):
        if (acknowledgement != ACKNOWLEDGEMENT or not isinstance(owner, RequestIdentity)
                or not _identifier(owner.actor_id) or owner.data_classification not in _CLASSIFICATIONS
                or not _identifier(instance_id) or not _identifier(route_slot)
                or type(binding_version) is not int or binding_version < 1
                or not isinstance(gateway, ActionAuthorizationGateway)
                or not isinstance(audit_sink, AuditSink) or isinstance(audit_sink, NullAuditSink)
                or isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float))
                or not math.isfinite(timeout_seconds) or not 0 < timeout_seconds <= 3600):
            raise GovernanceBoundaryError("governance.transition_binding_invalid")
        try:
            path = Path(database)
            resolved = path.resolve(strict=True)
            if not resolved.is_file() or path.is_symlink():
                raise ValueError
        except (OSError, ValueError, TypeError):
            raise GovernanceBoundaryError("governance.transition_binding_invalid") from None
        self.owner = owner
        self.instance_id = instance_id
        self.database = resolved
        self.route_slot = route_slot
        self.binding_version = binding_version
        self.gateway = gateway
        self.audit = audit_sink
        self.timeout = timeout_seconds
        self._lock = Lock()

    def _audit(self, descriptor, capability, operation, decision):
        try:
            self.audit.write(AuditRecord(
                event_type="authorization.session_transition_preflight", decision=decision,
                reason_code="governance.transition_preflight_" + decision,
                actor_id=self.owner.actor_id, capability=capability, operation=operation,
                target=_hash(descriptor.route_slot),
                data_classification=self.owner.data_classification,
                idempotency_key=_hash(descriptor.correlation_id),
                metadata={"contract": TRANSITION_CONTRACT,
                          "descriptor_digest": descriptor.digest,
                          "qualification": "source_preflight_only"},
            ))
        except Exception:
            raise GovernanceBoundaryError("governance.audit_unavailable") from None

    @contextmanager
    def authenticated_create(self, identity: RequestIdentity):
        if identity != self.owner:
            raise GovernanceBoundaryError("governance.session_owner_mismatch")
        if not self._lock.acquire(blocking=False):
            raise GovernanceBoundaryError("governance.transition_busy")
        authority = None
        try:
            descriptor = CreateSessionDescriptor(
                TRANSITION_CONTRACT, self.instance_id, str(self.database),
                self.owner.actor_id, self.owner.data_classification, self.binding_version,
                self.route_slot, 0, uuid4().hex, uuid4().hex, uuid4().hex,
            )
            authority = CandidateCreateSessionAuthority(self, descriptor, self.timeout)
            authority.authorize(identity, descriptor)
            yield authority
        finally:
            if authority is not None:
                authority.revoke()
            self._lock.release()
