"""Worker/client/transport fixtures without Hermes or native Windows calls."""
import io
import json
import hashlib
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from project_maya.bridge.audit import RequiredAudit
from project_maya.bridge.host_files import HostDocument, HostFileError, open_private
from project_maya.bridge.protocol import Decoder, ProtocolError, encode
from project_maya.bridge.service import DocumentBridge, RESOURCE
from project_maya.bridge.transport import PrivateChannel
from project_maya.bridge.worker import CASES, serve
from project_maya.hermes_plugins.bridge import BridgeClient, TOOL, SCHEMA


class TransportTests(unittest.TestCase):
    def test_complete_receive_and_write(self):
        destination = io.BytesIO()
        channel = PrivateChannel(io.BytesIO(encode({"x": 1})), destination)
        self.assertEqual(channel.receive(), {"x": 1})
        channel.send({"answer": True})
        self.assertEqual(Decoder().feed(destination.getvalue()), [{"answer": True}])

    def test_trailing_header_rejected(self):
        channel = PrivateChannel(io.BytesIO(), io.BytesIO())
        with self.assertRaises(ProtocolError):
            channel.send_frame(encode({}) + b'\x01')

    def test_service_frames_consume_budget(self):
        channel = PrivateChannel(io.BytesIO(), io.BytesIO())
        channel._encoder.total = 131071
        with self.assertRaises(ProtocolError):
            channel.send_frame(encode({}))
        self.assertTrue(channel.closed)

    def test_short_write_and_eof_close(self):
        destination = Mock()
        destination.write.return_value = 0
        channel = PrivateChannel(io.BytesIO(), destination)
        with self.assertRaises(ProtocolError):
            channel.send({})
        self.assertTrue(channel.closed)
        with self.assertRaises(ProtocolError):
            PrivateChannel(io.BytesIO(encode({})[:-1]), io.BytesIO()).receive()


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.attempt = 'a'*32
        self.channel = Mock()
        self.client = BridgeClient(self.channel, self.attempt)
        self.grant = dict(v=1, type='grant', attempt=self.attempt, lease='b'*64,
                          ttl_ms=2000, next_seq=1, operation='document.read', resource=RESOURCE)
        self.response = dict(v=1, type='response', attempt=self.attempt, seq=1,
                             status='ok', code='bridge.document_read', data={'text': 'synthetic'})
        self.channel.receive.return_value = self.response

    def test_exact_tool_handler(self):
        self.client.bind_grant(self.grant)
        result = json.loads(self.client.handle({'resource': RESOURCE}))
        self.assertEqual(result, self.response)
        self.assertNotIn('actor_id', self.channel.send.call_args.args[0])
        self.assertEqual(json.loads(self.client.handle({'resource': RESOURCE})), {'error':'bridge.unavailable'})

    def test_wrong_target_never_sends(self):
        self.assertEqual(json.loads(self.client.handle({'resource': '../secret'})), {'error':'bridge.denied'})
        self.channel.send.assert_not_called()

    def test_grant_and_response_schema(self):
        for key, value in (('ttl_ms', True), ('lease', 'secret'), ('next_seq', True), ('attempt', 'wrong')):
            grant = dict(self.grant, **{key:value})
            with self.assertRaises(ProtocolError):
                self.client.bind_grant(grant)
        for key, value in (('seq',2), ('data',{'text':'x'*1025}), ('v',True), ('code','private exception')):
            self.client.bind_grant(self.grant)
            self.channel.receive.return_value = dict(self.response, **{key:value})
            self.assertEqual(json.loads(self.client.handle({'resource':RESOURCE})), {'error':'bridge.unavailable'})

    def test_registration_uses_existing_registry(self):
        registry = Mock()
        registry.get_entry.side_effect = [None, SimpleNamespace(handler=self.client.handle, toolset='maya_bridge')]
        self.client.register(registry)
        self.assertEqual(registry.register.call_args.kwargs['schema'], SCHEMA)
        self.assertFalse(registry.register.call_args.kwargs['override'])
        registry.get_entry.side_effect = None
        registry.get_entry.return_value = object()
        with self.assertRaises(ProtocolError):
            self.client.register(registry)


class WorkerTests(unittest.TestCase):
    def test_schedule_matches_approved_successor(self):
        root=Path(__file__).resolve().parents[1]
        contract=json.loads((root/'docs/architecture/maya_authorization_bridge_v1_tests_10.json').read_text())
        self.assertEqual(list(CASES),contract['native_case_order'])
        self.assertEqual(contract['native_case_count'],10)
        self.assertEqual(sum(x['expected_document_reads'] for x in contract['native_cases']),2)
        self.assertEqual(sum(x['expected_document_releases'] for x in contract['native_cases']),1)
        self.assertEqual({x['id'] for x in contract['local_required_cases']} & {'N09','N11'}, {'N09','N11'})

    def test_all_ten_cases_real_policy_and_core(self):
        attempt, sid, channel_id = 'a'*32, 'S-1-5-21-1-2-3-500', 'b'*64
        config = dict(operator_sid=sid, attempt=attempt, channel_id=channel_id, document_sha256='c'*64)
        rules = [dict(capability='file.read', target=RESOURCE, operation='read', actor_id='windows:'+sid),
                 dict(capability='file.disclose', target='runtime:'+attempt, operation='release', actor_id='windows:'+sid)]
        clock = Mock(return_value=0)
        document = SimpleNamespace(opens=0)
        def read():
            document.opens += 1
            return b'synthetic'
        document.read = read
        class Channel:
            index = 0
            phase = 'issue'
            grant = old_token = None
            replies = []
            def send(self, message):
                self.replies.append(message)
                if message['type'] == 'grant_reply':
                    self.grant = message['grant']
                    if self.index == 0: self.old_token = self.grant['lease']
                    self.phase = 'dispatch'
                elif message['type'] == 'dispatch_reply':
                    self.phase = 'observed'
                elif message['type'] == 'delivery_ack':
                    self.index += 1
                    self.phase = 'issue'
            def receive(self):
                if self.index == len(CASES):
                    return dict(v=1,type='shutdown',attempt=attempt)
                case = CASES[self.index]
                identity = dict(v=1,attempt=attempt,request_id=format(self.index+1,'032x'))
                if self.phase == 'observed':
                    return dict(identity,type='delivery_result',case=case,delivered=case=='N01')
                if self.phase == 'issue':
                    return dict(identity,type='issue',case=case)
                if case == 'N02': return dict(identity,type='no_request')
                request = dict(v=1,type='request',attempt=attempt,lease=self.grant['lease'],seq=self.grant['next_seq'],
                               operation='document.read',resource=RESOURCE)
                if case == 'N04': request['resource']='wrong'
                if case == 'N05': request['actor_id']='admin'
                if case == 'N06': request['lease']=self.old_token
                if case == 'N07': clock.return_value += 2.1
                if case == 'N12': request['operation']='execute'
                return dict(identity,type='dispatch',request=request)
        channel = Channel()
        audit = RequiredAudit(io.BytesIO())
        audit.write = Mock()
        def service_factory(*args):
            return DocumentBridge(*args, clock=clock)
        with patch('project_maya.bridge.worker.open_private', return_value=io.BytesIO(json.dumps({'allow':rules}).encode())), \
             patch('project_maya.bridge.worker.HostDocument', return_value=document), \
             patch('project_maya.bridge.worker.DocumentBridge', side_effect=service_factory):
            self.assertEqual(serve(channel, Path('host'), config, audit), 0)
        effects = [x['effects'] for x in channel.replies if x['type']=='dispatch_reply']
        self.assertEqual([x['case'] for x in effects], list(CASES))
        self.assertEqual(sum(x['reads'] for x in effects), 2)
        self.assertEqual(sum(x['prepared_releases'] for x in effects), 1)
        self.assertEqual(effects[0]['prepared_content_bytes'], 9)
        self.assertEqual(channel.replies[-1]['type'], 'worker_complete')

    def test_host_reader_requires_verified_digest(self):
        reader = HostDocument(Path('host'), 'a'*64)
        with patch('project_maya.bridge.host_files.open_private', return_value=io.BytesIO(b'wrong')):
            with self.assertRaises(HostFileError):
                reader.read()
        self.assertEqual(reader.opens, 1)

    def test_host_handle_flags_paths_links_and_sizes(self):
        root = Path('C:/MayaHost').absolute()
        path = root / 'document.txt'
        api = Mock()
        api.CreateFileW.return_value = 123
        api.GetFinalPathNameByHandleW.side_effect = lambda handle, buffer, size, flags: self.final_name(buffer, path)
        def info(handle, ptr):
            ptr._obj.attributes = 0
            ptr._obj.links = 1
            ptr._obj.size_high = 0
            ptr._obj.size_low = 8
            return True
        api.GetFileInformationByHandle.side_effect = info
        stream = io.BytesIO(b'fixture')
        with patch('project_maya.bridge.host_files.ctypes.WinDLL', return_value=api), \
             patch('msvcrt.open_osfhandle', return_value=1234), \
             patch('project_maya.bridge.host_files.os.fdopen', return_value=stream):
            self.assertIs(open_private(path, root), stream)
        self.assertEqual(api.CreateFileW.call_args.args[2], 0)
        self.assertEqual(api.CreateFileW.call_args.args[4:6], (3, 0x00200000))
        for flag, links, high, low in ((0x400,1,0,8),(0x10,1,0,8),(0,2,0,8),(0,1,1,0),(0,1,0,1025)):
            def bad_info(handle, ptr):
                ptr._obj.attributes,ptr._obj.links,ptr._obj.size_high,ptr._obj.size_low=flag,links,high,low
                return True
            api.GetFileInformationByHandle.side_effect = bad_info
            with patch('project_maya.bridge.host_files.ctypes.WinDLL', return_value=api):
                with self.assertRaises(HostFileError):
                    open_private(path, root)
        api.GetFileInformationByHandle.side_effect = info
        api.GetFinalPathNameByHandleW.side_effect = lambda handle, buffer, size, flags: self.final_name(buffer, root/'other.txt')
        with patch('project_maya.bridge.host_files.ctypes.WinDLL', return_value=api):
            with self.assertRaises(HostFileError):
                open_private(path, root)
        self.assertGreaterEqual(api.CloseHandle.call_count, 6)

    @staticmethod
    def final_name(buffer, path):
        buffer.value = '\\\\?\\'+str(path)
        return len(buffer.value)


if __name__ == '__main__':
    unittest.main()
