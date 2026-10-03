import json
import io
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from contextlib import redirect_stdout

from project_maya.adapters.hermes import HermesMemoryProviderBridge
from project_maya.config import config_from_mapping
from project_maya.hermes_plugins.candidate import (
    ACKNOWLEDGEMENT, _CandidateStartup, _validate_test_scope,
    _verify_loaded_artifact, initialize_test_only_home, main, build_test_only_product,
)
from project_maya.hermes_plugins.governance import GovernanceBoundaryError, require_runtime_contract
from tests.test_phase0_contracts import valid_config_mapping


class TestCandidateStartup(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "candidate"
        self.home = initialize_test_only_home(self.root, acknowledgement=ACKNOWLEDGEMENT)
        self.env = patch.dict(os.environ, {"HERMES_HOME": str(self.home)}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def config(self, mutate=None):
        data = valid_config_mapping()
        data["deployment"]["data_dir"] = str(self.root)
        data["governance"]["policy_file"] = str(self.root / "governance/policy.json")
        data["llm"].update(mode="local", provider="openai-compatible", model="synthetic-model",
                            endpoint="http://127.0.0.1:9/v1", credential_ref=None)
        data["broker"] = {"mode": "disabled"}
        data["runtime"]["enabled_profiles"] = ["maya-core"]
        data["metabase"]["enabled"] = False
        for item in data["integrations"].values():
            item["enabled"] = False
            item["credential_mode"] = "customer_owned"
        if mutate:
            mutate(data)
        return config_from_mapping(data)

    def test_explicit_acknowledgement_and_new_home_required(self):
        with self.assertRaisesRegex(GovernanceBoundaryError, "acknowledgement_required"):
            initialize_test_only_home(self.root.parent / "other", acknowledgement="")
        with self.assertRaisesRegex(GovernanceBoundaryError, "home_creation_failed"):
            initialize_test_only_home(self.root, acknowledgement=ACKNOWLEDGEMENT)
        with self.assertRaisesRegex(GovernanceBoundaryError, "acknowledgement_required"):
            _validate_test_scope(self.config(), "")
        _validate_test_scope(self.config(), ACKNOWLEDGEMENT)

    def test_candidate_iteration_limit_is_explicit_and_bounded(self):
        for value in (0, 4, True, "2", None):
            with self.subTest(value=value), self.assertRaisesRegex(GovernanceBoundaryError, "iteration_limit_invalid"):
                build_test_only_product(self.config(), wheel_path=Path("unused.whl"),
                                        acknowledgement=ACKNOWLEDGEMENT, actor_id="operator",
                                        iteration_limit=value)

    def test_external_routes_credentials_and_profiles_are_rejected(self):
        cases = [
            lambda d: d["llm"].update(endpoint="https://api.openai.com/v1"),
            lambda d: d["llm"].update(credential_ref="secret://llm/openai"),
            lambda d: d["runtime"].update(enabled_profiles=["maya-core", "maya-browser"]),
            lambda d: d["broker"].update(mode="runtime", endpoint="https://example.test"),
            lambda d: d["metabase"].update(enabled=True),
            lambda d: d["integrations"]["google"].update(enabled=True),
        ]
        for mutate in cases:
            with self.subTest(mutate=mutate), self.assertRaisesRegex(GovernanceBoundaryError, "scope_invalid"):
                _validate_test_scope(self.config(mutate), ACKNOWLEDGEMENT)

    def test_customer_state_and_ambient_credentials_are_rejected(self):
        for name in (".env", "config.yaml", "plugins"):
            path = self.home / name
            path.write_text("synthetic", encoding="utf-8")
            with self.assertRaisesRegex(GovernanceBoundaryError, "home_invalid"):
                _validate_test_scope(self.config(), ACKNOWLEDGEMENT)
            path.unlink()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "synthetic"}):
            with self.assertRaisesRegex(GovernanceBoundaryError, "home_invalid"):
                _validate_test_scope(self.config(), ACKNOWLEDGEMENT)
        (self.root / ".maya-governance-candidate.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(GovernanceBoundaryError, "home_invalid"):
            _validate_test_scope(self.config(), ACKNOWLEDGEMENT)

    def test_wrong_wheel_is_rejected_before_import(self):
        wheel = self.root / "wrong.whl"
        wheel.write_bytes(b"synthetic")
        with patch("project_maya.hermes_plugins.candidate.find_spec") as imports:
            with self.assertRaisesRegex(GovernanceBoundaryError, "artifact_invalid"):
                _verify_loaded_artifact(wheel)
            imports.assert_not_called()

    def test_native_binding_order_idempotence_and_removal_fail_closed(self):
        events = []
        module = Mock()
        module.enable_mandatory_middleware.side_effect = lambda: events.append("enable")
        module.validate_mandatory_middleware.return_value = True
        native = Mock()
        ctx = native.PluginContext.return_value
        ctx.register_middleware.side_effect = lambda kind, cb: events.append(kind)
        plugin = Mock()
        scope = Mock()
        startup = _CandidateStartup(plugin, Path("synthetic.whl"), scope)
        with patch("project_maya.hermes_plugins.candidate._verify_loaded_artifact"), \
             patch("project_maya.hermes_plugins.candidate.import_module", side_effect=lambda n: module if n.endswith("middleware") else native):
            startup()
            startup()
            self.assertEqual(events, ["enable", "llm_execution", "tool_execution", "tool_result", "model_output"])
            self.assertEqual(module.require_middleware.call_count, 4)
            module.validate_mandatory_middleware.return_value = False
            with self.assertRaisesRegex(GovernanceBoundaryError, "registration_failed"):
                startup()
            self.assertEqual(ctx.register_middleware.call_count, 4)
            self.assertEqual(scope.call_count, 3)

    def test_registration_errors_are_fixed_and_production_guard_unchanged(self):
        module = Mock()
        module.enable_mandatory_middleware.side_effect = RuntimeError("private diagnostic")
        with patch("project_maya.hermes_plugins.candidate._verify_loaded_artifact"), \
             patch("project_maya.hermes_plugins.candidate.import_module", return_value=module):
            with self.assertRaisesRegex(GovernanceBoundaryError, "^governance.candidate_registration_failed$"):
                _CandidateStartup(Mock(), Path("synthetic.whl"), Mock())()
        with self.assertRaisesRegex(GovernanceBoundaryError, "contract_unsupported"):
            require_runtime_contract(SimpleNamespace())

    def test_bridge_lifecycle_does_not_ingest_conversations(self):
        memory = Mock()
        bridge = HermesMemoryProviderBridge(memory)
        bridge.on_turn_start(1, "synthetic conversation")
        bridge.on_session_end([{"content": "synthetic conversation"}])
        self.assertEqual(memory.mock_calls, [])

    def test_candidate_launcher_errors_are_fixed_and_secret_safe(self):
        config = self.root / "invalid.json"
        config.write_text("private diagnostic", encoding="utf-8")
        output = io.StringIO()
        with redirect_stdout(output):
            result = main(["--config", str(config), "--wheel", "missing.whl",
                           "--acknowledge", ACKNOWLEDGEMENT, "--actor", "operator"])
        self.assertEqual(result, 1)
        self.assertNotIn("private diagnostic", output.getvalue())
        self.assertFalse(json.loads(output.getvalue())["production_qualified"])


if __name__ == "__main__":
    unittest.main()
