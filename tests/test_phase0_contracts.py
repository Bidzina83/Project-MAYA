import unittest
from pathlib import Path

from project_maya import (
    ActionDeniedError,
    ActionRequest,
    BrokerMode,
    ComponentProfile,
    ConfigError,
    ConnectorCapability,
    ConnectorManifest,
    CredentialMode,
    DenyByDefaultGateway,
    GovernanceDecision,
    SecretRef,
    SecretReferenceError,
    config_from_mapping,
    require_authorized,
)


def valid_config_mapping():
    data_dir = Path.cwd() / "maya-data"
    return {
        "schema_version": 2,
        "product": {"edition": "standard", "instance_id": "maya-test"},
        "deployment": {
            "class": "desktop",
            "network_policy": "standard",
            "data_dir": str(data_dir),
        },
        "runtime": {
            "hermes_compatibility": ">=0.1",
            "enabled_profiles": ["maya-core", "maya-metabase"],
        },
        "broker": {"mode": "runtime", "endpoint": "https://broker.example"},
        "llm": {
            "mode": "customer_owned",
            "provider": "openai",
            "model": "gpt-test",
            "credential_ref": "secret://llm/openai",
        },
        "integrations": {
            "google": {
                "enabled": True,
                "credential_mode": "broker",
                "credential_ref": "secret://integrations/google",
            },
            "telegram": {
                "enabled": False,
                "credential_mode": "customer_owned",
                "credential_ref": "secret://integrations/telegram",
            },
        },
        "memory": {
            "hermes_provider": "local",
            "retriever": "local_vector",
            "registry": "sqlite",
            "governance_enabled": True,
        },
        "governance": {
            "policy_file": str(data_dir / "governance" / "default.yaml"),
            "default_action": "deny",
            "minimum_memory_trust": 0.7,
        },
        "metabase": {
            "enabled": True,
            "deployment": "managed_local",
            "endpoint": "http://127.0.0.1:3000",
            "application_database": {
                "engine": "sqlite",
                "credential_ref": "secret://metabase/application-db",
            },
            "analytics_sources": [
                {
                    "name": "maya_operational",
                    "engine": "sqlite",
                    "credential_ref": "secret://metabase/maya-operational",
                }
            ],
        },
        "local_api": {"bind": "127.0.0.1", "port": 8765, "remote_access": False},
    }


class TestPhase0Contracts(unittest.TestCase):
    def test_config_from_mapping_accepts_v2_shape(self):
        config = config_from_mapping(valid_config_mapping())

        self.assertEqual(config.broker.mode, BrokerMode.RUNTIME)
        self.assertEqual(config.schema_version, 2)
        self.assertIn(ComponentProfile.CORE, config.runtime.enabled_profiles)
        self.assertTrue(config.metabase.enabled)

    def test_config_requires_schema_version(self):
        data = valid_config_mapping()
        data.pop("schema_version")

        with self.assertRaisesRegex(ConfigError, "schema_version is required"):
            config_from_mapping(data)

    def test_config_rejects_unsupported_schema_version(self):
        data = valid_config_mapping()
        data["schema_version"] = 1

        with self.assertRaisesRegex(ConfigError, "schema_version must be 2"):
            config_from_mapping(data)

    def test_config_rejects_shared_telegram_broker(self):
        data = valid_config_mapping()
        data["integrations"]["telegram"]["enabled"] = True
        data["integrations"]["telegram"]["credential_mode"] = "broker"

        with self.assertRaisesRegex(
            ConfigError, "telegram must use a customer-owned credential"
        ):
            config_from_mapping(data)

    def test_config_rejects_ambiguous_metabase_storage(self):
        data = valid_config_mapping()
        data["metabase"]["application_database"]["credential_ref"] = "metabase.db"

        with self.assertRaisesRegex(ConfigError, "secret://"):
            config_from_mapping(data)

    def test_config_rejects_remote_local_api_in_phase1(self):
        data = valid_config_mapping()
        data["local_api"]["bind"] = "0.0.0.0"
        data["local_api"]["remote_access"] = True

        with self.assertRaisesRegex(ConfigError, "remote_access"):
            config_from_mapping(data)

    def test_config_requires_loopback_local_api_bind(self):
        data = valid_config_mapping()
        data["local_api"]["bind"] = "0.0.0.0"

        with self.assertRaisesRegex(ConfigError, "loopback"):
            config_from_mapping(data)

    def test_config_requires_memory_governance(self):
        data = valid_config_mapping()
        data["memory"]["governance_enabled"] = False

        with self.assertRaisesRegex(ConfigError, "memory.governance_enabled"):
            config_from_mapping(data)

    def test_config_requires_runtime_audit(self):
        data = valid_config_mapping()
        data["governance"]["audit_enabled"] = False

        with self.assertRaisesRegex(ConfigError, "governance.audit_enabled"):
            config_from_mapping(data)

    def test_secret_refs_parse_without_exposing_values(self):
        ref = SecretRef.parse("secret://integrations/google")

        self.assertEqual(ref.name, "integrations/google")
        self.assertEqual(str(ref), "secret://integrations/google")
        with self.assertRaises(SecretReferenceError):
            SecretRef.parse("not-a-secret")

    def test_connector_manifest_requires_declared_capabilities(self):
        manifest = ConnectorManifest(
            name="google",
            credential_mode=CredentialMode.BROKER,
            credential_ref="secret://integrations/google",
            capabilities=(
                ConnectorCapability(
                    name="drive.read",
                    scopes=("https://www.googleapis.com/auth/drive.readonly",),
                ),
            ),
        )

        manifest.validate()

    def test_connector_manifest_rejects_broker_telegram(self):
        manifest = ConnectorManifest(
            name="telegram",
            credential_mode=CredentialMode.BROKER,
            credential_ref="secret://integrations/telegram",
            capabilities=(ConnectorCapability(name="message.send", can_write=True),),
        )

        with self.assertRaisesRegex(ConfigError, "telegram cannot use broker"):
            manifest.validate()

    def test_governance_is_deny_by_default(self):
        request = ActionRequest(
            actor_id="operator",
            capability="file.write",
            target=str(Path.cwd() / "maya-data" / "report.md"),
            operation="write",
        )
        gateway = DenyByDefaultGateway()
        result = gateway.authorize(request)

        self.assertEqual(result.decision, GovernanceDecision.DENY)
        with self.assertRaises(ActionDeniedError):
            require_authorized(gateway, request)


if __name__ == "__main__":
    unittest.main()
