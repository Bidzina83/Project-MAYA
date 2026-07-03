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
            "DOCUMENTS_EXTRA_REQUIREMENTS",
            "dependencies.python.markdown",
            "documents-extra-ready",
            "dependencies.runtime.java",
            "dependencies.database.metabase-application",
            "dependencies.database.metabase-analytics-sources",
        ):
            self.assertIn(expected, script)

    def test_setup_declares_documents_extras_without_default_install(self):
        setup_py = Path("setup.py").read_text(encoding="utf-8")

        for expected in (
            "'documents': DOCUMENTS_REQUIREMENTS",
            "'documents-preview'",
            "'Markdown>=3.5'",
            "'Pillow>=10.0'",
            "'pypdf>=4.0'",
            "'reportlab>=4.0'",
            "'PyMuPDF>=1.24'",
        ):
            self.assertIn(expected, setup_py)

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
        documents = Path(
            "docs/architecture/phase3_documents_pdf_readiness.md"
        ).read_text(encoding="utf-8")
        metabase = Path("docs/architecture/phase3_metabase_readiness.md").read_text(
            encoding="utf-8"
        )

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
            "Markdown",
            "Pillow",
            "pdftoppm",
            "Microsoft Office",
            "Google",
            "Slack",
            "Telegram",
            "local endpoint",
        ):
            self.assertIn(expected, contracts)
        self.assertIn("Known Limits", closure)
        for expected in (
            "project-maya[documents]",
            "project-maya[documents-preview]",
            "Hermes-Agent-Maya-Skills",
            "does not package trained Maya skills",
        ):
            self.assertIn(expected, documents)
        for expected in (
            "dependencies.runtime.java",
            "dependencies.database.metabase-application",
            "dependencies.database.metabase-analytics-sources",
            "Maya persistent memory is not reported as an analytics source",
            "does not:",
        ):
            self.assertIn(expected, metabase)


if __name__ == "__main__":
    unittest.main()
