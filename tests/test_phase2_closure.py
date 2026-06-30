from pathlib import Path
import unittest


class TestPhase2Closure(unittest.TestCase):
    def test_phase2_closure_evidence_maps_acceptance_criteria(self):
        doc = Path("docs/architecture/phase2_closure.md").read_text(
            encoding="utf-8"
        )

        for expected in (
            "Enterprise operates without Maya cloud services.",
            "Approved Step Evidence",
            "`broker.mode=disabled`",
            "Customer-owned model credentials",
            "Google, Slack, and Telegram credential modes",
            "Connector validation reports capabilities, scopes",
            "provider-token revocation",
            "Local API, governed runtime, model egress policy",
            "Enterprise config profiles",
            "Local model endpoint readiness",
            "Secret backend extension point",
            "Clean package verification",
            "Closure audit maps accepted capabilities",
        ):
            self.assertIn(expected, doc)

    def test_phase2_closure_links_required_tests_and_docs(self):
        doc = Path("docs/architecture/phase2_closure.md").read_text(
            encoding="utf-8"
        )

        for expected in (
            "docs/architecture/phase2_scope.md",
            "docs/architecture/phase2_model_validation.md",
            "docs/architecture/phase2_connector_contracts.md",
            "docs/architecture/phase2_broker_disabled_runtime_path.md",
            "docs/architecture/phase2_enterprise_config_profiles.md",
            "docs/architecture/phase2_local_model_endpoint_readiness.md",
            "docs/architecture/phase2_secret_backend_extension.md",
            "docs/architecture/local_integration_reset.md",
            "docs/architecture/phase2_package_verification.md",
            "tests/test_phase2_model_config.py",
            "tests/test_phase2_connector_contracts.py",
            "tests/test_phase2_connector_validation.py",
            "tests/test_phase2_reset_revocation.py",
            "tests/test_phase2_broker_disabled_runtime.py",
            "tests/test_phase2_enterprise_config_profiles.py",
            "tests/test_phase2_local_model_endpoint_readiness.py",
            "tests/test_phase2_secret_backend_extension.py",
            "tests/test_phase2_package_verification.py",
            "scripts/verify_phase1_package.py",
        ):
            self.assertIn(expected, doc)

    def test_phase2_closure_maps_all_approved_steps(self):
        doc = Path("docs/architecture/phase2_closure.md").read_text(
            encoding="utf-8"
        )

        for step in range(1, 12):
            self.assertIn(f"| {step}.", doc)


if __name__ == "__main__":
    unittest.main()
