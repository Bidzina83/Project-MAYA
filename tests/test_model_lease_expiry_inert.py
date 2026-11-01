"""M04a fake clocks only in inert fixtures; never native runtime/security setup."""
import copy
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch

from project_maya.bridge.audit import RequiredAudit
from project_maya.bridge.model_lease_expiry import ExpiredGrantBridge, checked_elapsed, verify_expiry_audit
from project_maya.bridge.model_service import OfflineModelBridge, ModelDenied, digest
from project_maya.bridge.model_route_validation import route_request
from project_maya.bridge.model_worker import serve_model
from project_maya.bridge.protocol import ProtocolError
from project_maya.bridge.service import HostBinding
from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins.model_bridge import ExpiredGrantChannelClient
from test_model_bridge_worker_inert import ATTEMPT,CHANNEL,SID,CANARY,OUTPUT,LITERALS,CoordinatorFixture,expected_request,policy


class ExpiryTests(unittest.TestCase):
    def setUp(self):
        sync=patch('project_maya.bridge.audit.os.fsync');sync.start();self.addCleanup(sync.stop)
        self.now=[0.0];self.age=2.1;self.records=[];self.stream=Mock()
        self.stream.write.side_effect=lambda raw:self.records.append(json.loads(raw)) or len(raw)
        self.audit=RequiredAudit(self.stream);self.peer=CoordinatorFixture()
        self.config=dict(operator_sid=SID,attempt=ATTEMPT,channel_id=CHANNEL,utc_day='2026-10-24',canary=CANARY,fixture_text=OUTPUT)
        self.binding=HostBinding(SID,ATTEMPT,CHANNEL)
        self.peer.modify=self.advance

    def advance(self, message):
        if message['type']=='model_dispatch':self.now[0]=self.age
        return message

    def service(self):
        return ExpiredGrantBridge(self.binding,PolicyAuthorizationGateway(tuple(PolicyRule(**r) for r in policy()['allow'])),
            self.audit,expected_request(),OUTPUT,clock=lambda:self.now[0])

    def run_worker(self, **kwargs):
        def fixture_factory(*args,**kw):return ExpiredGrantBridge(*args,**kw,clock=lambda:self.now[0])
        with patch('project_maya.bridge.model_lease_expiry.ExpiredGrantBridge',side_effect=fixture_factory):
            return serve_model(self.peer,self.config,kwargs.pop('rules',policy()),LITERALS.read_bytes(),
                self.audit,self.peer.write_expected,expire_grant=True,**kwargs)

    def raw(self):return b''.join(json.dumps(r).encode()+b'\n' for r in self.records)
    def verify(self, raw=None, **kwargs):
        return verify_expiry_audit(self.raw() if raw is None else raw,self.binding,
            kwargs.get('service_id',self.peer.sent[0]['service_request_id']),kwargs.get('command_id',format(2,'032x')),
            kwargs.get('lease',self.peer.sent[1]['grant']['lease']),expected_request(),digest(OUTPUT.encode()),kwargs.get('age','2100'))

    def reject_service(self, service, grant):
        with self.assertRaises((ModelDenied,ProtocolError)):
            service.prepare_runtime(route_request(self.binding,grant['lease'],expected_request()),CHANNEL)

    def test_worker_exact_expiry_audit_and_zero_gateway(self):
        with patch.object(PolicyAuthorizationGateway,'authorize',side_effect=AssertionError('no gateway')) as gateway:
            result=self.run_worker();gateway.assert_not_called()
        self.assertEqual(result['case'],'M04a');self.assertEqual(result['stage'],'lease_expired')
        self.assertEqual(result['worker_elapsed_ms'],'2100');self.assertEqual(result['request_validated'],'false')
        self.assertEqual(result['request_preflight_verified'],'true');self.assertEqual(self.verify(),1)
        self.assertEqual([m['type'] for m in self.peer.sent],['model_worker_ready','model_grant_reply','model_lease_expired'])
        self.assertNotIn(CANARY,self.raw().decode());self.assertNotIn(self.peer.sent[1]['grant']['lease'],self.raw().decode())

    def test_before_at_after_expiry_and_upper_bound(self):
        for age,accepted in ((1.999,False),(2.0,True),(2.1,True),(30.0,True),(30.001,False)):
            self.now[0]=0;service=self.service();service.bind_command('d'*32);grant=service.issue();self.now[0]=age
            self.reject_service(service,grant)
            if accepted:self.assertEqual(service.evidence()['case'],'M04a')
            else:
                with self.assertRaises(ProtocolError):service.evidence()
            self.assertEqual(service.gateway_calls,0);self.assertEqual(service.dispatches,0)

    def test_fresh_positive_separate_service_still_dispatches(self):
        service=OfflineModelBridge(self.binding,PolicyAuthorizationGateway(tuple(PolicyRule(**r) for r in policy()['allow'])),
            self.audit,expected_request(),OUTPUT,clock=lambda:0)
        grant=service.issue();reply=service.prepare_runtime(route_request(self.binding,grant['lease'],expected_request()),CHANNEL)
        self.assertEqual(reply['status'],'ok');self.assertEqual(service.gateway_calls,2);self.assertEqual(service.dispatches,1);service.close()

    def test_original_guard_must_actually_reject(self):
        service=self.service();service.bind_command('d'*32);grant=service.issue();self.now[0]=2.1
        with patch.object(OfflineModelBridge,'_live',return_value=None):self.reject_service(service,grant)
        with self.assertRaises(ProtocolError):service.evidence()
        self.assertFalse(service.expiry_observed);self.assertEqual(service.gateway_calls,0)

    def test_unknown_guard_exception_is_not_expiry(self):
        service=self.service();service.bind_command('d'*32);grant=service.issue();self.now[0]=2.1
        with patch.object(OfflineModelBridge,'_live',side_effect=RuntimeError('private')):self.reject_service(service,grant)
        with self.assertRaises(ProtocolError):service.evidence()
        self.assertFalse(service.validation_recorded)

    def test_uncertain_guard_failure_is_not_accepted(self):
        service=self.service();service.bind_command('d'*32);grant=service.issue();self.now[0]=2.1
        with patch.object(OfflineModelBridge,'_live',side_effect=ModelDenied(True)):self.reject_service(service,grant)
        with self.assertRaises(ProtocolError):service.evidence()
        self.assertFalse(service.expiry_observed)

    def test_grant_retiming_or_token_replacement_is_not_expiry_evidence(self):
        for field,value in (('_expires',1.0),('_expires',12.0),('_token','f'*64)):
            self.now[0]=0;service=self.service();service.bind_command('d'*32);service.issue()
            setattr(service,field,value);self.now[0]=2.1
            self.reject_service(service,{'lease':service._token})
            with self.subTest(field=field),self.assertRaises(ProtocolError):service.evidence()
            self.assertFalse(service.expiry_observed)

    def test_revoked_closed_failed_audit_or_wrong_phase_not_expiry(self):
        for fault in ('revoked','closed','audit','phase'):
            self.now[0]=0;self.audit=RequiredAudit(self.stream);service=self.service();service.bind_command('d'*32);grant=service.issue()
            if fault=='revoked':service.revoke()
            elif fault=='closed':service.close()
            elif fault=='audit':self.audit.failed=True
            else:service._phase='runtime_delivered'
            self.now[0]=2.1;self.reject_service(service,grant)
            with self.subTest(fault=fault),self.assertRaises(ProtocolError):service.evidence()
            self.assertFalse(service.expiry_observed)

    def test_unissued_or_missing_command_or_second_issue_block(self):
        service=self.service()
        self.reject_service(service,{'lease':'e'*64})
        with self.assertRaises(ProtocolError):service.evidence()
        service=self.service();grant=service.issue();self.now[0]=2.1;self.reject_service(service,grant)
        with self.assertRaises(ProtocolError):service.evidence()
        self.now[0]=0;service=self.service();service.issue()
        with self.assertRaises(ModelDenied):service.issue()
        service.close()

    def test_bad_request_at_expiry_cannot_pass(self):
        changes={'v':True,'seq':True,'attempt':'f'*32,'route':'wrong','lease':'f'*64,
            'method':'GET','path':'/other','body':expected_request().decode()+' ','extra':1}
        for key,value in changes.items():
            self.now[0]=0;service=self.service();service.bind_command('d'*32);grant=service.issue();self.now[0]=2.1
            message=route_request(self.binding,grant['lease'],expected_request());message[key]=value
            with self.subTest(key=key),self.assertRaises(ProtocolError):service.prepare_runtime(message,CHANNEL)
            with self.assertRaises(ProtocolError):service.evidence()
            self.assertFalse(service.preflight_verified)

    def test_wrong_channel_and_missing_field_not_expiry(self):
        for key in (None,'body','lease','attempt'):
            self.now[0]=0;service=self.service();service.bind_command('d'*32);grant=service.issue();self.now[0]=2.1
            message=route_request(self.binding,grant['lease'],expected_request())
            if key:del message[key]
            with self.subTest(key=key),self.assertRaises(ProtocolError):service.prepare_runtime(message,'f'*64 if key is None else CHANNEL)
            with self.assertRaises(ProtocolError):service.evidence()

    def test_nonfinite_clock_is_not_success(self):
        for age in (float('nan'),float('inf'),float('-inf')):
            self.now[0]=0;service=self.service();service.bind_command('d'*32);grant=service.issue();self.now[0]=age
            self.reject_service(service,grant)
            with self.assertRaises(ProtocolError):service.evidence()

    def test_required_audit_faults_never_emit_expiry_reply(self):
        for fault in ('short','write','flush','sync'):
            self.now[0]=0;self.peer=CoordinatorFixture();self.peer.modify=self.advance;self.audit=RequiredAudit(self.stream)
            self.stream.write.side_effect=lambda raw:len(raw);self.stream.flush.side_effect=None
            with patch('project_maya.bridge.audit.os.fsync') as sync:
                if fault=='short':self.stream.write.side_effect=lambda raw:len(raw)-1
                elif fault=='write':self.stream.write.side_effect=OSError('private')
                elif fault=='flush':self.stream.flush.side_effect=OSError('private')
                else:sync.side_effect=OSError('private')
                with self.subTest(fault=fault),self.assertRaises(ProtocolError):self.run_worker()
                self.assertTrue(self.audit.failed);self.assertNotIn('model_lease_expired',[m['type'] for m in self.peer.sent])

    def test_every_audit_binding_and_dynamic_age_must_match(self):
        self.run_worker();record=copy.deepcopy(self.records[0])
        for key in record['metadata']:
            self.records[0]=copy.deepcopy(record);self.records[0]['metadata'][key]='wrong'
            with self.subTest(key=key),self.assertRaises(ProtocolError):self.verify()
        for key in record:
            self.records[0]=copy.deepcopy(record);del self.records[0][key]
            with self.subTest(key=key),self.assertRaises(ProtocolError):self.verify()
        self.records[0]=record
        for change in ({'age':'2101'},{'service_id':'f'*32},{'command_id':'f'*32},{'lease':'f'*64}):
            with self.assertRaises(ProtocolError):self.verify(**change)
        for raw in (b'',self.raw()[:-1],self.raw()*2,b'\xff\n',b'x'*131073):
            with self.assertRaises((ProtocolError,UnicodeError)):self.verify(raw)

    def test_elapsed_is_canonical_bounded_decimal_string(self):
        for value in ('2000','2100','30000'):self.assertEqual(checked_elapsed(value),int(value))
        for value in (2000,True,None,'02000','1999','30001','2000.0','+2000','2000\n','2e3'):
            with self.subTest(value=value),self.assertRaises(ProtocolError):checked_elapsed(value)

    def test_other_modes_and_M02_policy_rejected(self):
        for mode in ('deny_egress','wrong_model','wrong_route','wrong_attempt','wrong_body'):
            with self.assertRaises(ProtocolError):self.run_worker(**{mode:True})
        with self.assertRaises(ProtocolError):self.run_worker(rules={'allow':policy()['allow'][1:]})
        for value in (1,None,'M04a'):
            with self.assertRaises(ProtocolError):
                serve_model(self.peer,self.config,policy(),LITERALS.read_bytes(),self.audit,self.peer.write_expected,expire_grant=value)

    def test_expiry_child_control_case_and_reason_are_exact(self):
        from test_model_denial_inert import ChildDenialTransportTests
        helper=ChildDenialTransportTests();right=dict(v=1,type='model_denied',attempt=ATTEMPT,seq=1,case='M04a',reason='lease_expired')
        for reply,expected in ((right,True),(dict(right,case='M03d'),False),(dict(right,reason='request_body_rejected'),False),(dict(right,v=True),False)):
            client=helper.client(reply,ExpiredGrantChannelClient)
            with self.assertRaises(ProtocolError):client.exchange(expected_request())
            self.assertEqual(client.denial_observed,expected)

    def test_expiry_entries_guard_without_loading_runtime(self):
        root=Path(__file__).resolve().parents[1]/'src/project_maya/windows_runtime'
        for name in ('model_expiry_child_entry.py','model_expiry_worker_entry.py'):
            with patch('sys.platform','linux'),self.assertRaises(SystemExit) as caught:runpy.run_path(str(root/name),run_name='__main__')
            self.assertEqual(caught.exception.code,2)

    def test_native_wait_is_before_begin_not_inside_RPC(self):
        root=Path(__file__).resolve().parents[1]/'src/project_maya/windows_runtime'
        runtime=(root/'ModelBridgeRuntime.cs').read_text();start=runtime.index('var issued=Reply(')
        wait=runtime.index('ModelExpiryAdmission.WaitBeforeBegin(',start)
        begin=runtime.index('var begin=Message("model_begin")',start)
        dispatch=runtime.index('var dispatch=Command("model_dispatch")',begin)
        self.assertLess(start,wait);self.assertLess(wait,begin);self.assertLess(begin,dispatch)
        timing=(root/'ModelExpiryAdmission.cs').read_text()
        native=timing[timing.index('internal static long WaitBeforeBegin'):timing.index('// Pure scheduling core')]
        self.assertIn('Stopwatch.StartNew()',native);self.assertIn('Thread.Sleep',native)
        self.assertNotIn('clock=',(root.parent/'bridge/model_worker.py').read_text())
