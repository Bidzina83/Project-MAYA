"""Source-overlay caller acknowledgement; never a production activation path."""
from contextlib import contextmanager
from dataclasses import dataclass
from threading import Lock, get_ident
from types import MappingProxyType

from ..audit import AuditRecord
from ..governance import ActionRequest, AuthorizationResult
from .governance import GovernanceBoundaryError, _current_task, _session_write
from .session_creation import CandidateNativeSessionCreate, _digest
from .session_requests import ACKNOWLEDGEMENT

CONTRACT = "project-maya.create-caller-acknowledgement.v1"


@dataclass(frozen=True)
class _CleanupBinding:
    descriptor: object
    thread: int
    task: object


class CandidateCallerPreparation:
    """Normal-exit acknowledgement of one host-owned synchronous preparation.

    Cleanup can only reduce authority on its exact pending receipt. The body
    receives no scope, bearer authority, append, model or tool permission.
    Construction requires the separate staged sink/reader overlay.
    """

    contract = CONTRACT

    def __init__(self, coordinator, *, acknowledgement):
        if (acknowledgement != ACKNOWLEDGEMENT or type(coordinator) is not CandidateNativeSessionCreate
                or getattr(coordinator, "caller_contract", None) != CONTRACT
                or getattr(coordinator.store, "_maya_caller_preparation", None) is not None):
            raise GovernanceBoundaryError("governance.caller_overlay_required")
        self.coordinator = coordinator
        self.store = coordinator.store
        self.binding = coordinator.binding
        self._limits = self._host_limits()
        self._lock = Lock()
        self._current = None
        self._phase = "idle"
        self.store._maya_caller_preparation = self

    def _host_limits(self):
        b = self.binding
        return b.owner, b.instance_id, b.database, b.route_slot, b.binding_version, b.timeout

    def _require(self, store, identity):
        from hermes_cli.middleware import mandatory_middleware_enabled, validate_mandatory_middleware
        if (store is not self.store or store._db is not self.coordinator.database
                or getattr(store, "_maya_create_coordinator", None) is not self.coordinator
                or getattr(store, "_maya_caller_preparation", None) is not self
                or identity != self.binding.owner or self._limits != self._host_limits()
                or not mandatory_middleware_enabled() or validate_mandatory_middleware() is not True):
            raise GovernanceBoundaryError("governance.caller_binding_invalid")

    def _bound(self, conn, descriptor, expected):
        self._require(self.store, self.binding.owner)
        if (descriptor.instance_id != self.binding.instance_id or descriptor.database != str(self.binding.database)
                or descriptor.principal != self.binding.owner.actor_id
                or descriptor.classification != self.binding.owner.data_classification
                or descriptor.binding_version != self.binding.binding_version
                or descriptor.route_slot != self.binding.route_slot):
            raise GovernanceBoundaryError("governance.caller_binding_invalid")
        state = self.coordinator._state_in_transaction(conn) if conn.in_transaction else self.coordinator._state(conn)
        generation, routes, raw = state
        route = routes.get(descriptor.route_slot)
        row = conn.execute(
            "SELECT descriptor_digest,principal,binding_version,operation,target_session,"
            "expected_route_version,result_route_version,state,generation,projection_hash "
            "FROM maya_session_transitions_v1 WHERE correlation_id=?", (descriptor.correlation_id,)).fetchone()
        correlated = conn.execute("SELECT correlation_id FROM maya_session_routes_v1 WHERE route_slot=?",
                                  (descriptor.route_slot,)).fetchone()
        if (row is None or tuple(row) != (descriptor.digest, descriptor.principal, descriptor.binding_version,
                "create", descriptor.target_session, 0, 1, expected, generation, _digest(raw))
                or route != {"session_id": descriptor.target_session, "version": 1}
                or correlated is None or correlated[0] != descriptor.correlation_id
                or self.coordinator.index.read_bytes() != raw
                or conn.execute("SELECT 1 FROM maya_session_transitions_v1 WHERE correlation_id<>? "
                                "AND state<>'caller_acknowledged' LIMIT 1", (descriptor.correlation_id,)).fetchone()):
            raise GovernanceBoundaryError("governance.caller_receipt_invalid")

    def _audit(self, descriptor, operation, decision):
        try:
            self.binding.audit.write(AuditRecord(
                event_type="authorization.create_caller", decision=decision,
                reason_code="governance.caller_" + operation + "_" + decision,
                actor_id=descriptor.principal, capability="session.transition", operation=operation,
                target="sha256:" + _digest(descriptor.route_slot.encode()),
                data_classification=descriptor.classification,
                idempotency_key="sha256:" + _digest(descriptor.correlation_id.encode()),
                metadata={"contract": CONTRACT, "qualification": "source_candidate_only"}))
        except Exception:
            raise GovernanceBoundaryError("governance.caller_audit_unavailable") from None

    def _commit(self, conn):
        conn.commit()

    def _acknowledge(self, authority):
        if self._phase != "acknowledging" or self._current is None or authority is not self._current[0]:
            raise GovernanceBoundaryError("governance.caller_scope_invalid")
        descriptor = authority.descriptor
        with self.coordinator._exclusive(), self.store._lock, self.coordinator.database._lock:
            conn = self.coordinator.database._conn
            with authority.publication_guard(self.binding.owner, descriptor):
                self._bound(conn, descriptor, "published_pending_caller")
                action = ActionRequest(actor_id=descriptor.principal, capability="session.transition",
                    operation="acknowledge_create", target=descriptor.route_slot,
                    data_classification=descriptor.classification, idempotency_key=descriptor.correlation_id,
                    metadata={"contract": CONTRACT, "descriptor_digest": descriptor.digest})
                try:
                    result = self.binding.gateway.authorize(action)
                except Exception:
                    raise GovernanceBoundaryError("governance.caller_policy_unavailable") from None
                allowed = isinstance(result, AuthorizationResult) and result.allowed and not result.constraints and not result.redactions
                authority._check(self.binding.owner, descriptor)
                self._audit(descriptor, "acknowledge_create", "allow" if allowed else "deny")
                if not allowed:
                    raise GovernanceBoundaryError("governance.caller_ack_denied")
                conn.execute("BEGIN IMMEDIATE")
                try:
                    self._bound(conn, descriptor, "published_pending_caller")
                    authority._check(self.binding.owner, descriptor)
                    changed = conn.execute("UPDATE maya_session_transitions_v1 SET state='caller_acknowledged' "
                        "WHERE correlation_id=? AND descriptor_digest=? AND state='published_pending_caller'",
                        (descriptor.correlation_id, descriptor.digest))
                    if changed.rowcount != 1:
                        raise GovernanceBoundaryError("governance.caller_receipt_invalid")
                    self._commit(conn)
                except BaseException:
                    conn.rollback()
                    raise

    def _quarantine(self, cleanup):
        # This is not expired create authority: it can only reduce this exact
        # host-bound pending receipt, and may never acknowledge or repair it.
        if (self._phase != "failed" or self._current is None or cleanup is not self._current[1]
                or cleanup.thread != get_ident() or cleanup.task is not _current_task()):
            raise GovernanceBoundaryError("governance.caller_cleanup_invalid")
        descriptor = cleanup.descriptor
        try:
            self._audit(descriptor, "quarantine_create", "deny")
        except GovernanceBoundaryError:
            pass  # Pending remains blocked even when the failure audit is unavailable.
        with self.coordinator._exclusive(), self.store._lock, self.coordinator.database._lock:
            conn = self.coordinator.database._conn
            self._bound(conn, descriptor, "published_pending_caller")
            conn.execute("BEGIN IMMEDIATE")
            try:
                self._bound(conn, descriptor, "published_pending_caller")
                changed = conn.execute("UPDATE maya_session_transitions_v1 SET state='caller_quarantined' "
                    "WHERE correlation_id=? AND descriptor_digest=? AND state='published_pending_caller'",
                    (descriptor.correlation_id, descriptor.digest))
                if changed.rowcount != 1:
                    raise GovernanceBoundaryError("governance.caller_cleanup_invalid")
                conn.commit()
            except BaseException:
                conn.rollback()
                raise

    @contextmanager
    def prepare(self, store, identity):
        self._require(store, identity)
        if _session_write.get() is not None or not self._lock.acquire(blocking=False):
            raise GovernanceBoundaryError("governance.caller_scope_busy")
        try:
            with self.binding.authenticated_create(identity) as authority:
                receipt = store.create_owned_session_candidate(authority)
                if receipt["state"] != "published_pending_caller" or receipt["dispatch_allowed"] is not False:
                    raise GovernanceBoundaryError("governance.caller_receipt_invalid")
                cleanup = _CleanupBinding(authority.descriptor, get_ident(), _current_task())
                self._current = (authority, cleanup)
                self._phase = "preparing"
                try:
                    yield MappingProxyType(dict(receipt))
                    self._phase = "acknowledging"
                    self._acknowledge(authority)
                except BaseException:
                    self._phase = "failed"
                    try:
                        self._quarantine(cleanup)
                    except BaseException:
                        # Preserve the original exception/cancellation. Durable
                        # pending state, not successful cleanup, is the gate.
                        pass
                    raise
        finally:
            self._current = None
            self._phase = "idle"
            self._lock.release()
