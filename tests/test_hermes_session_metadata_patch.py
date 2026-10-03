"""Native metadata transactions and scoped close reporting, without real workers."""
import ast
import subprocess
import sys
from threading import Lock
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from tests import test_hermes_session_writer_callers_patch as callers

ROOT = callers.ROOT


class TestHermesSessionMetadataPatch(unittest.TestCase):
    def setUp(self):
        self.host = callers.TestHermesSessionWriterCallersPatch()
        self.addCleanup(self.host.doCleanups)
        self.host.setUp()
        target = self.host.host.host.target
        result = subprocess.run(['git', 'apply', '--whitespace=error', str(ROOT / 'patches/hermes/0018-session-metadata-and-close-reporting.patch')],
                                cwd=target, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        tree = ast.parse((target / 'hermes_state.py').read_text(encoding='utf-8'))
        tree.body = [n for n in tree.body if not (isinstance(n, ast.ImportFrom) and n.module in {'agent.memory_manager', 'hermes_constants'})]
        scope = {'__name__': 'native_metadata_state', 'sanitize_context': lambda value: value, 'get_hermes_home': lambda: target}
        exec(compile(tree, str(target / 'hermes_state.py'), 'exec'), scope)
        self.host.db.close()
        self.db = scope['SessionDB'](target / 'atomic.db')
        self.addCleanup(self.db.close)
        self.host.db = self.db
        self.host.agent._session_db = self.db
        self.engine = self.host.engine
        self.statements = []
        self.db._conn.set_trace_callback(self.statements.append)
        tree = ast.parse((target / 'run_agent.py').read_text(encoding='utf-8'))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'AIAgent')
        close = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'close')
        module = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0), close], type_ignores=[])
        self.cleanup_vm, self.cleanup_browser, self.kill_all = Mock(), Mock(), Mock()
        scope = {'cleanup_vm': self.cleanup_vm, 'cleanup_browser': self.cleanup_browser}
        exec(compile(ast.fix_missing_locations(module), 'complete-native-close', 'exec'), scope)
        self.agent = self.host.agent
        self.agent.close = scope['close'].__get__(self.agent)
        self.agent._active_children_lock = Lock()
        self.agent._active_children = []
        self.agent.client = object()
        self.agent._close_openai_client = Mock()
        self.agent._session_messages = [{'role': 'user', 'content': 'safe'}]
        patcher = patch.dict(sys.modules, {'tools.process_registry': SimpleNamespace(process_registry=SimpleNamespace(kill_all=self.kill_all))})
        patcher.start()
        self.addCleanup(patcher.stop)

    def bound(self, operations=frozenset({'metadata'})):
        return self.host.bound(operations=operations)

    def session(self):
        return self.db.get_session('synthetic-session')

    def test_end_first_reason_wins_and_reopen_preserves_native_semantics(self):
        self.host.mandatory()
        with self.bound():
            self.db.end_session('synthetic-session', 'first')
            first = self.session()
            self.db.end_session('synthetic-session', 'second')
            self.assertEqual(self.session()['end_reason'], 'first')
            self.assertEqual(self.session()['ended_at'], first['ended_at'])
            self.db.reopen_session('synthetic-session')
        self.assertIsNone(self.session()['ended_at'])
        self.assertIsNone(self.session()['end_reason'])

    def test_allowed_config_model_and_cwd_metadata(self):
        self.host.mandatory()
        with self.bound():
            self.db.update_session_meta('synthetic-session', '{"safe": "value"}', model='new-model')
            self.db.update_session_model('synthetic-session', 'latest-model')
            self.db.update_session_cwd('synthetic-session', 'synthetic-location')
        self.assertEqual(self.session()['model'], 'latest-model')
        self.assertEqual(self.session()['cwd'], 'synthetic-location')
        self.assertEqual(self.session()['model_config'], '{"safe": "value"}')

    def test_metadata_denials_preserve_entire_row_before_transaction(self):
        before = self.session()
        self.host.mandatory()
        actions = (
            lambda: self.db.end_session('synthetic-session', 'done'),
            lambda: self.db.reopen_session('synthetic-session'),
            lambda: self.db.update_session_cwd('synthetic-session', 'other'),
            lambda: self.db.update_session_model('synthetic-session', 'other'),
            lambda: self.db.update_session_meta('synthetic-session', '{}'),
            lambda: self.db.update_token_counts('synthetic-session', input_tokens=5),
        )
        for action in actions:
            with self.bound(frozenset({'append'})), self.assertRaises(self.engine.MandatoryMiddlewareError):
                action()
            self.assertEqual(self.session(), before)
        self.assertFalse(any(sql.startswith('BEGIN') for sql in self.statements))

    def test_serialized_secret_metadata_is_blocked(self):
        before = self.session()
        self.host.mandatory()
        actions = (
            lambda: self.db.update_session_meta('synthetic-session', '{"api_key":"synthetic"}'),
            lambda: self.db.end_session('synthetic-session', 'sk-proj-syntheticcredential0123456789'),
            lambda: self.db.update_token_counts('synthetic-session', cost_source='sk-proj-syntheticcredential0123456789'),
        )
        for action in actions:
            with self.bound(), self.assertRaises(self.engine.MandatoryMiddlewareError):
                action()
            self.assertEqual(self.session(), before)
        self.assertFalse(any(sql.startswith('BEGIN') for sql in self.statements))

    def test_token_delta_and_absolute_updates_preserve_counters(self):
        self.host.mandatory()
        with self.bound():
            self.db.update_token_counts('synthetic-session', input_tokens=4, output_tokens=2, api_call_count=1)
            self.db.update_token_counts('synthetic-session', input_tokens=3, output_tokens=1, api_call_count=1)
            self.assertEqual(self.session()['input_tokens'], 7)
            self.assertEqual(self.session()['api_call_count'], 2)
            self.db.update_token_counts('synthetic-session', input_tokens=10, output_tokens=5, api_call_count=3, absolute=True)
        self.assertEqual(self.session()['input_tokens'], 10)
        self.assertEqual(self.session()['output_tokens'], 5)
        self.assertEqual(self.session()['api_call_count'], 3)

    def test_accounting_does_not_implicitly_create_a_missing_session(self):
        self.db._conn.execute("DELETE FROM sessions WHERE id = 'synthetic-session'")
        self.db._conn.commit()
        self.host.mandatory()
        with self.bound(), self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, 'session_write_unqualified'):
            self.db.update_token_counts('synthetic-session', input_tokens=5)
        self.assertIsNone(self.session())

    def test_metadata_sql_failure_rolls_back_with_fixed_error(self):
        self.db._conn.execute("CREATE TRIGGER fail_meta BEFORE UPDATE ON sessions BEGIN SELECT RAISE(ABORT, 'synthetic-private-metadata-error'); END")
        self.db._conn.commit()
        before = self.session()
        self.host.mandatory()
        with self.bound(), self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, 'session_write_failed') as caught:
            self.db.update_token_counts('synthetic-session', input_tokens=5)
        self.assertNotIn('synthetic-private', str(caught.exception))
        self.assertEqual(self.session(), before)

    def test_close_denial_is_reported_after_resource_cleanup(self):
        self.host.mandatory()
        with self.bound(frozenset({'append'})), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.agent.close()
        self.kill_all.assert_called_once()
        self.cleanup_vm.assert_called_once()
        self.cleanup_browser.assert_called_once()
        self.agent._close_openai_client.assert_called_once()
        self.assertIsNone(self.agent.client)
        self.assertEqual(self.agent._session_messages, [])
        self.assertIsNone(self.session()['ended_at'])

    def test_authorized_close_finalizes_session(self):
        self.host.mandatory()
        with self.bound():
            self.agent.close()
        self.assertEqual(self.session()['end_reason'], 'agent_close')

    def test_ordinary_accounting_retains_implicit_create_and_close_best_effort(self):
        self.db.update_token_counts('other-session', input_tokens=5)
        self.assertEqual(self.db.get_session('other-session')['input_tokens'], 5)
        self.agent._session_db = Mock()
        self.agent._session_db.end_session.side_effect = RuntimeError('synthetic failure')
        self.agent.close()
        self.cleanup_vm.assert_called_once()


if __name__ == '__main__':
    unittest.main()
