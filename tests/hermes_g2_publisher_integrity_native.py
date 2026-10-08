"""Pre-replacement byte/count validation for both native create and reset."""
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / ('tests/' + name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


verification = load('hermes_g2_publisher_reset_native')
verified_source = verification.verified_source
create = load('hermes_g2_create_native')
contention = load('hermes_g2_reset_contention_native')


@pytest.fixture
def publication_host(request, tmp_path, monkeypatch):
    pipeline = request.node.callspec.params['pipeline']
    fixture = (create.host if pipeline == 'create' else contention.reset_host).__wrapped__(tmp_path, monkeypatch)
    value = next(fixture)
    try:
        yield value
    finally:
        next(fixture, None)


@pytest.mark.parametrize('pipeline', ['create', 'reset'])
@pytest.mark.parametrize('fault', ['zero_count', 'boolean_count', 'corrupt_full_count'])
def test_incomplete_or_corrupt_temp_never_replaces(publication_host, monkeypatch, pipeline, fault):
    from hermes_cli import middleware
    from project_maya.hermes_plugins import session_creation
    if pipeline == 'create':
        store, db, binding, coordinator = publication_host
    else:
        h = publication_host
        store, db, binding, coordinator = h.store, h.db, h.binding, h.reset.coordinator
    before = coordinator.index.read_bytes()
    fdopen = session_creation.os.fdopen
    replacements = []

    class FaultyWriter:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            self.stream.__enter__()
            return self

        def __exit__(self, *args):
            return self.stream.__exit__(*args)

        def write(self, raw):
            self.stream.write(raw[:-1] + b'X' if fault == 'corrupt_full_count' else raw)
            return 0 if fault == 'zero_count' else True if fault == 'boolean_count' else len(raw)

        def flush(self):
            return self.stream.flush()

        def fileno(self):
            return self.stream.fileno()

    with monkeypatch.context() as injection:
        injection.setattr(session_creation.os, 'fdopen', lambda *a, **k: FaultyWriter(fdopen(*a, **k)))
        injection.setattr(session_creation.os, 'replace', lambda *a: replacements.append(a))
        with pytest.raises(middleware.MandatoryMiddlewareError):
            if pipeline == 'create':
                with binding.authenticated_create(binding.owner) as authority:
                    store.create_owned_session_candidate(authority)
            else:
                with store.prepare_owned_reset_candidate(binding.owner):
                    pytest.fail('corrupt projection reached caller')
    assert not replacements and coordinator.index.read_bytes() == before
    assert not list(coordinator.directory.glob('.maya-projection-*'))
    assert db._conn.execute('SELECT count(*) FROM sessions').fetchone()[0] == (1 if pipeline == 'create' else 2)
    assert db._conn.execute('SELECT state FROM maya_session_transitions_v1 ORDER BY result_route_version DESC LIMIT 1').fetchone()[0] == 'committed_pending_projection'
    assert not db._conn.in_transaction and not store._entries
