"""M03a in-memory source checks, never native Hermes/SDK/security execution."""
import copy
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch

from project_maya.bridge.audit import RequiredAudit
from project_maya.bridge.model_service import ModelDenied, OfflineModelBridge, digest
from project_maya.bridge.model_validation import WrongModelBridge, verify_validation_audit, wrong_model_request
from project_maya.bridge.model_worker import serve_model
from project_maya.bridge.protocol import ProtocolError
from project_maya.bridge.service import HostBinding
from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins.model_bridge import WrongModelChannelClient
from test_model_bridge_worker_inert import ATTEMPT, CANARY, CHANNEL, LITERALS, OUTPUT, SID, CoordinatorFixture, expected_request, policy


class ValidationTests(unittest.TestCase):
    def setUp(self):
        sync=patch('project_maya.bridge.audit.os.fsync');sync.start();self.addCleanup(sync.stop)
        self.records=[];self.stream=Mock()
        self.stream.write.side_effect=lambda raw:self.records.append(json.loads(raw)) or len(raw)
        self.audit=RequiredAudit(self.stream);self.peer=CoordinatorFixture()
        self.config=dict(operator_sid=SID,attempt=ATTEMPT,channel_id=CHANNEL,utc_day='2026-10-24',canary=CANARY,fixture_text=OUTPUT)
        self.change=lambda raw:wrong_model_request(raw)
        def modify(message):
            if message['type']=='model_dispatch':
                message['request']['body']=self.change(message['request']['body'].encode()).decode()
            return message
        self.peer.modify=modify

    def run_worker(self, **kwargs):
        return serve_model(self.peer,self.config,kwargs.pop('rules',policy()),LITERALS.read_bytes(),
            self.audit,self.peer.write_expected,wrong_model=True,**kwargs)

    def raw(self):return b''.join(json.dumps(r).encode()+b'\n' for r in self.records)
    def verify(self, raw=None):
        return verify_validation_audit(self.raw() if raw is None else raw,HostBinding(SID,ATTEMPT,CHANNEL),
            self.peer.sent[0]['service_request_id'],format(2,'032x'),expected_request(),
            wrong_model_request(expected_request()),digest(OUTPUT.encode()))

    def test_fixed_mutation_changes_only_model(self):
        original=expected_request();mutant=wrong_model_request(original)
        a=json.loads(original);b=json.loads(mutant)
        self.assertEqual(b.pop('model'),'maya-offline-wire-v0');a.pop('model')
        self.assertEqual(a,b);self.assertEqual(len(original),len(mutant))

    def test_unreviewed_original_format_or_model_rejected(self):
        original=expected_request()
        for raw in (b'{}',original.replace(b'wire-v1',b'wire-v0'),json.dumps(json.loads(original)).encode()):
            with self.subTest(raw=raw[:20]),self.assertRaises((ProtocolError,ModelDenied)):wrong_model_request(raw)

    def test_valid_request_positive_uses_existing_gateway_on_fresh_service(self):
        bridge=OfflineModelBridge(HostBinding(SID,ATTEMPT,CHANNEL),
            PolicyAuthorizationGateway(tuple(PolicyRule(**r) for r in policy()['allow'])),self.audit,expected_request(),OUTPUT)
        grant=bridge.issue()
        reply=bridge.prepare_runtime(dict(v=1,type='model_request',attempt=ATTEMPT,route='maya.offline.model.v1',
            lease=grant['lease'],seq=1,method='POST',path='/v1/chat/completions',body=expected_request().decode()),CHANNEL)
        self.assertEqual(bridge.dispatches,1);self.assertEqual(bridge.gateway_calls,2)
        self.assertEqual(reply['status'],'ok');bridge.close()

    def test_worker_exact_boundary_and_ledger_before_gateway(self):
        result=self.run_worker()
        self.assertEqual(result['case'],'M03a');self.assertEqual(result['stage'],'request_model')
        for key in ('gateway_calls','dispatches','runtime_prepared','runtime_released','operator_prepared','operator_released'):
            self.assertEqual(result[key],'0')
        self.assertEqual(self.verify(),1)
        self.assertEqual([m['type'] for m in self.peer.sent],['model_worker_ready','model_grant_reply','model_validation_rejected'])
        self.assertNotIn(CANARY,self.raw().decode())

    def test_gateway_is_not_called_in_negative(self):
        with patch.object(PolicyAuthorizationGateway,'authorize',side_effect=AssertionError('must not call')) as call:
            self.run_worker();call.assert_not_called()

    def test_M02_policy_cannot_mask_validation_failure(self):
        with self.assertRaises(ProtocolError):self.run_worker(rules={'allow':policy()['allow'][1:]})
        self.assertEqual(self.peer.sent,[])

    def test_incompatible_and_non_boolean_modes_rejected(self):
        with self.assertRaises(ProtocolError):self.run_worker(deny_egress=True)
        for mode in (1,None,'M03a'):
            with self.subTest(mode=mode),self.assertRaises(ProtocolError):
                serve_model(self.peer,self.config,policy(),LITERALS.read_bytes(),self.audit,self.peer.write_expected,wrong_model=mode)

    def test_valid_unmutated_request_is_not_negative_pass(self):
        self.change=lambda raw:raw
        with self.assertRaises(ProtocolError):self.run_worker()
        self.assertNotIn('model_validation_rejected',[m['type'] for m in self.peer.sent])

    def test_second_field_mutation_does_not_pass(self):
        def change(raw):
            body=json.loads(wrong_model_request(raw));body['max_tokens']=31
            return json.dumps(body,ensure_ascii=False,separators=(',',':')).encode()
        self.change=change
        with self.assertRaises(ProtocolError):self.run_worker()

    def test_wrong_route_attempt_lease_or_extra_field_not_model_rejection(self):
        original_modify=self.peer.modify
        for key in ('route','attempt','lease','extra'):
            self.peer=CoordinatorFixture()
            def modify(message):
                message=original_modify(message)
                if message['type']=='model_dispatch':message['request'][key]='wrong'
                return message
            self.peer.modify=modify
            with self.subTest(key=key),self.assertRaises(ProtocolError):self.run_worker()
            self.assertNotIn('model_validation_rejected',[m['type'] for m in self.peer.sent])

    def test_missing_command_binding_rejected(self):
        service=WrongModelBridge(HostBinding(SID,ATTEMPT,CHANNEL),PolicyAuthorizationGateway(()),self.audit,expected_request(),OUTPUT)
        with self.assertRaises(ProtocolError):service.metadata()
        service.bind_command('1'*32)
        with self.assertRaises(ProtocolError):service.bind_command('2'*32)
        service.close()

    def test_unknown_exception_cannot_be_reported_as_validation(self):
        with patch('project_maya.bridge.model_service.checked_request',side_effect=RuntimeError('private')):
            with self.assertRaises(RuntimeError):self.run_worker()
        self.assertNotIn('private',json.dumps(self.peer.sent))

    def test_audit_faults_never_return_validation_reply(self):
        for fault in ('short','write','flush','sync'):
            self.peer=CoordinatorFixture()
            def mutate(message):
                if message['type']=='model_dispatch':message['request']['body']=wrong_model_request(message['request']['body'].encode()).decode()
                return message
            self.peer.modify=mutate;self.audit=RequiredAudit(self.stream)
            self.stream.write.side_effect=lambda raw:len(raw);self.stream.flush.side_effect=None
            with patch('project_maya.bridge.audit.os.fsync') as sync:
                if fault=='short':self.stream.write.side_effect=lambda raw:len(raw)-1
                elif fault=='write':self.stream.write.side_effect=OSError('secret')
                elif fault=='flush':self.stream.flush.side_effect=OSError('secret')
                else:sync.side_effect=OSError('secret')
                with self.subTest(fault=fault),self.assertRaises(ProtocolError):self.run_worker()
                self.assertTrue(self.audit.failed)
                self.assertNotIn('model_validation_rejected',[m['type'] for m in self.peer.sent])

    def test_ledger_bindings_cannot_be_rebound_or_omitted(self):
        self.run_worker();original=copy.deepcopy(self.records[0])
        for key in original['metadata']:
            self.records[0]=copy.deepcopy(original);self.records[0]['metadata'][key]='wrong'
            with self.subTest(key=key),self.assertRaises(ProtocolError):self.verify()
        for key in original:
            self.records[0]=copy.deepcopy(original);del self.records[0][key]
            with self.subTest(key=key),self.assertRaises(ProtocolError):self.verify()
        self.records[0]=original
        for raw in (b'',self.raw()[:-1],self.raw()*2,b'\xff\n',b'x'*131073):
            with self.subTest(length=len(raw)),self.assertRaises((ProtocolError,UnicodeError)):self.verify(raw)

    def test_failed_or_unreached_stage_cannot_be_evidence(self):
        service=WrongModelBridge(HostBinding(SID,ATTEMPT,CHANNEL),PolicyAuthorizationGateway(()),self.audit,expected_request(),OUTPUT)
        service.bind_command('1'*32);service.close()
        with self.assertRaises(ProtocolError):service.evidence()

    def test_expiry_or_revocation_is_not_model_validation(self):
        for expired in (True,False):
            now=[0.0]
            service=WrongModelBridge(HostBinding(SID,ATTEMPT,CHANNEL),PolicyAuthorizationGateway(()),
                self.audit,expected_request(),OUTPUT,clock=lambda:now[0])
            service.bind_command('1'*32);grant=service.issue()
            if expired:now[0]=3.0
            else:service.revoke()
            request=dict(v=1,type='model_request',attempt=ATTEMPT,route='maya.offline.model.v1',
                lease=grant['lease'],seq=1,method='POST',path='/v1/chat/completions',body=wrong_model_request(expected_request()).decode())
            with self.assertRaises(ModelDenied):service.prepare_runtime(request,CHANNEL)
            with self.assertRaises(ProtocolError):service.evidence()
            self.assertEqual(service.gateway_calls,0);self.assertFalse(service.validation_recorded)

    def test_unrelated_exception_after_ready_is_not_validation_rejection(self):
        from project_maya.bridge.model_service import checked_request
        mutant=wrong_model_request(expected_request())
        def fail_only_at_mutant(raw):
            if raw==mutant:raise RuntimeError('private late error')
            return checked_request(raw)
        with patch('project_maya.bridge.model_service.checked_request',side_effect=fail_only_at_mutant):
            with self.assertRaises(ProtocolError):self.run_worker()
        self.assertEqual([m['type'] for m in self.peer.sent],['model_worker_ready','model_grant_reply'])
        self.assertNotIn('private late error',json.dumps(self.peer.sent))

    def test_native_entries_guard_before_runtime_loading(self):
        root=Path(__file__).resolve().parents[1]/'src/project_maya/windows_runtime'
        for name in ('model_validation_child_entry.py','model_validation_worker_entry.py'):
            with self.subTest(name=name),patch('sys.platform','linux'),self.assertRaises(SystemExit) as caught:
                runpy.run_path(str(root/name),run_name='__main__')
            self.assertEqual(caught.exception.code,2)

    def test_child_denial_control_is_case_bound(self):
        # Exercise the real fixed endpoint validator, without native SDK construction.
        from test_model_denial_inert import ChildDenialTransportTests
        helper=ChildDenialTransportTests()
        right=dict(v=1,type='model_denied',attempt=ATTEMPT,seq=1,case='M03a',reason='request_model_rejected')
        for reply, expected in ((right,True),(dict(right,case='M02'),False),
                                (dict(right,reason='gateway_egress_denied'),False),(dict(right,v=True),False)):
            client=helper.client(reply,WrongModelChannelClient)
            with self.assertRaises(ProtocolError):client.exchange(expected_request())
            self.assertEqual(client.denial_observed,expected)
