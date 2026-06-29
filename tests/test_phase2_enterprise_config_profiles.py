import json
import tempfile
import unittest
from pathlib import Path

from project_maya import (
    BrokerMode,
    ComponentProfile,
    ConfigProfileError,
    CredentialMode,
    Edition,
    ModelConfigStatus,
    build_local_product,
    config_to_mapping,
    load_config_profile,
    validate_configured_connectors,
    validate_model_config,
)


class TestPhase2EnterpriseConfigProfiles(unittest.TestCase):
    def test_enterprise_byo_profile_validates_without_broker_or_secret_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-enterprise"
            config = load_config_profile(
                Path("docs/config/enterprise-byo-broker-disabled.json"),
                data_dir=data_dir,
                instance_id="enterprise-byo-test",
            )

        self.assertEqual(config.product.edition, Edition.ENTERPRISE)
        self.assertEqual(config.product.instance_id, "enterprise-byo-test")
        self.assertEqual(config.deployment.data_dir, data_dir)
        self.assertEqual(config.broker.mode, BrokerMode.DISABLED)
        self.assertIsNone(config.broker.endpoint)
        self.assertIn(ComponentProfile.CORE, config.runtime.enabled_profiles)
        self.assertIn(ComponentProfile.MESSAGING, config.runtime.enabled_profiles)
        self.assertEqual(config.memory.retriever, "local_json")
        self.assertTrue(config.memory.governance_enabled)
        self.assertTrue(config.governance.audit_enabled)
        product = build_local_product(config, actor_id="operator")
        self.assertEqual(product.agent.name, "project_maya.enterprise-byo-test")
        self.assertEqual(product.retriever.stats()["records"], 0)

        model_validation = validate_model_config(config)
        self.assertEqual(model_validation.status, ModelConfigStatus.VALID)
        self.assertEqual(model_validation.credential_ref_state, "configured")
        self.assertFalse(model_validation.network_used)

        connector_modes = {
            name: integration.credential_mode
            for name, integration in config.integrations.items()
        }
        self.assertEqual(
            connector_modes,
            {
                "google": CredentialMode.CUSTOMER_OWNED,
                "slack": CredentialMode.CUSTOMER_OWNED,
                "telegram": CredentialMode.CUSTOMER_OWNED,
            },
        )
        connector_validations = validate_configured_connectors(
            config.integrations,
            broker_mode=config.broker.mode,
        )
        self.assertTrue(all(validation.valid for validation in connector_validations))
        self.assertFalse(any(validation.network_used for validation in connector_validations))

        normalized = config_to_mapping(config)
        serialized = json.dumps(normalized, sort_keys=True)
        self.assertNotIn("${MAYA_DATA_DIR}", serialized)
        self.assertNotIn("${MAYA_INSTANCE_ID}", serialized)
        self.assertNotIn("token", serialized.lower())
        self.assertNotIn("password", serialized.lower())

    def test_local_model_profile_validates_with_disabled_connectors(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-local-model"
            config = load_config_profile(
                Path("docs/config/enterprise-local-model-broker-disabled.json"),
                data_dir=data_dir,
                instance_id="enterprise-local-model-test",
            )

        self.assertEqual(config.product.edition, Edition.ENTERPRISE)
        self.assertEqual(config.broker.mode, BrokerMode.DISABLED)
        self.assertEqual(config.llm.mode, "local")
        self.assertEqual(config.llm.provider, "openai-compatible")
        self.assertEqual(config.llm.endpoint, "http://127.0.0.1:11434/v1")
        self.assertIsNone(config.llm.credential_ref)
        self.assertIn(ComponentProfile.LOCAL_MODELS, config.runtime.enabled_profiles)

        model_validation = validate_model_config(config)
        self.assertEqual(model_validation.status, ModelConfigStatus.VALID)
        self.assertEqual(model_validation.endpoint_state, "local_configured")
        self.assertEqual(model_validation.credential_ref_state, "not_configured")

        connector_validations = validate_configured_connectors(
            config.integrations,
            broker_mode=config.broker.mode,
        )
        self.assertTrue(all(validation.valid for validation in connector_validations))
        self.assertTrue(all(not validation.enabled for validation in connector_validations))
        self.assertTrue(
            all(validation.credential_ref_state == "not_configured"
                for validation in connector_validations)
        )

    def test_profile_loader_requires_absolute_data_dir(self):
        with self.assertRaisesRegex(ConfigProfileError, "data_dir must be absolute"):
            load_config_profile(
                Path("docs/config/enterprise-byo-broker-disabled.json"),
                data_dir=Path("relative-maya-data"),
            )

    def test_profile_loader_rejects_unknown_placeholders(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile_path = Path(tmp) / "profile.json"
            profile_path.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "product": {
                            "edition": "enterprise",
                            "instance_id": "${UNKNOWN}",
                        },
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ConfigProfileError,
                r"unsupported profile placeholder: \$\{UNKNOWN\}",
            ):
                load_config_profile(profile_path, data_dir=Path(tmp) / "maya-data")


if __name__ == "__main__":
    unittest.main()
