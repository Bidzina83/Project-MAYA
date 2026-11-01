"""M04c in-memory effects, clocks and protocol; no bundled runtime/native setup."""
import copy
from datetime import datetime, timedelta
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch

from project_maya.bridge.audit import RequiredAudit
from project_maya.bridge.model_audit import verify_model_audit
from project_maya.bridge.model_lease_replay import ConsumedGrantBridge, replay_metadata, verify_replay_audit
from project_maya.bridge.model_route_validation import route_request
from project_maya.bridge.model_service import ModelDenied, OfflineModelBridge, digest
from project_maya.bridge.model_worker import serve_model
from project_maya.bridge.protocol import ProtocolError
from project_maya.bridge.service import HostBinding
from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
from test_model_bridge_worker_inert import ATTEMPT,CHANNEL,SID,CANARY,OUTPUT,LITERALS,CoordinatorFixture,expected_request,policy


class ReplayPeer(CoordinatorFixture):
    def receive(self):
        kinds=('model_issue','model_dispatch','model_runtime_delivered','model_dispatch')
        kind=kinds[self.index];self.index+=1
        message=dict(v=1,type=kind,attempt=ATTEMPT,request_id=format(self.index,'032x'))
        if kind=='model_dispatch':
            message['request']=route_request(HostBinding(SID,ATTEMPT,CHANNEL),self.sent[1]['grant']['lease'],self.expected)
        elif kind=='model_runtime_delivered':message['response_sha256']=self.sent[2]['response']['response_sha256']
        return self.modify(message)


class ReplayTests(unittest.TestCase):
    def setUp(self):
        sync=patch('project_maya.bridge.audit.os.fsync');sync.start();self.addCleanup(sync.stop)
        self.now=[0.0];self.records=[];self.stream=Mock()
        self.stream.write.side_effect=lambda raw:self.records.append(json.loads(raw)) or len(raw)
        self.audit=RequiredAudit(self.stream);self.peer=ReplayPeer();self.peer.modify=self.advance
        self.binding=HostBinding(SID,ATTEMPT,CHANNEL)
        self.config=dict(operator_sid=SID,attempt=ATTEMPT,channel_id=CHANNEL,utc_day='2026-10-24',canary=CANARY,fixture_text=OUTPUT)

    def advance(self,message):
        if self.peer.index>1:self.now[0]=self.peer.index*0.2
        return message

    def service(self):
        return ConsumedGrantBridge(self.binding,PolicyAuthorizationGateway(tuple(PolicyRule(**r) for r in policy()['allow'])),
            self.audit,expected_request(),OUTPUT,clock=lambda:self.now[0])

    def prefix(self,confirm=True):
        self.now[0]=0;service=self.service();grant=service.issue();service.bind_first('2'*32)
        message=route_request(self.binding,grant['lease'],expected_request())
        self.now[0]=0.2;reply=service.prepare_runtime(message,CHANNEL)
        if confirm:
            self.now[0]=0.6;service.confirm_runtime_delivery(reply['response_sha256'],'3'*32)
        return service,grant,message,reply

    def replay(self,service,message):
        service.bind_replay('4'*32);self.now[0]=0.8
        with self.assertRaises(ModelDenied) as failure:service.prepare_runtime(message,CHANNEL)
        self.assertTrue(failure.exception.uncertain)

    def run_worker(self,**kwargs):
        def fixture_factory(*args,**kw):return ConsumedGrantBridge(*args,**kw,clock=lambda:self.now[0])
        with patch('project_maya.bridge.model_lease_replay.ConsumedGrantBridge',side_effect=fixture_factory):
            return serve_model(self.peer,self.config,kwargs.pop('rules',policy()),LITERALS.read_bytes(),self.audit,self.peer.write_expected,replay_grant=True,**kwargs)

    def raw(self):return b''.join(json.dumps(r).encode()+b'\n' for r in self.records)
    def verify(self,raw=None,**kw):
        return verify_replay_audit(self.raw() if raw is None else raw,self.binding,
            kw.get('service_id',self.peer.sent[0]['service_request_id']),kw.get('first_id',format(2,'032x')),
            kw.get('delivery_id',format(3,'032x')),kw.get('replay_id',format(4,'032x')),
            kw.get('lease',self.peer.sent[1]['grant']['lease']),expected_request(),
            self.peer.sent[2]['response']['body'].encode(),digest(OUTPUT.encode()),kw.get('delivery_age','600'),kw.get('age','800'))

    def test_worker_retains_positive_prefix_and_new_ID_consumed_rejection(self):
        result=self.run_worker()
        self.assertEqual(self.verify(),5);self.assertEqual(len(result),50)
        self.assertEqual([m['type'] for m in self.peer.sent],['model_worker_ready','model_grant_reply','model_dispatch_reply','model_runtime_ack','model_lease_consumed'])
        self.assertEqual([r['event_type'] for r in self.records],['model_bridge.'+s for s in
            ('egress_intent','dispatch_outcome','runtime_release_intent','runtime_delivery','lease_consumed')])
        self.assertEqual(result['gateway_calls'],'2');self.assertEqual(result['dispatches'],'1');self.assertEqual(result['runtime_released'],'1')
        self.assertEqual(result['operator_released'],'0');self.assertEqual(result['original_denial_uncertain'],'true')
        self.assertEqual(result['request_validated'],'true');self.assertEqual(result['replay_request_validated'],'false')
        self.assertEqual(self.peer.sent[3]['delivery_elapsed_ms'],'600');self.assertEqual(result['worker_elapsed_ms'],'800')
        self.assertNotIn(CANARY,self.raw().decode());self.assertNotIn(self.peer.sent[1]['grant']['lease'],self.raw().decode())

    def test_original_guard_must_reject_without_additional_gateway(self):
        service,grant,message,reply=self.prefix();self.now[0]=0.8;service.bind_replay('4'*32)
        with patch.object(OfflineModelBridge,'_live',return_value=None),self.assertRaises(ModelDenied):service.prepare_runtime(message,CHANNEL)
        self.assertEqual(service.gateway_calls,2);self.assertEqual(service.dispatches,1)
        with self.assertRaises(ProtocolError):service.evidence()
        self.assertFalse(service.consumption_observed)

    def test_generic_or_wrong_uncertainty_is_not_consumption(self):
        for failure in (RuntimeError('private'),ModelDenied(False)):
            self.audit=RequiredAudit(self.stream);service,grant,message,reply=self.prefix();service.bind_replay('4'*32)
            with patch.object(OfflineModelBridge,'_live',side_effect=failure),self.assertRaises(ModelDenied):service.prepare_runtime(message,CHANNEL)
            with self.assertRaises(ProtocolError):service.evidence()
            self.assertEqual(service.dispatches,1);self.assertFalse(service.consumption_observed)

    def test_truthful_delivery_still_recorded_when_too_late_or_revoked(self):
        for fault in ('expired','revoked'):
            self.audit=RequiredAudit(self.stream);self.records=[];service,grant,message,reply=self.prefix(False)
            if fault=='expired':self.now[0]=2.0
            else:service.revoke()
            with self.assertRaises(ProtocolError):service.confirm_runtime_delivery(reply['response_sha256'],'3'*32)
            self.assertEqual(service.confirmed_runtime_releases,1);self.assertEqual(service.dispatches,1)
            self.assertEqual(self.records[-1]['event_type'],'model_bridge.runtime_delivery')
            with self.assertRaises(ProtocolError):service.evidence()

    def test_request_at_before_after_expiry_and_nonfinite_or_backward_clock(self):
        for age,accepted in ((1.999,True),(2.0,False),(2.1,False),(0.5,False),(float('nan'),False),(float('inf'),False)):
            self.audit=RequiredAudit(self.stream);service,grant,message,reply=self.prefix();service.bind_replay('4'*32);self.now[0]=age
            with self.assertRaises(ModelDenied):service.prepare_runtime(message,CHANNEL)
            if accepted:self.assertEqual(service.evidence()['stage'],'lease_consumed')
            else:
                with self.assertRaises(ProtocolError):service.evidence()
            self.assertEqual(service.gateway_calls,2);self.assertEqual(service.confirmed_runtime_releases,1)

    def test_expiry_crossing_guard_and_fifth_commit_is_blocked(self):
        service,grant,message,reply=self.prefix();service.bind_replay('4'*32)
        original=OfflineModelBridge._live
        def cross(instance,phase):self.now[0]=2.0;return original(instance,phase)
        with patch.object(OfflineModelBridge,'_live',cross),self.assertRaises(ModelDenied):service.prepare_runtime(message,CHANNEL)
        with self.assertRaises(ProtocolError):service.evidence()
        self.audit=RequiredAudit(self.stream);self.records=[];service,grant,message,reply=self.prefix();service.bind_replay('4'*32)
        self.stream.flush.side_effect=lambda:self.now.__setitem__(0,2.0) if len(self.records)==5 else None
        with self.assertRaises(ModelDenied):service.prepare_runtime(message,CHANNEL)
        with self.assertRaises(ProtocolError):service.evidence()
        self.assertEqual(service.confirmed_runtime_releases,1)

    def test_state_grant_response_or_prior_effect_confounds_block(self):
        changes=(('_phase','issued'),('_closed',True),('_revoked',True),('_token','f'*64),('_expires',9.0),('_response',b'{}'),
            ('gateway_calls',3),('dispatch_attempted',False),('confirmed_runtime_releases',0),('prepared_operator_releases',1))
        for field,value in changes:
            self.audit=RequiredAudit(self.stream);service,grant,message,reply=self.prefix();setattr(service,field,value)
            with self.subTest(field=field),self.assertRaises(ProtocolError):service.bind_replay('4'*32)
            with self.assertRaises(ProtocolError):service.evidence()

    def test_bad_replayed_envelope_or_channel_cannot_qualify(self):
        for key,value in (('v',True),('seq',True),('attempt','f'*32),('route','wrong'),('lease','f'*64),('method','GET'),
                ('path','/other'),('body','changed'),('extra',1),('channel','f'*64)):
            self.audit=RequiredAudit(self.stream);service,grant,message,reply=self.prefix();service.bind_replay('4'*32)
            if key!='channel':message[key]=value
            with self.subTest(key=key),self.assertRaises(ProtocolError):service.prepare_runtime(message,value if key=='channel' else CHANNEL)
            with self.assertRaises(ProtocolError):service.evidence()
            self.assertEqual(service.gateway_calls,2);self.assertEqual(service.dispatches,1)

    def test_missing_first_or_delivery_and_duplicate_bindings_block(self):
        service=self.service()
        with self.assertRaises(ProtocolError):service.bind_replay('4'*32)
        service,grant,message,reply=self.prefix(False)
        with self.assertRaises(ProtocolError):service.bind_replay('4'*32)
        for command in ('2'*32,'3'*32,'bad'):
            self.audit=RequiredAudit(self.stream);service,grant,message,reply=self.prefix()
            with self.assertRaises(ProtocolError):service.bind_replay(command)
        service,grant,message,reply=self.prefix();service.bind_replay('4'*32)
        with self.assertRaises(ProtocolError):service.bind_replay('5'*32)

    def test_poisoned_audit_or_second_issue_cannot_resume_service(self):
        service,grant,message,reply=self.prefix();self.audit.failed=True
        with self.assertRaises(ProtocolError):service.bind_replay('4'*32)
        self.assertEqual(service.confirmed_runtime_releases,1)
        with self.assertRaises(ProtocolError):service.issue()

    def test_bad_first_request_and_no_receipt_do_not_fake_prefix(self):
        self.now[0]=0;service=self.service();grant=service.issue();service.bind_first('2'*32)
        message=route_request(self.binding,grant['lease'],expected_request());message['body']='wrong'
        with self.assertRaises(ProtocolError):service.prepare_runtime(message,CHANNEL)
        self.assertEqual(service.dispatches,0);self.assertEqual(self.records,[])
        with self.assertRaises(ProtocolError):service.evidence()

    def test_worker_duplicate_ID_or_wrong_order_is_not_guard_evidence(self):
        for which in ('duplicate','early','extra','wrong_receipt'):
            self.now[0]=0;self.audit=RequiredAudit(self.stream);self.peer=ReplayPeer()
            def mutate(m):
                self.advance(m)
                if which=='duplicate' and self.peer.index==4:m['request_id']=format(2,'032x')
                if which=='early' and self.peer.index==3:m['type']='model_dispatch'
                if which=='extra' and self.peer.index==4:m['extra']=True
                if which=='wrong_receipt' and self.peer.index==3:m['response_sha256']='f'*64
                return m
            self.peer.modify=mutate
            with self.assertRaises((ProtocolError,ModelDenied)):self.run_worker()
            self.assertNotIn('model_lease_consumed',[m['type'] for m in self.peer.sent])

    def test_policy_and_other_modes_stay_exclusive(self):
        for mode in ('deny_egress','wrong_model','wrong_route','wrong_attempt','wrong_body','expire_grant','revoke_grant'):
            with self.assertRaises(ProtocolError):self.run_worker(**{mode:True})
        with self.assertRaises(ProtocolError):self.run_worker(rules={'allow':policy()['allow'][1:]})
        for value in (True,1,None,'M04c'):
            if value is True:continue
            with self.assertRaises(ProtocolError):
                serve_model(self.peer,self.config,policy(),LITERALS.read_bytes(),self.audit,self.peer.write_expected,replay_grant=value)

    def test_all_required_audit_faults_block_and_never_erase_prefix(self):
        for event in range(1,6):
            for fault in ('short','write','flush','sync'):
                self.now[0]=0;self.records=[];self.audit=RequiredAudit(self.stream);self.peer=ReplayPeer();self.peer.modify=self.advance
                self.stream.flush.side_effect=None
                def write(raw):
                    self.records.append(json.loads(raw))
                    if len(self.records)==event:
                        if fault=='write':raise OSError('private')
                        if fault=='short':return len(raw)-1
                    return len(raw)
                def commit(*args):
                    if len(self.records)==event:raise OSError('private')
                self.stream.write.side_effect=write
                with patch('project_maya.bridge.audit.os.fsync') as sync:
                    if fault=='flush':self.stream.flush.side_effect=commit
                    if fault=='sync':sync.side_effect=commit
                    with self.subTest(event=event,fault=fault),self.assertRaises((ProtocolError,ModelDenied)):self.run_worker()
                    self.assertEqual(len(self.records),event,(event,fault,[r['event_type'] for r in self.records]))
                    self.assertTrue(self.audit.failed);self.assertNotIn('model_lease_consumed',[m['type'] for m in self.peer.sent])
                    if event==5:
                        self.assertEqual(self.records[3]['event_type'],'model_bridge.runtime_delivery')
                        self.assertEqual(self.records[3]['metadata']['dispatches'],'1')

    def test_every_ledger_metadata_field_is_exact(self):
        self.run_worker();original=copy.deepcopy(self.records)
        for i,record in enumerate(original):
            for key in record['metadata']:
                self.records=copy.deepcopy(original);self.records[i]['metadata'][key]='wrong'
                with self.subTest(record=i,key=key),self.assertRaises(ProtocolError):self.verify()
            for key in record:
                self.records=copy.deepcopy(original);del self.records[i][key]
                with self.subTest(record=i,key=key),self.assertRaises(ProtocolError):self.verify()
        self.records=original
        for kw in ({'delivery_age':'601'},{'age':'801'},{'first_id':'f'*32},{'delivery_id':'f'*32},{'replay_id':'f'*32},
                {'lease':'f'*64},{'service_id':'f'*32}):
            with self.assertRaises(ProtocolError):self.verify(**kw)

    def test_prefix_cannot_be_truncated_reordered_or_fabricated_as_six(self):
        self.run_worker();raw=self.raw();lines=raw.splitlines(keepends=True)
        for bad in (b'',raw[:-1],b''.join(lines[:4]),lines[4]+b''.join(lines[:4]),raw+lines[-1],lines[0]+raw,
                raw.replace(b'"schema_version": 1',b'"schema_version": true'),b'\xff\n\n\n\n\n',b'x'*131073,
                raw.replace(b'"decision": "allow"',b'"decision":"allow","decision":"allow"')):
            with self.assertRaises((ProtocolError,UnicodeError)):self.verify(bad)
        with self.assertRaises(ProtocolError):
            verify_model_audit(raw,self.binding,self.peer.sent[0]['service_request_id'],expected_request(),
                self.peer.sent[2]['response']['body'].encode(),OUTPUT,(format(3,'032x'),format(5,'032x')))

    def test_timestamp_order_and_extra_operator_event_rejected(self):
        self.run_worker();original=copy.deepcopy(self.records)
        last = datetime.fromisoformat(self.records[-1]['timestamp'].replace('Z', '+00:00'))
        self.records[0]['timestamp'] = (last + timedelta(seconds=1)).isoformat()
        with self.assertRaises(ProtocolError):self.verify()
        self.records=original;self.records[4]['event_type']='model_bridge.operator_release_intent'
        with self.assertRaises(ProtocolError):self.verify()

    def test_age_and_command_order_bounds(self):
        service,grant,message,reply=self.prefix();self.replay(service,message);meta=service.evidence()
        args=(self.binding,service.request_id,'2'*32,'3'*32,'4'*32,grant['lease'],expected_request(),reply['body'].encode(),digest(OUTPUT.encode()))
        self.assertEqual(meta['delivery_elapsed_ms'],'600')
        for delivery,age in (('600','599'),('600','2000'),('0600','800'),(600,'800'),('600',True)):
            with self.assertRaises(ProtocolError):replay_metadata(*args,delivery,age)

    def test_native_entries_guard_and_positive_one_request_path(self):
        root=Path(__file__).resolve().parents[1]/'src/project_maya/windows_runtime'
        for name in ('model_replay_child_entry.py','model_replay_worker_entry.py'):
            with patch('sys.platform','linux'),self.assertRaises(SystemExit) as result:runpy.run_path(str(root/name),run_name='__main__')
            self.assertEqual(result.exception.code,2)
        child=(root/'model_child_entry.py').read_text()
        negative=child[child.index('negative ='):child.index('\n        if (any',child.index('negative ='))]
        self.assertNotIn('replay_grant',negative)
        source=(root/'ModelBridgeRuntime.cs').read_text()
        self.assertIn('ModelValidationAdmission.Enabled && !ModelReplayAdmission.Enabled',source)
        ack=source.index('var runtimeAck=Reply(')
        replay=source.index('return RunReplay(',ack)
        final=source.index('record["model_stage"]="native_final"',ack)
        self.assertLess(ack,replay);self.assertLess(replay,final)
        branch=source[source.index('uint RunReplay('):source.index('public void Dispose()')]
        self.assertNotIn('publish(',branch);self.assertNotIn('model_prepare_final',branch);self.assertNotIn('model_denied',branch)
        self.assertNotIn('clock=',(root.parent/'bridge/model_worker.py').read_text())

    def test_existing_child_client_denies_second_request_without_changes(self):
        from test_model_bridge_inert import ModelTransportTests
        helper=ModelTransportTests()
        helper.test_close_one_transport_does_not_close_shared_channel()
