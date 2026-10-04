"""Source-only native create coordinator; no frontend or production activation."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
from time import time

from ..audit import AuditRecord
from .governance import GovernanceBoundaryError
from .session_requests import ACKNOWLEDGEMENT
from .session_transitions import CandidateCreateSessionAuthority, CandidateCreateSessionBinding

CREATE_CONTRACT = "project-maya.native-session-create.v1"


def projection_bytes(instance, database, generation, routes):
    return (json.dumps({"contract": CREATE_CONTRACT, "instance_id": instance,
                       "database": database, "generation": generation, "routes": routes},
                      sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _safe_path(path):
    path = Path(path).absolute()
    if str(path).startswith("\\\\"):
        raise GovernanceBoundaryError("governance.transition_path_unsafe")
    for item in (path, *path.parents):
        if item.exists() or item.is_symlink():
            info = item.lstat()
            if (stat.S_ISLNK(info.st_mode)
                    or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
                raise GovernanceBoundaryError("governance.transition_path_unsafe")
    return path


class CandidateNativeSessionCreate:
    """Bind one actual native SessionStore and its existing SQLite connection.

    Schema, empty projection and lockfile must be explicitly provisioned by a
    fixture. This coordinator never creates/repairs a database or adopts old rows.
    All native ordinary create/reset/switch operations remain blocked.
    """

    contract = CREATE_CONTRACT

    def __init__(self, store, binding, *, acknowledgement):
        from gateway.session import SessionStore
        from hermes_state import SessionDB
        if (acknowledgement != ACKNOWLEDGEMENT or type(store) is not SessionStore
                or type(getattr(store, "_db", None)) is not SessionDB
                or not isinstance(binding, CandidateCreateSessionBinding)
                or getattr(store, "_maya_create_coordinator", None) is not None
                or not callable(getattr(store, "create_owned_session_candidate", None))):
            raise GovernanceBoundaryError("governance.transition_store_invalid")
        self.store = store
        self.database = store._db
        self.binding = binding
        self.directory = _safe_path(store.sessions_dir)
        self.index = self.directory / "sessions.json"
        self.lockfile = self.directory / "maya-session-projection.lock"
        self._validate_paths()
        store._maya_create_coordinator = self

    def _validate_paths(self):
        if (not _safe_path(self.directory).is_dir()
                or _safe_path(self.database.db_path).resolve(strict=True) != self.binding.database
                or not _safe_path(self.index).is_file()
                or not _safe_path(self.lockfile).is_file()):
            raise GovernanceBoundaryError("governance.transition_store_invalid")

    @contextmanager
    def _exclusive(self):
        try:
            import portalocker
            if portalocker.__version__ != "3.2.0":
                raise GovernanceBoundaryError("governance.transition_lock_unqualified")
            self._validate_paths()
            with portalocker.Lock(self.lockfile, mode="r+b", timeout=0, fail_when_locked=True):
                self._validate_paths()
                yield
        except GovernanceBoundaryError:
            raise
        except ImportError:
            raise GovernanceBoundaryError("governance.transition_lock_unavailable") from None
        except portalocker.exceptions.LockException:
            raise GovernanceBoundaryError("governance.transition_busy") from None

    def _state(self, conn):
        if (conn.in_transaction or conn.execute("PRAGMA foreign_keys").fetchone()[0] != 1):
            raise GovernanceBoundaryError("governance.transition_store_invalid")
        return self._state_in_transaction(conn)

    def _state_in_transaction(self, conn):
        row = conn.execute("SELECT instance_id,database_id,generation,projection_hash,index_path "
                           "FROM maya_session_projection_v1 WHERE singleton=1 AND schema_version=1").fetchone()
        if (row is None or row[0] != self.binding.instance_id or row[1] != str(self.binding.database)
                or row[4] != str(self.index)
                or conn.execute("SELECT count(*) FROM maya_session_projection_v1").fetchone()[0] != 1
                or conn.execute("PRAGMA foreign_key_check").fetchone() is not None):
            raise GovernanceBoundaryError("governance.transition_store_invalid")
        if conn.execute("SELECT 1 FROM sessions s LEFT JOIN maya_session_owners_v1 o "
                        "ON s.id=o.session_id WHERE o.session_id IS NULL LIMIT 1").fetchone():
            raise GovernanceBoundaryError("governance.transition_owner_unknown")
        if conn.execute("SELECT 1 FROM maya_session_owners_v1 WHERE principal<>? OR instance_id<>? "
                        "OR database_id<>? OR binding_version<>? OR classification<>? LIMIT 1",
                        (self.binding.owner.actor_id, self.binding.instance_id, str(self.binding.database),
                         self.binding.binding_version, self.binding.owner.data_classification)).fetchone():
            raise GovernanceBoundaryError("governance.transition_owner_mismatch")
        routes = {r[0]: {"session_id": r[1], "version": r[2]} for r in conn.execute(
            "SELECT r.route_slot,r.session_id,r.route_version FROM maya_session_routes_v1 r "
            "JOIN maya_session_owners_v1 o ON o.session_id=r.session_id AND o.principal=r.principal "
            "WHERE o.lifecycle_status='active' ORDER BY r.route_slot")}
        if len(routes) != conn.execute("SELECT count(*) FROM maya_session_routes_v1").fetchone()[0]:
            raise GovernanceBoundaryError("governance.transition_store_invalid")
        raw = projection_bytes(row[0], row[1], row[2], routes)
        if _digest(raw) != row[3]:
            raise GovernanceBoundaryError("governance.transition_projection_invalid")
        return row[2], routes, raw

    def _publish(self, raw):
        self._validate_paths()
        name = None
        try:
            fd, name = tempfile.mkstemp(prefix=".maya-projection-", dir=self.directory)
            with os.fdopen(fd, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            self._validate_paths()
            os.replace(name, self.index)  # Strict replacement: never copy on EXDEV/EBUSY.
            name = None
            if self.index.read_bytes() != raw:
                raise GovernanceBoundaryError("governance.transition_projection_invalid")
        finally:
            if name is not None:
                Path(name).unlink(missing_ok=True)

    def _commit(self, conn):
        conn.commit()

    def create(self, store, authority):
        from hermes_cli.middleware import mandatory_middleware_enabled, validate_mandatory_middleware
        if (store is not self.store or getattr(store, "_maya_create_coordinator", None) is not self
                or store._db is not self.database or not mandatory_middleware_enabled()
                or validate_mandatory_middleware() is not True
                or not isinstance(authority, CandidateCreateSessionAuthority)
                or authority._host is not self.binding):
            raise GovernanceBoundaryError("governance.transition_context_invalid")
        descriptor = authority.descriptor
        identity = self.binding.owner
        committed = False
        commit_attempted = False
        try:
            authority.begin_attempt(identity, descriptor)
            with self._exclusive(), store._lock, self.database._lock:
                conn = self.database._conn
                authority.authorize(identity, descriptor)
                generation, routes, old_raw = self._state(conn)
                if (self.index.read_bytes() != old_raw
                        or conn.execute("SELECT 1 FROM maya_session_transitions_v1 "
                                        "WHERE state<>'published' LIMIT 1").fetchone()):
                    raise GovernanceBoundaryError("governance.transition_recovery_required")
                conn.execute("BEGIN IMMEDIATE")
                try:
                    current, routes, raw = self._state_in_transaction(conn)
                    if current != generation or raw != old_raw or descriptor.route_slot in routes:
                        raise GovernanceBoundaryError("governance.transition_stale")
                    if conn.execute("SELECT 1 FROM maya_session_transitions_v1 WHERE correlation_id=?",
                                    (descriptor.correlation_id,)).fetchone():
                        raise GovernanceBoundaryError("governance.transition_replay")
                    routes[descriptor.route_slot] = {"session_id": descriptor.target_session, "version": 1}
                    raw = projection_bytes(self.binding.instance_id, str(self.binding.database), generation + 1, routes)
                    conn.execute("INSERT INTO sessions(id,source,user_id,started_at) VALUES (?,?,?,?)",
                                 (descriptor.target_session, "maya-governed-candidate", identity.actor_id, time()))
                    conn.execute("INSERT INTO maya_session_owners_v1 "
                                 "(session_id,instance_id,database_id,principal,classification,binding_version,lifecycle_status) "
                                 "VALUES (?,?,?,?,?,?,'active')", (descriptor.target_session, descriptor.instance_id,
                                 descriptor.database, descriptor.principal, descriptor.classification, descriptor.binding_version))
                    conn.execute("INSERT INTO maya_session_routes_v1 VALUES (?,?,?,?,?)",
                                 (descriptor.route_slot, descriptor.principal, descriptor.target_session, 1, descriptor.correlation_id))
                    conn.execute("INSERT INTO maya_session_transitions_v1 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                                 (descriptor.correlation_id, descriptor.digest, descriptor.principal,
                                  descriptor.binding_version, "create", descriptor.target_session, 0, 1,
                                  "committed_pending_projection", generation + 1, _digest(raw),
                                  "sha256:" + _digest(descriptor.correlation_id.encode())))
                    changed = conn.execute("UPDATE maya_session_projection_v1 SET generation=?,projection_hash=? "
                                           "WHERE singleton=1 AND generation=?", (generation + 1, _digest(raw), generation))
                    if changed.rowcount != 1:
                        raise GovernanceBoundaryError("governance.transition_stale")
                    with authority.commit_guard(identity, descriptor):
                        commit_attempted = True
                        self._commit(conn)
                    committed = True
                except BaseException:
                    conn.rollback()
                    raise
                with authority.publication_guard(identity, descriptor):
                    self._publish(raw)
                conn.execute("BEGIN IMMEDIATE")
                try:
                    current, _, current_raw = self._state_in_transaction(conn)
                    if current != generation + 1 or current_raw != raw or self.index.read_bytes() != raw:
                        raise GovernanceBoundaryError("governance.transition_projection_invalid")
                    authority._check(identity, descriptor)
                    conn.execute("UPDATE maya_session_transitions_v1 SET state='projection_verified' "
                                 "WHERE correlation_id=? AND state='committed_pending_projection'",
                                 (descriptor.correlation_id,))
                    conn.commit()
                except BaseException:
                    conn.rollback()
                    raise
                try:
                    self.binding.audit.write(AuditRecord(
                        event_type="outcome.session_transition", decision="allow",
                        reason_code="governance.transition_published", actor_id=identity.actor_id,
                        capability="session.transition", target="sha256:" + _digest(descriptor.route_slot.encode()),
                        operation="create", data_classification=identity.data_classification,
                        idempotency_key="sha256:" + _digest(descriptor.correlation_id.encode()),
                        metadata={"contract": CREATE_CONTRACT, "qualification": "source_candidate_only"},
                    ))
                except Exception:
                    raise GovernanceBoundaryError("governance.transition_audit_pending") from None
                with authority.publication_guard(identity, descriptor):
                    conn.execute("BEGIN IMMEDIATE")
                    try:
                        current, _, current_raw = self._state_in_transaction(conn)
                        if current != generation + 1 or current_raw != raw or self.index.read_bytes() != raw:
                            raise GovernanceBoundaryError("governance.transition_projection_invalid")
                        changed = conn.execute("UPDATE maya_session_transitions_v1 SET state='published' "
                                               "WHERE correlation_id=? AND state='projection_verified'",
                                               (descriptor.correlation_id,))
                        if changed.rowcount != 1:
                            raise GovernanceBoundaryError("governance.transition_recovery_required")
                        conn.commit()
                    except BaseException:
                        conn.rollback()
                        raise
                # Return an explicitly unqualified receipt, not a conversation
                # scope/SessionEntry. Native reader/cache composition is still open.
                return {"session_id": descriptor.target_session, "correlation_id": descriptor.correlation_id,
                        "state": "published", "qualification": "source_candidate_only", "dispatch_allowed": False}
        except GovernanceBoundaryError:
            raise
        except Exception:
            code = ("governance.transition_recovery_required" if committed or commit_attempted
                    else "governance.transition_store_failed")
            raise GovernanceBoundaryError(code) from None
