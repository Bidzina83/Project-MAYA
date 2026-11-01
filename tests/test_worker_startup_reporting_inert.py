"""Mocked startup-layer tests; no Win32 handles, native runtime or security setup."""
import ast
from contextlib import ExitStack
import io
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from project_maya.bridge import model_worker as worker
from project_maya.bridge.model_validation import wrong_model_request
from test_model_bridge_worker_inert import ATTEMPT, SID, CHANNEL, CANARY, OUTPUT, LITERALS, policy, CoordinatorFixture

ROOT=Path(__file__).resolve().parents[1]


def reporter(stderr):
    # Load only the reporting class, not the guarded product bootstrap/launch.
    tree=ast.parse((ROOT/'src/project_maya/windows_runtime/model_validation_worker_entry.py').read_bytes())
    node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='StartupDiagnostic')
    namespace={'sys':SimpleNamespace(stderr=stderr)}
    exec(compile(ast.Module(body=[node],type_ignores=[]),'startup_reporter_fixture','exec'),namespace)
    return namespace['StartupDiagnostic']()


class MemoryFile(io.BytesIO):
    def __init__(self, raw=b'', fault=None, descriptor=11):
        super().__init__(raw);self.fault=fault;self.descriptor=descriptor;self.closed_bytes=None
    def fileno(self):return self.descriptor
    def write(self, raw):
        if self.fault=='write':raise OSError('private request and path')
        return super().write(raw)
    def flush(self):
        if self.fault=='flush':raise OSError('private flush')
        return super().flush()
    def close(self):
        if not self.closed:self.closed_bytes=self.getvalue()
        super().close()
        if self.fault=='close':raise OSError('private close')


class StartupReporterTests(unittest.TestCase):
    def test_all_stages_and_allowed_types_are_bounded_and_message_free(self):
        for stage in reporter(io.StringIO()).stages:
            stream=io.StringIO();diagnostic=reporter(stream);diagnostic.mark(stage)
            diagnostic.fail(ValueError('SECRET_CANARY'))
            if stage=='ready_sent':self.assertEqual(stream.getvalue(),'')
            else:self.assertEqual(stream.getvalue(),'MAYA_WORKER_STARTUP_V1|'+stage+'|ValueError\n')
            self.assertNotIn('SECRET_CANARY',stream.getvalue());self.assertLess(len(stream.getvalue()),256)

    def test_unknown_error_type_redacted_and_report_is_single_use(self):
        class PrivateTenantError(Exception):pass
        stream=io.StringIO();diagnostic=reporter(stream)
        diagnostic.fail(PrivateTenantError('secret'));diagnostic.fail(ValueError('second'))
        self.assertEqual(stream.getvalue(),'MAYA_WORKER_STARTUP_V1|bootstrap_preflight|OtherError\n')

    def test_reporting_write_failure_cannot_raise_or_trigger_retry(self):
        class Broken:
            def write(self,raw):raise OSError('secret')
        diagnostic=reporter(Broken());diagnostic.fail(ValueError());diagnostic.fail(ValueError())
        self.assertTrue(diagnostic.sent)

    def test_python_and_CSharp_allowlists_match_exactly(self):
        text=(ROOT/'src/project_maya/windows_runtime/WorkerStartupCapture.cs').read_text()
        diagnostic=reporter(io.StringIO())
        stages=set(re.findall(r'"([^"]+)"',re.search(r'Stages=\{(.*?)\};',text,re.S).group(1)))
        errors=set(re.findall(r'"([^"]+)"',re.search(r'Errors=\{(.*?)\};',text,re.S).group(1)))
        self.assertEqual(stages,diagnostic.stages)
        self.assertEqual(errors,diagnostic.errors|{'OtherError','PreflightRejected'})


class StartupMainFixtures(unittest.TestCase):
    def setUp(self):
        self.stderr=io.StringIO();self.diagnostic=reporter(self.stderr)
        self.runtime=Path('C:/MayaInertReporting/runtime');self.host=self.runtime.parent/'host'
        self.config=dict(operator_sid=SID,attempt=ATTEMPT,channel_id=CHANNEL,utc_day='2026-10-31',canary=CANARY,fixture_text=OUTPUT)
        self.literals=LITERALS.read_bytes();self.opened=[];self.files={};self.fault=None;self.audit_fault=False
        self.peer=CoordinatorFixture()
        def modify(message):
            if message['type']=='model_dispatch':message['request']['body']=wrong_model_request(message['request']['body'].encode()).decode()
            return message
        self.peer.modify=modify

    def open(self,path,root,**kwargs):
        self.assertEqual(root,self.host);self.assertEqual(path.parent,root)
        self.opened.append(path.name)
        if self.fault==path.name:raise PermissionError('private host path')
        if path.name=='worker.json':
            raw=b'not json' if self.fault=='config_parse' else json.dumps(self.config).encode()
        elif path.name=='policy.json':raw=json.dumps(policy()).encode()
        else:raw=b''
        fault=self.fault if path.name=='request.json' and self.fault in ('write','flush','close') else None
        file=MemoryFile(raw,fault,12 if path.name=='audit.jsonl' else 11)
        if path.name=='request.json':
            write=file.write
            def capture_expected(data):
                count=write(data)
                self.peer.expected=bytes(data)
                return count
            file.write=capture_expected
        self.files[path.name]=file
        return file

    def run_main(self, *, wrong_route=False, wrong_attempt=False, wrong_body=False, expire_grant=False, revoke_grant=False, replay_grant=False, same_client_budget=False):
        flags=SimpleNamespace(**{n:getattr(sys.flags,n) for n in dir(sys.flags) if not n.startswith('_')})
        flags.isolated=flags.no_site=flags.dont_write_bytecode=1
        with ExitStack() as stack:
            stack.enter_context(patch.object(worker.sys,'version_info',(3,13,14)))
            stack.enter_context(patch.object(worker.sys,'flags',flags))
            stack.enter_context(patch.object(worker.os,'name','nt'))
            stack.enter_context(patch.object(worker,'__file__',str(self.runtime/'project_maya/bridge/model_worker.py')))
            stack.enter_context(patch.object(worker.Path,'cwd',return_value=self.host))
            stack.enter_context(patch.object(worker.Path,'read_bytes',return_value=self.literals))
            stack.enter_context(patch.object(worker,'open_private',side_effect=self.open))
            stack.enter_context(patch.object(worker,'PrivateChannel',return_value=self.peer))
            def distribution(name):
                if self.fault=='dependency':raise ImportError('private metadata')
                versions={'cryptography':'46.0.7','cffi':'2.0.0','pycparser':'3.0'}
                return SimpleNamespace(version=versions[name],locate_file=lambda _:self.runtime/'dependencies')
            stack.enter_context(patch.object(worker.importlib.metadata,'distribution',side_effect=distribution))
            def fsync(fd):
                if self.fault=='sync' and fd==11:raise OSError('private sync')
            stack.enter_context(patch.object(worker.os,'fsync',side_effect=fsync))
            stack.enter_context(patch.dict(sys.modules))
            sys.modules.pop('openai',None);sys.modules.pop('run_agent',None)
            return worker.main(wrong_model=not (wrong_route or wrong_attempt or wrong_body or expire_grant or revoke_grant or replay_grant or same_client_budget),wrong_route=wrong_route,
                wrong_attempt=wrong_attempt,wrong_body=wrong_body,expire_grant=expire_grant,revoke_grant=revoke_grant,replay_grant=replay_grant,same_client_budget=same_client_budget,startup=self.diagnostic)

    def test_budget_startup_main_preserves_four_positive_records_and_terminal_snapshot(self):
        from test_model_adapter_budget_inert import BudgetCoordinator
        self.peer=BudgetCoordinator()
        self.assertEqual(self.run_main(same_client_budget=True),0)
        self.assertEqual(self.stderr.getvalue(),'');self.assertTrue(self.diagnostic.ready)
        self.assertEqual(self.peer.sent[-1]['type'],'model_adapter_complete')
        records=[json.loads(line) for line in self.files['audit.jsonl'].closed_bytes.splitlines()]
        self.assertEqual(len(records),4)
        self.assertEqual(records[-1]['event_type'],'model_bridge.runtime_delivery')
        self.assertEqual(self.peer.sent[-1]['effects']['confirmed_runtime_releases'],1)

    def test_budget_terminal_failure_cannot_be_reported_as_completion(self):
        from test_model_adapter_budget_inert import BudgetCoordinator
        self.peer=BudgetCoordinator()
        with patch('project_maya.bridge.model_adapter_budget.finish_adapter_budget',side_effect=ValueError('private')):
            self.assertEqual(self.run_main(same_client_budget=True),3)
        self.assertEqual(self.stderr.getvalue(),'')
        self.assertEqual(self.peer.sent[-1]['type'],'model_runtime_ack')

    def test_replay_startup_main_retains_four_positive_records_and_one_denial(self):
        from test_model_lease_replay_inert import ReplayPeer
        from project_maya.bridge.model_lease_replay import ConsumedGrantBridge
        now=[0.0];self.peer=ReplayPeer()
        def advance(message):
            if self.peer.index>1:now[0]=self.peer.index*0.2
            return message
        self.peer.modify=advance
        def fixture_factory(*args,**kwargs):return ConsumedGrantBridge(*args,**kwargs,clock=lambda:now[0])
        with patch('project_maya.bridge.model_lease_replay.ConsumedGrantBridge',side_effect=fixture_factory):
            self.assertEqual(self.run_main(replay_grant=True),0)
        self.assertEqual(self.stderr.getvalue(),'');self.assertTrue(self.diagnostic.ready)
        self.assertEqual(self.opened,['worker.json','policy.json','audit.jsonl','request.json'])
        self.assertEqual(self.peer.sent[-1]['type'],'model_lease_consumed')
        records=[json.loads(line) for line in self.files['audit.jsonl'].closed_bytes.splitlines()]
        self.assertEqual(len(records),5);self.assertEqual(records[3]['event_type'],'model_bridge.runtime_delivery')
        self.assertEqual(records[4]['metadata']['runtime_released'],'1')

    def test_replay_setup_failure_stays_nonzero_and_failure_only(self):
        with patch('project_maya.bridge.model_lease_replay.ConsumedGrantBridge',side_effect=ValueError('private')):
            self.assertEqual(self.run_main(replay_grant=True),3)
        self.assertEqual(self.stderr.getvalue(),'MAYA_WORKER_STARTUP_V1|service_construct|ValueError\n')

    def test_revocation_startup_main_uses_same_files_and_two_records(self):
        from test_model_lease_revocation_inert import RevokePeer
        from project_maya.bridge.model_lease_revocation import RevokedGrantBridge
        now=[0.0];self.peer=RevokePeer()
        def advance(message):
            if message['type']=='model_revoke':now[0]=0.1
            if message['type']=='model_dispatch':now[0]=0.8
            return message
        self.peer.modify=advance
        def fixture_factory(*args,**kwargs):return RevokedGrantBridge(*args,**kwargs,clock=lambda:now[0])
        with patch('project_maya.bridge.model_lease_revocation.RevokedGrantBridge',side_effect=fixture_factory):
            self.assertEqual(self.run_main(revoke_grant=True),0)
        self.assertEqual(self.stderr.getvalue(),'');self.assertTrue(self.diagnostic.ready)
        self.assertEqual(self.opened,['worker.json','policy.json','audit.jsonl','request.json'])
        self.assertEqual(self.peer.sent[-1]['type'],'model_lease_revoked')
        records=[json.loads(line) for line in self.files['audit.jsonl'].closed_bytes.splitlines()]
        self.assertEqual([r['event_type'] for r in records],['model_bridge.grant_revoked','model_bridge.lease_revoked'])

    def test_revocation_setup_failure_preserves_failure_only_diagnostics(self):
        with patch('project_maya.bridge.model_lease_revocation.RevokedGrantBridge',side_effect=ValueError('private')):
            self.assertEqual(self.run_main(revoke_grant=True),3)
        self.assertEqual(self.stderr.getvalue(),'MAYA_WORKER_STARTUP_V1|service_construct|ValueError\n')

    def test_expiry_startup_main_uses_same_host_files_and_audit(self):
        from project_maya.bridge.model_lease_expiry import ExpiredGrantBridge
        now=[0.0]
        def advance(message):
            if message['type']=='model_dispatch':now[0]=2.1
            return message
        self.peer.modify=advance
        def fixture_factory(*args,**kwargs):return ExpiredGrantBridge(*args,**kwargs,clock=lambda:now[0])
        with patch('project_maya.bridge.model_lease_expiry.ExpiredGrantBridge',side_effect=fixture_factory):
            self.assertEqual(self.run_main(expire_grant=True),0)
        self.assertEqual(self.stderr.getvalue(),'');self.assertTrue(self.diagnostic.ready)
        self.assertEqual(self.opened,['worker.json','policy.json','audit.jsonl','request.json'])
        self.assertEqual(self.peer.sent[-1]['type'],'model_lease_expired')
        self.assertEqual(json.loads(self.files['audit.jsonl'].closed_bytes)['event_type'],'model_bridge.lease_expired')

    def test_expiry_setup_failure_is_not_accepted_as_expected_expiry(self):
        with patch('project_maya.bridge.model_lease_expiry.ExpiredGrantBridge',side_effect=ValueError('private')):
            self.assertEqual(self.run_main(expire_grant=True),3)
        self.assertEqual(self.stderr.getvalue(),'MAYA_WORKER_STARTUP_V1|service_construct|ValueError\n')

    def test_body_startup_uses_existing_files_and_single_named_rejection(self):
        from project_maya.bridge.model_body_validation import wrong_body_request
        def mutate(message):
            if message['type']=='model_dispatch':message['request']['body']=wrong_body_request(message['request']['body'].encode()).decode()
            return message
        self.peer.modify=mutate
        self.assertEqual(self.run_main(wrong_body=True),0)
        self.assertEqual(self.stderr.getvalue(),'');self.assertTrue(self.diagnostic.ready)
        self.assertEqual(self.peer.sent[-1]['type'],'model_body_rejected')
        self.assertEqual(self.opened,['worker.json','policy.json','audit.jsonl','request.json'])
        self.assertEqual(json.loads(self.files['audit.jsonl'].closed_bytes)['event_type'],'model_bridge.body_rejected')

    def test_body_constructor_failure_keeps_nonzero_exit_and_failure_reporting(self):
        with patch('project_maya.bridge.model_body_validation.WrongBodyBridge',side_effect=ValueError('private')):
            self.assertEqual(self.run_main(wrong_body=True),3)
        self.assertEqual(self.stderr.getvalue(),'MAYA_WORKER_STARTUP_V1|service_construct|ValueError\n')

    def test_attempt_startup_main_preserves_actual_config_and_outer_attempt(self):
        from project_maya.bridge.model_attempt_validation import mismatched_attempt
        def mutate(message):
            if message['type']=='model_dispatch':message['request']['attempt']=mismatched_attempt(self.config['attempt'])
            return message
        self.peer.modify=mutate
        self.assertEqual(self.run_main(wrong_attempt=True),0)
        self.assertEqual(self.stderr.getvalue(),'');self.assertTrue(self.diagnostic.ready)
        self.assertEqual(self.peer.sent[-1]['type'],'model_attempt_rejected')
        self.assertEqual(self.peer.sent[-1]['attempt'],self.config['attempt'])
        record=json.loads(self.files['audit.jsonl'].closed_bytes)
        self.assertEqual(record['event_type'],'model_bridge.attempt_rejected')
        self.assertEqual(record['actor_id'],'windows:'+SID)
        self.assertEqual(record['metadata']['attempt'],ATTEMPT)

    def test_attempt_service_setup_error_keeps_failure_only_reporting(self):
        with patch('project_maya.bridge.model_attempt_validation.WrongAttemptBridge',side_effect=ValueError('private')):
            self.assertEqual(self.run_main(wrong_attempt=True),3)
        self.assertEqual(self.stderr.getvalue(),'MAYA_WORKER_STARTUP_V1|service_construct|ValueError\n')

    def test_route_startup_main_uses_same_private_files_and_reporter(self):
        def mutate(message):
            if message['type']=='model_dispatch':message['request']['route']='maya.offline.model.v0'
            return message
        self.peer.modify=mutate
        self.assertEqual(self.run_main(wrong_route=True),0)
        self.assertEqual(self.stderr.getvalue(),'');self.assertTrue(self.diagnostic.ready)
        self.assertEqual(self.opened,['worker.json','policy.json','audit.jsonl','request.json'])
        self.assertEqual(self.peer.sent[-1]['type'],'model_route_rejected')
        record=json.loads(self.files['audit.jsonl'].closed_bytes)
        self.assertEqual(record['event_type'],'model_bridge.route_rejected')

    def test_route_startup_failure_keeps_failure_only_diagnostics(self):
        with patch('project_maya.bridge.model_route_validation.WrongRouteBridge',side_effect=ValueError('private')):
            self.assertEqual(self.run_main(wrong_route=True),3)
        self.assertEqual(self.stderr.getvalue(),'MAYA_WORKER_STARTUP_V1|service_construct|ValueError\n')

    def test_startup_main_with_real_serialized_config_reaches_normal_service(self):
        self.assertEqual(self.run_main(),0)
        self.assertEqual(self.stderr.getvalue(),'');self.assertTrue(self.diagnostic.ready)
        self.assertEqual(self.opened,['worker.json','policy.json','audit.jsonl','request.json'])
        self.assertEqual(len(self.files['request.json'].closed_bytes),2618)
        self.assertEqual(self.peer.sent[-1]['type'],'model_validation_rejected')

    def test_main_reports_exact_failure_stage_and_keeps_nonzero_exit(self):
        for fault,stage,code in (
            ('dependency','dependency_readback','ImportError'),
            ('worker.json','config_read','PermissionError'),('config_parse','config_read','ProtocolError'),
            ('policy.json','policy_read','PermissionError'),('audit.jsonl','audit_open','PermissionError'),
            ('request.json','request_open','PermissionError'),('write','request_write','OSError'),
            ('flush','request_flush','OSError'),('sync','request_sync','OSError'),('close','request_close','OSError')):
            self.setUp();self.fault=fault
            with self.subTest(fault=fault):
                self.assertEqual(self.run_main(),3)
                self.assertEqual(self.stderr.getvalue(),'MAYA_WORKER_STARTUP_V1|'+stage+'|'+code+'\n')
                self.assertFalse(self.diagnostic.ready)

    def test_service_constructor_failure_is_not_hidden(self):
        with patch('project_maya.bridge.model_validation.WrongModelBridge',side_effect=ValueError('private constructor')):
            self.assertEqual(self.run_main(),3)
        self.assertEqual(self.stderr.getvalue(),'MAYA_WORKER_STARTUP_V1|service_construct|ValueError\n')

    def test_ready_write_failure_is_not_readiness(self):
        self.peer.send=lambda _:(_ for _ in ()).throw(OSError('private pipe'))
        self.assertEqual(self.run_main(),3)
        self.assertEqual(self.stderr.getvalue(),'MAYA_WORKER_STARTUP_V1|ready_send|OSError\n')

    def test_post_ready_fault_is_not_mislabelled_startup(self):
        self.peer.receive=lambda:(_ for _ in ()).throw(RuntimeError('later private failure'))
        self.assertEqual(self.run_main(),3)
        self.assertEqual(self.stderr.getvalue(),'');self.assertTrue(self.diagnostic.ready)
