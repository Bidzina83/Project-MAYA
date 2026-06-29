import unittest

from project_maya import (
    BrokerMode,
    ConfigError,
    CredentialMode,
    build_connector_manifest,
    config_from_mapping,
    get_connector_contract,
)

from tests.test_phase0_contracts import valid_config_mapping


class TestPhase2ConnectorContracts(unittest.TestCase):
    def test_google_slack_and_telegram_contracts_declare_supported_modes(self):
        google = get_connector_contract("google")
        slack = get_connector_contract("slack")
        telegram = get_connector_contract("telegram")

        self.assertEqual(
            google.supported_credential_modes,
            (
                CredentialMode.BROKER,
                CredentialMode.CUSTOMER_OWNED,
                CredentialMode.DISABLED,
            ),
        )
        self.assertEqual(
            slack.supported_credential_modes,
            (
                CredentialMode.BROKER,
                CredentialMode.CUSTOMER_OWNED,
                CredentialMode.DISABLED,
            ),
        )
        self.assertEqual(
            telegram.supported_credential_modes,
            (CredentialMode.CUSTOMER_OWNED, CredentialMode.DISABLED),
        )

    def test_enterprise_broker_disabled_accepts_customer_owned_connectors(self):
        config_data = valid_config_mapping()
        config_data["product"]["edition"] = "enterprise"
        config_data["broker"] = {"mode": "disabled", "endpoint": None}
        config_data["integrations"] = {
            "google": {
                "enabled": True,
                "credential_mode": "customer_owned",
                "credential_ref": "secret://integrations/google",
            },
            "slack": {
                "enabled": True,
                "credential_mode": "customer_owned",
                "credential_ref": "secret://integrations/slack",
            },
            "telegram": {
                "enabled": True,
                "credential_mode": "customer_owned",
                "credential_ref": "secret://integrations/telegram",
            },
        }

        config = config_from_mapping(config_data)

        self.assertEqual(config.integrations["google"].credential_mode, CredentialMode.CUSTOMER_OWNED)
        self.assertEqual(config.integrations["slack"].credential_mode, CredentialMode.CUSTOMER_OWNED)
        self.assertEqual(config.integrations["telegram"].credential_mode, CredentialMode.CUSTOMER_OWNED)

    def test_broker_disabled_rejects_broker_google_and_slack(self):
        for connector in ("google", "slack"):
            with self.subTest(connector=connector):
                config_data = valid_config_mapping()
                config_data["product"]["edition"] = "enterprise"
                config_data["broker"] = {"mode": "disabled", "endpoint": None}
                config_data["integrations"] = {
                    "google": {
                        "enabled": True,
                        "credential_mode": "customer_owned",
                        "credential_ref": "secret://integrations/google",
                    },
                    "slack": {
                        "enabled": True,
                        "credential_mode": "customer_owned",
                        "credential_ref": "secret://integrations/slack",
                    },
                    "telegram": {
                        "enabled": True,
                        "credential_mode": "customer_owned",
                        "credential_ref": "secret://integrations/telegram",
                    },
                }
                config_data["integrations"][connector] = {
                    "enabled": True,
                    "credential_mode": "broker",
                    "credential_ref": f"secret://integrations/{connector}",
                }

                with self.assertRaisesRegex(
                    ConfigError,
                    f"{connector}.credential_mode=broker requires broker mode",
                ):
                    config_from_mapping(config_data)

    def test_telegram_rejects_broker_and_local_only_modes(self):
        cases = (
            ("broker", "telegram must use a customer-owned credential"),
            ("local_only", "telegram.credential_mode must be one of"),
        )
        for mode, message in cases:
            with self.subTest(mode=mode):
                config_data = valid_config_mapping()
                config_data["integrations"]["telegram"] = {
                    "enabled": True,
                    "credential_mode": mode,
                    "credential_ref": "secret://integrations/telegram",
                }

                with self.assertRaisesRegex(ConfigError, message):
                    config_from_mapping(config_data)

    def test_credential_bearing_modes_require_secret_reference(self):
        config_data = valid_config_mapping()
        config_data["integrations"]["google"] = {
            "enabled": True,
            "credential_mode": "customer_owned",
        }

        with self.assertRaisesRegex(
            ConfigError,
            "google.credential_ref is required",
        ):
            config_from_mapping(config_data)

    def test_disabled_connector_rejects_credential_reference(self):
        config_data = valid_config_mapping()
        config_data["integrations"]["google"] = {
            "enabled": False,
            "credential_mode": "disabled",
            "credential_ref": "secret://integrations/google",
        }

        with self.assertRaisesRegex(
            ConfigError,
            "google.credential_ref must be absent",
        ):
            config_from_mapping(config_data)

    def test_connector_manifest_uses_contract_capabilities_and_allowlists(self):
        config = config_from_mapping(valid_config_mapping())
        manifest = build_connector_manifest(
            "google",
            config.integrations["google"],
            broker_mode=BrokerMode.RUNTIME,
        )

        self.assertEqual(manifest.name, "google")
        self.assertEqual(manifest.credential_mode, CredentialMode.BROKER)
        self.assertIn("users", manifest.allowlists)
        self.assertIn("resources", manifest.allowlists)
        self.assertIn(
            "drive.read",
            {capability.name for capability in manifest.capabilities},
        )
        self.assertTrue(manifest.revocation_supported)


if __name__ == "__main__":
    unittest.main()
