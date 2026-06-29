from pathlib import Path
import unittest


class TestPhase2Closure(unittest.TestCase):
    def test_phase2_closure_evidence_maps_acceptance_criteria(self):
        doc = Path("docs/architecture/phase2_closure.md").read_text(
            encoding="utf-8"
        )

        for expected in (
            "Enterprise operates without Maya cloud services.",
            "`broker.mode=disabled`",
            "Customer-owned model credentials",
            "Google, Slack, and Telegram credential modes",
            "Connector validation reports capabilities, scopes",
            "provider-token revocation",
            "Local API, governed runtime, model egress policy",
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
            "docs/architecture/local_integration_reset.md",
            "docs/architecture/phase2_package_verification.md",
            "tests/test_phase2_model_config.py",
            "tests/test_phase2_connector_contracts.py",
            "tests/test_phase2_connector_validation.py",
            "tests/test_phase2_reset_revocation.py",
            "tests/test_phase2_package_verification.py",
        ):
            self.assertIn(expected, doc)


if __name__ == "__main__":
    unittest.main()
