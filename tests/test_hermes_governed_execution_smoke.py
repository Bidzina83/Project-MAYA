import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from project_maya import build_local_product, config_from_mapping
from project_maya.cli import main as maya_cli
from tests.test_phase0_contracts import valid_config_mapping


class FakeMemoryManager:
    def add_provider(self, provider):
        self.provider = provider


class SmokeAIAgent:
    def __init__(self, **kwargs):
        if "agent_name" in kwargs:
            raise TypeError("unexpected agent_name")
        self.session_id = "smoke-session"
        self._memory_manager = FakeMemoryManager()
        SMOKE_EVENTS.append(("init", kwargs))

    def chat(self, message):
        SMOKE_EVENTS.append(("chat", message))
        return {"reply": f"hermes:{message}"}

    def shutdown_memory_provider(self):
        self._memory_manager.provider.shutdown()

    def close(self):
        SMOKE_EVENTS.append(("close",))


SMOKE_EVENTS = []


class TestHermesGovernedExecutionSmoke(unittest.TestCase):
    def test_build_local_product_run_emits_runtime_and_model_egress_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path, data_dir = _write_smoke_config(Path(tmp))
            config = config_from_mapping(
                json.loads(config_path.read_text(encoding="utf-8"))
            )
            SMOKE_EVENTS.clear()

            product = build_local_product(config)
            with product:
                result = product.run(
                    "prepare briefing",
                    idempotency_key="smoke-1",
                    data_classification="confidential",
                )

            records = _audit_records(data_dir)

        self.assertEqual(result, {"reply": "hermes:prepare briefing"})
        self.assertEqual(SMOKE_EVENTS[0][0], "init")
        self.assertIn(("chat", "prepare briefing"), SMOKE_EVENTS)
        self.assertIn(("close",), SMOKE_EVENTS)
        self.assertEqual(
            [record["capability"] for record in records],
            ["runtime.execute", "model.egress"],
        )
        self.assertEqual(
            [record["event_type"] for record in records],
            ["authorization.runtime", "authorization.model_egress"],
        )
        self.assertEqual(records[0]["target"], "hermes-agent")
        self.assertEqual(records[0]["idempotency_key"], "smoke-1")
        self.assertEqual(records[1]["target"], "model:openai")
        self.assertEqual(records[1]["data_classification"], "confidential")

    def test_maya_run_cli_emits_runtime_and_model_egress_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path, data_dir = _write_smoke_config(Path(tmp))
            SMOKE_EVENTS.clear()

            with patch("builtins.print") as printed:
                exit_code = maya_cli(
                    [
                        "run",
                        "--config",
                        str(config_path),
                        "--input",
                        "summarize workspace",
                        "--idempotency-key",
                        "cli-smoke-1",
                        "--data-classification",
                        "restricted",
                    ]
            )
            output = json.loads(printed.call_args.args[0])
            records = _audit_records(data_dir)
            audit_text = (
                data_dir / "governance" / "audit" / "runtime.jsonl"
            ).read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            output,
            {"result": {"reply": "hermes:summarize workspace"}},
        )
        self.assertIn(("chat", "summarize workspace"), SMOKE_EVENTS)
        self.assertEqual(
            [record["capability"] for record in records],
            ["runtime.execute", "model.egress"],
        )
        self.assertEqual(records[0]["idempotency_key"], "cli-smoke-1")
        self.assertEqual(records[1]["data_classification"], "restricted")
        self.assertNotIn("summarize workspace", audit_text)
        self.assertNotIn("secret://", audit_text)


def _write_smoke_config(tmp: Path) -> tuple[Path, Path]:
    data_dir = tmp / "maya-data"
    policy_path = data_dir / "governance" / "policy.json"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text(
        json.dumps(
            {
                "allow": [
                    {
                        "actor_id": "local-user",
                        "capability": "runtime.execute",
                        "target": "hermes-agent",
                        "operation": "run",
                    },
                    {
                        "actor_id": "local-user",
                        "capability": "model.egress",
                        "target": "model:openai",
                        "operation": "infer",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    config = valid_config_mapping()
    config["deployment"]["data_dir"] = str(data_dir)
    config["runtime"]["enabled_profiles"] = ["maya-core"]
    config["runtime"]["hermes_factory"] = f"{__name__}:SmokeAIAgent"
    config["runtime"]["hermes_runtime_version"] = "smoke-hermes"
    config["memory"]["retriever"] = "local_json"
    config["governance"]["policy_file"] = str(policy_path)
    config_path = tmp / "maya-smoke.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return config_path, data_dir


def _audit_records(data_dir: Path) -> list[dict[str, object]]:
    audit_path = data_dir / "governance" / "audit" / "runtime.jsonl"
    return [
        json.loads(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
    ]


if __name__ == "__main__":
    unittest.main()
