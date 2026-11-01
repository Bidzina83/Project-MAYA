"""M04b fixtures use inert clocks/streams, never native setup or bundled SDK."""
import copy
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch

from project_maya.bridge.audit import RequiredAudit
from project_maya.bridge.model_lease_revocation import RevokedGrantBridge, checked_age, revocation_metadata, verify_revocation_audit
from project_maya.bridge.model_route_validation import route_request
from project_maya.bridge.model_service import ModelDenied, OfflineModelBridge, digest
from project_maya.bridge.model_worker import serve_model
from project_maya.bridge.protocol import ProtocolError
from project_maya.bridge.service import HostBinding
from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins.model_bridge import RevokedGrantChannelClient
from test_model_bridge_worker_inert import ATTEMPT,CHANNEL,SID,CANARY,OUTPUT,LITERALS,CoordinatorFixture,expected_request,policy


class RevokePeer(CoordinatorFixture):
    def receive(self):
        kinds=('model_issue','model_revoke','model_dispatch')
        kind=kinds[self.index];self.index+=1
        message=dict(v=1,type=kind,attempt=ATTEMPT,request_id=format(self.index,'032x'))
        if kind=='model_revoke':message['lease']=self.sent[1]['grant']['lease']
        if kind=='model_dispatch':
            message['request']=route_request(HostBinding(SID,ATTEMPT,CHANNEL),self.sent[1]['grant']['lease'],self.expected)
        return self.modify(message)


class RevocationTests(unittest.TestCase):
    def setUp(self):
        sync=patch('project_maya.bridge.audit.os.fsync');sync.start();self.addCleanup(sync.stop)
        self.now=[0.0];self.records=[];self.stream=Mock()
        self.stream.write.side_effect=lambda raw:self.records.append(json.loads(raw)) or len(raw)
        self.audit=RequiredAudit(self.stream);self.peer=RevokePeer();self.peer.modify=self.advance
        self.binding=HostBinding(SID,ATTEMPT,CHANNEL)
        self.config=dict(operator_sid=SID,attempt=ATTEMPT,channel_id=CHANNEL,utc_day='2026-10-24',canary=CANARY,fixture_text=OUTPUT)

    def advance(self,message):
        if message['type']=='model_revoke':self.now[0]=0.1
        if message['type']=='model_dispatch':self.now[0]=0.8
        return message

    def service(self):
        return RevokedGrantBridge(self.binding,PolicyAuthorizationGateway(tuple(PolicyRule(**r) for r in policy()['allow'])),
            self.audit,expected_request(),OUTPUT,clock=lambda:self.now[0])

    def issued(self):
        self.now[0]=0;service=self.service();grant=service.issue();return service,grant

    def revoked(self):
        service,grant=self.issued();self.now[0]=0.1
        ack=service.revoke_issued(grant['lease'],'2'*32);service.bind_command('3'*32)
        return service,grant,ack

    def reject(self,service,grant):
        with self.assertRaises((ModelDenied,ProtocolError)):
            service.prepare_runtime(route_request(self.binding,grant['lease'],expected_request()),CHANNEL)
        self.assertEqual(service.gateway_calls,0);self.assertEqual(service.dispatches,0)

    def run_worker(self,**kwargs):
        def fixture_factory(*args,**kw):return RevokedGrantBridge(*args,**kw,clock=lambda:self.now[0])
        with patch('project_maya.bridge.model_lease_revocation.RevokedGrantBridge',side_effect=fixture_factory):
            return serve_model(self.peer,self.config,kwargs.pop('rules',policy()),LITERALS.read_bytes(),
                self.audit,self.peer.write_expected,revoke_grant=True,**kwargs)

    def raw(self):return b''.join(json.dumps(r).encode()+b'\n' for r in self.records)
    def verify(self,raw=None,**kw):
        return verify_revocation_audit(self.raw() if raw is None else raw,self.binding,
            kw.get('service_id',self.peer.sent[0]['service_request_id']),kw.get('revoke_id',format(2,'032x')),
            kw.get('dispatch_id',format(3,'032x')),kw.get('lease',self.peer.sent[1]['grant']['lease']),
            expected_request(),digest(OUTPUT.encode()),kw.get('revoke_age','100'),kw.get('age','800'))

    def test_exact_worker_revoke_ack_rejection_and_two_events(self):
        with patch.object(PolicyAuthorizationGateway,'authorize',side_effect=AssertionError('no gateway')) as gateway:
            result=self.run_worker();gateway.assert_not_called()
        self.assertEqual(result['stage'],'lease_revoked');self.assertEqual(result['worker_elapsed_ms'],'800')
        self.assertEqual(result['revoke_elapsed_ms'],'100');self.assertEqual(result['original_guard_rejected'],'true')
        self.assertEqual(self.verify(),2)
        self.assertEqual([m['type'] for m in self.peer.sent],['model_worker_ready','model_grant_reply','model_revoke_ack','model_lease_revoked'])
        self.assertEqual([r['event_type'] for r in self.records],['model_bridge.grant_revoked','model_bridge.lease_revoked'])
        self.assertEqual(self.peer.sent[2]['evidence'],self.records[0]['metadata'])
        self.assertEqual(result,self.records[1]['metadata']);self.assertEqual(len(result),39)
        self.assertNotIn(CANARY,self.raw().decode());self.assertNotIn(self.peer.sent[1]['grant']['lease'],self.raw().decode())

    def test_original_revoke_called_once_and_no_grant_state_change(self):
        service,grant=self.issued();before=(service._token,service._expires,service._phase,service._closed)
        original=OfflineModelBridge.revoke;calls=[]
        with patch.object(OfflineModelBridge,'revoke',lambda instance:calls.append(instance) or original(instance)):
            ack=service.revoke_issued(grant['lease'],'2'*32)
        self.assertEqual(calls,[service]);self.assertEqual(before,(service._token,service._expires,service._phase,service._closed))
        self.assertTrue(service._revoked);ack['grant_unexpired']='forged'
        service.bind_command('3'*32);self.reject(service,grant)
        self.assertEqual(service.evidence()['grant_unexpired'],'true')

    def test_original_revoke_cannot_be_replaced_by_ack(self):
        service,grant=self.issued()
        with patch.object(OfflineModelBridge,'revoke',return_value=None),self.assertRaises(ProtocolError):
            service.revoke_issued(grant['lease'],'2'*32)
        self.assertEqual(self.records,[])

    def test_original_guard_required_and_generic_uncertain_not_success(self):
        for fault in (None,RuntimeError('private'),ModelDenied(True)):
            self.audit=RequiredAudit(self.stream);service,grant,ack=self.revoked()
            with patch.object(OfflineModelBridge,'_live',side_effect=fault):self.reject(service,grant)
            with self.assertRaises(ProtocolError):service.evidence()
            self.assertFalse(service.revocation_observed)

    def test_before_at_after_expiry_during_request(self):
        for age,allowed in ((0.1,True),(1.999,True),(2.0,False),(2.1,False)):
            self.audit=RequiredAudit(self.stream);service,grant,ack=self.revoked();self.now[0]=age
            self.reject(service,grant)
            if allowed:self.assertEqual(service.evidence()['case'],'M04b')
            else:
                with self.assertRaises(ProtocolError):service.evidence()

    def test_expired_or_invalid_clock_cannot_ack_revoke(self):
        for age in (2.0,2.1,-1.0,float('nan'),float('inf'),float('-inf')):
            self.audit=RequiredAudit(self.stream);service,grant=self.issued();self.now[0]=age
            with self.subTest(age=age),self.assertRaises(ProtocolError):service.revoke_issued(grant['lease'],'2'*32)

    def test_backward_or_nonfinite_request_clock_blocks(self):
        for age in (0.09,float('nan'),float('inf'),float('-inf')):
            self.audit=RequiredAudit(self.stream);service,grant,ack=self.revoked();self.now[0]=age
            self.reject(service,grant)
            with self.assertRaises(ProtocolError):service.evidence()

    def test_expiry_crossing_original_guard_blocks(self):
        service,grant,ack=self.revoked();original=OfflineModelBridge._live
        def cross(instance,phase):
            self.now[0]=2.0;return original(instance,phase)
        with patch.object(OfflineModelBridge,'_live',cross):self.reject(service,grant)
        with self.assertRaises(ProtocolError):service.evidence()

    def test_expiry_crossing_either_required_audit_commit_blocks(self):
        for event in (1,2):
            self.audit=RequiredAudit(self.stream);self.records=[];self.stream.flush.side_effect=None
            service,grant=self.issued()
            self.stream.flush.side_effect=lambda:self.now.__setitem__(0,2.0) if len(self.records)==event else None
            if event==1:
                with self.assertRaises(ProtocolError):service.revoke_issued(grant['lease'],'2'*32)
                self.assertIsNone(service._ack_snapshot)
            else:
                service.revoke_issued(grant['lease'],'2'*32);service.bind_command('3'*32);self.reject(service,grant)
                with self.assertRaises(ProtocolError):service.evidence()
                self.assertFalse(service.validation_recorded)

    def test_revoke_context_confounds_block(self):
        for field,value in (('_phase','new'),('_phase','runtime_delivered'),('_closed',True),('_revoked',True),
                ('_token','f'*64),('_expires',8.0),('gateway_calls',1),('dispatch_attempted',True)):
            self.audit=RequiredAudit(self.stream);service,grant=self.issued();setattr(service,field,value)
            with self.subTest(field=field),self.assertRaises(ProtocolError):service.revoke_issued(grant['lease'],'2'*32)

    def test_failed_audit_wrong_state_and_all_preexisting_effects_block_request(self):
        for field,value in (('_closed',True),('_phase','runtime_delivered'),('_token','f'*64),('_expires',9.0),
                ('gateway_calls',1),('dispatch_attempted',True),('prepared_runtime_releases',1),('confirmed_runtime_releases',1),
                ('prepared_operator_releases',1),('confirmed_operator_releases',1)):
            self.audit=RequiredAudit(self.stream);service,grant,ack=self.revoked();setattr(service,field,value)
            prior=service.gateway_calls
            with self.assertRaises((ModelDenied,ProtocolError)):
                service.prepare_runtime(route_request(self.binding,grant['lease'],expected_request()),CHANNEL)
            self.assertEqual(service.gateway_calls,prior)
            with self.assertRaises(ProtocolError):service.evidence()
        self.audit=RequiredAudit(self.stream);service,grant,ack=self.revoked();self.audit.failed=True
        self.reject(service,grant)
        with self.assertRaises(ProtocolError):service.evidence()

    def test_unissued_wrong_lease_ID_second_revoke_or_issue_blocks(self):
        with self.assertRaises(ProtocolError):self.service().revoke_issued('f'*64,'2'*32)
        for lease,command in (('f'*64,'2'*32),(None,'2'*32),('correct','bad')):
            service,grant=self.issued()
            with self.assertRaises(ProtocolError):service.revoke_issued(grant['lease'] if lease=='correct' else lease,command)
        service,grant,ack=self.revoked()
        with self.assertRaises(ProtocolError):service.revoke_issued(grant['lease'],'4'*32)
        service,grant,ack=self.revoked()
        with self.assertRaises(ProtocolError):service.issue()

    def test_no_ack_or_unrevoked_cannot_dispatch(self):
        service,grant=self.issued();self.reject(service,grant)
        with self.assertRaises(ProtocolError):service.evidence()
        service,grant,ack=self.revoked();service._revoked=False;self.reject(service,grant)
        with self.assertRaises(ProtocolError):service.evidence()

    def test_bad_request_channel_or_missing_command_is_not_revocation(self):
        for key,value in (('v',True),('seq',True),('attempt','f'*32),('route','wrong'),('lease','f'*64),
                ('method','GET'),('path','/other'),('body','wrong'),('extra',1),('channel','f'*64),('command',None)):
            self.audit=RequiredAudit(self.stream);service,grant,ack=self.revoked()
            message=route_request(self.binding,grant['lease'],expected_request())
            if key=='command':service._command_id=None
            elif key!='channel':message[key]=value
            with self.subTest(key=key),self.assertRaises(ProtocolError):service.prepare_runtime(message,value if key=='channel' else CHANNEL)
            with self.assertRaises(ProtocolError):service.evidence()

    def test_command_binding_requires_ack_unique_single_ID(self):
        service,grant=self.issued()
        with self.assertRaises(ProtocolError):service.bind_command('3'*32)
        service,grant,ack=self.revoked()
        with self.assertRaises(ProtocolError):service.bind_command('4'*32)
        service,grant=self.issued();service.revoke_issued(grant['lease'],'2'*32)
        with self.assertRaises(ProtocolError):service.bind_command('2'*32)

    def test_worker_revoke_order_fields_and_seen_ID_guards(self):
        faults=(lambda m:dict(m,request_id='1'*32),
            lambda m:dict(m,type='model_dispatch') if m['type']=='model_revoke' else m,
            lambda m:dict(m,type='model_revoke') if m['type']=='model_dispatch' else m,
            lambda m:dict(m,lease='f'*64) if m['type']=='model_revoke' else m,
            lambda m:dict(m,attempt='f'*32) if m['type']=='model_revoke' else m,
            lambda m:dict(m,extra=True) if m['type']=='model_revoke' else m)
        for mutate in faults:
            self.now[0]=0;self.audit=RequiredAudit(self.stream);self.peer=RevokePeer()
            self.peer.modify=lambda m:self.advance(mutate(m))
            with self.assertRaises(ProtocolError):self.run_worker()
            self.assertNotIn('model_lease_revoked',[m['type'] for m in self.peer.sent])

    def test_old_profile_rejects_revoke_command(self):
        with self.assertRaises(ProtocolError):
            serve_model(self.peer,self.config,policy(),LITERALS.read_bytes(),self.audit,self.peer.write_expected)
        self.assertNotIn('model_revoke_ack',[m['type'] for m in self.peer.sent])

    def test_other_modes_policy_and_nonboolean_mode_block(self):
        for mode in ('deny_egress','wrong_model','wrong_route','wrong_attempt','wrong_body','expire_grant'):
            with self.assertRaises(ProtocolError):self.run_worker(**{mode:True})
        with self.assertRaises(ProtocolError):self.run_worker(rules={'allow':policy()['allow'][1:]})
        for value in (1,None,'M04b'):
            with self.assertRaises(ProtocolError):
                serve_model(self.peer,self.config,policy(),LITERALS.read_bytes(),self.audit,self.peer.write_expected,revoke_grant=value)

    def test_audit_faults_on_both_records_never_complete(self):
        for event in (1,2):
            for fault in ('short','write','flush','sync'):
                self.now[0]=0;self.records=[];self.audit=RequiredAudit(self.stream);self.peer=RevokePeer();self.peer.modify=self.advance
                self.stream.flush.side_effect=None
                def write(raw):
                    self.records.append(json.loads(raw))
                    if len(self.records)==event:
                        if fault=='write':raise OSError('private')
                        if fault=='short':return len(raw)-1
                    return len(raw)
                self.stream.write.side_effect=write
                def commit():
                    if len(self.records)==event:raise OSError('private')
                with patch('project_maya.bridge.audit.os.fsync') as sync:
                    if fault=='flush':self.stream.flush.side_effect=commit
                    if fault=='sync':sync.side_effect=commit
                    with self.subTest(event=event,fault=fault),self.assertRaises(ProtocolError):self.run_worker()
                    self.assertTrue(self.audit.failed);self.assertNotIn('model_lease_revoked',[m['type'] for m in self.peer.sent])
                    if event==1:self.assertNotIn('model_revoke_ack',[m['type'] for m in self.peer.sent])

    def test_every_audit_field_and_envelope_is_exact(self):
        self.run_worker();original=copy.deepcopy(self.records)
        for i in (0,1):
            for key in original[i]['metadata']:
                self.records=copy.deepcopy(original);self.records[i]['metadata'][key]='forged'
                with self.subTest(record=i,key=key),self.assertRaises(ProtocolError):self.verify()
            for key in original[i]:
                self.records=copy.deepcopy(original);del self.records[i][key]
                with self.subTest(record=i,key=key),self.assertRaises(ProtocolError):self.verify()
        self.records=original
        for kw in ({'revoke_age':'101'},{'age':'801'},{'service_id':'f'*32},{'revoke_id':'f'*32},
                {'dispatch_id':'f'*32},{'dispatch_id':''},{'lease':'f'*64}):
            with self.assertRaises(ProtocolError):self.verify(**kw)

    def test_missing_extra_swapped_duplicate_or_malformed_audit_blocks(self):
        self.run_worker();raw=self.raw();lines=raw.splitlines(keepends=True)
        for bad in (b'',raw[:-1],raw+lines[0],lines[0],lines[1],lines[1]+lines[0],lines[0]*2,
                raw.replace(b'"schema_version": 1',b'"schema_version": true'),b'\xff\n\n',b'x'*131073,
                raw.replace(b'"decision": "deny"',b'"decision":"deny","decision":"deny"')):
            with self.assertRaises((ProtocolError,UnicodeError)):self.verify(bad)

    def test_age_types_bounds_order_and_metadata(self):
        for age in ('0','1','1999'):self.assertEqual(checked_age(age),int(age))
        for age in ('00','0200','2000','-1','1.0','1\n','+1','1e2',True,100,None):
            with self.subTest(age=age),self.assertRaises(ProtocolError):checked_age(age)
        args=(self.binding,'1'*32,'2'*32,'3'*32,'f'*64,expected_request(),digest(OUTPUT.encode()))
        with self.assertRaises(ProtocolError):revocation_metadata(*args,'100','99')

    def test_separate_fresh_positive_service_still_dispatches(self):
        service=OfflineModelBridge(self.binding,PolicyAuthorizationGateway(tuple(PolicyRule(**r) for r in policy()['allow'])),
            self.audit,expected_request(),OUTPUT,clock=lambda:0)
        grant=service.issue();reply=service.prepare_runtime(route_request(self.binding,grant['lease'],expected_request()),CHANNEL)
        self.assertEqual(reply['status'],'ok');self.assertEqual(service.dispatches,1);service.close()

    def test_child_control_exact_case_reason_and_one_request_budget(self):
        from test_model_denial_inert import ChildDenialTransportTests
        helper=ChildDenialTransportTests();right=dict(v=1,type='model_denied',attempt=ATTEMPT,seq=1,case='M04b',reason='lease_revoked')
        for reply,accepted in ((right,True),(dict(right,case='M04a'),False),(dict(right,reason='lease_expired'),False),(dict(right,v=True),False)):
            client=helper.client(reply,RevokedGrantChannelClient)
            with self.assertRaises(ProtocolError):client.exchange(expected_request())
            self.assertEqual(client.denial_observed,accepted)
            with self.assertRaises(ProtocolError):client.exchange(expected_request())
            self.assertEqual(client.requests,1)

    def test_fixed_entries_guard_before_loading_runtime(self):
        root=Path(__file__).resolve().parents[1]/'src/project_maya/windows_runtime'
        for name in ('model_revoke_child_entry.py','model_revoke_worker_entry.py'):
            with patch('sys.platform','linux'),self.assertRaises(SystemExit) as result:runpy.run_path(str(root/name),run_name='__main__')
            self.assertEqual(result.exception.code,2)

    def test_native_schedule_ack_before_begin_no_clock_injection(self):
        root=Path(__file__).resolve().parents[1]/'src/project_maya/windows_runtime'
        source=(root/'ModelBridgeRuntime.cs').read_text()
        revoke=source.index('var revoke=Command("model_revoke")')
        ack=source.index('ModelValidationAdmission.Evidence(evidence,revokeExpected)',revoke)
        begin=source.index('var begin=Message("model_begin")',ack)
        dispatch=source.index('var dispatch=Command("model_dispatch")',begin)
        self.assertLess(revoke,ack);self.assertLess(ack,begin);self.assertLess(begin,dispatch)
        self.assertNotIn('clock=',(root.parent/'bridge/model_worker.py').read_text())
        self.assertNotIn('WaitBeforeBegin',(root/'ModelRevocationAdmission.cs').read_text())
        self.assertIn('HERMES_MODEL_REVOKE &&',(root/'ProtectedPython.cs').read_text())
