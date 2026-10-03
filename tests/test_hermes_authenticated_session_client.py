"""Source CLI authentication over real loopback HTTP and native session SQLite."""
from contextlib import contextmanager, redirect_stdout
from dataclasses import replace
from io import StringIO
import json
from threading import Thread
import unittest
from unittest.mock import Mock, patch

from project_maya.config import config_from_mapping
from project_maya.hermes_plugins.session_client import CandidateSessionClientError, main, run_authenticated_cli_request
from project_maya.hermes_plugins.session_requests import ACKNOWLEDGEMENT, REQUEST_BINDING_CONTRACT
from project_maya.local_api import LocalAPIRequest, build_local_api_http_server
from tests import test_hermes_authenticated_session_requests as requests_tests
from tests.test_phase0_contracts import valid_config_mapping


class TestAuthenticatedSessionClient(unittest.TestCase):
    def setUp(self):
        self.host = requests_tests.TestAuthenticatedSessionRequests()
        self.addCleanup(self.host.doCleanups)
        self.host.setUp()
        self.token = 'synthetic-local-api-token'

    @contextmanager
    def server(self):
        server = build_local_api_http_server(self.host.api)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        mapping = valid_config_mapping()
        mapping['deployment']['data_dir'] = str(self.host.native.target / 'data')
        mapping['local_api'] = {'bind': '127.0.0.1', 'port': server.server_address[1], 'remote_access': False}
        config = config_from_mapping(mapping)
        def connect(address, *args, **kwargs):
            self.assertEqual(address[0], '127.0.0.1')
            return self.host.loopback_connect(address, *args, **kwargs)
        try:
            with patch('socket.create_connection', side_effect=connect):
                yield config, mapping
        finally:
            server.shutdown()
            server.server_close()
            thread.join(5)
            self.assertFalse(thread.is_alive())

    def execute(self, config, token=None):
        return run_authenticated_cli_request(config, token=self.token if token is None else token,
            message='safe CLI input', acknowledgement=ACKNOWLEDGEMENT)

    def test_cli_request_authenticates_before_real_native_write(self):
        with self.server() as (config, _):
            self.assertEqual(self.execute(config), 'accepted')
        self.assertEqual(self.host.rows()[0]['content'], 'safe CLI input')

    def test_invalid_token_never_dispatches(self):
        with self.server() as (config, _), self.assertRaises(CandidateSessionClientError):
            self.execute(config, 'wrong')
        self.host.agent.run.assert_not_called()
        self.assertEqual(self.host.rows(), [])

    def test_unbound_server_is_not_a_fallback(self):
        self.host.api._candidate_session_binding = None
        with self.server() as (config, _), self.assertRaises(CandidateSessionClientError):
            self.execute(config)
        self.host.agent.run.assert_not_called()

    def test_required_binding_header_stops_direct_unbound_post(self):
        self.host.api._candidate_session_binding = None
        response = self.host.api.handle(LocalAPIRequest('POST', '/v1/run',
            {'Authorization': 'Bearer ' + self.token, 'X-Maya-Session-Binding': REQUEST_BINDING_CONTRACT},
            b'{"input":"safe"}'))
        self.assertEqual(response.status_code, 403)
        self.host.agent.run.assert_not_called()

    def test_binding_removed_between_status_and_run_does_not_execute(self):
        handle = self.host.api.handle
        def remove_after_status(request):
            response = handle(request)
            if request.path == '/v1/session-binding':
                self.host.api._candidate_session_binding = None
            return response
        with patch.object(self.host.api, 'handle', side_effect=remove_after_status), self.server() as (config, _):
            with self.assertRaises(CandidateSessionClientError):
                self.execute(config)
        self.host.agent.run.assert_not_called()

    def test_response_cannot_echo_token_or_secret_fields(self):
        for result in (self.token, {'api_key': 'synthetic'}):
            self.host.agent.run.side_effect = None
            self.host.agent.run.return_value = result
            with self.server() as (config, _), self.assertRaises(CandidateSessionClientError) as caught:
                self.execute(config)
            self.assertNotIn(self.token, str(caught.exception))

    def test_remote_host_and_header_injection_stop_before_transport(self):
        mapping = valid_config_mapping()
        mapping['local_api'] = {'bind': '127.0.0.1', 'port': 8765, 'remote_access': False}
        valid = config_from_mapping(mapping)
        config = replace(valid, local_api=replace(valid.local_api, bind='192.0.2.10'))
        with patch('project_maya.hermes_plugins.session_client.HTTPConnection') as connection:
            with self.assertRaises(CandidateSessionClientError):
                self.execute(config)
            with self.assertRaises(CandidateSessionClientError):
                self.execute(valid, 'unsafe\r\nheader')
        connection.assert_not_called()

    def test_redirect_is_rejected_without_followup_or_secret_disclosure(self):
        mapping = valid_config_mapping()
        mapping['local_api'] = {'bind': '127.0.0.1', 'port': 8765, 'remote_access': False}
        connection = Mock()
        connection.getresponse.return_value.status = 302
        with patch('project_maya.hermes_plugins.session_client.HTTPConnection', return_value=connection) as factory:
            with self.assertRaises(CandidateSessionClientError):
                self.execute(config_from_mapping(mapping))
        self.assertEqual(factory.call_count, 1)
        connection.request.assert_called_once()
        connection.getresponse.return_value.read.assert_not_called()

    def test_decoded_token_echo_is_rejected_before_post(self):
        mapping = valid_config_mapping()
        mapping['local_api'] = {'bind': '127.0.0.1', 'port': 8765, 'remote_access': False}
        connection = Mock()
        response = connection.getresponse.return_value
        response.status = 200
        response.read.return_value = json.dumps({'session_binding_contract': REQUEST_BINDING_CONTRACT,
            'qualification': 'source_candidate_only', 'result': self.token}).replace('-', '\\u002d').encode()
        with patch('project_maya.hermes_plugins.session_client.HTTPConnection', return_value=connection):
            with self.assertRaises(CandidateSessionClientError) as caught:
                self.execute(config_from_mapping(mapping))
        self.assertNotIn(self.token, str(caught.exception))
        connection.request.assert_called_once()

    def test_cli_entrypoint_reads_token_from_stdin_and_keeps_authority_at_server(self):
        output = StringIO()
        with self.server() as (_, mapping):
            config_path = self.host.native.target / 'client-config.json'
            request_path = self.host.native.target / 'client-request.txt'
            config_path.write_text(json.dumps(mapping), encoding='utf-8')
            request_path.write_text('safe CLI file input', encoding='utf-8')
            with patch('sys.stdin', StringIO(self.token + '\n')), redirect_stdout(output):
                code = main(['--config', str(config_path), '--request-file', str(request_path),
                             '--api-token-stdin', '--acknowledge', ACKNOWLEDGEMENT])
        self.assertEqual(code, 0)
        self.assertNotIn(self.token, output.getvalue())
        self.assertFalse(json.loads(output.getvalue())['production_qualified'])
        self.assertEqual(self.host.rows()[0]['content'], 'safe CLI file input')

    def test_cli_argument_errors_do_not_echo_credentials(self):
        output = StringIO()
        with redirect_stdout(output):
            code = main(['--unrecognized', self.token])
        self.assertEqual(code, 1)
        self.assertNotIn(self.token, output.getvalue())


if __name__ == '__main__':
    unittest.main()
