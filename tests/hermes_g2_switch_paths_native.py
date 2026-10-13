"""Bounded switch path guards and malformed projection rejection; frozen Patch 37."""
import importlib.util
import json
from pathlib import Path
import stat
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tests" / path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


fixtures = module("switch_path_fixture", "hermes_g2_switch_uncertainty_native.py")
paths = module("switch_path_junction", "hermes_g2_reset_paths_native.py")
switch_host = fixtures.switch_host
secret_safe_output = fixtures.secret_safe_output


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    import hermes_state
    sys.path.insert(0, str(ROOT / "scripts"))
    from verify_governance_g2_switch_storage_paths import verify_worker_stage
    verify_worker_stage(Path(hermes_state.__file__).resolve().parent.parent)


def no_dispatch(h):
    assert not h.agents and not h.requests and not h.wire and not h.store._entries
    assert not h.db._conn.in_transaction and h.switch._active is h.switch_preparation._current is None
    assert h.reader._active is None and h.switch_preparation._phase == "idle"
    assert h.db._conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert h.db._conn.execute("PRAGMA foreign_key_check").fetchone() is None


def denied_reader(h):
    from hermes_cli import middleware
    with pytest.raises(middleware.MandatoryMiddlewareError):
        h.store.read_owned_session_candidate(h.binding.owner)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        with h.store.authenticated_owned_session_candidate(h.binding.owner):
            pytest.fail("unsafe projection reached caller")


@pytest.mark.parametrize("boundary", ["before_switch", "after_commit", "temp_complete", "before_ack", "reader"])
def test_actual_directory_junction_blocks_switch(switch_host, tmp_path, monkeypatch, boundary):
    from hermes_cli import middleware
    from project_maya.hermes_plugins import session_creation
    h = switch_host
    coordinator = h.original[3]
    if boundary == "reader":
        with h.store.prepare_owned_switch_candidate(h.binding.owner, h.source):
            pass
    original = fixtures.persisted(tmp_path)
    expected = original[1]
    sentinel = coordinator.directory / "fixture-sentinel"
    sentinel.write_bytes(b"UNCHANGED_PATH_FIXTURE")
    link = None

    def relocate():
        nonlocal link
        assert link is None
        link = paths.relocated_directory(coordinator.directory, tmp_path)
        link.__enter__()

    try:
        with monkeypatch.context() as injection:
            if boundary in {"before_switch", "reader"}:
                relocate()
            elif boundary == "after_commit":
                commit = h.switch._commit
                def commit_then_link(conn):
                    commit(conn)
                    relocate()
                injection.setattr(h.switch, "_commit", commit_then_link)
            elif boundary == "temp_complete":
                fdopen = session_creation.os.fdopen
                class CompletedWriter:
                    def __init__(self, stream):
                        self.stream = stream
                    def __enter__(self):
                        self.stream.__enter__()
                        return self.stream
                    def __exit__(self, *args):
                        result = self.stream.__exit__(*args)
                        relocate()
                        return result
                injection.setattr(session_creation.os, "fdopen", lambda *a, **k: CompletedWriter(fdopen(*a, **k)))
            if boundary == "reader":
                denied_reader(h)
            else:
                with pytest.raises(middleware.MandatoryMiddlewareError):
                    with h.store.prepare_owned_switch_candidate(h.binding.owner, h.source):
                        assert boundary == "before_ack", "unsafe path reached caller"
                        expected = coordinator.index.read_bytes()
                        relocate()
            assert sentinel.read_bytes() == b"UNCHANGED_PATH_FIXTURE"
            assert coordinator.index.read_bytes() == expected
            assert not list(coordinator.directory.glob(".maya-projection-*"))
    finally:
        if link is not None:
            link.__exit__(None, None, None)
    no_dispatch(h)
    if boundary in {"before_switch", "reader"}:
        assert fixtures.persisted(tmp_path) == original
    else:
        fixtures.blocked(h, tmp_path, "published_pending_caller" if boundary == "before_ack"
                         else "committed_pending_projection", old_projection=boundary != "before_ack")


@pytest.mark.parametrize("boundary", ["before_switch", "after_commit"])
@pytest.mark.parametrize("component", ["directory", "database", "index", "lock"])
@pytest.mark.parametrize("kind", ["reparse", "symlink"])
def test_scoped_file_attribute_guard(switch_host, tmp_path, monkeypatch, boundary, component, kind):
    h = switch_host
    coordinator = h.original[3]
    path = {"directory": coordinator.directory, "database": Path(h.db.db_path),
            "index": coordinator.index, "lock": coordinator.lockfile}[component].absolute()
    before = fixtures.persisted(tmp_path)
    lstat = Path.lstat
    hits = []

    def unsafe_info(item, *args, **kwargs):
        info = lstat(item, *args, **kwargs)
        if item.absolute() == path:
            hits.append(component)
            return SimpleNamespace(st_mode=stat.S_IFLNK if kind == "symlink" else info.st_mode,
                st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT if kind == "reparse" else 0)
        return info

    with monkeypatch.context() as injection:
        if boundary == "before_switch":
            injection.setattr(Path, "lstat", unsafe_info)
        else:
            commit = h.switch._commit
            def commit_then_arm(conn):
                commit(conn)
                injection.setattr(Path, "lstat", unsafe_info)
            injection.setattr(h.switch, "_commit", commit_then_arm)
        fixtures.run_failed(h)
    assert hits and coordinator.index.read_bytes() == before[1]
    no_dispatch(h)
    if boundary == "before_switch":
        assert fixtures.persisted(tmp_path) == before
    else:
        fixtures.blocked(h, tmp_path, "committed_pending_projection", old_projection=True)


@pytest.mark.parametrize("component", ["index", "lock"])
@pytest.mark.parametrize("kind", ["missing", "directory"])
def test_missing_or_nonfile_projection_storage(switch_host, tmp_path, component, kind):
    h = switch_host
    coordinator = h.original[3]
    path = coordinator.index if component == "index" else coordinator.lockfile
    root = tmp_path.resolve(strict=True)
    path = path.resolve(strict=True)
    saved = path.with_name(path.name + ".fixture-saved")
    assert path.is_relative_to(root) and saved.is_relative_to(root) and not saved.exists()
    before = fixtures.persisted(tmp_path)
    raw = path.read_bytes()
    path.rename(saved)
    try:
        if kind == "directory":
            path.mkdir()
        fixtures.run_failed(h)
        assert path.is_dir() if kind == "directory" else not path.exists()
        assert saved.read_bytes() == raw
    finally:
        if kind == "directory":
            assert path.resolve(strict=True).is_relative_to(root)
            path.rmdir()
        assert saved.resolve(strict=True).is_relative_to(root) and path.parent.resolve(strict=True).is_relative_to(root)
        saved.rename(path)
    assert fixtures.persisted(tmp_path) == before
    no_dispatch(h)


def test_unc_denied_before_filesystem_access(switch_host, tmp_path, monkeypatch):
    h = switch_host
    before = fixtures.persisted(tmp_path)
    stat_path = Path.stat
    attempts = []
    def no_unc_access(path, *args, **kwargs):
        if str(path).startswith("\\\\"):
            attempts.append(str(path))
            raise AssertionError("UNC path touched filesystem")
        return stat_path(path, *args, **kwargs)
    with monkeypatch.context() as injection:
        injection.setattr(h.original[3], "directory", Path(r"\\maya-invalid\share\sessions"))
        injection.setattr(Path, "stat", no_unc_access)
        fixtures.run_failed(h)
    assert not attempts and fixtures.persisted(tmp_path) == before
    no_dispatch(h)


@pytest.mark.parametrize("boundary", ["before_switch", "reader"])
@pytest.mark.parametrize("damage", ["invalid_json", "contract", "instance", "database", "generation",
                                   "missing_route", "wrong_target", "route_version"])
def test_malformed_projection_never_adopted(switch_host, tmp_path, boundary, damage):
    h = switch_host
    if boundary == "reader":
        with h.store.prepare_owned_switch_candidate(h.binding.owner, h.source):
            pass
    coordinator = h.original[3]
    before = fixtures.persisted(tmp_path)
    envelope = json.loads(before[1])
    if damage == "invalid_json":
        raw = b"{invalid-projection\n"
    else:
        if damage in {"contract", "instance", "database"}:
            envelope[{"contract": "contract", "instance": "instance_id", "database": "database"}[damage]] = "synthetic-foreign"
        elif damage == "generation":
            envelope["generation"] += 1
        elif damage == "missing_route":
            envelope["routes"] = {}
        elif damage == "wrong_target":
            envelope["routes"][h.binding.route_slot]["session_id"] = h.child if boundary == "reader" else h.source
        else:
            envelope["routes"][h.binding.route_slot]["version"] += 1
        raw = (json.dumps(envelope, sort_keys=True, separators=(",", ":")) + "\n").encode()
    assert raw != before[1]
    coordinator.index.write_bytes(raw)
    try:
        if boundary == "reader":
            denied_reader(h)
        else:
            fixtures.run_failed(h)
        assert fixtures.persisted(tmp_path) == (before[0], raw)
        no_dispatch(h)
    finally:
        coordinator.index.write_bytes(before[1])
    assert fixtures.persisted(tmp_path) == before
