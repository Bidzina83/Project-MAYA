"""M02 source fixtures only. No bundled Hermes/SDK or Windows setup execution."""
import copy
import io
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch

from project_maya.bridge.audit import RequiredAudit
from project_maya.bridge.model_denial import denial_evidence, verify_denial_audit
from project_maya.bridge.model_service import digest
from project_maya.bridge.model_worker import serve_model
from project_maya.bridge.protocol import ProtocolError
from project_maya.bridge.service import HostBinding
from project_maya.bridge.transport import PrivateChannel
from project_maya.hermes_plugins.model_bridge import EgressDenialChannelClient, ModelChannelClient
from test_model_bridge_worker_inert import (
    ATTEMPT, CANARY, CHANNEL, LITERALS, OUTPUT, SID, CoordinatorFixture, expected_request, policy,
)


class DenialWorkerTests(unittest.TestCase):
    def setUp(self):
        sync = patch("project_maya.bridge.audit.os.fsync")
        sync.start(); self.addCleanup(sync.stop)
        self.records = []
        self.stream = Mock()
        self.stream.write.side_effect = lambda raw: self.records.append(json.loads(raw)) or len(raw)
        self.audit = RequiredAudit(self.stream)
        self.channel = CoordinatorFixture()
        self.config = dict(operator_sid=SID, attempt=ATTEMPT, channel_id=CHANNEL,
                           utc_day="2026-10-24", canary=CANARY, fixture_text=OUTPUT)

    def run_worker(self, rules=None, mode=True):
        rules = {"allow":policy()["allow"][1:]} if rules is None else rules
        return serve_model(self.channel, self.config, rules, LITERALS.read_bytes(),
                           self.audit, self.channel.write_expected, deny_egress=mode)

    def raw(self):
        return b"".join(json.dumps(r).encode()+b"\n" for r in self.records)

    def verify(self, raw=None):
        return verify_denial_audit(self.raw() if raw is None else raw,
            HostBinding(SID, ATTEMPT, CHANNEL), self.channel.sent[0]["service_request_id"],
            expected_request(), digest(OUTPUT.encode()))

    def test_real_gateway_denial_zero_effects_exact_ledger(self):
        result = self.run_worker()
        self.assertEqual(result, dict(case="M02", boundary="gateway_egress", request_validated=True,
            gateway_denied=True, dispatches=0, confirmed_runtime_releases=0,
            confirmed_operator_releases=0, real_inference=False))
        self.assertEqual([m["type"] for m in self.channel.sent],
                         ["model_worker_ready", "model_grant_reply", "model_egress_denied"])
        self.assertEqual(self.channel.index, 2)
        self.assertEqual(self.verify(), 1)
        self.assertNotIn(CANARY, self.raw().decode())

    def test_M01_allow_policy_rejected_by_M02_before_worker_ready(self):
        with self.assertRaises(ProtocolError): self.run_worker(policy())
        self.assertEqual(self.channel.sent, [])

    def test_M02_policy_rejected_by_positive_profile(self):
        with self.assertRaises(ProtocolError): self.run_worker(mode=False)
        self.assertEqual(self.channel.sent, [])

    def test_non_boolean_mode_rejected(self):
        for mode in (1, 0, "M02", None):
            with self.subTest(mode=mode), self.assertRaises(ProtocolError): self.run_worker(mode=mode)

    def test_different_policy_actor_or_rule_rejected(self):
        for field in ("actor_id", "target", "operation", "capability"):
            rules = {"allow":copy.deepcopy(policy()["allow"][1:])}
            rules["allow"][0][field] = "*"
            with self.subTest(field=field), self.assertRaises(ProtocolError): self.run_worker(rules)

    def test_bad_body_is_not_accepted_as_gateway_denial(self):
        def modify(message):
            if message["type"] == "model_dispatch": message["request"]["body"] = "{}"
            return message
        self.channel.modify = modify
        with self.assertRaises(ProtocolError): self.run_worker()
        self.assertNotIn("model_egress_denied", [m["type"] for m in self.channel.sent])

    def test_wrong_route_lease_attempt_is_not_expected_denial(self):
        for key in ("route", "lease", "attempt"):
            self.channel = CoordinatorFixture()
            def modify(message):
                if message["type"] == "model_dispatch": message["request"][key] = "bad"
                return message
            self.channel.modify = modify
            with self.subTest(key=key), self.assertRaises(ProtocolError): self.run_worker()
            self.assertNotIn("model_egress_denied", [m["type"] for m in self.channel.sent])

    def test_gateway_exception_not_accepted(self):
        with patch("project_maya.governance.PolicyAuthorizationGateway.authorize", side_effect=RuntimeError("secret")):
            with self.assertRaises(ProtocolError): self.run_worker()
        self.assertNotIn("secret", json.dumps(self.channel.sent))

    def test_audit_write_flush_and_sync_faults_never_return_denial(self):
        for stage in ("write", "flush", "sync"):
            self.channel = CoordinatorFixture()
            self.audit = RequiredAudit(self.stream)
            self.stream.write.side_effect = (lambda raw:len(raw))
            self.stream.flush.side_effect = None
            target = "project_maya.bridge.audit.os.fsync"
            with patch(target) as sync:
                if stage == "write": self.stream.write.side_effect = OSError("private")
                elif stage == "flush": self.stream.flush.side_effect = OSError("private")
                else: sync.side_effect = OSError("private")
                with self.subTest(stage=stage), self.assertRaises(ProtocolError): self.run_worker()
                self.assertTrue(self.audit.failed)
                self.assertNotIn("model_egress_denied", [m["type"] for m in self.channel.sent])

    def test_short_audit_write_blocks(self):
        self.stream.write.side_effect = lambda raw:len(raw)-1
        with self.assertRaises(ProtocolError): self.run_worker()

    def test_ledger_mutations_rejected(self):
        self.run_worker()
        original = copy.deepcopy(self.records[0])
        for key in original:
            self.records[0] = copy.deepcopy(original)
            del self.records[0][key]
            with self.subTest(missing=key), self.assertRaises(ProtocolError): self.verify()
        for key in original["metadata"]:
            self.records[0] = copy.deepcopy(original)
            self.records[0]["metadata"][key] = "wrong"
            with self.subTest(metadata=key), self.assertRaises(ProtocolError): self.verify()
        for key, value in (("decision","allow"), ("schema_version",True), ("capability","model.output"),
                           ("timestamp","2026-10-24T12:00:00+04:00"), ("timestamp","2026-02-30T12:00:00Z")):
            self.records[0] = copy.deepcopy(original)
            self.records[0][key] = value
            with self.subTest(key=key,value=value), self.assertRaises(ProtocolError): self.verify()
        self.records[0] = original
        for raw in (b"", self.raw()[:-1], self.raw()*2, b"\xff\n", b"x"*131073):
            with self.subTest(size=len(raw)), self.assertRaises((ProtocolError, UnicodeError)): self.verify(raw)

    def test_uncertain_effect_or_unreached_gateway_rejected(self):
        values = dict(closed=True, request_validated=True, egress_gateway_denied=True,
                      dispatch_attempted=False, dispatches=0, prepared_runtime_releases=0,
                      confirmed_runtime_releases=0, prepared_operator_releases=0,
                      confirmed_operator_releases=0)
        for key,value in values.items():
            changed = values.copy(); changed[key] = not value if type(value) is bool else 1
            service = Mock(**changed)
            with self.subTest(key=key), self.assertRaises(ProtocolError): denial_evidence(service,self.audit)


class ChildDenialTransportTests(unittest.TestCase):
    def test_new_native_bootstraps_exit_before_loading_runtime_off_windows(self):
        runtime = Path(__file__).resolve().parents[1]/"src/project_maya/windows_runtime"
        for name in ("model_deny_child_entry.py", "model_deny_worker_entry.py"):
            with self.subTest(name=name), patch("sys.platform", "linux"), self.assertRaises(SystemExit) as exit:
                runpy.run_path(str(runtime/name), run_name="not_product_main")
            self.assertEqual(exit.exception.code, 2)

    def client(self, reply, cls=EgressDenialChannelClient):
        source = io.BytesIO()
        PrivateChannel(io.BytesIO(),source).send(reply)
        source.seek(0)
        client = cls(PrivateChannel(source,io.BytesIO()),ATTEMPT)
        client.bind_grant(dict(v=1,type="model_grant",attempt=ATTEMPT,route="maya.offline.model.v1",
            lease="e"*64,seq=1,ttl_ms=2000,request_sha256=digest(expected_request())))
        return client

    def test_exact_denial_observed_but_never_returns_response(self):
        reply = dict(v=1,type="model_denied",attempt=ATTEMPT,seq=1,case="M02",reason="gateway_egress_denied")
        client = self.client(reply)
        with self.assertRaises(ProtocolError): client.exchange(expected_request())
        self.assertTrue(client.denial_observed)
        self.assertTrue(client.closed)
        with self.assertRaises(ProtocolError): client.exchange(expected_request())
        self.assertEqual(client.requests,1)

    def test_forged_missing_extra_denial_controls_not_observed(self):
        original = dict(v=1,type="model_denied",attempt=ATTEMPT,seq=1,case="M02",reason="gateway_egress_denied")
        variants = [dict(original, v=True),dict(original,seq=True),dict(original,attempt="b"*32),
                    dict(original,case="M03"),dict(original,body="private"),dict(original,reason="error")]
        variants += [{k:v for k,v in original.items() if k != key} for key in original]
        for reply in variants:
            client = self.client(reply)
            with self.subTest(reply=reply), self.assertRaises(ProtocolError): client.exchange(expected_request())
            self.assertFalse(client.denial_observed)

    def test_positive_endpoint_does_not_accept_denial_as_model_response(self):
        client = self.client(dict(v=1,type="model_denied",attempt=ATTEMPT,seq=1,
                                 case="M02",reason="gateway_egress_denied"), ModelChannelClient)
        with self.assertRaises(ProtocolError): client.exchange(expected_request())
