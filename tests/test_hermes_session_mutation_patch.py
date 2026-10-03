"""Native direct mutation descriptors and real SQLite destructive rollback."""
import ast
import subprocess

from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
from tests import test_hermes_session_write_patch as writes

ROOT = writes.ROOT


class TestHermesSessionMutationPatch(writes.TestHermesSessionWritePatch):
    def setUp(self):
        super().setUp()
        target = self.host.host.target
        applied = subprocess.run(['git', 'apply', '--whitespace=error', str(ROOT / 'patches/hermes/0016-native-session-mutation-descriptors.patch')],
                                 cwd=target, capture_output=True, text=True)
        self.assertEqual(applied.returncode, 0, applied.stderr)
        tree = ast.parse((target / 'hermes_state.py').read_text(encoding='utf-8'))
        tree.body = [n for n in tree.body if not (isinstance(n, ast.ImportFrom) and n.module in {'agent.memory_manager', 'hermes_constants'})]
        scope = {'__name__': 'native_mutation_state', 'sanitize_context': lambda value: value, 'get_hermes_home': lambda: target}
        exec(compile(tree, str(target / 'hermes_state.py'), 'exec'), scope)
        self.db.close()
        self.db = scope['SessionDB'](target / 'atomic.db')
        self.addCleanup(self.db.close)
        self.agent._session_db = self.db
        self.statements = []
        self.db._conn.set_trace_callback(self.statements.append)

    def mandatory(self, allowed=True):
        super().mandatory(allowed)
        if allowed:
            self.plugin.gateway = PolicyAuthorizationGateway(tuple(
                PolicyRule('session.write', target='session:synthetic-session', operation=operation, actor_id='alice')
                for operation in ('create', 'append', 'rewrite', 'compact', 'metadata', 'delete')
            ) + (PolicyRule('model.output', target='model:openai', operation='disclose', actor_id='alice'),))

    def snapshot(self):
        return (self.db.get_messages('synthetic-session', include_inactive=True),
                self.db.get_session('synthetic-session'),
                [tuple(row) for row in self.db._conn.execute('SELECT rowid, content FROM messages_fts ORDER BY rowid')])

    def seed(self):
        self.db.append_message('synthetic-session', 'user', 'original')
        self.statements.clear()

    def test_unmapped_direct_writers_block_before_mutation(self):
        self.mandatory()
        for action in (lambda: self.db.end_session('synthetic-session', 'done'),
                       lambda: self.db.update_session_model('synthetic-session', 'other-model')):
            with self.bound(), self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, 'session_write_unqualified'):
                action()
        self.assert_no_begin()

    def test_create_validates_exact_serialized_metadata(self):
        self.db._conn.execute("DELETE FROM sessions WHERE id = 'synthetic-session'")
        self.db._conn.commit()
        self.mandatory()
        with self.bound(operations=frozenset({'create'})):
            self.db.create_session('synthetic-session', 'test', model_config={'safe': 'value'}, system_prompt='safe prompt')
        self.assertEqual(self.db.get_session('synthetic-session')['system_prompt'], 'safe prompt')

    def test_sensitive_create_metadata_does_not_create_session(self):
        self.db._conn.execute("DELETE FROM sessions WHERE id = 'synthetic-session'")
        self.db._conn.commit()
        self.statements.clear()
        self.mandatory()
        with self.bound(operations=frozenset({'create'})), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.db.create_session('synthetic-session', 'test', model_config={'api_key': 'synthetic'})
        self.assertIsNone(self.db.get_session('synthetic-session'))
        self.assert_no_begin()

    def test_prompt_update_requires_metadata_permission(self):
        self.mandatory()
        with self.bound(operations=frozenset({'metadata'})):
            self.db.update_system_prompt('synthetic-session', 'safe snapshot')
        self.assertEqual(self.db.get_session('synthetic-session')['system_prompt'], 'safe snapshot')
        before = self.snapshot()
        with self.bound(), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.db.update_system_prompt('synthetic-session', 'not authorized')
        self.assertEqual(self.snapshot(), before)

    def test_denied_rewrite_and_compaction_preserve_transcript_flags_counters_and_fts(self):
        self.seed()
        before = self.snapshot()
        self.mandatory()
        for operation, method in (('rewrite', self.db.replace_messages), ('compact', self.db.archive_and_compact)):
            with self.bound(operations=frozenset({operation})), self.assertRaises(self.engine.MandatoryMiddlewareError):
                method('synthetic-session', [{'role': 'assistant', 'content': 'sk-proj-syntheticcredential0123456789'}])
            self.assertEqual(self.snapshot(), before)
            self.assert_no_begin()

    def test_rewrite_and_compaction_second_insert_failure_roll_back_destructive_changes(self):
        self.seed()
        self.db._conn.execute("CREATE TRIGGER fail_second BEFORE INSERT ON messages WHEN NEW.content = 'fail' BEGIN SELECT RAISE(ABORT, 'synthetic-private-database-error'); END")
        self.db._conn.commit()
        before = self.snapshot()
        self.mandatory()
        for operation, method in (('rewrite', self.db.replace_messages), ('compact', self.db.archive_and_compact)):
            with self.bound(operations=frozenset({operation})), self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, 'session_write_failed') as caught:
                method('synthetic-session', [{'role': 'user', 'content': 'safe'}, {'role': 'user', 'content': 'fail'}])
            self.assertNotIn('synthetic-private', str(caught.exception))
            self.assertEqual(self.snapshot(), before)

    def test_allowed_compaction_preserves_archived_history(self):
        self.seed()
        self.mandatory()
        with self.bound(operations=frozenset({'compact'})):
            count = self.db.archive_and_compact('synthetic-session', [{'role': 'assistant', 'content': 'summary'}])
        self.assertEqual(count, 1)
        self.assertEqual([row['content'] for row in self.rows()], ['summary'])
        self.assertEqual(len(self.db.get_messages('synthetic-session', include_inactive=True)), 2)
        self.assertEqual(self.db.get_session('synthetic-session')['message_count'], 1)

    def test_allowed_rewrite_and_explicit_clear_permission(self):
        self.seed()
        self.mandatory()
        with self.bound(operations=frozenset({'rewrite'})):
            self.db.replace_messages('synthetic-session', [{'role': 'user', 'content': 'replacement'}])
        self.assertEqual([row['content'] for row in self.rows()], ['replacement'])
        with self.bound(), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.db.clear_messages('synthetic-session')
        with self.bound(operations=frozenset({'delete'})):
            self.db.clear_messages('synthetic-session')
        self.assertEqual(self.rows(), [])
        self.assertEqual(self.db.get_session('synthetic-session')['message_count'], 0)
