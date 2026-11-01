"""M03c memory-only worker/codec fixtures; no native Hermes, SDK or Win32 setup."""
import copy
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch

from project_maya.bridge.audit import RequiredAudit
from project_maya.bridge.model_service import ModelDenied, OfflineModelBridge, digest
from project_maya.bridge.model_attempt_validation import (
    mismatched_attempt, WrongAttemptBridge, attempt_request, attempt_projection, verify_attempt_audit,
)
from project_maya.bridge.model_worker import serve_model
from project_maya.bridge.protocol import ProtocolError
from project_maya.bridge.service import HostBinding
from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins.model_bridge import WrongAttemptChannelClient
from test_model_bridge_worker_inert import (
    ATTEMPT, SID, CHANNEL, CANARY, OUTPUT, LITERALS, CoordinatorFixture, expected_request, policy,
)


WRONG_ATTEMPT = mismatched_attempt(ATTEMPT)


class AttemptTests(unittest.TestCase):
    def test_deterministic_first_digit_change_for_all_hex_digits(self):
        for digit in '0123456789abcdef':
            original = digit+'f'*31
            observed = mismatched_attempt(original)
            self.assertEqual(observed, ('1' if digit == '0' else '0')+original[1:])
            self.assertEqual(len(observed), 32)
            self.assertNotEqual(observed, original)
        for invalid in ('', 'A'*32, 'a'*31, 'a'*33, None, 1):
            with self.subTest(invalid=invalid), self.assertRaises(ProtocolError): mismatched_attempt(invalid)

    def setUp(self):
        sync = patch('project_maya.bridge.audit.os.fsync'); sync.start(); self.addCleanup(sync.stop)
        self.records = []
        self.stream = Mock()
        self.stream.write.side_effect = lambda raw: self.records.append(json.loads(raw)) or len(raw)
        self.audit = RequiredAudit(self.stream)
        self.peer = CoordinatorFixture()
        self.peer.modify = self.mutate
        self.config = dict(operator_sid=SID, attempt=ATTEMPT, channel_id=CHANNEL,
            utc_day='2026-10-24', canary=CANARY, fixture_text=OUTPUT)
        self.binding = HostBinding(SID, ATTEMPT, CHANNEL)

    def mutate(self, message):
        if message['type'] == 'model_dispatch':
            message['request']['attempt'] = WRONG_ATTEMPT
        return message

    def run_worker(self, **kwargs):
        return serve_model(self.peer, self.config, kwargs.pop('rules', policy()), LITERALS.read_bytes(),
            self.audit, self.peer.write_expected, wrong_attempt=True, **kwargs)

    def raw(self):
        return b''.join(json.dumps(record).encode()+b'\n' for record in self.records)

    def verify(self, raw=None, **kwargs):
        return verify_attempt_audit(self.raw() if raw is None else raw, self.binding,
            kwargs.get('service_id', self.peer.sent[0]['service_request_id']),
            kwargs.get('command_id', format(2, '032x')),
            kwargs.get('lease', self.peer.sent[1]['grant']['lease']),
            kwargs.get('body', expected_request()), digest(OUTPUT.encode()))

    def service(self, clock=lambda: 0):
        return WrongAttemptBridge(self.binding,
            PolicyAuthorizationGateway(tuple(PolicyRule(**rule) for rule in policy()['allow'])),
            self.audit, expected_request(), OUTPUT, clock=clock)

    def test_exact_single_attempt_mutation_preserves_all_body_bytes(self):
        original = attempt_request(self.binding, 'e'*64, expected_request())
        mutant = attempt_request(self.binding, 'e'*64, expected_request(), mutant=True)
        self.assertEqual([key for key in original if original[key] != mutant[key]], ['attempt'])
        self.assertEqual(mutant['body'].encode(), expected_request())
        first = attempt_projection(self.binding, 'e'*64, expected_request())
        second = attempt_projection(self.binding, 'e'*64, expected_request(), mutant=True)
        self.assertNotEqual(digest(first), digest(second)); self.assertEqual(len(first), len(second))
        self.assertNotIn(('e'*64).encode(), first); self.assertNotIn(CANARY.encode(), first)

    def test_named_attempt_boundary_exact_ledger_zero_gateway_effects(self):
        with patch.object(PolicyAuthorizationGateway, 'authorize', side_effect=AssertionError('forbidden')) as gateway:
            result = self.run_worker(); gateway.assert_not_called()
        self.assertEqual(result['case'], 'M03c'); self.assertEqual(result['stage'], 'request_attempt')
        self.assertEqual(result['request_sha256'], result['mutated_request_sha256'])
        for key in ('gateway_calls', 'dispatches', 'runtime_prepared', 'runtime_released', 'operator_prepared', 'operator_released'):
            self.assertEqual(result[key], '0')
        self.assertEqual(self.verify(), 1)
        self.assertEqual([m['type'] for m in self.peer.sent], ['model_worker_ready', 'model_grant_reply', 'model_attempt_rejected'])
        self.assertNotIn(CANARY, self.raw().decode()); self.assertNotIn(self.peer.sent[1]['grant']['lease'], self.raw().decode())

    def test_positive_control_fresh_service_still_dispatches(self):
        service = OfflineModelBridge(self.binding,
            PolicyAuthorizationGateway(tuple(PolicyRule(**r) for r in policy()['allow'])),
            self.audit, expected_request(), OUTPUT)
        grant = service.issue()
        reply = service.prepare_runtime(attempt_request(self.binding, grant['lease'], expected_request()), CHANNEL)
        self.assertEqual(reply['status'], 'ok'); self.assertEqual(service.gateway_calls, 2)
        self.assertEqual(service.dispatches, 1); service.close()

    def test_unmutated_or_second_changed_field_cannot_pass(self):
        variants = {'attempt':ATTEMPT, 'route':'maya.offline.model.v0', 'lease':'f'*64, 'seq':2,
            'method':'GET', 'path':'/other', 'body':expected_request().decode()+' ', 'extra':0, 'v':True}
        for key, value in variants.items():
            self.peer = CoordinatorFixture()
            def mutate(message):
                message = self.mutate(message)
                if message['type'] == 'model_dispatch': message['request'][key] = value
                return message
            self.peer.modify = mutate
            with self.subTest(key=key), self.assertRaises(ProtocolError): self.run_worker()
            self.assertNotIn('model_attempt_rejected', [m['type'] for m in self.peer.sent])

    def test_wrong_outer_attempt_is_not_the_inner_diagnostic(self):
        def mutate(message):
            message = self.mutate(message)
            if message['type'] == 'model_dispatch': message['attempt'] = WRONG_ATTEMPT
            return message
        self.peer.modify = mutate
        with self.assertRaises(ProtocolError): self.run_worker()
        self.assertNotIn('model_attempt_rejected', [m['type'] for m in self.peer.sent])

    def test_nonfixed_mutant_does_not_pass(self):
        def mutate(message):
            if message['type'] == 'model_dispatch': message['request']['attempt'] = 'f'*32
            return message
        self.peer.modify = mutate
        with self.assertRaises(ProtocolError): self.run_worker()
        self.assertNotIn('model_attempt_rejected', [m['type'] for m in self.peer.sent])

    def test_effect_or_wrong_boundary_observation_cannot_be_admitted(self):
        for field, value in (('gateway_calls',1),('dispatch_attempted',True),('request_validated',True),
                ('egress_gateway_denied',True),('envelope_identity_validated',True),
                ('envelope_attempt_context_validated',False),('validation_stage','request_route'),
                ('prepared_runtime_releases',1),('confirmed_runtime_releases',1),
                ('prepared_operator_releases',1),('confirmed_operator_releases',1)):
            service = self.service(); service.bind_command('d'*32); grant = service.issue()
            with self.assertRaises(ModelDenied):
                service.prepare_runtime(attempt_request(self.binding, grant['lease'], expected_request(), mutant=True), CHANNEL)
            self.assertEqual(service.evidence()['case'],'M03c')
            setattr(service,field,value)
            with self.subTest(field=field), self.assertRaises(ProtocolError): service.evidence()

    def test_each_missing_envelope_field_rejected(self):
        for key in ('v','type','attempt','route','lease','seq','method','path','body'):
            service = self.service(); service.bind_command('d'*32); grant = service.issue()
            message = attempt_request(self.binding, grant['lease'], expected_request(), mutant=True); del message[key]
            with self.subTest(key=key), self.assertRaises(ProtocolError): service.prepare_runtime(message, CHANNEL)
            with self.assertRaises(ProtocolError): service.evidence()

    def test_channel_binding_failure_not_route_evidence(self):
        service = self.service(); service.bind_command('d'*32); grant = service.issue()
        with self.assertRaises(ModelDenied):
            service.prepare_runtime(attempt_request(self.binding, grant['lease'], expected_request(), mutant=True), 'f'*64)
        with self.assertRaises(ProtocolError): service.evidence()
        self.assertFalse(service.envelope_identity_validated)

    def test_expiry_revocation_closed_or_unissued_are_not_negative_passes(self):
        for fault in ('expired','revoked','closed','unissued'):
            now = [0]; service = self.service(clock=lambda:now[0]); service.bind_command('d'*32)
            grant = service.issue() if fault != 'unissued' else {'lease':'e'*64}
            if fault == 'expired': now[0] = 3
            if fault == 'revoked': service.revoke()
            if fault == 'closed': service.close()
            with self.subTest(fault=fault), self.assertRaises((ModelDenied, ProtocolError)):
                service.prepare_runtime(attempt_request(self.binding, grant['lease'], expected_request(), mutant=True), CHANNEL)
            with self.assertRaises(ProtocolError): service.evidence()
            self.assertFalse(service.validation_recorded); self.assertEqual(service.gateway_calls, 0)

    def test_command_binding_required_once(self):
        service = self.service(); service.issue()
        with self.assertRaises(ProtocolError): service.metadata()
        service.bind_command('d'*32)
        with self.assertRaises(ProtocolError): service.bind_command('e'*32)
        service.close()
        with self.assertRaises(ProtocolError): service.evidence()

    def test_M02_policy_or_non_boolean_or_combined_mode_rejected(self):
        with self.assertRaises(ProtocolError): self.run_worker(rules={'allow':policy()['allow'][1:]})
        for mode in (1, None, 'M03c'):
            with self.subTest(mode=mode), self.assertRaises(ProtocolError):
                serve_model(self.peer, self.config, policy(), LITERALS.read_bytes(), self.audit,
                    self.peer.write_expected, wrong_attempt=mode)
        for mode in ('deny_egress','wrong_model','wrong_route'):
            with self.subTest(mode=mode), self.assertRaises(ProtocolError): self.run_worker(**{mode:True})

    def test_required_audit_failures_never_emit_success(self):
        for fault in ('write','short','flush','sync'):
            self.peer = CoordinatorFixture(); self.peer.modify = self.mutate
            self.audit = RequiredAudit(self.stream); self.stream.flush.side_effect = None
            self.stream.write.side_effect = lambda raw:len(raw)
            with patch('project_maya.bridge.audit.os.fsync') as sync:
                if fault == 'write': self.stream.write.side_effect = OSError('private')
                elif fault == 'short': self.stream.write.side_effect = lambda raw:len(raw)-1
                elif fault == 'flush': self.stream.flush.side_effect = OSError('private')
                else: sync.side_effect = OSError('private')
                with self.subTest(fault=fault), self.assertRaises(ProtocolError): self.run_worker()
                self.assertTrue(self.audit.failed)
                self.assertNotIn('model_attempt_rejected', [m['type'] for m in self.peer.sent])

    def test_all_ledger_fields_and_rebound_grant_or_ids_rejected(self):
        self.run_worker(); record = copy.deepcopy(self.records[0])
        for key in record['metadata']:
            self.records[0] = copy.deepcopy(record); self.records[0]['metadata'][key] = 'wrong'
            with self.subTest(key=key), self.assertRaises(ProtocolError): self.verify()
        for key in record:
            self.records[0] = copy.deepcopy(record); del self.records[0][key]
            with self.subTest(key=key), self.assertRaises(ProtocolError): self.verify()
        self.records[0] = record
        for changed in ({'lease':'f'*64}, {'service_id':'f'*32}, {'command_id':'f'*32}, {'body':expected_request()+b' '}):
            with self.subTest(changed=tuple(changed)), self.assertRaises(ProtocolError): self.verify(**changed)
        for raw in (b'',self.raw()[:-1],self.raw()*2,b'\xff\n',b'x'*131073):
            with self.subTest(length=len(raw)), self.assertRaises((ProtocolError, UnicodeError)): self.verify(raw)

    def test_generic_failure_after_ready_is_not_route_rejection(self):
        with patch.object(WrongAttemptBridge, 'prepare_runtime', side_effect=RuntimeError('private')):
            with self.assertRaises(RuntimeError): self.run_worker()
        self.assertNotIn('model_attempt_rejected', [m['type'] for m in self.peer.sent])

    def test_child_control_case_and_reason_are_exact(self):
        from test_model_denial_inert import ChildDenialTransportTests
        helper = ChildDenialTransportTests()
        right = dict(v=1, type='model_denied', attempt=ATTEMPT, seq=1, case='M03c', reason='request_attempt_rejected')
        for reply, observed in ((right,True),(dict(right,case='M03b'),False),
                (dict(right,reason='request_model_rejected'),False),(dict(right,v=True),False)):
            client = helper.client(reply, WrongAttemptChannelClient)
            with self.assertRaises(ProtocolError): client.exchange(expected_request())
            self.assertEqual(client.denial_observed, observed)

    def test_route_entries_fail_preflight_without_loading_runtime(self):
        root = Path(__file__).resolve().parents[1]/'src/project_maya/windows_runtime'
        for name in ('model_attempt_child_entry.py','model_attempt_worker_entry.py'):
            with self.subTest(name=name), patch('sys.platform','linux'), self.assertRaises(SystemExit) as caught:
                runpy.run_path(str(root/name), run_name='__main__')
            self.assertEqual(caught.exception.code, 2)

    def test_validation_support_import_does_not_launch(self):
        root = Path(__file__).resolve().parents[1]/'src/project_maya/windows_runtime'
        namespace = runpy.run_path(str(root/'model_validation_worker_entry.py'), run_name='inert_support')
        self.assertTrue(callable(namespace['launch']))
