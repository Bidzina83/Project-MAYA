"""Host-broker unit controls; not native or Windows containment qualification."""

import json
import threading
from urllib.error import HTTPError
from urllib.request import Request, ProxyHandler, build_opener
import unittest

from project_maya.audit import NullAuditSink
from project_maya.governance import (
    AuthorizationResult, GovernanceDecision, PolicyAuthorizationGateway, PolicyRule,
)
from project_maya.hermes_plugins.restricted_broker import (
    BrokerDenied, BrokerIdentity, RestrictedBroker,
)
from project_maya.hermes_plugins.restricted_broker_http import build_test_broker_server


class Audit:
    def __init__(self):
        self.records = []
        self.fail = False

    def write(self, record):
        if self.fail:
            raise RuntimeError("synthetic-secret")
        self.records.append(record)


class BrokerTests(unittest.TestCase):
    def setUp(self):
        self.audit, self.effects, self.now = Audit(), [], [1.0]
        self.gateway = PolicyAuthorizationGateway(tuple(
            PolicyRule(capability=c, actor_id="operator")
            for c in ("file.read", "memory.search", "model.egress", "model.output")
        ))
        self.broker = self.make()

    def make(self, **kwargs):
        defaults = dict(identity=BrokerIdentity("operator", "request-1", "confidential"),
                        gateway=self.gateway, audit=self.audit, document_id="doc-1",
                        memory_id="smb-1", clock=lambda: self.now[0],
                        read_document=lambda: self.effect("document"),
                        search_memory=lambda query: self.effect("memory"),
                        model_transport=lambda body: self.effect("model"),
                        validate_result=lambda result: result)
        defaults.update(kwargs)
        return RestrictedBroker(**defaults)

    def effect(self, value):
        self.effects.append(value)
        return {"value": value}

    def call(self, route="/maya/document/read", body=None, token=None):
        return self.broker.handle(token or self.broker.admission_token, route,
                                  json.dumps(body or {"document_id": "doc-1"}).encode())

    def test_allowed_read_policy_and_audit_before_effect(self):
        self.assertEqual(self.call(), {"value": "document"})
        record = self.audit.records[0]
        self.assertEqual(record.actor_id, "operator")
        self.assertEqual(record.data_classification, "confidential")
        self.assertNotIn(self.broker.admission_token, record.to_json())

    def test_model_and_followup_authorized_separately(self):
        body = {"model": "gpt-6-luna", "input": "synthetic prompt"}
        self.call("/v1/responses", body)
        self.call()
        self.call("/v1/responses", body)
        self.assertEqual(self.effects, ["model", "document", "model"])
        self.assertEqual(len(self.audit.records), 3)
        self.assertNotIn("synthetic prompt", self.audit.records[0].to_json())

    def test_memory_route(self):
        self.call("/maya/memory/search", {"memory_id": "smb-1", "query": "sales"})
        self.assertEqual(self.effects, ["memory"])

    def test_wrong_token_no_effect(self):
        with self.assertRaises(BrokerDenied):
            self.call(token="wrong")
        self.assertEqual(self.effects, [])

    def test_missing_token_no_effect(self):
        with self.assertRaises(BrokerDenied):
            self.broker.handle("", "/maya/document/read", b'{}')
        self.assertEqual(self.effects, [])

    def test_revoked_token(self):
        self.broker.revoke()
        with self.assertRaises(BrokerDenied):
            self.call()

    def test_expired_token(self):
        self.now[0] = 31
        with self.assertRaises(BrokerDenied):
            self.call()

    def test_new_broker_cannot_adopt_old_admission(self):
        old = self.broker.admission_token
        self.broker = self.make()
        with self.assertRaises(BrokerDenied):
            self.call(token=old)

    def test_wrong_target_and_body_authority(self):
        for body in ({"document_id": "other"},
                     {"document_id": "doc-1", "actor_id": "admin"},
                     {"document_id": "doc-1", "classification": "public"}):
            self.broker = self.make()
            with self.subTest(body=body), self.assertRaises(BrokerDenied):
                self.call(body=body)
        self.assertEqual(self.effects, [])

    def test_unsupported_routes(self):
        for route in ("/maya/policy/write", "https://example.org", "/v1/chat/completions"):
            self.broker = self.make()
            with self.subTest(route=route), self.assertRaises(BrokerDenied):
                self.call(route)
        self.assertEqual(self.effects, [])

    def test_bad_model_and_store(self):
        for body in ({"model": "other", "input": "x"},
                     {"model": "gpt-6-luna", "input": "x", "store": True}):
            self.broker = self.make()
            with self.subTest(body=body), self.assertRaises(BrokerDenied):
                self.call("/v1/responses", body)
        self.assertEqual(self.effects, [])

    def test_duplicate_json_key(self):
        with self.assertRaises(BrokerDenied):
            self.broker.handle(self.broker.admission_token, "/maya/document/read",
                               b'{"document_id":"other","document_id":"doc-1"}')

    def test_invalid_and_oversized_json(self):
        for raw in (b'not json', b'[]', b'x' * (256 * 1024 + 1)):
            self.broker = self.make()
            with self.subTest(size=len(raw)), self.assertRaises(BrokerDenied):
                self.broker.handle(self.broker.admission_token, "/maya/document/read", raw)

    def test_denied_policy_zero_effect(self):
        self.broker = self.make(gateway=PolicyAuthorizationGateway(()))
        with self.assertRaises(BrokerDenied):
            self.call()
        self.assertEqual(self.effects, [])
        self.assertEqual(self.audit.records[0].decision, "deny")

    def test_audit_failure_zero_effect_and_fixed_error(self):
        self.audit.fail = True
        with self.assertRaisesRegex(BrokerDenied, "^broker.request_failed$"):
            self.call()
        self.assertEqual(self.effects, [])

    def test_constraint_is_not_allow(self):
        class Constrained:
            def authorize(self, request):
                return AuthorizationResult(GovernanceDecision.ALLOW, "x", constraints=("limit",))
        self.broker = self.make(gateway=Constrained())
        with self.assertRaises(BrokerDenied):
            self.call()
        self.assertEqual(self.effects, [])

    def test_budget(self):
        self.broker = self.make(max_effects=1)
        self.call()
        with self.assertRaises(BrokerDenied):
            self.call()
        self.assertEqual(self.effects, ["document"])

    def test_expiry_during_effect_no_result(self):
        def read():
            self.now[0] = 31
            return {"value": "secret"}
        self.broker = self.make(read_document=read)
        with self.assertRaises(BrokerDenied):
            self.call()

    def test_delivery_validated_once_then_revoked(self):
        token = self.broker.admission_token
        self.assertEqual(self.broker.deliver(token, "answer"), "answer")
        with self.assertRaises(BrokerDenied):
            self.broker.deliver(token, "answer")

    def test_output_validator_failure_no_delivery(self):
        def reject(result):
            raise RuntimeError("synthetic-secret")
        self.broker = self.make(validate_result=reject)
        with self.assertRaisesRegex(BrokerDenied, "^broker.delivery_failed$"):
            self.broker.deliver(self.broker.admission_token, "raw")

    def test_null_audit_refused(self):
        with self.assertRaises(ValueError):
            self.make(audit=NullAuditSink())

    def test_revoke_does_not_wait_for_running_effect(self):
        entered, finish = threading.Event(), threading.Event()
        errors = []
        def read():
            entered.set()
            if not finish.wait(3):
                raise RuntimeError("test.timeout")
            return "result"
        self.broker = self.make(read_document=read)
        def run():
            try:
                self.call()
            except BrokerDenied as error:
                errors.append(str(error))
        worker = threading.Thread(target=run)
        worker.start()
        try:
            self.assertTrue(entered.wait(3))
            self.broker.revoke()
        finally:
            finish.set()
            worker.join(3)
        self.assertFalse(worker.is_alive())
        self.assertEqual(errors, ["broker.admission_denied"])

    def test_nonfinite_json_rejected(self):
        for value in (b'NaN', b'Infinity', b'1e999'):
            self.broker = self.make()
            with self.subTest(value=value), self.assertRaises(BrokerDenied):
                self.broker.handle(self.broker.admission_token, "/v1/responses",
                    b'{"model":"gpt-6-luna","input":' + value + b'}')
        self.assertEqual(self.effects, [])

    def test_denial_revokes_remaining_request(self):
        token = self.broker.admission_token
        with self.assertRaises(BrokerDenied):
            self.call("/maya/policy/write")
        with self.assertRaisesRegex(BrokerDenied, "broker.admission_denied"):
            self.call(token=token)
        self.assertEqual(self.effects, [])

    def test_actual_loopback_server_allowed_and_denied(self):
        server = build_test_broker_server(self.broker)
        worker = threading.Thread(target=server.serve_forever)
        worker.start()
        try:
            endpoint = f"http://127.0.0.1:{server.server_port}/maya/document/read"
            opener = build_opener(ProxyHandler({}))
            def request(token):
                return Request(endpoint, data=b'{"document_id":"doc-1"}',
                    headers={"Authorization": "Bearer " + token,
                             "Content-Type": "application/json"})
            with opener.open(request(self.broker.admission_token), timeout=3) as response:
                self.assertEqual(json.load(response), {"value": "document"})
            with self.assertRaises(HTTPError) as raised:
                opener.open(request("wrong"), timeout=3)
            self.assertEqual(raised.exception.code, 403)
            self.assertEqual(json.load(raised.exception), {"error": "broker.denied"})
            raised.exception.close()
            self.assertEqual(self.effects, ["document"])
        finally:
            server.shutdown()
            server.server_close()
            worker.join(3)


if __name__ == "__main__":
    unittest.main()
