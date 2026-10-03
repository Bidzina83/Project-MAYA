"""Candidate final-row checks with native Hermes SQLite storage, offline."""
import ast
import hashlib
import shutil
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from project_maya.hermes_plugins.governance import bind_request_identity
from tests import test_hermes_persistence_observer_patch as persistence

ROOT = persistence.recovery_tests.ROOT


class TestHermesSessionRowPatch(unittest.TestCase):
    def setUp(self):
        self.host = persistence.TestHermesPersistenceObserverPatch()
        self.addCleanup(self.host.doCleanups)
        self.host.setUp()
        self.engine = self.host.engine
        target = self.host.target
        for name, destination in (('cli.py', 'cli.py'), ('conversation_compression.py', 'agent/conversation_compression.py')):
            shutil.copyfile(ROOT / 'tests/fixtures/hermes_middleware' / name, target / destination)
        result = subprocess.run(
            ['git', 'apply', '--whitespace=error', str(ROOT / 'patches/hermes/0013-outer-caller-denial-propagation.patch')],
            cwd=target, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run(
            ['git', 'apply', '--whitespace=error', str(ROOT / 'patches/hermes/0014-effective-session-row-validation.patch')],
            cwd=target, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        tree = ast.parse((target / 'run_agent.py').read_text(encoding='utf-8'))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'AIAgent')
        method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '_flush_messages_to_session_db')
        scope = {'logger': self.host.logger, '_is_multimodal_tool_result': lambda value: False}
        module = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0), method], type_ignores=[])
        exec(compile(ast.fix_missing_locations(module), 'native-row-writer', 'exec'), scope)
        self.agent = self.host.agent
        self.agent._flush_messages_to_session_db = scope[method.name].__get__(self.agent)
        self.scope = scope
        # Only unrelated home discovery and memory-read sanitization are inert.
        # The complete SessionDB implementation, schema, SQL and transactions run.
        fixture = ROOT / 'tests/fixtures/hermes_middleware/hermes_state.py'
        tree = ast.parse(fixture.read_text(encoding='utf-8'))
        tree.body = [n for n in tree.body if not (isinstance(n, ast.ImportFrom) and n.module in {'agent.memory_manager', 'hermes_constants'})]
        state_scope = {'__name__': 'native_test_state', 'sanitize_context': lambda value: value,
                       'get_hermes_home': lambda: target}
        exec(compile(tree, str(fixture), 'exec'), state_scope)
        self.db = state_scope['SessionDB'](target / 'rows.db')
        self.addCleanup(self.db.close)
        self.db.create_session('synthetic-session', 'test')
        self.agent._session_db = self.db
        self.capture = Mock(wraps=self.db.append_message)
        self.db.append_message = self.capture

    def test_allowed_mapping_roundtrips_native_sqlite_and_deduplicates(self):
        self.host.mandatory()
        messages = [{'role': 'assistant', 'content': [{'type': 'text', 'text': 'safe'}, {'type': 'image_url', 'image_url': 'synthetic'}],
                     'reasoning': 'safe reasoning', 'tool_calls': [{'name': 'read_file', 'arguments': '{}'}]}]
        with bind_request_identity('alice'):
            self.agent._flush_messages_to_session_db(messages, [])
            self.agent._flush_messages_to_session_db(messages, [])
        rows = self.db.get_messages('synthetic-session')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['content'], 'safe\n[screenshot]')
        self.assertEqual(rows[0]['reasoning'], 'safe reasoning')
        self.assertEqual(rows[0]['tool_calls'][0]['name'], 'read_file')
        self.capture.assert_called_once()

    def test_attribute_derived_tool_arguments_are_checked_before_sqlite(self):
        self.host.mandatory()
        class Message(dict):
            pass
        msg = Message(role='assistant', content='safe')
        msg.tool_calls = [SimpleNamespace(function=SimpleNamespace(name='read_file', arguments='sk-proj-syntheticcredential0123456789'))]
        with bind_request_identity('alice'), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.agent._flush_messages_to_session_db([msg], [])
        self.assertEqual(self.db.get_messages('synthetic-session'), [])
        self.capture.assert_not_called()
        self.assertEqual(self.agent._last_flushed_db_idx, 0)
        self.host.logger.warning.assert_not_called()

    def test_transformed_multimodal_result_denial_preserves_prior_rows(self):
        self.db.append_message('synthetic-session', 'user', 'previous')
        self.capture.reset_mock()
        before = self.db.get_messages('synthetic-session')
        self.host.mandatory()
        self.scope['_is_multimodal_tool_result'] = lambda value: True
        self.scope['_multimodal_text_summary'] = lambda value: 'sk-proj-syntheticcredential0123456789'
        with bind_request_identity('alice'), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.agent._flush_messages_to_session_db([{'role': 'tool', 'content': 'safe'}], [])
        self.assertEqual(self.db.get_messages('synthetic-session'), before)
        self.capture.assert_not_called()

    def test_normal_mode_keeps_native_mapping_without_identity(self):
        self.agent._flush_messages_to_session_db([{'role': 'user', 'content': 'ordinary'}], [])
        self.assertEqual(self.db.get_messages('synthetic-session')[0]['content'], 'ordinary')

    def test_later_denial_does_not_claim_batch_rollback(self):
        self.host.mandatory()
        class Message(dict):
            pass
        denied = Message(role='assistant', content='safe')
        denied.tool_calls = [SimpleNamespace(function=SimpleNamespace(name='read_file', arguments='sk-proj-syntheticcredential0123456789'))]
        with bind_request_identity('alice'), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.agent._flush_messages_to_session_db([{'role': 'user', 'content': 'approved first'}, denied], [])
        rows = self.db.get_messages('synthetic-session')
        self.assertEqual([row['content'] for row in rows], ['approved first'])
        self.capture.assert_called_once()

    def test_native_fixture_matches_pinned_source(self):
        fixture = ROOT / 'tests/fixtures/hermes_middleware/hermes_state.py'
        self.assertEqual(hashlib.sha256(fixture.read_bytes()).hexdigest(), STATE_SHA256)


STATE_SHA256 = '2092d272d091c297e8b51429d8a635d13ed12aa2d607384119241991ade63797'

if __name__ == '__main__':
    unittest.main()
