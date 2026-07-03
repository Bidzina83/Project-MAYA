from pathlib import Path
import unittest


class TestPhase3Closure(unittest.TestCase):
    def test_phase3_closure_maps_acceptance_criteria(self):
        doc = Path("docs/architecture/phase3_dependency_readiness_closure.md").read_text(
            encoding="utf-8"
        )

        for expected in (
            "Capability Dependency and Readiness Foundation",
            "Approved Step Evidence",
            "Acceptance Evidence",
            "Dependency contracts are typed, deterministic",
            "Contracts distinguish Python packages",
            "`maya doctor` reports readiness",
            "Missing optional dependencies warn",
            "Missing required dependencies fail",
            "Disabled profiles and disabled connectors do not fail doctor",
            "Clean package verification proves dependency metadata ships in the wheel",
        ):
            self.assertIn(expected, doc)

    def test_phase3_closure_links_required_tests_and_docs(self):
        doc = Path("docs/architecture/phase3_dependency_readiness_closure.md").read_text(
            encoding="utf-8"
        )

        for expected in (
            "docs/architecture/phase3_dependency_readiness_scope.md",
            "docs/architecture/phase3_dependency_contracts.md",
            "docs/architecture/phase3_documents_pdf_readiness.md",
            "docs/architecture/phase3_metabase_readiness.md",
            "docs/architecture/phase3_browser_readiness.md",
            "docs/architecture/phase3_local_model_readiness.md",
            "docs/architecture/phase3_messaging_readiness.md",
            "src/project_maya/dependencies.py",
            "src/project_maya/doctor.py",
            "setup.py",
            "scripts/verify_phase1_package.py",
            "tests/test_phase3_dependency_readiness.py",
            "tests/test_phase3_package_verification.py",
            "tests/test_phase3_closure.py",
            "tests/test_phase2_connector_validation.py",
            "tests/test_phase2_connector_contracts.py",
            "tests/test_phase2_local_model_endpoint_readiness.py",
        ):
            self.assertIn(expected, doc)

    def test_phase3_closure_maps_all_approved_steps(self):
        doc = Path("docs/architecture/phase3_dependency_readiness_closure.md").read_text(
            encoding="utf-8"
        )

        for step in range(1, 12):
            self.assertIn(f"| {step}.", doc)

    def test_phase3_closure_records_completed_surfaces_and_limits(self):
        doc = Path("docs/architecture/phase3_dependency_readiness_closure.md").read_text(
            encoding="utf-8"
        )

        for expected in (
            "`dependencies.python.project_maya`",
            "`dependencies.python.reportlab`",
            "`dependencies.runtime.java`",
            "`dependencies.browser.executable`",
            "`dependencies.endpoint.local-model`",
            "`dependencies.connector.google-contract`",
            "Non-Goals Still Deferred",
            "automatic installation of Poppler",
            "trained Maya skill packaging",
            "full Metabase service lifecycle",
            "browser launch",
            "local model runtime installation",
            "live Google, Slack, or Telegram OAuth",
            "platform support claims",
        ):
            self.assertIn(expected, doc)


if __name__ == "__main__":
    unittest.main()
