"""Trusted session-write candidate with the complete native SQLite backend."""
import ast
import asyncio
from contextlib import contextmanager
from contextvars import copy_context
import subprocess
from threading import Thread
from types import SimpleNamespace
import unittest

from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins.governance import bind_request_identity, bind_session_write
from tests import test_hermes_session_row_patch as row_tests

ROOT = row_tests.ROOT


class TestHermesSessionWritePatch(unittest.TestCase):
    def setUp(self):
        self.host = row_tests.TestHermesSessionRowPatch()
        self.addCleanup(self.host.doCleanups)
        self.host.setUp()
        target = self.host.host.target
        state_path = target / 'hermes_state.py'
        state_path.write_bytes((ROOT / 'tests/fixtures/hermes_middleware/hermes_state.py').read_bytes())
        result = subprocess.run(['git', 'apply', '--whitespace=error', str(ROOT / 'patches/hermes/0015-trusted-session-write-and-atomic-append.patch')],
                                cwd=target, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.engine = self.host.engine
        # Reload the exact patched native module; its host bindings start empty.
        exec(compile((target / 'hermes_cli/middleware.py').read_text(encoding='utf-8'), 'native-session-middleware', 'exec'), self.engine.__dict__)
        tree = ast.parse(state_path.read_text(encoding='utf-8'))
        tree.body = [n for n in tree.body if not (isinstance(n, ast.ImportFrom) and n.module in {'agent.memory_manager', 'hermes_constants'})]
        scope = {'__name__': 'native_session_state', 'sanitize_context': lambda value: value, 'get_hermes_home': lambda: target}
        exec(compile(tree, str(state_path), 'exec'), scope)
        self.db = scope['SessionDB'](target / 'atomic.db')
        self.addCleanup(self.db.close)
        self.db.create_session('synthetic-session', 'test')
        self.plugin = self.host.host.host.host.plugin
        self.manager = self.host.host.host.host.manager
        self.statements = []
        self.db._conn.set_trace_callback(self.statements.append)
        tree = ast.parse((target / 'run_agent.py').read_text(encoding='utf-8'))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'AIAgent')
        method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '_flush_messages_to_session_db')
        module = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0), method], type_ignores=[])
        scope = self.host.scope.copy()
        exec(compile(ast.fix_missing_locations(module), 'native-atomic-flush', 'exec'), scope)
        self.agent = self.host.agent
        self.agent._flush_messages_to_session_db = scope[method.name].__get__(self.agent)
        self.agent._session_db = self.db

    def mandatory(self, allowed=True):
        self.host.host.mandatory()
        self.plugin.gateway = PolicyAuthorizationGateway((
            PolicyRule('session.write', target='session:synthetic-session', operation='append', actor_id='alice'),
            PolicyRule('model.output', target='model:openai', operation='disclose', actor_id='alice'),
        ) if allowed else ())
        ctx = SimpleNamespace(register_middleware=lambda kind, callback: self.manager._middleware.__setitem__(kind, [callback]))
        self.plugin.register_session_write_candidate(ctx, self.engine)
        self.assertTrue(self.engine.validate_mandatory_middleware())

    @contextmanager
    def bound(self, *, request='request-1', session='synthetic-session', database=None, operations=frozenset({'append'})):
        with bind_request_identity('alice'), bind_session_write(request, session, database or self.db.db_path, operations):
            yield

    def rows(self):
        return self.db.get_messages('synthetic-session')

    def assert_no_begin(self):
        self.assertFalse(any(sql.startswith('BEGIN') for sql in self.statements))

    def test_allowed_batch_single_transaction_counters_and_restart(self):
        self.mandatory()
        with self.bound():
            ids = self.db.append_messages('synthetic-session', [
                {'role': 'user', 'content': 'safe'},
                {'role': 'assistant', 'content': 'safe result', 'tool_calls': [{'name': 'read_file', 'arguments': '{}'}]},
            ])
        self.assertEqual(len(ids), 2)
        self.assertEqual(sum(sql.startswith('BEGIN') for sql in self.statements), 1)
        self.assertEqual(sum(sql == 'COMMIT' for sql in self.statements), 1)
        session = self.db.get_session('synthetic-session')
        self.assertEqual(session['message_count'], 2)
        self.assertEqual(session['tool_call_count'], 1)
        self.db.close()
        self.db = type(self.db)(self.db.db_path)
        self.addCleanup(self.db.close)
        self.assertEqual(len(self.rows()), 2)

    def test_denied_first_middle_and_last_leave_zero_rows_and_counters(self):
        self.mandatory()
        for index in range(3):
            batch = [{'role': 'user', 'content': 'safe'} for _ in range(3)]
            batch[index]['content'] = 'sk-proj-syntheticcredential0123456789'
            self.statements.clear()
            with self.bound(), self.assertRaises(self.engine.MandatoryMiddlewareError):
                self.db.append_messages('synthetic-session', batch)
            self.assert_no_begin()
            self.assertEqual(self.rows(), [])
            self.assertEqual(self.db.get_session('synthetic-session')['message_count'], 0)

    def test_final_serialization_is_checked_before_sqlite(self):
        self.mandatory()
        original = self.db._encode_content
        self.db._encode_content = lambda value: 'sk-proj-syntheticcredential0123456789'
        with self.bound(), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.db.append_messages('synthetic-session', [{'role': 'user', 'content': 'safe'}])
        self.db._encode_content = original
        self.assert_no_begin()
        self.assertEqual(self.rows(), [])

    def test_database_failure_on_second_insert_rolls_back_rows_counters_and_fts(self):
        self.db._conn.execute("CREATE TRIGGER fail_second BEFORE INSERT ON messages WHEN NEW.content = 'fail' BEGIN SELECT RAISE(ABORT, 'synthetic failure'); END")
        self.db._conn.commit()
        self.mandatory()
        with self.bound(), self.assertRaises(Exception):
            self.db.append_messages('synthetic-session', [{'role': 'user', 'content': 'safe'}, {'role': 'user', 'content': 'fail'}])
        self.assertEqual(self.rows(), [])
        self.assertEqual(self.db.get_session('synthetic-session')['message_count'], 0)
        self.assertEqual(self.db._conn.execute('SELECT count(*) FROM messages_fts').fetchone()[0], 0)
        self.assertIn('ROLLBACK', self.statements)

    def test_missing_context_and_identity_fail_before_begin(self):
        self.mandatory()
        for context in (bind_request_identity('alice'), bind_request_identity('bob')):
            with context, self.assertRaises(self.engine.MandatoryMiddlewareError):
                self.db.append_message('synthetic-session', 'user', 'safe')
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.db.append_message('synthetic-session', 'user', 'safe')
        self.assert_no_begin()

    def test_session_database_and_operation_bindings_are_enforced(self):
        self.mandatory()
        for kwargs in ({'session': 'other'}, {'database': self.db.db_path.with_name('other.db')}, {'operations': frozenset({'delete'})}):
            with self.bound(**kwargs), self.assertRaises(self.engine.MandatoryMiddlewareError):
                self.db.append_message('synthetic-session', 'user', 'safe')
        self.assert_no_begin()

    def test_removed_callback_fails_closed(self):
        self.mandatory()
        self.manager._middleware['session_write'].clear()
        with self.bound(), self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, 'gate_missing'):
            self.db.append_message('synthetic-session', 'user', 'safe')
        self.assert_no_begin()

    def test_policy_denial_does_not_reuse_model_output_permission(self):
        self.mandatory(allowed=False)
        self.plugin.gateway = PolicyAuthorizationGateway((PolicyRule('model.output', target='model:openai', operation='disclose', actor_id='alice'),))
        with self.bound(), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.db.append_message('synthetic-session', 'user', 'safe')
        self.assert_no_begin()

    def test_audit_failure_blocks_write_and_is_secret_safe(self):
        self.mandatory()
        self.plugin.audit.write.side_effect = RuntimeError('synthetic-private-audit-details')
        with self.bound(), self.assertRaises(self.engine.MandatoryMiddlewareError) as caught:
            self.db.append_message('synthetic-session', 'user', 'safe')
        self.assertNotIn('synthetic-private', str(caught.exception))
        self.assert_no_begin()

    def test_unmapped_direct_writers_block_before_mutation(self):
        self.mandatory()
        for action in (lambda: self.db.create_session('other', 'test'),
                       lambda: self.db.replace_messages('synthetic-session', []),
                       lambda: self.db.archive_and_compact('synthetic-session', []),
                       lambda: self.db.update_system_prompt('synthetic-session', 'new'),
                       lambda: self.db.clear_messages('synthetic-session')):
            with self.bound(), self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, 'session_write_unqualified'):
                action()
        self.assert_no_begin()

    def test_copied_context_cannot_authorize_worker_thread(self):
        self.mandatory()
        failures = []
        def worker():
            try:
                self.db.append_message('synthetic-session', 'user', 'safe')
            except Exception as error:
                failures.append(error)
        with self.bound():
            copied = copy_context()
            thread = Thread(target=lambda: copied.run(worker))
            thread.start()
            thread.join()
        self.assertEqual(len(failures), 1)
        self.assertIsInstance(failures[0], self.engine.MandatoryMiddlewareError)
        self.assert_no_begin()

    def test_child_async_task_cannot_inherit_write_authority(self):
        self.mandatory()
        async def parent():
            async def child():
                with self.assertRaises(self.engine.MandatoryMiddlewareError):
                    self.db.append_message('synthetic-session', 'user', 'safe')
            with self.bound():
                await asyncio.create_task(child())
        asyncio.run(parent())
        self.assert_no_begin()

    def test_normal_mode_retains_public_append_and_rewrite(self):
        row_id = self.db.append_message('synthetic-session', 'tool', 'safe', reasoning='legacy reasoning')
        self.assertIsInstance(row_id, int)
        self.assertEqual(self.rows()[0]['reasoning'], 'legacy reasoning')
        self.db.replace_messages('synthetic-session', [{'role': 'user', 'content': 'replacement'}])
        self.assertEqual(self.rows()[0]['content'], 'replacement')

    def test_candidate_has_no_production_marker(self):
        self.assertFalse(hasattr(self.engine, 'MAYA_GOVERNANCE_CONTRACT'))
        self.assertEqual(self.engine.SESSION_WRITE_CONTRACT, 'project-maya.hermes-session-write.v1')

    def test_incremental_flush_commit_updates_tracking_and_deduplicates(self):
        self.mandatory()
        messages = [{'role': 'user', 'content': 'safe'}, {'role': 'assistant', 'content': 'safe result'}]
        with self.bound():
            self.agent._flush_messages_to_session_db(messages, [])
            self.agent._flush_messages_to_session_db(messages, [])
        self.assertEqual(len(self.rows()), 2)
        self.assertEqual(self.agent._last_flushed_db_idx, 2)
        self.assertEqual(self.agent._flushed_db_message_ids, {id(msg) for msg in messages})
        self.assertEqual(sum(sql.startswith('BEGIN') for sql in self.statements), 1)

    def test_incremental_database_failure_preserves_flush_tracking(self):
        self.db._conn.execute("CREATE TRIGGER fail_second BEFORE INSERT ON messages WHEN NEW.content = 'fail' BEGIN SELECT RAISE(ABORT, 'synthetic-private-database-error'); END")
        self.db._conn.commit()
        self.mandatory()
        previous = {1234}
        self.agent._flushed_db_message_ids = previous
        self.agent._flushed_db_message_session_id = 'synthetic-session'
        self.agent._last_flushed_db_idx = 1
        with self.bound(), self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, 'session_write_failed') as caught:
            self.agent._flush_messages_to_session_db([{'role': 'user', 'content': 'safe'}, {'role': 'user', 'content': 'fail'}], [])
        self.assertNotIn('synthetic-private', str(caught.exception))
        self.assertEqual(self.rows(), [])
        self.assertIs(self.agent._flushed_db_message_ids, previous)
        self.assertEqual(previous, {1234})
        self.assertEqual(self.agent._last_flushed_db_idx, 1)
        self.host.host.logger.warning.assert_not_called()

    def test_incremental_later_row_denial_commits_nothing(self):
        self.mandatory()
        class Message(dict):
            pass
        denied = Message(role='assistant', content='safe')
        denied.tool_calls = [SimpleNamespace(function=SimpleNamespace(name='read_file', arguments='sk-proj-syntheticcredential0123456789'))]
        with self.bound(), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.agent._flush_messages_to_session_db([{'role': 'user', 'content': 'safe'}, denied], [])
        self.assertEqual(self.rows(), [])
        self.assertEqual(self.agent._last_flushed_db_idx, 0)
        self.assertFalse(hasattr(self.agent, '_flushed_db_message_ids'))
        self.assert_no_begin()

    def test_context_resets_and_actor_switch_is_denied(self):
        self.mandatory()
        with self.bound(), bind_request_identity('bob'), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.db.append_message('synthetic-session', 'user', 'safe')
        with bind_request_identity('alice'), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.db.append_message('synthetic-session', 'user', 'safe')
        self.assert_no_begin()

    def test_captured_same_thread_context_expires_after_request(self):
        self.mandatory()
        with self.bound():
            captured = copy_context()
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            captured.run(self.db.append_message, 'synthetic-session', 'user', 'safe')
        self.assert_no_begin()

    def test_incremental_flush_does_not_fall_back_to_unqualified_session_creation(self):
        self.mandatory()
        self.agent._session_db_created = False
        with self.bound(), self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, 'session_write_unqualified'):
            self.agent._flush_messages_to_session_db([{'role': 'user', 'content': 'safe'}], [])
        self.assertEqual(self.rows(), [])
        self.assertEqual(self.agent._last_flushed_db_idx, 0)
        self.assert_no_begin()


if __name__ == '__main__':
    unittest.main()
