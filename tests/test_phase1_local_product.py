import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from project_maya.cli import main as maya_cli
from project_maya.memory import LocalJsonRetriever, MemoryRetriever
from tests.test_phase0_contracts import valid_config_mapping


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
            config_path = Path(tmp) / "maya.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            with patch("builtins.print") as printed:
                exit_code = maya_cli(["doctor", "--config", str(config_path)])

        self.assertEqual(exit_code, 1)
        output = "\n".join(call.args[0] for call in printed.call_args_list)
        self.assertIn("pass\tconfig\tconfiguration valid", output)
        self.assertIn("fail\thermes.compatibility", output)


if __name__ == "__main__":
    unittest.main()
