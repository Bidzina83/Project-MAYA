"""Separate storage faults against frozen Patch 34, including short writes."""
import errno
import importlib.util
from pathlib import Path
import sqlite3
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("storage_contention", ROOT / "tests/hermes_g2_reset_contention_native.py")
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
reset_host = fixtures.reset_host


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    import hermes_state
    sys.path.insert(0, str(ROOT / "scripts"))
    from verify_governance_g2_reset_storage import verify_stage
    verify_stage(Path(hermes_state.__file__).resolve().parent.parent)


def unavailable():
    raise OSError("SYNTHETIC_STORAGE_FAILURE")


def blocked(h, directory, state):
    from hermes_cli import middleware
    fixtures.committed_once(h, state)
    assert h.preparation._confirmed is None and h.preparation._current is None
    assert h.reset._active is None and not h.db._conn.in_transaction
    before = fixtures.persisted(directory)
    for action in (lambda: h.store.read_owned_session_candidate(h.binding.owner),
                   lambda: h.store.prepare_owned_reset_candidate(h.binding.owner).__enter__()):
        with pytest.raises(middleware.MandatoryMiddlewareError):
            action()
    assert fixtures.persisted(directory) == before
    assert not h.agents and not h.requests and not h.store._entries


@pytest.mark.parametrize("fault", ["create", "write", "flush", "fsync", "replace_exdev", "replace_busy", "short_write"])
def test_projection_storage_failure_preserves_complete_original(reset_host, tmp_path, monkeypatch, fault):
    from hermes_cli import middleware
    from project_maya.hermes_plugins import session_creation
    h = reset_host
    original = h.reset.coordinator.index.read_bytes()
    calls = []
    fdopen = session_creation.os.fdopen
    replace = session_creation.os.replace
    mkstemp = session_creation.tempfile.mkstemp
    fsync = session_creation.os.fsync

    class FaultyStream:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            self.stream.__enter__()
            return self

        def __exit__(self, *args):
            return self.stream.__exit__(*args)

        def write(self, raw):
            calls.append("write")
            if fault in {"write", "short_write"}:
                written = self.stream.write(raw[:len(raw) // 2])
                if fault == "write":
                    unavailable()
                return written
            return self.stream.write(raw)

        def flush(self):
            calls.append("flush")
            if fault == "flush":
                unavailable()
            return self.stream.flush()

        def fileno(self):
            return self.stream.fileno()

    def temporary(*args, **kwargs):
        calls.append("create")
        if fault == "create":
            unavailable()
        return mkstemp(*args, **kwargs)

    def synchronize(fd):
        calls.append("fsync")
        if fault == "fsync":
            unavailable()
        return fsync(fd)

    def replacement(source, target):
        calls.append("replace")
        if fault.startswith("replace_"):
            raise OSError(errno.EXDEV if fault == "replace_exdev" else errno.EBUSY, "SYNTHETIC_STORAGE_FAILURE")
        return replace(source, target)

    with monkeypatch.context() as injection:
        injection.setattr(session_creation.tempfile, "mkstemp", temporary)
        injection.setattr(session_creation.os, "fdopen", lambda *a, **k: FaultyStream(fdopen(*a, **k)))
        injection.setattr(session_creation.os, "fsync", synchronize)
        injection.setattr(session_creation.os, "replace", replacement)
        with pytest.raises(middleware.MandatoryMiddlewareError) as error:
            with h.store.prepare_owned_reset_candidate(h.binding.owner):
                pytest.fail("failed projection reached caller")
        assert "SYNTHETIC_STORAGE_FAILURE" not in str(error.value)
    assert not list(h.reset.coordinator.directory.glob(".maya-projection-*"))
    # Failure must be detected before replacing the old complete projection.
    assert h.reset.coordinator.index.read_bytes() == original
    if fault in {"create", "write", "flush", "fsync", "short_write"}:
        assert "replace" not in calls
    else:
        assert calls.count("replace") == 1
    blocked(h, tmp_path, "committed_pending_projection")


@pytest.mark.parametrize("operation", ["route_state", "end", "acknowledge_reset"])
def test_authorization_audit_writer_failure(reset_host, tmp_path, monkeypatch, operation):
    from hermes_cli import middleware
    h = reset_host
    before = fixtures.persisted(tmp_path)
    audit = h.binding.audit.write
    failures = []
    def write(record):
        if record.event_type == "authorization.session_reset" and record.operation == operation:
            failures.append(record.operation)
            unavailable()
        return audit(record)
    with monkeypatch.context() as injection:
        injection.setattr(h.binding.audit, "write", write)
        with pytest.raises(middleware.MandatoryMiddlewareError) as error:
            with h.store.prepare_owned_reset_candidate(h.binding.owner):
                pass
        assert "SYNTHETIC_STORAGE_FAILURE" not in str(error.value)
    assert failures
    if operation == "acknowledge_reset":
        blocked(h, tmp_path, "caller_quarantined")
    else:
        assert fixtures.persisted(tmp_path) == before
        assert h.store.read_owned_session_candidate(h.binding.owner).session_id == h.source
        assert not h.agents and not h.requests


@pytest.mark.parametrize("phase", ["acknowledging", "failed"])
def test_sqlite_receipt_update_failure(reset_host, tmp_path, monkeypatch, phase):
    from hermes_cli import middleware
    h = reset_host
    denied = []
    def authorize(action, table, column, database, trigger):
        if action == sqlite3.SQLITE_UPDATE and table == "maya_session_transitions_v1" and h.preparation._phase == phase:
            denied.append((table, column))
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    try:
        if phase == "acknowledging":
            audit = h.preparation._audit
            def arm(authority, operation, decision):
                audit(authority, operation, decision)
                if operation == "acknowledge_reset":
                    h.db._conn.set_authorizer(authorize)
            monkeypatch.setattr(h.preparation, "_audit", arm)
            with pytest.raises(middleware.MandatoryMiddlewareError):
                with h.store.prepare_owned_reset_candidate(h.binding.owner):
                    pass
        else:
            with pytest.raises(ValueError, match="synthetic_caller_failure"):
                with h.store.prepare_owned_reset_candidate(h.binding.owner):
                    h.db._conn.set_authorizer(authorize)
                    raise ValueError("synthetic_caller_failure")
    finally:
        h.db._conn.set_authorizer(None)
    assert denied
    blocked(h, tmp_path, "caller_quarantined" if phase == "acknowledging" else "published_pending_caller")
