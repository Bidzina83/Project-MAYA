import json
import tempfile
import unittest
from pathlib import Path

from project_maya import (
    ActionDeniedError,
    ActionRequest,
    GovernanceDecision,
    build_local_product,
    config_from_mapping,
    load_policy_gateway,
    require_authorized,
)
from tests.test_phase0_contracts import valid_config_mapping


class FakeMemoryManager:
    provider = None

    @property
    def providers(self):
        return [self.provider] if self.provider else []

    def get_provider(self, name):
        return next((p for p in self.providers if p.name == name), None)

    def add_provider(self, provider):
        self.provider = provider


class TestPhase1Policy(unittest.TestCase):
    def test_doctor_warns_when_parseable_policy_denies_runtime_readiness(self):
        from project_maya import DoctorStatus, config_from_mapping
        from project_maya.doctor import _governance_policy_check
        from tests.test_phase0_contracts import valid_config_mapping

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "policy.json"
            data = valid_config_mapping()
            data["governance"]["policy_file"] = str(path)
            path.write_text(json.dumps({"schema_version": 1, "default_action": "deny", "rules": []}))
            check = _governance_policy_check(config_from_mapping(data))
            self.assertEqual(check.status, DoctorStatus.WARN)
            for capability in ("runtime.execute", "memory.read", "model.egress"):
                self.assertIn(capability, check.message)
            path.write_text(json.dumps({"allow": [
                {"actor_id": "local-user", "capability": "runtime.execute", "target": "hermes-agent", "operation": "run"},
                {"actor_id": "local-user", "capability": "memory.read", "operation": "search"},
                {"actor_id": "local-user", "capability": "model.egress", "target": "model:" + data["llm"]["provider"], "operation": "infer"},
            ]}))
            self.assertEqual(_governance_policy_check(config_from_mapping(data)).status, DoctorStatus.PASS)

    def test_policy_gateway_allows_matching_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            policy_path = Path(tmp) / "policy.json"
            policy_path.write_text(
                json.dumps(
                    {
                        "allow": [
                            {
                                "actor_id": "operator",
                                "capability": "runtime.execute",
                                "target": "hermes-agent",
                                "operation": "run",
                                "reason_code": "policy.runtime_execute",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            gateway = load_policy_gateway(policy_path)
            result = gateway.authorize(
                ActionRequest(
                    actor_id="operator",
                    capability="runtime.execute",
                    target="hermes-agent",
                    operation="run",
                )
            )

        self.assertEqual(result.decision, GovernanceDecision.ALLOW)
        self.assertEqual(result.reason_code, "policy.runtime_execute")

    def test_policy_gateway_denies_without_matching_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            policy_path = Path(tmp) / "policy.json"
            policy_path.write_text(json.dumps({"allow": []}), encoding="utf-8")
            gateway = load_policy_gateway(policy_path)

            with self.assertRaises(ActionDeniedError):
                require_authorized(
                    gateway,
                    ActionRequest(
                        actor_id="operator",
                        capability="runtime.execute",
                        target="hermes-agent",
                        operation="run",
                    ),
                )

    def test_policy_gateway_rejects_malformed_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            policy_path = Path(tmp) / "policy.json"
            policy_path.write_text(json.dumps([]), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "policy must be an object"):
                load_policy_gateway(str(policy_path))

    def test_build_local_product_loads_policy_file(self):
        events = []

        class FakeAIAgent:
            def __init__(self, **kwargs):
                if "agent_name" in kwargs:
                    raise TypeError("unexpected agent_name")
                self.session_id = "policy-test-session"
                self._memory_manager = FakeMemoryManager()

            def chat(self, message):
                events.append(("chat", message))
                return "allowed"

            def shutdown_memory_provider(self):
                self._memory_manager.provider.shutdown()

        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            policy_path = data_dir / "governance" / "policy.json"
            policy_path.parent.mkdir(parents=True)
            policy_path.write_text(
                json.dumps(
                    {
                        "allow": [
                            {
                                "actor_id": "operator",
                                "capability": "runtime.execute",
                                "target": "hermes-agent",
                                "operation": "run",
                            },
                            {
                                "actor_id": "operator",
                                "capability": "model.egress",
                                "target": "model:openai",
                                "operation": "infer",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            config_data = valid_config_mapping()
            config_data["deployment"]["data_dir"] = str(data_dir)
            config_data["runtime"]["enabled_profiles"] = ["maya-core"]
            config_data["runtime"]["hermes_factory"] = f"{__name__}:FakeAIAgent"
            config_data["memory"]["retriever"] = "local_json"
            config_data["governance"]["policy_file"] = str(policy_path)

            globals()["FakeAIAgent"] = FakeAIAgent
            try:
                product = build_local_product(
                    config_from_mapping(config_data),
                    actor_id="operator",
                )
                product.agent.start()
                result = product.agent.run("hello")
                product.agent.stop()
            finally:
                globals().pop("FakeAIAgent", None)

        self.assertEqual(result, "allowed")
        self.assertEqual(events, [("chat", "hello")])


if __name__ == "__main__":
    unittest.main()
