"""Separate publisher, authorization-audit and SQLite faults on frozen Patch 37."""
import errno
import importlib.util
from pathlib import Path
import sqlite3
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("switch_storage_fixture", ROOT / "tests/hermes_g2_switch_uncertainty_native.py")
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
switch_host = fixtures.switch_host
secret_safe_output = fixtures.secret_safe_output


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    import hermes_state
    sys.path.insert(0, str(ROOT / "scripts"))
    from verify_governance_g2_switch_storage_paths import verify_worker_stage
    verify_worker_stage(Path(hermes_state.__file__).resolve().parent.parent)


@pytest.mark.parametrize("fault", ["create", "write", "flush", "fsync", "replace_exdev", "replace_busy",
                                  "short_write", "false_full_write"])
def test_storage_preserves_complete_old_projection(switch_host, tmp_path, monkeypatch, fault):
    from project_maya.hermes_plugins import session_creation
    h = switch_host
    coordinator = h.original[3]
    old = coordinator.index.read_bytes()
    calls = []
    fdopen, replace = session_creation.os.fdopen, session_creation.os.replace
    mkstemp, fsync = session_creation.tempfile.mkstemp, session_creation.os.fsync

    class Writer:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            self.stream.__enter__()
            return self

        def __exit__(self, *args):
            return self.stream.__exit__(*args)

        def write(self, raw):
            calls.append("write")
            if fault in {"write", "short_write", "false_full_write"}:
                written = self.stream.write(raw[:len(raw) // 2])
                if fault == "write":
                    fixtures.failure()
                return len(raw) if fault == "false_full_write" else written
            return self.stream.write(raw)

        def flush(self):
            calls.append("flush")
            if fault == "flush":
                fixtures.failure()
            return self.stream.flush()

        def fileno(self):
            return self.stream.fileno()

    def temporary(*args, **kwargs):
        calls.append("create")
        if fault == "create":
            fixtures.failure()
        return mkstemp(*args, **kwargs)

    def synchronize(fd):
        calls.append("fsync")
        if fault == "fsync":
            fixtures.failure()
        return fsync(fd)

    def replacement(source, target):
        calls.append("replace")
        if fault.startswith("replace_"):
            raise OSError(errno.EXDEV if fault == "replace_exdev" else errno.EBUSY, "SYNTHETIC_PRIVATE_FAILURE")
        return replace(source, target)

    with monkeypatch.context() as injection:
        injection.setattr(session_creation.tempfile, "mkstemp", temporary)
        injection.setattr(session_creation.os, "fdopen", lambda *a, **k: Writer(fdopen(*a, **k)))
        injection.setattr(session_creation.os, "fsync", synchronize)
        injection.setattr(session_creation.os, "replace", replacement)
        fixtures.run_failed(h)
    assert coordinator.index.read_bytes() == old
    assert not list(coordinator.directory.glob(".maya-projection-*"))
    assert calls.count("replace") == (1 if fault.startswith("replace_") else 0)
    fixtures.blocked(h, tmp_path, "committed_pending_projection", old_projection=True)


@pytest.mark.parametrize("operation", ["route_state", "end", "reopen", "switch", "acknowledge_switch"])
def test_authorization_audit_failure(switch_host, tmp_path, monkeypatch, operation):
    h = switch_host
    before = fixtures.persisted(tmp_path)
    audit = h.binding.audit.write
    hits = []

    def unavailable(record):
        if record.event_type == "authorization.session_switch" and record.operation == operation:
            hits.append(operation)
            fixtures.failure()
        return audit(record)

    with monkeypatch.context() as injection:
        injection.setattr(h.binding.audit, "write", unavailable)
        fixtures.run_failed(h)
    assert hits
    if operation == "acknowledge_switch":
        fixtures.blocked(h, tmp_path, "caller_quarantined")
    else:
        assert fixtures.persisted(tmp_path) == before
        assert h.store.read_owned_session_candidate(h.binding.owner).session_id == h.child
        assert not h.agents and not h.requests and not h.wire and not h.db._conn.in_transaction


@pytest.mark.parametrize("phase", ["projection_verified", "published_pending_caller", "acknowledging", "failed"])
def test_sqlite_receipt_update_fault(switch_host, tmp_path, monkeypatch, phase):
    from hermes_cli import middleware
    h = switch_host
    p = h.switch_preparation
    hits = []
    armed = False

    def authorize(action, table, column, database, trigger):
        if armed and action == sqlite3.SQLITE_UPDATE and table == "maya_session_transitions_v1":
            hits.append((table, column))
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    change = p._change

    def faulting_change(authority, old, new):
        nonlocal armed
        armed = new == phase or (phase == "acknowledging" and new == "caller_acknowledged")
        h.db._conn.set_authorizer(authorize)
        try:
            return change(authority, old, new)
        finally:
            armed = False
            h.db._conn.set_authorizer(None)

    try:
        if phase == "failed":
            with pytest.raises(ValueError, match="synthetic_caller_failure"):
                with h.store.prepare_owned_switch_candidate(h.binding.owner, h.source):
                    armed = True
                    h.db._conn.set_authorizer(authorize)
                    raise ValueError("synthetic_caller_failure")
        else:
            monkeypatch.setattr(p, "_change", faulting_change)
            with pytest.raises(middleware.MandatoryMiddlewareError):
                with h.store.prepare_owned_switch_candidate(h.binding.owner, h.source):
                    pass
    finally:
        h.db._conn.set_authorizer(None)
    assert hits
    expected = {"projection_verified": "committed_pending_projection",
                "published_pending_caller": "projection_verified", "acknowledging": "caller_quarantined",
                "failed": "published_pending_caller"}[phase]
    fixtures.blocked(h, tmp_path, expected)
