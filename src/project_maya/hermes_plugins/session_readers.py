"""Source-candidate published-route reader and fixed G1 conversation scope."""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime
from threading import Lock, get_ident

from ..audit import AuditRecord
from ..governance import ActionRequest, AuthorizationResult
from .governance import GovernanceBoundaryError, _current_task, _identity, _session_write
from .session_creation import CandidateNativeSessionCreate, _digest
from .session_requests import ACKNOWLEDGEMENT, CandidateSessionRequestBinding

READER_CONTRACT = "project-maya.published-session-reader.v1"


class CandidatePublishedSessionReader:
    """One host-selected route, never a selector supplied by a request.

    Fresh authentication belongs to the trusted host. The projection lock is
    retained during a selected conversation scope, but native SQLite/store locks
    are released before user execution or an await. G1 remains the lease owner.
    """

    contract = READER_CONTRACT

    def __init__(self, coordinator, *, acknowledgement):
        if (acknowledgement != ACKNOWLEDGEMENT or type(coordinator) is not CandidateNativeSessionCreate
                or getattr(coordinator.store, "_maya_published_reader", None) is not None
                or not callable(getattr(coordinator.store, "read_owned_session_candidate", None))):
            raise GovernanceBoundaryError("governance.session_reader_invalid")
        self.coordinator = coordinator
        self.store = coordinator.store
        self.binding = coordinator.binding
        self._selection_lock = Lock()
        self._active = None
        self._host_limits = (self.binding.owner, self.binding.instance_id, self.binding.database,
                             self.binding.route_slot, self.binding.binding_version, self.binding.timeout)
        self.store._maya_published_reader = self

    def _require(self, store, identity):
        from hermes_cli.middleware import mandatory_middleware_enabled, validate_mandatory_middleware
        if (store is not self.store or getattr(store, "_maya_published_reader", None) is not self
                or getattr(store, "_maya_create_coordinator", None) is not self.coordinator
                or store._db is not self.coordinator.database or not mandatory_middleware_enabled()
                or validate_mandatory_middleware() is not True
                or identity != self.binding.owner
                or self._host_limits != (self.binding.owner, self.binding.instance_id, self.binding.database,
                                        self.binding.route_slot, self.binding.binding_version, self.binding.timeout)):
            raise GovernanceBoundaryError("governance.session_reader_invalid")

    def _authorize(self, identity, operation, target):
        action = ActionRequest(actor_id=identity.actor_id, capability="session.read", operation=operation,
                               target=target, data_classification=identity.data_classification,
                               metadata={"contract": READER_CONTRACT})
        try:
            result = self.binding.gateway.authorize(action)
            allowed = (isinstance(result, AuthorizationResult) and result.allowed
                       and not result.constraints and not result.redactions)
        except Exception:
            raise GovernanceBoundaryError("governance.authorization_unavailable") from None
        try:
            self.binding.audit.write(AuditRecord(
                event_type="authorization.published_session_read", decision="allow" if allowed else "deny",
                reason_code="governance.session_read_allowed" if allowed else "governance.session_read_denied",
                actor_id=identity.actor_id, capability="session.read", target="sha256:" + _digest(target.encode()),
                operation=operation, data_classification=identity.data_classification,
                metadata={"contract": READER_CONTRACT, "qualification": "source_candidate_only"},
            ))
        except Exception:
            raise GovernanceBoundaryError("governance.audit_unavailable") from None
        if not allowed:
            raise GovernanceBoundaryError("governance.session_read_denied")

    def _validated_entry(self, identity):
        """Called under projection, native store and native SQLite locks."""
        from gateway.session import SessionEntry
        self._require(self.store, identity)
        self._authorize(identity, "route_state", self.binding.route_slot)
        conn = self.coordinator.database._conn
        _, routes, raw = self.coordinator._state(conn)
        if (self.coordinator.index.read_bytes() != raw
                or conn.execute("SELECT 1 FROM maya_session_transitions_v1 WHERE state<>'published' LIMIT 1").fetchone()):
            raise GovernanceBoundaryError("governance.transition_recovery_required")
        route = routes.get(self.binding.route_slot)
        if route is None:
            raise GovernanceBoundaryError("governance.session_route_unavailable")
        row = conn.execute(
            "SELECT s.started_at,r.route_version,t.target_session,t.state,t.principal,t.binding_version "
            "FROM maya_session_routes_v1 r JOIN sessions s ON s.id=r.session_id "
            "JOIN maya_session_transitions_v1 t ON t.correlation_id=r.correlation_id "
            "WHERE r.route_slot=? AND s.ended_at IS NULL AND s.archived=0 "
            "AND s.source='maya-governed-candidate' AND s.parent_session_id IS NULL",
            (self.binding.route_slot,),
        ).fetchone()
        if (row is None or row[1] != route["version"] or row[2] != route["session_id"]
                or row[3] != "published" or row[4] != identity.actor_id or row[5] != self.binding.binding_version):
            raise GovernanceBoundaryError("governance.session_route_unavailable")
        stamp = datetime.fromtimestamp(row[0])
        return SessionEntry(session_key=self.binding.route_slot, session_id=route["session_id"],
                            created_at=stamp, updated_at=stamp)

    def _clear_cache(self):
        with self.store._lock:
            self.store._entries = {}
            self.store._loaded = False

    def read(self, store, identity):
        try:
            self._require(store, identity)
            with self.coordinator._exclusive(), store._lock, self.coordinator.database._lock:
                entry = self._validated_entry(identity)
                # Neither existing cache entries nor returned mutable entries
                # carry ownership, approval state, prompt history or authority.
                store._entries = {entry.session_key: deepcopy(entry)}
                store._loaded = False  # Never permit the ordinary-loader fast path.
                return deepcopy(entry)
        except GovernanceBoundaryError:
            self._clear_cache()
            raise
        except Exception:
            self._clear_cache()
            raise GovernanceBoundaryError("governance.session_read_failed") from None

    @contextmanager
    def authenticated_request(self, identity):
        self._require(self.store, identity)
        if _session_write.get() is not None or not self._selection_lock.acquire(blocking=False):
            raise GovernanceBoundaryError("governance.session_request_busy")
        entered = False
        try:
            with self.coordinator._exclusive():
                with self.store._lock, self.coordinator.database._lock:
                    entry = self._validated_entry(identity)
                    self._authorize(identity, "history", entry.session_id)
                    scope = CandidateSessionRequestBinding(
                        identity, entry.session_id, self.binding.database, frozenset({"append"}), ACKNOWLEDGEMENT,
                        audit_sink=self.binding.audit, timeout_seconds=self.binding.timeout,
                    )
                # No native store/SQLite locks or transactions cross execution.
                with scope.authenticated_request(identity):
                    root = _session_write.get()
                    self._active = root
                    try:
                        with self.store._lock:
                            self.store._entries = {entry.session_key: deepcopy(entry)}
                            self.store._loaded = False
                        entered = True
                        yield deepcopy(entry)
                    finally:
                        self._active = None
                        self._clear_cache()
        except GovernanceBoundaryError:
            self._clear_cache()
            raise
        except Exception:
            self._clear_cache()
            if entered:
                raise
            raise GovernanceBoundaryError("governance.session_scope_failed") from None
        finally:
            self._selection_lock.release()

    def load_transcript(self, store, session_id):
        bound = _session_write.get()
        selected = self._active
        if bound is None or selected is None:
            raise GovernanceBoundaryError("governance.session_context_invalid")
        root = bound.lease
        while root.parent is not None:
            root = root.parent
        if (root is not selected.lease or not bound.lease.is_active
                or bound.identity != selected.identity or bound.identity != _identity.get()
                or bound.request_id != selected.request_id or bound.database != selected.database
                or bound.session_id != selected.session_id or session_id != selected.session_id
                or bound.thread_id != get_ident() or bound.task is not _current_task()):
            raise GovernanceBoundaryError("governance.session_context_invalid")
        self._require(store, bound.identity)
        with store._lock, self.coordinator.database._lock:
            entry = self._validated_entry(bound.identity)
            if entry.session_id != session_id:
                raise GovernanceBoundaryError("governance.session_context_invalid")
            self._authorize(bound.identity, "history", session_id)
            if not bound.lease.is_active:
                raise GovernanceBoundaryError("governance.session_context_invalid")
        messages = self.coordinator.database.get_messages_as_conversation(session_id)
        with store._lock, self.coordinator.database._lock:
            if self._validated_entry(bound.identity).session_id != session_id or not bound.lease.is_active:
                raise GovernanceBoundaryError("governance.session_context_invalid")
        return messages
