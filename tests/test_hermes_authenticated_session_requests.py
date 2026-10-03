"""Authenticated Local API to real native SQLite; no provider or production host."""
import ast
from contextvars import copy_context
from dataclasses import replace
import json
import socket
import subprocess
from threading import Lock, Thread
from types import SimpleNamespace
import unittest
import urllib.request
from unittest.mock import Mock, patch

from project_maya.audit import LocalJsonlAuditSink

from project_maya.hermes_plugins.governance import RequestIdentity, bind_request_identity
from project_maya.hermes_plugins.session_requests import ACKNOWLEDGEMENT, CandidateSessionRequestBinding
from project_maya.local_api import BearerTokenAuthenticator, LocalAPI, LocalAPIRequest, build_local_api_http_server
from tests import test_hermes_compression_lock_patch as locks
from tests.test_phase1_local_api import StaticSecretStore


class TestAuthenticatedSessionRequests(unittest.TestCase):
    def setUp(self):
        self.loopback_connect = socket.create_connection
        self.native = locks.TestHermesCompressionLockPatch()
        self.addCleanup(self.native.doCleanups)
        self.native.setUp()
        self.native.mandatory()
        self.db = self.native.db
        self.engine = self.native.engine
        self.owner = RequestIdentity('alice', 'confidential')
        self.audit = LocalJsonlAuditSink(self.native.target / 'api-authentication.jsonl')
        self.binding = CandidateSessionRequestBinding(self.owner, 'synthetic-session', self.db.db_path,
            frozenset({'append'}), ACKNOWLEDGEMENT, audit_sink=self.audit)
        self.store = StaticSecretStore({'secret://local-api/token': 'synthetic-local-api-token'})
        self.auth = BearerTokenAuthenticator(self.store, actor_id='alice')
        self.agent = SimpleNamespace(run=Mock(side_effect=self.append))
        self.api = LocalAPI(agent=self.agent, runtime=SimpleNamespace(), authenticator=self.auth,
                            candidate_session_binding=self.binding)
        result = subprocess.run(['git', 'apply', '--whitespace=error', str(locks.ROOT / 'patches/hermes/0020-unqualified-gateway-session-routing.patch')],
                                cwd=self.native.target, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def append(self, message, **kwargs):
        self.db.append_message('synthetic-session', 'user', message)
        return 'accepted'

    def request(self, payload=None, token='synthetic-local-api-token', **kwargs):
        return self.api.handle(LocalAPIRequest('POST', '/v1/run',
            {'Authorization': 'Bearer ' + token, **kwargs},
            json.dumps(payload or {'input': 'safe input'}).encode()))

    def rows(self):
        return self.db.get_messages('synthetic-session')

    def test_authenticated_identity_reaches_native_gateway_and_sqlite(self):
        self.assertEqual(self.request().status_code, 200)
        self.assertEqual(self.rows()[0]['content'], 'safe input')
        self.agent.run.assert_called_once_with('safe input', idempotency_key=None, data_classification='confidential')

    def test_bad_missing_and_revoked_tokens_never_invoke_agent(self):
        self.assertEqual(self.request(token='wrong').status_code, 401)
        self.assertEqual(self.api.handle(LocalAPIRequest('POST', '/v1/run', body=b'{"input":"safe"}')).status_code, 401)
        self.store._values.clear()
        self.assertEqual(self.request().status_code, 401)
        self.agent.run.assert_not_called()
        self.assertEqual(self.rows(), [])

    def test_body_cannot_supply_identity_session_database_or_permissions(self):
        for key in ('actor_id', 'session_id', 'database', 'operations', 'request_id'):
            self.assertEqual(self.request({'input': 'safe', key: 'forged'}).status_code, 400)
        self.agent.run.assert_not_called()
        self.assertEqual(self.rows(), [])

    def test_headers_do_not_override_host_identity(self):
        self.assertEqual(self.request(**{'X-Actor-ID': 'mallory', 'X-Session-ID': 'other'}).status_code, 200)
        self.assertEqual(len(self.rows()), 1)

    def test_classification_cannot_be_downgraded(self):
        self.assertEqual(self.request({'input': 'safe', 'data_classification': 'public'}).status_code, 403)
        self.agent.run.assert_not_called()
        self.assertEqual(self.rows(), [])

    def test_authenticated_other_actor_cannot_use_owner_session(self):
        self.api._authenticator = BearerTokenAuthenticator(self.store, actor_id='mallory')
        self.assertEqual(self.request().status_code, 403)
        self.assertEqual(self.rows(), [])

    def test_boolean_only_authenticator_cannot_select_a_privileged_fallback(self):
        self.api._authenticator = SimpleNamespace(authenticate=lambda headers: True)
        self.assertEqual(self.request().status_code, 401)
        self.agent.run.assert_not_called()

    def test_wrong_runtime_actor_or_session_cannot_write(self):
        def wrong_actor(message, **kwargs):
            with bind_request_identity('mallory', 'confidential'):
                return self.append(message)
        self.agent.run.side_effect = wrong_actor
        self.assertEqual(self.request().status_code, 500)
        self.agent.run.side_effect = lambda message, **kwargs: self.db.append_message('other-session', 'user', message)
        self.assertEqual(self.request().status_code, 500)
        self.assertEqual(self.rows(), [])

    def test_expired_request_context_cannot_write_after_return(self):
        captured = []
        def capture(message, **kwargs):
            captured.append(copy_context())
            return self.append(message)
        self.agent.run.side_effect = capture
        self.assertEqual(self.request().status_code, 200)
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            captured[0].run(self.db.append_message, 'synthetic-session', 'user', 'late')
        self.assertEqual(len(self.rows()), 1)

    def test_failure_releases_scope_and_returns_only_fixed_error(self):
        self.agent.run.side_effect = RuntimeError('synthetic-local-api-token private-path')
        response = self.request()
        self.assertEqual(response.status_code, 500)
        self.assertNotIn('synthetic-local-api-token', response.json_bytes().decode())
        self.agent.run.side_effect = self.append
        self.assertEqual(self.request().status_code, 200)
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.db.append_message('synthetic-session', 'user', 'unbound')

    def test_concurrent_request_cannot_reuse_active_session_scope(self):
        responses = []
        with self.binding.authenticated_request(self.owner):
            thread = Thread(target=lambda: responses.append(self.request()))
            thread.start()
            thread.join(5)
            self.assertFalse(thread.is_alive())
        self.assertEqual(responses[0].status_code, 403)
        self.agent.run.assert_not_called()
        self.assertEqual(self.request().status_code, 200)

    def test_missing_native_contract_or_callback_stops_before_agent(self):
        with patch.object(self.engine, 'SESSION_WRITE_CONTRACT', 'unqualified'):
            self.assertEqual(self.request().status_code, 403)
        self.native.host.host.manager._middleware['session_write'] = []
        self.assertEqual(self.request().status_code, 403)
        self.agent.run.assert_not_called()

    def test_scope_requires_acknowledgement_and_preprovisioned_database(self):
        for changes in ({'acknowledgement': ''}, {'database': self.native.target / 'absent.db'}, {'operations': frozenset({'unknown'})}):
            with self.assertRaises(Exception):
                replace(self.binding, **changes)
        self.assertFalse((self.native.target / 'absent.db').exists())

    def test_authentication_audit_is_secret_safe_and_failure_blocks_dispatch(self):
        self.assertEqual(self.request({'input': 'safe input', 'idempotency_key': 'caller-key'}).status_code, 200)
        record = json.loads(self.audit.path.read_text())
        self.assertEqual(record['actor_id'], 'alice')
        self.assertTrue(self.agent.run.call_args.kwargs['idempotency_key'].startswith('sha256:'))
        self.assertTrue(record['idempotency_key'].startswith('sha256:'))
        for value in ('synthetic-local-api-token', 'synthetic-session', 'safe input', 'caller-key', str(self.db.db_path)):
            self.assertNotIn(value, self.audit.path.read_text())
        self.agent.run.reset_mock()
        with patch.object(self.audit, 'write', side_effect=RuntimeError('private error')):
            self.assertEqual(self.request().status_code, 403)
        self.agent.run.assert_not_called()
        self.assertEqual(len(self.rows()), 1)

    def test_unqualified_gateway_routes_stop_before_index_or_database_access(self):
        tree = ast.parse((self.native.target / 'gateway/session.py').read_text(encoding='utf-8'))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'SessionStore')
        methods = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in {'get_or_create_session', 'reset_session', 'switch_session'}]
        scope = {}
        module = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0), *methods], type_ignores=[])
        exec(compile(ast.fix_missing_locations(module), 'native-session-routing', 'exec'), scope)
        store = SimpleNamespace(_entries={'existing': 'unchanged'}, _save=Mock(), _db=Mock(), _generate_session_key=Mock())
        for name, args in (('get_or_create_session', (object(),)), ('reset_session', ('existing',)), ('switch_session', ('existing', 'other'))):
            with self.binding.authenticated_request(self.owner), self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, 'session_write_unqualified'):
                scope[name](store, *args)
        self.assertEqual(store._entries, {'existing': 'unchanged'})
        store._save.assert_not_called()
        store._generate_session_key.assert_not_called()
        self.assertEqual(store._db.mock_calls, [])
        # Ordinary mode keeps the complete native resume/no-op branches.
        entry = SimpleNamespace(suspended=False, resume_pending=True, session_id='synthetic-session')
        store._entries = {'existing': entry}
        store._lock = Lock()
        store._ensure_loaded_locked = Mock()
        store._generate_session_key.return_value = 'existing'
        scope['_now'] = lambda: 42
        with patch.object(self.engine, 'mandatory_middleware_enabled', return_value=False):
            self.assertIs(scope['get_or_create_session'](store, object()), entry)
            self.assertIsNone(scope['reset_session'](store, 'missing'))
            self.assertIs(scope['switch_session'](store, 'existing', 'synthetic-session'), entry)
        store._save.assert_called_once()
        self.assertEqual(entry.updated_at, 42)

    def test_loopback_http_authentication_binds_in_request_thread(self):
        server = build_local_api_http_server(self.api)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            request = urllib.request.Request(f'http://127.0.0.1:{server.server_address[1]}/v1/run',
                data=b'{"input":"safe HTTP input"}', headers={'Authorization': 'Bearer synthetic-local-api-token'}, method='POST')
            def connect(address, *args, **kwargs):
                self.assertEqual(address[0], '127.0.0.1')
                return self.loopback_connect(address, *args, **kwargs)
            with patch('socket.create_connection', side_effect=connect), urllib.request.urlopen(request, timeout=5) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(json.loads(response.read())['result'], 'accepted')
        finally:
            server.shutdown()
            server.server_close()
            thread.join(5)
        self.assertEqual(self.rows()[0]['content'], 'safe HTTP input')


if __name__ == '__main__':
    unittest.main()
