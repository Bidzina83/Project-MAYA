"""Complete native writer callers over real SQLite; no gateway identity inference."""
import ast
from datetime import datetime
import hashlib
import shutil
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

from tests import test_hermes_session_mutation_patch as mutations
from tests.test_hermes_caller_denial_patch import native_function

ROOT = mutations.ROOT


class TestHermesSessionWriterCallersPatch(mutations.TestHermesSessionMutationPatch):
    def setUp(self):
        super().setUp()
        target = self.host.host.target
        (target / 'gateway').mkdir(exist_ok=True)
        for name in ('session', 'mirror'):
            shutil.copyfile(ROOT / 'tests/fixtures/hermes_middleware' / ('gateway_' + name + '.py'), target / 'gateway' / (name + '.py'))
        result = subprocess.run(['git', 'apply', '--whitespace=error', str(ROOT / 'patches/hermes/0017-session-writer-caller-denial-propagation.patch')],
                                cwd=target, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.logger = Mock()
        self.mirror_scope = {'logger': self.logger, 'datetime': datetime,
                             '_find_session_id': lambda *args, **kwargs: 'synthetic-session'}
        append = native_function(target / 'gateway/mirror.py', '_append_to_sqlite', self.mirror_scope)
        self.mirror_scope['_append_to_sqlite'] = append
        self.mirror = native_function(target / 'gateway/mirror.py', 'mirror_to_session', self.mirror_scope)
        tree = ast.parse((target / 'gateway/session.py').read_text(encoding='utf-8'))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'SessionStore')
        methods = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in {'append_to_transcript', 'rewrite_transcript'}]
        scope = {'logger': self.logger}
        module = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0), *methods], type_ignores=[])
        exec(compile(ast.fix_missing_locations(module), 'native-transcript-callers', 'exec'), scope)
        self.store = SimpleNamespace(_db=self.db)
        self.append = lambda message, native=scope['append_to_transcript']: native(self.store, 'synthetic-session', message)
        self.rewrite = lambda messages, native=scope['rewrite_transcript']: native(self.store, 'synthetic-session', messages)
        tree = ast.parse((target / 'run_agent.py').read_text(encoding='utf-8'))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'AIAgent')
        methods = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in {'_ensure_db_session', '_flush_messages_to_session_db'}]
        scope = self.host.scope.copy()
        scope.update(_session_source_for_agent=lambda platform: 'test', _launch_cwd_for_session=lambda source: None)
        module = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0), *methods], type_ignores=[])
        exec(compile(ast.fix_missing_locations(module), 'native-session-initializer', 'exec'), scope)
        for method in methods:
            setattr(self.agent, method.name, scope[method.name].__get__(self.agent))
        self.agent._session_init_model_config = {}
        self.agent._parent_session_id = None
        self.opened = []
        def open_db():
            db = type(self.db)(self.db.db_path)
            self.opened.append(db)
            self.addCleanup(db.close)
            return db
        patcher = patch.dict(sys.modules, {'hermes_state': SimpleNamespace(SessionDB=open_db)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_incremental_flush_does_not_fall_back_to_unqualified_session_creation(self):
        self.mandatory()
        self.agent._session_db_created = False
        with self.bound(), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.agent._flush_messages_to_session_db([{'role': 'user', 'content': 'safe'}], [])
        self.assertFalse(self.agent._session_db_created)
        self.assertEqual(self.rows(), [])
        self.assert_no_begin()

    def test_authorized_native_initializer_then_atomic_append(self):
        self.db._conn.execute("DELETE FROM sessions WHERE id = 'synthetic-session'")
        self.db._conn.commit()
        self.agent._session_db_created = False
        self.mandatory()
        with self.bound(operations=frozenset({'create', 'append'})):
            self.agent._flush_messages_to_session_db([{'role': 'user', 'content': 'safe'}], [])
        self.assertTrue(self.agent._session_db_created)
        self.assertEqual(len(self.rows()), 1)
        self.assertEqual(self.agent._last_flushed_db_idx, 1)

    def test_native_initializer_denial_is_not_logged_or_retried(self):
        self.agent._session_db_created = False
        self.mandatory()
        with self.bound(), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.agent._ensure_db_session()
        self.assertFalse(self.agent._session_db_created)
        self.host.host.logger.warning.assert_not_called()
        self.assert_no_begin()

    def test_transcript_append_and_rewrite_use_bound_authority(self):
        self.mandatory()
        with self.bound():
            self.append({'role': 'user', 'content': 'safe'})
        with self.bound(operations=frozenset({'rewrite'})):
            self.rewrite([{'role': 'assistant', 'content': 'replacement'}])
        self.assertEqual([row['content'] for row in self.rows()], ['replacement'])

    def test_transcript_denials_propagate_without_log_or_state_change(self):
        self.seed()
        before = self.snapshot()
        self.mandatory()
        for action in (lambda: self.append({'role': 'user', 'content': 'safe'}),
                       lambda: self.rewrite([{'role': 'user', 'content': 'replacement'}])):
            with self.assertRaises(self.engine.MandatoryMiddlewareError):
                action()
        self.assertEqual(self.snapshot(), before)
        self.logger.debug.assert_not_called()
        self.assert_no_begin()

    def test_mirror_denial_escapes_both_callers_and_closes_native_connection(self):
        self.mandatory()
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.mirror('telegram', 'synthetic-chat', 'safe')
        self.assertEqual(self.rows(), [])
        self.assertTrue(all(db._conn is None for db in self.opened))
        self.logger.debug.assert_not_called()

    def test_allowed_mirror_preserves_native_sqlite_storage(self):
        self.mandatory()
        with self.bound():
            result = self.mirror('telegram', 'synthetic-chat', 'safe')
        self.assertTrue(result)
        self.assertEqual(self.rows()[0]['content'], 'safe')
        self.assertTrue(all(db._conn is None for db in self.opened))

    def test_ordinary_transcript_and_mirror_errors_remain_best_effort(self):
        self.store._db = Mock()
        self.store._db.append_message.side_effect = RuntimeError('synthetic failure')
        self.append({'role': 'user', 'content': 'safe'})
        self.mirror_scope['_append_to_sqlite'] = Mock(side_effect=RuntimeError('synthetic failure'))
        self.assertFalse(self.mirror('telegram', 'synthetic-chat', 'safe'))

    def test_native_gateway_fixtures_are_pinned(self):
        for name, digest in FIXTURE_HASHES.items():
            path = ROOT / 'tests/fixtures/hermes_middleware' / name
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)

    def test_missing_native_database_does_not_report_success(self):
        self.mandatory()
        self.store._db = None
        self.agent._session_db = None
        for action in (lambda: self.append({'role': 'user', 'content': 'safe'}),
                       lambda: self.rewrite([]), lambda: self.agent._ensure_db_session(),
                       lambda: self.agent._flush_messages_to_session_db([], [])):
            with self.bound(), self.assertRaises(self.engine.MandatoryMiddlewareError):
                action()
        self.assert_no_begin()


FIXTURE_HASHES = {
    'gateway_session.py': '6d36c5cfdd9cf36159c8295d5b7757f26b3bbae49dc4c7fbdfbd8bc4e763fc74',
    'gateway_mirror.py': '8c5b402386af657349f6f5ab95e1bd80dd0742fe91a02fa96d6d67cb0a749d8e',
}
