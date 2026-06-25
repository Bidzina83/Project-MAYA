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


class TestPhase1Policy(unittest.TestCase):
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

            def chat(self, message):
                events.append(("chat", message))
                return "allowed"

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
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            config_data = valid_config_mapping()
            config_data["deployment"]["data_dir"] = str(data_dir)
            config_data["runtime"]["enabled_profiles"] = ["maya-core"]
            config_data["runtime"][
                "hermes_factory"
            ] = "tests.test_phase1_policy:FakeAIAgent"
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
