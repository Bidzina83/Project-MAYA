import unittest

from project_maya import (
    ConfigError,
    DoctorStatus,
    ModelConfigStatus,
    build_local_product,
    config_from_mapping,
    run_doctor,
    validate_model_config,
)
from project_maya.adapters import HermesRuntimeAdapter

from tests.test_phase0_contracts import valid_config_mapping


class TestPhase2ModelConfig(unittest.TestCase):
    def test_customer_owned_model_credential_ref_validates_redacted(self):
        config_data = valid_config_mapping()
        config_data["product"]["edition"] = "enterprise"
        config_data["broker"] = {"mode": "disabled", "endpoint": None}

        validation = validate_model_config(config_from_mapping(config_data))

        self.assertEqual(validation.status, ModelConfigStatus.VALID)
        self.assertEqual(validation.credential_ref_state, "configured")
        self.assertFalse(validation.network_used)
        self.assertNotIn("secret://llm/openai", validation.redacted_summary())

    def test_customer_owned_model_requires_secret_reference(self):
        config_data = valid_config_mapping()
        config_data["product"]["edition"] = "enterprise"
        config_data["broker"] = {"mode": "disabled", "endpoint": None}
        config_data["llm"].pop("credential_ref")

        validation = validate_model_config(config_from_mapping(config_data))

        self.assertEqual(validation.status, ModelConfigStatus.INVALID)
        self.assertIn("requires llm.credential_ref", validation.message)

    def test_local_model_endpoint_validates_without_credential(self):
        config_data = valid_config_mapping()
        config_data["product"]["edition"] = "enterprise"
        config_data["broker"] = {"mode": "disabled", "endpoint": None}
        config_data["llm"] = {
            "mode": "local",
            "provider": "openai-compatible",
            "model": "llama-local",
            "endpoint": "http://127.0.0.1:11434/v1",
        }

        validation = validate_model_config(config_from_mapping(config_data))

        self.assertEqual(validation.status, ModelConfigStatus.VALID)
        self.assertEqual(validation.endpoint_state, "local_configured")
        self.assertEqual(validation.credential_ref_state, "not_configured")
        self.assertFalse(validation.network_used)

    def test_enterprise_broker_disabled_rejects_maya_managed_model_mode(self):
        config_data = valid_config_mapping()
        config_data["product"]["edition"] = "enterprise"
        config_data["broker"] = {"mode": "disabled", "endpoint": None}
        config_data["llm"] = {
            "mode": "maya_managed",
            "provider": "openai",
            "model": "gpt-test",
        }

        validation = validate_model_config(config_from_mapping(config_data))

        self.assertEqual(validation.status, ModelConfigStatus.INVALID)
        self.assertIn("requires Maya cloud services", validation.message)

    def test_doctor_reports_invalid_model_config_without_secret_value(self):
        config_data = valid_config_mapping()
        config_data["product"]["edition"] = "enterprise"
        config_data["broker"] = {"mode": "disabled", "endpoint": None}
        config_data["llm"].pop("credential_ref")
        config = config_from_mapping(config_data)

        report = run_doctor(config, HermesRuntimeAdapter(factory_path="missing:factory"))
        checks = {check.name: check for check in report.checks}

        self.assertEqual(checks["model.config"].status, DoctorStatus.FAIL)
        self.assertIn("credential_ref=not_configured", checks["model.config"].message)
        self.assertNotIn("secret://llm/openai", checks["model.config"].message)

    def test_local_product_requires_valid_model_config_before_assembly(self):
        config_data = valid_config_mapping()
        config_data["product"]["edition"] = "enterprise"
        config_data["broker"] = {"mode": "disabled", "endpoint": None}
        config_data["memory"]["retriever"] = "local_json"
        config_data["llm"] = {
            "mode": "local",
            "provider": "openai-compatible",
            "model": "llama-local",
        }
        config = config_from_mapping(config_data)

        with self.assertRaisesRegex(ConfigError, "local model mode requires"):
            build_local_product(config)


if __name__ == "__main__":
    unittest.main()
