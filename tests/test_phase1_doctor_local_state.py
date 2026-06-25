import json
import tempfile
import unittest
from pathlib import Path

from project_maya import AgentState, DoctorStatus, config_from_mapping, run_doctor
from project_maya.adapters import HermesRuntimeAdapter
from tests.test_phase0_contracts import valid_config_mapping


class TestPhase1DoctorLocalState(unittest.TestCase):
    def test_doctor_reports_first_run_local_state_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            config_data = valid_config_mapping()
            config_data["deployment"]["data_dir"] = str(data_dir)
            config_data["runtime"]["enabled_profiles"] = ["maya-core"]
            config_data["memory"]["retriever"] = "local_json"
            config_data["governance"]["policy_file"] = str(
                data_dir / "governance" / "policy.json"
            )
            config = config_from_mapping(config_data)

            report = run_doctor(
                config,
                HermesRuntimeAdapter(factory_path="missing.hermes:factory"),
                lifecycle_state=AgentState.CREATED,
            )

        checks = {check.name: check for check in report.checks}
        self.assertEqual(checks["lifecycle.agent"].status, DoctorStatus.PASS)
        self.assertIn("created", checks["lifecycle.agent"].message)
        self.assertEqual(checks["profiles.enabled"].status, DoctorStatus.PASS)
        self.assertIn("maya-core", checks["profiles.enabled"].message)
        self.assertEqual(checks["filesystem.data_dir"].status, DoctorStatus.WARN)
        self.assertEqual(checks["filesystem.disk_space"].status, DoctorStatus.PASS)
        self.assertIn("free=", checks["filesystem.disk_space"].message)
        self.assertEqual(checks["model.config"].status, DoctorStatus.PASS)
        self.assertIn("provider=openai", checks["model.config"].message)
        self.assertIn("credential_ref=configured", checks["model.config"].message)
        self.assertNotIn("secret://llm/openai", checks["model.config"].message)
        self.assertEqual(checks["memory.store"].status, DoctorStatus.WARN)
        self.assertEqual(checks["governance.policy"].status, DoctorStatus.WARN)
        self.assertIn("default deny", checks["governance.policy"].message)

    def test_doctor_reports_valid_local_memory_and_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            memory_path = data_dir / "memory" / "records.json"
            policy_path = data_dir / "governance" / "policy.json"
            memory_path.parent.mkdir(parents=True)
            policy_path.parent.mkdir(parents=True)
            memory_path.write_text(
                json.dumps([{"id": "note-1", "text": "hello"}]),
                encoding="utf-8",
            )
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
            config_data["memory"]["retriever"] = "local_json"
            config_data["governance"]["policy_file"] = str(policy_path)
            config = config_from_mapping(config_data)

            report = run_doctor(
                config,
                HermesRuntimeAdapter(factory_path="missing.hermes:factory"),
                lifecycle_state=AgentState.STOPPED,
            )

        checks = {check.name: check for check in report.checks}
        self.assertEqual(checks["lifecycle.agent"].status, DoctorStatus.PASS)
        self.assertIn("stopped", checks["lifecycle.agent"].message)
        self.assertIn("maya-core", checks["profiles.enabled"].message)
        self.assertEqual(checks["filesystem.data_dir"].status, DoctorStatus.PASS)
        self.assertEqual(checks["filesystem.disk_space"].status, DoctorStatus.PASS)
        self.assertEqual(checks["memory.store"].status, DoctorStatus.PASS)
        self.assertEqual(checks["governance.policy"].status, DoctorStatus.PASS)
        self.assertIn("records=1", checks["memory.store"].message)

    def test_doctor_fails_disk_space_when_data_dir_parent_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "missing-parent" / "maya-data"
            config_data = valid_config_mapping()
            config_data["deployment"]["data_dir"] = str(data_dir)
            config = config_from_mapping(config_data)

            report = run_doctor(
                config,
                HermesRuntimeAdapter(factory_path="missing.hermes:factory"),
                lifecycle_state=AgentState.CREATED,
            )

        checks = {check.name: check for check in report.checks}
        self.assertEqual(checks["filesystem.data_dir"].status, DoctorStatus.FAIL)
        self.assertEqual(checks["filesystem.disk_space"].status, DoctorStatus.FAIL)
        self.assertIn("parent is missing", checks["filesystem.disk_space"].message)

    def test_doctor_fails_malformed_local_memory_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            memory_path = data_dir / "memory" / "records.json"
            memory_path.parent.mkdir(parents=True)
            memory_path.write_text(json.dumps({"bad": "shape"}), encoding="utf-8")
            config_data = valid_config_mapping()
            config_data["deployment"]["data_dir"] = str(data_dir)
            config_data["runtime"]["enabled_profiles"] = ["maya-core"]
            config_data["memory"]["retriever"] = "local_json"
            config = config_from_mapping(config_data)

            report = run_doctor(
                config,
                HermesRuntimeAdapter(factory_path="missing.hermes:factory"),
            )

        checks = {check.name: check for check in report.checks}
        self.assertEqual(checks["memory.store"].status, DoctorStatus.FAIL)
        self.assertIn("JSON list", checks["memory.store"].message)

    def test_doctor_fails_malformed_governance_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            policy_path = data_dir / "governance" / "policy.json"
            policy_path.parent.mkdir(parents=True)
            policy_path.write_text(json.dumps([]), encoding="utf-8")
            config_data = valid_config_mapping()
            config_data["deployment"]["data_dir"] = str(data_dir)
            config_data["runtime"]["enabled_profiles"] = ["maya-core"]
            config_data["governance"]["policy_file"] = str(policy_path)
            config = config_from_mapping(config_data)

            report = run_doctor(
                config,
                HermesRuntimeAdapter(factory_path="missing.hermes:factory"),
            )

        checks = {check.name: check for check in report.checks}
        self.assertEqual(checks["governance.policy"].status, DoctorStatus.FAIL)
        self.assertIn("policy file invalid", checks["governance.policy"].message)

    def test_doctor_reports_failed_agent_lifecycle_as_failure(self):
        config = config_from_mapping(valid_config_mapping())

        report = run_doctor(
            config,
            HermesRuntimeAdapter(factory_path="missing.hermes:factory"),
            lifecycle_state=AgentState.FAILED,
        )

        checks = {check.name: check for check in report.checks}
        self.assertEqual(checks["lifecycle.agent"].status, DoctorStatus.FAIL)
        self.assertIn("failed", checks["lifecycle.agent"].message)


if __name__ == "__main__":
    unittest.main()
