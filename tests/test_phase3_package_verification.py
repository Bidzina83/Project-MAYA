from pathlib import Path
import unittest


class TestPhase3PackageVerification(unittest.TestCase):
    def test_package_verifier_checks_dependency_contract_surfaces(self):
        script = Path("scripts/verify_phase1_package.py").read_text(
            encoding="utf-8"
        )

        for expected in (
            "_verify_installed_dependency_contract_surfaces",
            "dependency_contracts",
            "evaluate_profile_readiness",
            "ComponentProfile.DOCUMENTS",
            "ComponentProfile.METABASE",
            "ComponentProfile.MESSAGING",
        ):
            self.assertIn(expected, script)

    def test_phase3_docs_record_scope_contracts_and_limits(self):
        scope = Path("docs/architecture/phase3_dependency_readiness_scope.md").read_text(
            encoding="utf-8"
        )
        contracts = Path("docs/architecture/phase3_dependency_contracts.md").read_text(
            encoding="utf-8"
        )
        closure = Path(
            "docs/architecture/phase3_dependency_readiness_closure.md"
        ).read_text(encoding="utf-8")

        for expected in (
            "python_package",
            "system_command",
            "external_service",
            "model_endpoint",
            "missing_required",
            "customer_managed",
            "does not:",
        ):
            self.assertIn(expected, scope)
        for expected in (
            "reportlab",
            "pypdf",
            "pdftoppm",
            "Microsoft Office",
            "Google",
            "Slack",
            "Telegram",
            "local endpoint",
        ):
            self.assertIn(expected, contracts)
        self.assertIn("Known Limits", closure)


if __name__ == "__main__":
    unittest.main()
