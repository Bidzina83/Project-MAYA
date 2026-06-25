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

    def authorize(self, request: ActionRequest):
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
            record = json.loads(audit_text)

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
            record = json.loads(audit_text)

        self.assertEqual(record["decision"], "deny")
        self.assertEqual(record["reason_code"], "test.deny")
        self.assertNotIn("do not log this", audit_text)

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
