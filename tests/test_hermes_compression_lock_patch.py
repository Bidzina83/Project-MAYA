"""Native compression locks and caller propagation with no provider or workers."""
import ast
from datetime import datetime
import os
import subprocess
from types import SimpleNamespace
import unittest
import uuid
from unittest.mock import Mock, patch

from tests import test_hermes_session_metadata_patch as metadata
from tests.test_hermes_caller_denial_patch import native_function

ROOT = metadata.ROOT


class TestHermesCompressionLockPatch(unittest.TestCase):
    def setUp(self):
        self.host = metadata.TestHermesSessionMetadataPatch()
        self.addCleanup(self.host.doCleanups)
        self.host.setUp()
        self.target = self.host.host.host.host.target
        result = subprocess.run(['git', 'apply', '--whitespace=error', str(ROOT / 'patches/hermes/0019-compression-lock-authorization.patch')],
                                cwd=self.target, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.engine = self.host.engine
        exec(compile((self.target / 'hermes_cli/middleware.py').read_text(encoding='utf-8'), 'native-lock-middleware', 'exec'), self.engine.__dict__)
        tree = ast.parse((self.target / 'hermes_state.py').read_text(encoding='utf-8'))
        tree.body = [n for n in tree.body if not (isinstance(n, ast.ImportFrom) and n.module in {'agent.memory_manager', 'hermes_constants'})]
        self.state_scope = {'__name__': 'native_lock_state', 'sanitize_context': lambda value: value, 'get_hermes_home': lambda: self.target}
        exec(compile(tree, str(self.target / 'hermes_state.py'), 'exec'), self.state_scope)
        self.host.db.close()
        self.db = self.state_scope['SessionDB'](self.target / 'atomic.db')
        self.addCleanup(self.db.close)
        self.host.db = self.db
        self.host.host.db = self.db
        self.statements = []
        self.db._conn.set_trace_callback(self.statements.append)
        self.logger = Mock()
        scope = {'logger': self.logger, 'os': os, 'datetime': datetime, 'uuid': uuid,
                 '_compression_lock_holder': lambda agent: 'synthetic-holder',
                 'estimate_request_tokens_rough': Mock(return_value=10), 'COMPACTION_STATUS': 'synthetic-status'}
        self.compress = native_function(self.target / 'agent/conversation_compression.py', 'compress_context', scope)
        self.agent = SimpleNamespace(_compression_feasibility_checked=True, compression_in_place=False,
            session_id='synthetic-session', model='test-model', platform='cli', log_prefix='',
            context_compressor=Mock(compression_count=1, _last_compress_aborted=True, _last_summary_error=None,
                                    _last_aux_model_failure_model=None),
            _memory_manager=None, _session_db=self.db, _emit_status=Mock(), _emit_warning=Mock(),
            _cached_system_prompt='safe prompt', _build_system_prompt=Mock(return_value='safe prompt'))
        self.agent.context_compressor.compress.return_value = [{'role': 'user', 'content': 'safe'}]
        self.messages = [{'role': 'user', 'content': 'safe input'}]

    def mandatory(self):
        self.host.host.mandatory()

    def bound(self, operations=frozenset({'metadata'})):
        return self.host.bound(operations)

    def locks(self):
        return [tuple(row) for row in self.db._conn.execute('SELECT * FROM compression_locks ORDER BY session_id')]

    def test_authorized_lock_ownership_and_idempotent_release(self):
        self.mandatory()
        with self.bound():
            self.assertTrue(self.db.try_acquire_compression_lock('synthetic-session', 'first'))
            self.assertFalse(self.db.try_acquire_compression_lock('synthetic-session', 'second'))
            self.db.release_compression_lock('synthetic-session', 'second')
            self.assertEqual(self.db.get_compression_lock_holder('synthetic-session'), 'first')
            self.db.release_compression_lock('synthetic-session', 'first')
            self.db.release_compression_lock('synthetic-session', 'first')
        self.assertEqual(self.locks(), [])

    def test_expired_lock_recovery_is_scoped_to_bound_session(self):
        self.db.try_acquire_compression_lock('other-session', 'other', ttl_seconds=-1)
        self.db.try_acquire_compression_lock('synthetic-session', 'stale', ttl_seconds=-1)
        other = self.db._conn.execute("SELECT * FROM compression_locks WHERE session_id='other-session'").fetchone()
        self.mandatory()
        with self.bound():
            self.assertTrue(self.db.try_acquire_compression_lock('synthetic-session', 'fresh'))
        self.assertEqual(tuple(self.db._conn.execute("SELECT * FROM compression_locks WHERE session_id='other-session'").fetchone()), tuple(other))

    def test_denied_acquire_and_release_do_not_begin_or_change_rows(self):
        self.db.try_acquire_compression_lock('synthetic-session', 'first')
        before = self.locks()
        self.statements.clear()
        self.mandatory()
        for action in (lambda: self.db.try_acquire_compression_lock('synthetic-session', 'second'),
                       lambda: self.db.release_compression_lock('synthetic-session', 'first')):
            with self.bound(frozenset({'append'})), self.assertRaises(self.engine.MandatoryMiddlewareError):
                action()
            self.assertEqual(self.locks(), before)
        self.assertFalse(any(sql.startswith('BEGIN') for sql in self.statements))

    def test_secret_holder_and_nonfinite_expiry_are_denied(self):
        self.mandatory()
        with self.bound():
            for holder, ttl in (('sk-proj-syntheticcredential0123456789', 300), ('safe', float('inf'))):
                with self.assertRaises(self.engine.MandatoryMiddlewareError):
                    self.db.try_acquire_compression_lock('synthetic-session', holder, ttl)
        self.assertEqual(self.locks(), [])
        self.assertFalse(any(sql.startswith('BEGIN') for sql in self.statements))

    def test_sql_failure_rolls_back_expired_lock_reclamation(self):
        self.db.try_acquire_compression_lock('synthetic-session', 'stale', ttl_seconds=-1)
        before = self.locks()
        self.db._conn.execute("CREATE TRIGGER fail_lock BEFORE INSERT ON compression_locks BEGIN SELECT RAISE(ABORT, 'synthetic-private-error'); END")
        self.db._conn.commit()
        self.mandatory()
        with self.bound(), self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, 'session_write_failed') as caught:
            self.db.try_acquire_compression_lock('synthetic-session', 'fresh')
        self.assertNotIn('synthetic-private', str(caught.exception))
        self.assertEqual(self.locks(), before)

    def test_real_caller_denial_stops_compressor_and_fallback(self):
        self.mandatory()
        with self.bound(frozenset({'append'})), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.compress(self.agent, self.messages, None)
        self.agent.context_compressor.compress.assert_not_called()
        self.logger.warning.assert_not_called()
        self.assertEqual(self.locks(), [])

    def test_missing_or_broken_lock_storage_stops_without_raw_diagnostics(self):
        self.mandatory()
        for db in (None, SimpleNamespace(), Mock(try_acquire_compression_lock=Mock(side_effect=RuntimeError('synthetic-private-error')))):
            self.agent._session_db = db
            with self.bound(), self.assertRaises(self.engine.MandatoryMiddlewareError) as caught:
                self.compress(self.agent, self.messages, None)
            self.assertNotIn('synthetic-private', str(caught.exception))
        self.agent.context_compressor.compress.assert_not_called()
        self.logger.warning.assert_not_called()

    def test_contention_stops_before_compression_without_releasing_foreign_lock(self):
        self.db.try_acquire_compression_lock('synthetic-session', 'other')
        before = self.locks()
        self.mandatory()
        with self.bound(), self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, 'session_lock_busy'):
            self.compress(self.agent, self.messages, None)
        self.assertEqual(self.locks(), before)
        self.agent.context_compressor.compress.assert_not_called()

    def test_aborted_summary_releases_real_native_lock(self):
        self.mandatory()
        with self.bound():
            result = self.compress(self.agent, self.messages, None)
        self.assertEqual(result[0], self.messages)
        self.assertEqual(self.locks(), [])
        self.agent.context_compressor.compress.assert_called_once()

    def test_release_denial_is_not_suppressed(self):
        self.mandatory()
        denial = self.engine.MandatoryMiddlewareError('callback_failed')
        with self.bound(), patch.object(self.db, 'release_compression_lock', side_effect=denial):
            with self.assertRaises(self.engine.MandatoryMiddlewareError) as caught:
                self.compress(self.agent, self.messages, None)
        self.assertIs(caught.exception, denial)
        self.assertEqual(len(self.locks()), 1)
        self.logger.debug.assert_not_called()

    def test_ordinary_broken_lock_caller_retains_native_fallback(self):
        self.agent._session_db = SimpleNamespace()
        self.assertEqual(self.compress(self.agent, self.messages, None)[0], self.messages)
        self.agent.context_compressor.compress.assert_called_once()
        self.logger.warning.assert_called_once()

    def test_missing_binding_or_callback_and_wrong_session_block_lock_writes(self):
        self.mandatory()
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.db.try_acquire_compression_lock('synthetic-session', 'first')
        with self.bound(), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.db.try_acquire_compression_lock('other-session', 'first')
        self.host.host.manager._middleware['session_write'] = []
        with self.bound(), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.db.try_acquire_compression_lock('synthetic-session', 'first')
        self.assertEqual(self.locks(), [])
        self.assertFalse(any(sql.startswith('BEGIN') for sql in self.statements))

    def test_summary_denial_propagates_and_releases_real_lock(self):
        self.mandatory()
        denial = self.engine.MandatoryMiddlewareError('callback_failed')
        self.agent.context_compressor.compress.side_effect = denial
        with self.bound(), self.assertRaises(self.engine.MandatoryMiddlewareError) as caught:
            self.compress(self.agent, self.messages, None)
        self.assertIs(caught.exception, denial)
        self.assertEqual(self.locks(), [])

    def test_invalid_holder_and_lock_lifetime_stop_before_transaction(self):
        self.mandatory()
        with self.bound():
            for holder, ttl in (('', 300), (None, 300), ('safe', 0), ('safe', -1), ('safe', True), ('safe', '300')):
                with self.assertRaises(self.engine.MandatoryMiddlewareError):
                    self.db.try_acquire_compression_lock('synthetic-session', holder, ttl)
            with self.assertRaises(self.engine.MandatoryMiddlewareError):
                self.db.release_compression_lock('synthetic-session', '')
        self.assertEqual(self.locks(), [])
        self.assertFalse(any(sql.startswith('BEGIN') for sql in self.statements))


if __name__ == '__main__':
    unittest.main()
