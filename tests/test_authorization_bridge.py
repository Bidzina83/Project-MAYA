"""Inert core tests: no native launcher, Hermes, SDK, pipe or security setup."""
import io
import json
import struct
import unittest
from unittest.mock import Mock, patch

from project_maya.bridge.audit import RequiredAudit
from project_maya.bridge.protocol import CHANNEL_LIMIT, Decoder, Encoder, ProtocolError, decode, encode
from project_maya.bridge.service import BridgeDenied, DocumentBridge, HostBinding, RESOURCE
from project_maya.governance import AuthorizationResult, GovernanceDecision, PolicyAuthorizationGateway, PolicyRule


class ProtocolTests(unittest.TestCase):
    def test_fragmented_roundtrip(self):
        wire = encode({"v": 1, "text": "fixture"})
        reader = Decoder()
        result = []
        for byte in wire:
            result.extend(reader.feed(bytes([byte])))
        self.assertEqual(result, [{"v": 1, "text": "fixture"}])
        reader.eof()

    def test_multiple_frames(self):
        self.assertEqual(Decoder().feed(encode({"a": 1}) + encode({"b": 2})), [{"a": 1}, {"b": 2}])

    def test_bad_json(self):
        for raw in (b'{"a":1,"a":2}', b'{"x":NaN}', b'{"x":Infinity}', b'{"x":1e999}',
                    b'{}{}', b'[]', b'\xef\xbb\xbf{}', b'\xff', b'{"x":"\\ud800"}'):
            with self.subTest(raw=raw), self.assertRaises(ProtocolError):
                decode(raw)

    def test_bad_lengths_and_terminal_state(self):
        for length in (0, 8193, 2**32-1):
            reader = Decoder()
            with self.assertRaises(ProtocolError):
                reader.feed(struct.pack("<I", length))
            self.assertTrue(reader.closed)
            with self.assertRaises(ProtocolError):
                reader.feed(encode({}))

    def test_truncated_eof(self):
        for raw in (b'\x03', struct.pack('<I', 3), struct.pack('<I', 3) + b'{'):
            reader = Decoder()
            reader.feed(raw)
            with self.assertRaises(ProtocolError):
                reader.eof()

    def test_frame_timeout_not_reset_by_trickle(self):
        clock = Mock(return_value=0)
        reader = Decoder(clock)
        reader.feed(b'\x03')
        clock.return_value = .9
        reader.feed(b'\x00')
        clock.return_value = 1
        with self.assertRaises(ProtocolError):
            reader.tick()

    def test_depth_and_encoding(self):
        value = {}
        for _ in range(8):
            value = {"x": value}
        with self.assertRaises(ProtocolError):
            encode(value)
        with self.assertRaises(ProtocolError):
            encode({"x": float("nan")})
        with self.assertRaises(ProtocolError):
            encode({"x": "a"*8192})

    def test_cumulative_budget(self):
        with self.assertRaises(ProtocolError):
            Decoder().feed(b'x'*(CHANNEL_LIMIT+1))
        writer = Encoder()
        writer.total = CHANNEL_LIMIT-1
        with self.assertRaises(ProtocolError):
            writer.frame({})
        self.assertTrue(writer.closed)


class AuditTests(unittest.TestCase):
    def test_real_record_flush_fsync(self):
        from project_maya.audit import AuditRecord
        stream = Mock()
        stream.write.side_effect = lambda raw: len(raw)
        record = AuditRecord("bridge.read_intent", "allow", "bridge.read_intent", "actor", "file.read", "target", "read", "internal-synthetic")
        with patch("project_maya.bridge.audit.os.fsync") as sync:
            RequiredAudit(stream).write(record)
        stream.flush.assert_called_once()
        sync.assert_called_once_with(stream.fileno())
        self.assertEqual(json.loads(stream.write.call_args.args[0])["event_type"], "bridge.read_intent")

    def test_short_write_poisoned(self):
        from project_maya.audit import AuditRecord
        stream = Mock()
        stream.write.return_value = 0
        sink = RequiredAudit(stream)
        record = AuditRecord("event", "allow", "reason", "actor", "cap", "target", "op", "internal")
        with self.assertRaisesRegex(OSError, "required_audit_failed"):
            sink.write(record)
        self.assertTrue(sink.failed)
        with self.assertRaises(OSError):
            sink.write(record)
        self.assertEqual(stream.write.call_count, 1)

    def test_flush_and_sync_failure_poisoned(self):
        from project_maya.audit import AuditRecord
        record = AuditRecord("event", "allow", "reason", "actor", "cap", "target", "op", "internal")
        for failure in ("flush", "sync"):
            stream = Mock()
            stream.write.side_effect = lambda raw: len(raw)
            if failure == "flush":
                stream.flush.side_effect = OSError("secret")
            sink = RequiredAudit(stream)
            with patch("project_maya.bridge.audit.os.fsync", side_effect=OSError("secret") if failure == "sync" else None):
                with self.assertRaisesRegex(OSError, '^bridge.required_audit_failed$'):
                    sink.write(record)
            self.assertTrue(sink.failed)

    def test_budget_failure_before_append(self):
        from project_maya.audit import AuditRecord
        stream = Mock()
        sink = RequiredAudit(stream, existing_bytes=131072)
        with self.assertRaises(OSError):
            sink.write(AuditRecord("event", "allow", "reason", "actor", "cap", "target", "op", "internal"))
        stream.write.assert_not_called()
        self.assertTrue(sink.failed)


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.binding = HostBinding("S-1-5-21-1-2-3-500", "a"*32, "b"*64)
        self.clock = Mock(return_value=0)
        self.audit = RequiredAudit(io.BytesIO())
        self.events = []
        self.audit.write = Mock(side_effect=lambda event: self.events.append(event))
        self.reader = Mock(return_value=b'MAYA synthetic private fixture')
        self.gateway = PolicyAuthorizationGateway((
            PolicyRule("file.read", RESOURCE, "read", "windows:"+self.binding.operator_sid),
            PolicyRule("file.disclose", "runtime:"+self.binding.attempt, "release", "windows:"+self.binding.operator_sid)))
        self.service = DocumentBridge(self.binding, self.gateway, self.audit, self.reader, self.clock)
        self.grant = self.service.issue()
        self.sender = Mock(side_effect=lambda raw: len(raw))

    def request(self, grant=None):
        grant = grant or self.grant
        return dict(v=1, type="request", attempt=self.binding.attempt, lease=grant["lease"],
                    seq=grant["next_seq"], operation="document.read", resource=RESOURCE)

    def handle(self, request=None, channel=None):
        self.service.handle(request if request is not None else self.request(), channel or self.binding.channel_id, self.sender)

    def test_allowed_two_gateways_and_audits_before_send(self):
        self.handle()
        self.assertEqual([x.event_type for x in self.events], ['bridge.read_intent', 'bridge.release_intent'])
        self.assertEqual(self.events[0].target, RESOURCE)
        self.assertEqual(self.events[1].target, 'runtime:'+self.binding.attempt)
        self.assertEqual(self.service.reads, 1)
        self.assertEqual(self.service.commits, 1)
        self.assertEqual(self.service.sent, 1)
        response = Decoder().feed(self.sender.call_args.args[0])[0]
        self.assertEqual(response["data"]["text"], self.reader.return_value.decode())
        self.assertNotIn(self.grant["lease"], ''.join(x.to_json() for x in self.events))

    def test_policy_denied_no_read(self):
        self.service._gateway = PolicyAuthorizationGateway(())
        with self.assertRaises(BridgeDenied):
            self.handle()
        self.reader.assert_not_called()
        self.sender.assert_not_called()

    def test_all_other_decisions_and_constraints_rejected(self):
        for decision in GovernanceDecision:
            if decision is GovernanceDecision.ALLOW:
                continue
            self.service._gateway = Mock(authorize=Mock(return_value=AuthorizationResult(decision, "reason")))
            with self.assertRaises(BridgeDenied):
                self.handle()
            self.grant = self.service.issue()
        self.service._gateway = Mock(authorize=Mock(return_value=AuthorizationResult(GovernanceDecision.ALLOW, "reason", constraints=("limit",))))
        with self.assertRaises(BridgeDenied):
            self.handle()
        self.reader.assert_not_called()

    def test_child_cannot_choose_identity_target_action_or_sequence(self):
        for key, value in (("actor_id", "admin"), ("resource", "../document.txt"), ("operation", "execute"),
                           ("seq", True), ("v", True), ("attempt", "c"*32), ("lease", "d"*64)):
            request = self.request()
            request[key] = value
            with self.assertRaises(BridgeDenied):
                self.handle(request)
            self.grant = self.service.issue()
        self.reader.assert_not_called()
        self.sender.assert_not_called()

    def test_channel_binding(self):
        with self.assertRaises(BridgeDenied):
            self.handle(channel="c"*64)
        self.reader.assert_not_called()

    def test_expiry(self):
        self.clock.return_value = 2
        with self.assertRaises(BridgeDenied):
            self.handle()
        self.reader.assert_not_called()

    def test_cancel_before_read(self):
        self.service.revoke()
        with self.assertRaises(BridgeDenied):
            self.handle()
        self.reader.assert_not_called()

    def test_replay_consumed_token(self):
        old = self.request()
        self.handle(old)
        self.grant = self.service.issue()
        old["seq"] = self.grant["next_seq"]
        with self.assertRaises(BridgeDenied):
            self.handle(old)
        self.assertEqual(self.reader.call_count, 1)
        self.assertEqual(self.sender.call_count, 1)

    def test_audit_failure_before_read(self):
        self.audit.write.side_effect = OSError("secret")
        with self.assertRaisesRegex(BridgeDenied, '^bridge.unavailable$'):
            self.handle()
        self.reader.assert_not_called()
        self.sender.assert_not_called()

    def test_disclosure_denial_after_read(self):
        self.service._gateway = PolicyAuthorizationGateway((PolicyRule("file.read", RESOURCE, "read", "windows:"+self.binding.operator_sid),))
        with self.assertRaises(BridgeDenied):
            self.handle()
        self.reader.assert_called_once()
        self.sender.assert_not_called()
        self.assertEqual(self.events[-1].capability, 'file.disclose')

    def test_release_audit_failure(self):
        self.audit.write.side_effect = [None, OSError("secret")]
        with self.assertRaises(BridgeDenied):
            self.handle()
        self.reader.assert_called_once()
        self.sender.assert_not_called()

    def test_cancel_during_read_blocks_release(self):
        def read():
            self.service.revoke()
            return b'synthetic'
        self.reader.side_effect = read
        with self.assertRaises(BridgeDenied):
            self.handle()
        self.sender.assert_not_called()

    def test_cancel_after_commit_does_not_fake_rollback(self):
        def send(raw):
            self.service.revoke()
            return len(raw)
        self.sender.side_effect = send
        self.handle()
        self.assertEqual((self.service.commits, self.service.sent), (1, 1))

    def test_partial_send_is_uncertain_and_not_retried(self):
        self.sender.return_value = 1
        self.sender.side_effect = None
        with self.assertRaisesRegex(BridgeDenied, '^bridge.uncertain$'):
            self.handle()
        self.assertEqual((self.service.commits, self.service.sent), (1, 0))
        with self.assertRaises(BridgeDenied):
            self.service.issue()
        self.sender.assert_called_once()

    def test_invalid_document_is_not_released(self):
        self.reader.return_value = b'x'*1025
        with self.assertRaises(BridgeDenied):
            self.handle()
        self.sender.assert_not_called()

    def test_gateway_exception_sanitized(self):
        self.service._gateway = Mock(authorize=Mock(side_effect=RuntimeError("private details")))
        with self.assertRaisesRegex(BridgeDenied, '^bridge.unavailable$'):
            self.handle()
        self.reader.assert_not_called()

    def test_reader_exception_is_an_attempt_not_zero_effect_claim(self):
        self.reader.side_effect = OSError("private path")
        with self.assertRaises(BridgeDenied):
            self.handle()
        self.assertEqual((self.service.read_attempts, self.service.reads), (1, 0))
        self.sender.assert_not_called()

    def test_required_audit_fault_prevents_next_lease(self):
        stream = Mock()
        stream.write.return_value = 0
        self.service._audit = RequiredAudit(stream)
        with self.assertRaises(BridgeDenied):
            self.handle()
        with self.assertRaises(BridgeDenied):
            self.service.issue()
        self.reader.assert_not_called()

    def test_denial_audit_failure_also_closes_channel(self):
        self.service._gateway = PolicyAuthorizationGateway(())
        self.audit.write.side_effect = OSError("secret")
        with self.assertRaises(BridgeDenied):
            self.handle()
        with self.assertRaises(BridgeDenied):
            self.service.issue()

    def test_unhandled_redaction_rejected(self):
        self.service._gateway = Mock(authorize=Mock(return_value=AuthorizationResult(
            GovernanceDecision.ALLOW, "reason", redactions={"text":"withheld"})))
        with self.assertRaises(BridgeDenied):
            self.handle()
        self.reader.assert_not_called()

    def test_request_and_lease_budget(self):
        for _ in range(15):
            self.service.revoke()
            self.grant = self.service.issue()
        self.service.revoke()
        with self.assertRaises(BridgeDenied):
            self.service.issue()

    def test_expiry_after_read_prevents_release(self):
        def read():
            self.clock.return_value = 2
            return b'synthetic'
        self.reader.side_effect = read
        with self.assertRaises(BridgeDenied):
            self.handle()
        self.sender.assert_not_called()

    def test_delivery_confirmation_is_audited_without_content(self):
        self.handle()
        self.service.delivery_observed(True, 'c'*32)
        event = self.events[-1]
        self.assertEqual(event.event_type, 'bridge.delivery_observed')
        self.assertEqual(event.reason_code, 'bridge.sent')
        self.assertNotIn('synthetic private fixture', event.to_json())

    def test_post_delivery_audit_failure_is_uncertain_not_rollback(self):
        self.handle()
        self.audit.write.side_effect = OSError('private')
        with self.assertRaisesRegex(BridgeDenied, '^bridge.uncertain$'):
            self.service.delivery_observed(True, 'c'*32)
        self.assertEqual((self.service.commits,self.service.sent), (1,1))
        with self.assertRaises(BridgeDenied):
            self.service.issue()

    def test_delivery_cannot_claim_success_after_denial(self):
        self.service.revoke()
        with self.assertRaises(BridgeDenied):
            self.handle()
        with self.assertRaises(BridgeDenied):
            self.service.delivery_observed(True, 'c'*32)


if __name__ == '__main__':
    unittest.main()
