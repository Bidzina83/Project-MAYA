import json
import tempfile
import unittest
from pathlib import Path

from project_maya import (
    ActionRequest,
    AuditRecord,
    AuthorizationResult,
    GovernanceDecision,
    GovernedAgentRuntime,
    LocalJsonlAuditSink,
    ModelEgressPolicy,
    config_from_mapping,
    run_doctor,
)
from project_maya.adapters import HermesRuntimeAdapter
from tests.test_phase0_contracts import valid_config_mapping


class RuntimeDouble:
    def __init__(self):
        self.events = []

    def attach_memory(self, memory_provider):
        self.events.append(("memory", memory_provider))

    def load_plugin(self, name, plugin=None):
        self.events.append(("plugin", name, plugin))

    def start(self, *, agent_name):
        self.events.append(("start", agent_name))

    def run(self, request, **kwargs):
        self.events.append(("run", request, kwargs))
        return "ok"

    def stop(self):
        self.events.append(("stop",))


class Gateway:
    def __init__(self, decision):
        self.decision = decision
        self.requests = []

    def authorize(self, request: ActionRequest):
        self.requests.append(request)
        return AuthorizationResult(
            decision=self.decision,
            reason_code=f"test.{self.decision.value}",
        )


class TestPhase1Audit(unittest.TestCase):
    def test_local_jsonl_audit_sink_appends_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "governance" / "audit" / "runtime.jsonl"
            sink = LocalJsonlAuditSink(path)

            sink.write(
                AuditRecord(
                    event_type="authorization.runtime",
                    decision="allow",
                    reason_code="test.allow",
                    actor_id="operator",
                    capability="runtime.execute",
                    target="hermes-agent",
                    operation="run",
                    data_classification="internal",
                )
            )
            sink.write(
                AuditRecord(
                    event_type="authorization.runtime",
                    decision="deny",
                    reason_code="test.deny",
                    actor_id="operator",
                    capability="runtime.execute",
                    target="hermes-agent",
                    operation="run",
                    data_classification="internal",
                )
            )
            records = [
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual([record["decision"] for record in records], ["allow", "deny"])
        self.assertEqual(records[0]["capability"], "runtime.execute")

    def test_governed_runtime_audits_allowed_action_without_prompt_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "runtime.jsonl"
            runtime = RuntimeDouble()
            governed = GovernedAgentRuntime(
                HermesRuntimeAdapter(factory=lambda **kwargs: runtime),
                Gateway(GovernanceDecision.ALLOW),
                actor_id="operator",
                audit_sink=LocalJsonlAuditSink(path),
            )
            governed.start(agent_name="maya")
            governed.run("sensitive prompt body", idempotency_key="turn-1")
            governed.stop()
            audit_text = path.read_text(encoding="utf-8")
            records = [
                json.loads(line) for line in audit_text.splitlines()
            ]
            record = records[0]

        self.assertEqual(record["decision"], "allow")
        self.assertEqual(record["reason_code"], "test.allow")
        self.assertEqual(record["idempotency_key"], "turn-1")
        self.assertNotIn("sensitive prompt body", audit_text)

    def test_governed_runtime_audits_denied_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "runtime.jsonl"
            governed = GovernedAgentRuntime(
                HermesRuntimeAdapter(factory=lambda **kwargs: RuntimeDouble()),
                Gateway(GovernanceDecision.DENY),
                actor_id="operator",
                audit_sink=LocalJsonlAuditSink(path),
            )

            with self.assertRaises(PermissionError):
                governed.run("do not log this")

            audit_text = path.read_text(encoding="utf-8")
            records = [
                json.loads(line) for line in audit_text.splitlines()
            ]
            record = records[0]

        self.assertEqual(record["decision"], "deny")
        self.assertEqual(record["reason_code"], "test.deny")
        self.assertNotIn("do not log this", audit_text)

    def test_governed_runtime_audits_model_egress_without_prompt_or_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "runtime.jsonl"
            gateway = Gateway(GovernanceDecision.ALLOW)
            governed = GovernedAgentRuntime(
                HermesRuntimeAdapter(factory=lambda **kwargs: RuntimeDouble()),
                gateway,
                actor_id="operator",
                audit_sink=LocalJsonlAuditSink(path),
                model_egress=ModelEgressPolicy(
                    mode="customer_owned",
                    provider="openai",
                    endpoint="https://api.openai.example/v1",
                    redaction="applied",
                    consent="policy",
                ),
            )

            governed.run(
                "secret prompt body",
                data_classification="confidential",
                idempotency_key="turn-2",
                credential_ref="secret://llm/openai",
            )

            audit_text = path.read_text(encoding="utf-8")
            records = [
                json.loads(line) for line in audit_text.splitlines()
            ]
            egress = records[1]

        self.assertEqual(
            [request.capability for request in gateway.requests],
            ["runtime.execute", "model.egress"],
        )
        self.assertEqual(egress["event_type"], "authorization.model_egress")
        self.assertEqual(egress["capability"], "model.egress")
        self.assertEqual(egress["target"], "model:openai")
        self.assertEqual(egress["operation"], "infer")
        self.assertEqual(egress["data_classification"], "confidential")
        self.assertEqual(egress["metadata"]["endpoint_configured"], "true")
        self.assertEqual(egress["metadata"]["redaction"], "applied")
        self.assertNotIn("secret prompt body", audit_text)
        self.assertNotIn("secret://llm/openai", audit_text)

    def test_governed_runtime_denies_model_egress_before_runtime_call(self):
        class EgressDenyGateway:
            def authorize(self, request: ActionRequest):
                decision = (
                    GovernanceDecision.DENY
                    if request.capability == "model.egress"
                    else GovernanceDecision.ALLOW
                )
                return AuthorizationResult(
                    decision=decision,
                    reason_code=f"test.{request.capability}",
                )

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "runtime.jsonl"
            runtime = RuntimeDouble()
            governed = GovernedAgentRuntime(
                HermesRuntimeAdapter(factory=lambda **kwargs: runtime),
                EgressDenyGateway(),
                actor_id="operator",
                audit_sink=LocalJsonlAuditSink(path),
                model_egress=ModelEgressPolicy(
                    mode="customer_owned",
                    provider="openai",
                ),
            )

            with self.assertRaises(PermissionError):
                governed.run("do not send")

            audit_text = path.read_text(encoding="utf-8")
            records = [
                json.loads(line) for line in audit_text.splitlines()
            ]

        self.assertEqual(records[1]["decision"], "deny")
        self.assertEqual(records[1]["capability"], "model.egress")
        self.assertEqual(runtime.events, [])
        self.assertNotIn("do not send", audit_text)

    def test_doctor_reports_audit_log_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            audit_path = data_dir / "governance" / "audit" / "runtime.jsonl"
            audit_path.parent.mkdir(parents=True)
            audit_path.write_text(
                AuditRecord(
                    event_type="authorization.runtime",
                    decision="allow",
                    reason_code="test.allow",
                    actor_id="operator",
                    capability="runtime.execute",
                    target="hermes-agent",
                    operation="run",
                    data_classification="internal",
                ).to_json()
                + "\n",
                encoding="utf-8",
            )
            config_data = valid_config_mapping()
            config_data["deployment"]["data_dir"] = str(data_dir)
            config_data["runtime"]["enabled_profiles"] = ["maya-core"]
            config = config_from_mapping(config_data)

            report = run_doctor(
                config,
                HermesRuntimeAdapter(factory_path="missing.hermes:factory"),
            )

        checks = {check.name: check for check in report.checks}
        self.assertEqual(checks["audit.runtime"].status.value, "pass")
        self.assertIn("runtime audit log valid", checks["audit.runtime"].message)


if __name__ == "__main__":
    unittest.main()
