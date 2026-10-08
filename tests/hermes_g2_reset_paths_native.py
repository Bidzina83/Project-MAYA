"""Bounded unsafe-path qualification on the unchanged Patch 35 host candidate."""
from contextlib import contextmanager
import importlib.util
import os
from pathlib import Path
import stat
import subprocess
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reset_path_fixture', ROOT / 'tests/hermes_g2_reset_contention_native.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
reset_host = fixtures.reset_host


@pytest.fixture(scope='module', autouse=True)
def verified_source():
    import hermes_state
    sys.path.insert(0, str(ROOT / 'scripts'))
    from verify_governance_g2_reset_paths import verify_stage
    verify_stage(Path(hermes_state.__file__).resolve().parent.parent)


@contextmanager
def relocated_directory(directory, root):
    directory, root = directory.resolve(strict=True), root.resolve(strict=True)
    target = directory.with_name('path-fixture-relocated')
    assert directory.is_relative_to(root) and target.is_relative_to(root) and not target.exists()
    directory.rename(target)
    linked = False
    try:
        if os.name == 'nt':
            quote = lambda value: "'" + str(value).replace("'", "''") + "'"
            command = 'New-Item -ItemType Junction -Path ' + quote(directory) + ' -Target ' + quote(target) + ' -ErrorAction Stop'
            result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command],
                                    capture_output=True, timeout=20)
            assert result.returncode == 0, 'fixture junction creation failed'
        else:
            directory.symlink_to(target, target_is_directory=True)
        linked = True
        info = directory.lstat()
        assert stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
        yield target
    finally:
        if linked:
            # Remove only the verified fixture link, never its target tree.
            assert directory.resolve(strict=True) == target
            os.rmdir(directory) if os.name == 'nt' else directory.unlink()
        target.rename(directory)


def no_dispatch(h):
    assert not h.agents and not h.requests and not h.store._entries
    assert not h.db._conn.in_transaction and h.reset._active is None and h.preparation._current is None
    assert h.db._conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    assert h.db._conn.execute('PRAGMA foreign_key_check').fetchone() is None


@pytest.mark.parametrize('boundary', ['before_reset', 'after_commit', 'temp_complete', 'before_ack', 'reader'])
def test_actual_directory_junction_blocks_reset(reset_host, tmp_path, monkeypatch, boundary):
    from hermes_cli import middleware
    from project_maya.hermes_plugins import session_creation
    h = reset_host
    if boundary == 'reader':
        with h.store.prepare_owned_reset_candidate(h.binding.owner):
            pass
    original = fixtures.persisted(tmp_path)
    expected_projection = original[1]
    sentinel = h.reset.coordinator.directory / 'fixture-sentinel'
    sentinel.write_bytes(b'UNCHANGED_PATH_FIXTURE')
    link = None
    def relocate():
        nonlocal link
        assert link is None
        link = relocated_directory(h.reset.coordinator.directory, tmp_path)
        link.__enter__()
    def denied_reader():
        for action in (lambda: h.store.read_owned_session_candidate(h.binding.owner),
                       lambda: h.store.authenticated_owned_session_candidate(h.binding.owner).__enter__()):
            with pytest.raises(middleware.MandatoryMiddlewareError):
                action()
    try:
        with monkeypatch.context() as injection:
            if boundary in {'before_reset', 'reader'}:
                relocate()
            elif boundary == 'after_commit':
                commit = h.reset._commit
                def commit_then_link(conn):
                    commit(conn)
                    relocate()
                injection.setattr(h.reset, '_commit', commit_then_link)
            elif boundary == 'temp_complete':
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
                injection.setattr(session_creation.os, 'fdopen', lambda *a, **k: CompletedWriter(fdopen(*a, **k)))
            if boundary == 'reader':
                denied_reader()
            else:
                with pytest.raises(middleware.MandatoryMiddlewareError):
                    with h.store.prepare_owned_reset_candidate(h.binding.owner):
                        assert boundary == 'before_ack', 'unsafe path reached caller'
                        expected_projection = h.reset.coordinator.index.read_bytes()
                        relocate()
            assert sentinel.read_bytes() == b'UNCHANGED_PATH_FIXTURE'
            assert h.reset.coordinator.index.read_bytes() == expected_projection
            assert not list(h.reset.coordinator.directory.glob('.maya-projection-*'))
    finally:
        if link is not None:
            link.__exit__(None, None, None)
    no_dispatch(h)
    if boundary in {'before_reset', 'reader'}:
        assert fixtures.persisted(tmp_path) == original
    else:
        fixtures.committed_once(h, 'published_pending_caller' if boundary == 'before_ack' else 'committed_pending_projection')
        assert h.preparation._confirmed is None
        denied_reader()


@pytest.mark.parametrize('boundary', ['before_reset', 'after_commit'])
@pytest.mark.parametrize('component', ['directory', 'database', 'index', 'lock'])
@pytest.mark.parametrize('kind', ['reparse', 'symlink'])
def test_file_attribute_guard_blocks_reset(reset_host, tmp_path, monkeypatch, boundary, component, kind):
    from hermes_cli import middleware
    h = reset_host
    coordinator = h.reset.coordinator
    path = {'directory': coordinator.directory, 'database': Path(h.db.db_path),
            'index': coordinator.index, 'lock': coordinator.lockfile}[component].absolute()
    before = fixtures.persisted(tmp_path)
    lstat = Path.lstat
    hits = []
    def unsafe_info(item, *args, **kwargs):
        info = lstat(item, *args, **kwargs)
        if item.absolute() == path:
            hits.append(component)
            return SimpleNamespace(st_mode=stat.S_IFLNK if kind == 'symlink' else info.st_mode,
                                   st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT if kind == 'reparse' else 0)
        return info
    with monkeypatch.context() as injection:
        if boundary == 'before_reset':
            injection.setattr(Path, 'lstat', unsafe_info)
        else:
            commit = h.reset._commit
            def commit_then_arm(conn):
                commit(conn)
                injection.setattr(Path, 'lstat', unsafe_info)
            injection.setattr(h.reset, '_commit', commit_then_arm)
        with pytest.raises(middleware.MandatoryMiddlewareError):
            with h.store.prepare_owned_reset_candidate(h.binding.owner):
                pytest.fail('unsafe attributes reached caller')
    assert hits and coordinator.index.read_bytes() == before[1]
    no_dispatch(h)
    assert h.preparation._confirmed is None
    if boundary == 'before_reset':
        assert fixtures.persisted(tmp_path) == before
    else:
        fixtures.committed_once(h, 'committed_pending_projection')


@pytest.mark.parametrize('component', ['index', 'lock'])
@pytest.mark.parametrize('kind', ['missing', 'directory'])
def test_missing_or_nonfile_projection_storage_denies(reset_host, tmp_path, component, kind):
    from hermes_cli import middleware
    h = reset_host
    path = h.reset.coordinator.index if component == 'index' else h.reset.coordinator.lockfile
    saved = path.with_name(path.name + '.fixture-saved')
    before = fixtures.persisted(tmp_path)
    saved_bytes = path.read_bytes()
    path.rename(saved)
    try:
        if kind == 'directory':
            path.mkdir()
        with pytest.raises(middleware.MandatoryMiddlewareError):
            with h.store.prepare_owned_reset_candidate(h.binding.owner):
                pytest.fail('invalid storage reached caller')
        assert path.is_dir() if kind == 'directory' else not path.exists()
        assert saved.read_bytes() == saved_bytes
    finally:
        if kind == 'directory':
            path.rmdir()
        saved.rename(path)
    assert fixtures.persisted(tmp_path) == before
    no_dispatch(h)


def test_unc_projection_rejected_before_filesystem_access(reset_host, tmp_path, monkeypatch):
    from hermes_cli import middleware
    h = reset_host
    before = fixtures.persisted(tmp_path)
    stat_path = Path.stat
    attempted = []
    def no_unc_access(path, *args, **kwargs):
        if str(path).startswith('\\\\'):
            attempted.append(str(path))
            raise AssertionError('UNC path touched filesystem')
        return stat_path(path, *args, **kwargs)
    with monkeypatch.context() as injection:
        injection.setattr(h.reset.coordinator, 'directory', Path(r'\\maya-invalid\share\sessions'))
        injection.setattr(Path, 'stat', no_unc_access)
        with pytest.raises(middleware.MandatoryMiddlewareError):
            with h.store.prepare_owned_reset_candidate(h.binding.owner):
                pytest.fail('UNC path reached caller')
    assert not attempted and fixtures.persisted(tmp_path) == before
    no_dispatch(h)
