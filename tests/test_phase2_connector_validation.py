import unittest

from project_maya import (
    BrokerMode,
    ConnectorHealthState,
    ConnectorValidationStatus,
    CredentialMode,
    DoctorStatus,
    config_from_mapping,
    run_doctor,
    validate_configured_connectors,
    validate_connector,
)
from project_maya.adapters import HermesRuntimeAdapter

from tests.test_phase0_contracts import valid_config_mapping


class TestPhase2ConnectorValidation(unittest.TestCase):
    def test_connector_validation_reports_redacted_status_without_network(self):
        config = config_from_mapping(valid_config_mapping())

        validation = validate_connector(
            "google",
            config.integrations["google"],
            broker_mode=BrokerMode.RUNTIME,
        )

        self.assertEqual(validation.status, ConnectorValidationStatus.VALID)
        self.assertEqual(validation.credential_ref_state, "configured")
        self.assertIn("drive.read", validation.capabilities)
        self.assertIn(
            "https://www.googleapis.com/auth/drive.readonly",
            validation.scopes,
        )
        self.assertEqual(validation.allowlist_state["users"], "not_configured")
        self.assertEqual(validation.health, ConnectorHealthState.UNAVAILABLE)
        self.assertFalse(validation.network_used)
        self.assertNotIn("secret://integrations/google", validation.redacted_summary())

    def test_disabled_connector_reports_disabled_health(self):
        config_data = valid_config_mapping()
        config_data["integrations"]["google"] = {
            "enabled": False,
            "credential_mode": "disabled",
        }
        config = config_from_mapping(config_data)

        validation = validate_connector(
            "google",
            config.integrations["google"],
            broker_mode=config.broker.mode,
        )

        self.assertEqual(validation.health, ConnectorHealthState.DISABLED)
        self.assertEqual(validation.credential_ref_state, "not_configured")
        self.assertIn("connector disabled", validation.message)

    def test_invalid_connector_validation_reports_failure_without_throwing(self):
        config_data = valid_config_mapping()
        config_data["broker"] = {"mode": "disabled", "endpoint": None}
        config_data["integrations"]["google"] = {
            "enabled": True,
            "credential_mode": "broker",
            "credential_ref": "secret://integrations/google",
        }
        integration = config_from_mapping(valid_config_mapping()).integrations["google"]

        validation = validate_connector(
            "google",
            integration,
            broker_mode=BrokerMode.DISABLED,
        )

        self.assertEqual(validation.status, ConnectorValidationStatus.INVALID)
        self.assertEqual(validation.health, ConnectorHealthState.INVALID)
        self.assertIn("requires broker mode", validation.message)
        self.assertNotIn("secret://integrations/google", validation.redacted_summary())

    def test_configured_connector_validation_sorts_results(self):
        config = config_from_mapping(valid_config_mapping())

        validations = validate_configured_connectors(
            config.integrations,
            broker_mode=config.broker.mode,
        )

        self.assertEqual([validation.name for validation in validations], ["google", "telegram"])

    def test_doctor_reports_connector_validation_status_redacted(self):
        config = config_from_mapping(valid_config_mapping())

        report = run_doctor(
            config,
            HermesRuntimeAdapter(factory_path="missing.hermes:factory"),
        )
        checks = {check.name: check for check in report.checks}

        self.assertEqual(checks["connectors.config"].status, DoctorStatus.PASS)
        self.assertIn("google:enabled,credential_mode=broker", checks["connectors.config"].message)
        self.assertIn("capabilities=drive.read,calendar.read", checks["connectors.config"].message)
        self.assertIn("health=unavailable", checks["connectors.config"].message)
        self.assertIn("network_used=false", checks["connectors.config"].message)
        self.assertNotIn("secret://integrations/google", checks["connectors.config"].message)


if __name__ == "__main__":
    unittest.main()
