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
            "dependencies.browser.executable",
            "dependencies.browser.automation-driver",
            "dependencies.browser.governance-policy",
            "dependencies.endpoint.local-model",
            "dependencies.runtime.local-model-family",
            "dependencies.model.local-model-artifact",
            "dependencies.connector.google-contract",
            "dependencies.connector.slack-governance",
            "dependencies.connector.telegram-contract",
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
        browser = Path("docs/architecture/phase3_browser_readiness.md").read_text(
            encoding="utf-8"
        )
        local_model = Path(
            "docs/architecture/phase3_local_model_readiness.md"
        ).read_text(encoding="utf-8")
        messaging = Path("docs/architecture/phase3_messaging_readiness.md").read_text(
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
        for expected in (
            "Phase 3 Closure Audit",
            "Approved Step Evidence",
            "Acceptance Evidence",
            "Readiness Foundation Limits",
            "Exit Statement",
        ):
            self.assertIn(expected, closure)
        for expected in (
            "project-maya[documents]",
            "project-maya[documents-preview]",
            "Hermes-Agent-Maya-Skills",
            "packages the approved `documents/pdf` skill artifact",
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
        for expected in (
            "dependencies.browser.executable",
            "dependencies.browser.automation-driver",
            "dependencies.browser.governance-policy",
            "does not:",
            "claim browser automation support",
        ):
            self.assertIn(expected, browser)
        for expected in (
            "dependencies.endpoint.local-model",
            "dependencies.runtime.local-model-family",
            "dependencies.model.local-model-artifact",
            "network-free",
            "does not:",
            "claim local model support",
        ):
            self.assertIn(expected, local_model)
        for expected in (
            "dependencies.connector.google-contract",
            "dependencies.connector.slack-governance",
            "dependencies.connector.telegram-contract",
            "Telegram remains customer-owned only",
            "does not:",
            "perform live OAuth",
        ):
            self.assertIn(expected, messaging)


if __name__ == "__main__":
    unittest.main()
