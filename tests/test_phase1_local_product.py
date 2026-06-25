import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from project_maya import (
    ActionRequest,
    AuthorizationResult,
    GovernanceDecision,
    build_local_product,
    config_from_mapping,
)
from project_maya.memory import LocalJsonRetriever, MemoryRetriever
from project_maya.cli import main as maya_cli
from tests.test_phase0_contracts import valid_config_mapping


class AllowGateway:
    def __init__(self):
        self.requests = []

    def authorize(self, request: ActionRequest):
        self.requests.append(request)
        return AuthorizationResult(
            decision=GovernanceDecision.ALLOW,
            reason_code="test.allow",
        )


class TestPhase1LocalProduct(unittest.TestCase):
    def test_local_json_retriever_persists_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            store_path = Path(tmp) / "memory" / "records.json"
            retriever = LocalJsonRetriever(store_path)
            memory = MemoryRetriever(retriever)

            memory.remember(
                {
                    "id": "decision-1",
                    "category": "architecture",
                    "text": "Hermes executes Maya through a governed adapter.",
                }
            )
            reopened = LocalJsonRetriever(store_path)

            self.assertEqual(reopened.get("decision-1")["category"], "architecture")
            self.assertEqual(
                reopened.search("governed adapter")[0]["id"],
                "decision-1",
            )
            self.assertEqual(reopened.stats()["records"], 1)

    def test_maya_doctor_cli_reports_missing_hermes(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = valid_config_mapping()
            config["runtime"]["enabled_profiles"] = ["maya-core"]
            config["memory"]["retriever"] = "local_json"
            config_path = Path(tmp) / "maya.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            with patch("builtins.print") as printed:
                exit_code = maya_cli(["doctor", "--config", str(config_path)])

        self.assertEqual(exit_code, 1)
        output = "\n".join(call.args[0] for call in printed.call_args_list)
        self.assertIn("pass\tconfig\tconfiguration valid", output)
        self.assertIn("fail\thermes.compatibility", output)

    def test_maya_doctor_cli_reports_unsupported_assembly(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = valid_config_mapping()
            config["runtime"]["enabled_profiles"] = ["maya-core"]
            config_path = Path(tmp) / "maya.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            with patch("builtins.print") as printed:
                exit_code = maya_cli(["doctor", "--config", str(config_path)])

        self.assertEqual(exit_code, 1)
        output = "\n".join(call.args[0] for call in printed.call_args_list)
        self.assertIn("fail\truntime.assembly", output)

    def test_build_local_product_uses_configured_runtime_and_memory(self):
        events = []

        class FakeAIAgent:
            def __init__(self, **kwargs):
                if "agent_name" in kwargs:
                    raise TypeError("unexpected agent_name")
                events.append(("init", kwargs))

            def chat(self, message):
                events.append(("chat", message))
                return "assembled response"

        with tempfile.TemporaryDirectory() as tmp:
            module_path = "tests.test_phase1_local_product:FakeAIAgent"
            config_data = valid_config_mapping()
            config_data["deployment"]["data_dir"] = str(Path(tmp) / "maya-data")
            config_data["runtime"]["enabled_profiles"] = ["maya-core"]
            config_data["runtime"]["hermes_factory"] = module_path
            config_data["runtime"]["hermes_runtime_version"] = "test-hermes"
            config_data["memory"]["retriever"] = "local_json"
            config_data["llm"]["model"] = "maya-model"
            config_data["llm"]["provider"] = "openrouter"

            globals()["FakeAIAgent"] = FakeAIAgent
            try:
                product = build_local_product(
                    config_from_mapping(config_data),
                    gateway=AllowGateway(),
                    actor_id="operator",
                )
                product.memory.remember({"id": "note-1", "text": "hello"})
                product.agent.start()
                result = product.agent.run("hello")
                product.agent.stop()
            finally:
                globals().pop("FakeAIAgent", None)

        self.assertEqual(result, "assembled response")
        self.assertEqual(product.memory.recall("note-1")["text"], "hello")
        self.assertEqual(events[0][0], "init")
        self.assertEqual(events[0][1]["model"], "maya-model")
        self.assertEqual(events[0][1]["provider"], "openrouter")


if __name__ == "__main__":
    unittest.main()
