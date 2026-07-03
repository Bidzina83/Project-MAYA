import unittest
from pathlib import Path
from unittest import mock

from project_maya import (
    AgentState,
    ComponentProfile,
    DependencyCategory,
    DependencyReadinessStatus,
    DoctorStatus,
    config_from_mapping,
    dependency_contracts,
    evaluate_profile_readiness,
    run_doctor,
)
from project_maya.adapters import HermesRuntimeAdapter
from tests.test_phase0_contracts import valid_config_mapping


def _config_with_profiles(*profiles: str):
    data = valid_config_mapping()
    data["runtime"]["enabled_profiles"] = list(profiles) or ["maya-core"]
    data["metabase"]["enabled"] = "maya-metabase" in data["runtime"]["enabled_profiles"]
    if not data["metabase"]["enabled"]:
        data["metabase"] = {
            "enabled": False,
            "deployment": "disabled",
            "endpoint": None,
            "application_database": None,
            "analytics_sources": [],
        }
    data["deployment"]["data_dir"] = str(Path.cwd() / "maya-data")
    data["governance"]["policy_file"] = str(
        Path(data["deployment"]["data_dir"]) / "governance" / "policy.json"
    )
    return config_from_mapping(data)


class TestPhase3DependencyReadiness(unittest.TestCase):
    def test_dependency_contracts_cover_all_component_profiles(self):
        contracts = dependency_contracts()
        profiles = {contract.profile for contract in contracts}

        self.assertIn(ComponentProfile.CORE, profiles)
        self.assertIn(ComponentProfile.DOCUMENTS, profiles)
        self.assertIn(ComponentProfile.METABASE, profiles)
        self.assertIn(ComponentProfile.BROWSER, profiles)
        self.assertIn(ComponentProfile.MESSAGING, profiles)
        self.assertIn(ComponentProfile.LOCAL_MODELS, profiles)
        self.assertTrue(
            all(contract.dependency_id and contract.check_name for contract in contracts)
        )

    def test_dependency_contract_categories_include_planned_types(self):
        categories = {contract.category for contract in dependency_contracts()}

        for category in (
            DependencyCategory.PYTHON_PACKAGE,
            DependencyCategory.SYSTEM_COMMAND,
            DependencyCategory.LOCAL_APPLICATION,
            DependencyCategory.SERVICE_RUNTIME,
            DependencyCategory.EXTERNAL_SERVICE,
            DependencyCategory.MODEL_ENDPOINT,
            DependencyCategory.CUSTOMER_MANAGED,
        ):
            self.assertIn(category, categories)

    def test_disabled_profile_readiness_does_not_fail(self):
        config = _config_with_profiles("maya-core")
        readiness = evaluate_profile_readiness(
            config,
            ComponentProfile.DOCUMENTS,
        )

        self.assertEqual(readiness.status, DependencyReadinessStatus.DISABLED)
        self.assertEqual(readiness.dependencies, ())

    def test_documents_profile_reports_required_and_optional_dependencies(self):
        config = _config_with_profiles("maya-core", "maya-documents")
        with mock.patch("project_maya.dependencies.shutil.which", return_value=None):
            readiness = evaluate_profile_readiness(
                config,
                ComponentProfile.DOCUMENTS,
            )

        by_id = {
            dependency.contract.dependency_id: dependency
            for dependency in readiness.dependencies
        }
        self.assertIn("python.reportlab", by_id)
        self.assertIn("python.pypdf", by_id)
        self.assertIn("python.markdown", by_id)
        self.assertIn("python.pillow", by_id)
        self.assertIn("command.pdftoppm", by_id)
        self.assertIn("application.ms-office", by_id)
        self.assertEqual(
            by_id["command.pdftoppm"].status,
            DependencyReadinessStatus.MISSING_OPTIONAL,
        )
        self.assertEqual(
            by_id["application.ms-office"].status,
            DependencyReadinessStatus.CUSTOMER_MANAGED,
        )

    def test_metabase_profile_reports_redacted_database_and_service_readiness(self):
        config = _config_with_profiles("maya-core", "maya-metabase")
        with mock.patch("project_maya.dependencies.shutil.which", return_value=None):
            readiness = evaluate_profile_readiness(
                config,
                ComponentProfile.METABASE,
            )

        by_id = {
            dependency.contract.dependency_id: dependency
            for dependency in readiness.dependencies
        }
        self.assertEqual(
            by_id["runtime.java"].status,
            DependencyReadinessStatus.MISSING_REQUIRED,
        )
        self.assertEqual(
            by_id["service.metabase"].status,
            DependencyReadinessStatus.CUSTOMER_MANAGED,
        )
        self.assertIn("deployment=managed_local", by_id["service.metabase"].message)
        self.assertIn("endpoint=loopback_configured", by_id["service.metabase"].message)
        self.assertEqual(
            by_id["database.metabase-application"].status,
            DependencyReadinessStatus.CUSTOMER_MANAGED,
        )
        self.assertIn(
            "credential_ref=configured",
            by_id["database.metabase-application"].message,
        )
        self.assertNotIn(
            "secret://metabase",
            by_id["database.metabase-application"].message,
        )
        self.assertEqual(
            by_id["database.metabase-analytics-sources"].status,
            DependencyReadinessStatus.CUSTOMER_MANAGED,
        )
        self.assertIn(
            "analytics_sources=1",
            by_id["database.metabase-analytics-sources"].message,
        )
        self.assertNotIn(
            "secret://metabase",
            by_id["database.metabase-analytics-sources"].message,
        )

    def test_metabase_profile_warns_when_no_analytics_sources_are_configured(self):
        data = valid_config_mapping()
        data["runtime"]["enabled_profiles"] = ["maya-core", "maya-metabase"]
        data["metabase"]["analytics_sources"] = []
        data["deployment"]["data_dir"] = str(Path.cwd() / "maya-data")
        config = config_from_mapping(data)

        readiness = evaluate_profile_readiness(
            config,
            ComponentProfile.METABASE,
        )

        by_id = {
            dependency.contract.dependency_id: dependency
            for dependency in readiness.dependencies
        }
        self.assertEqual(
            by_id["database.metabase-analytics-sources"].status,
            DependencyReadinessStatus.MISSING_OPTIONAL,
        )
        self.assertIn(
            "analytics_sources=0",
            by_id["database.metabase-analytics-sources"].message,
        )

    def test_metabase_profile_fails_when_profile_enabled_but_metabase_disabled(self):
        data = valid_config_mapping()
        data["runtime"]["enabled_profiles"] = ["maya-core", "maya-metabase"]
        data["deployment"]["data_dir"] = str(Path.cwd() / "maya-data")
        data["metabase"] = {
            "enabled": False,
            "deployment": "disabled",
            "endpoint": None,
            "application_database": None,
            "analytics_sources": [],
        }
        config = config_from_mapping(data)

        readiness = evaluate_profile_readiness(
            config,
            ComponentProfile.METABASE,
        )

        by_id = {
            dependency.contract.dependency_id: dependency
            for dependency in readiness.dependencies
        }
        self.assertEqual(
            readiness.status,
            DependencyReadinessStatus.MISSING_REQUIRED,
        )
        self.assertEqual(
            by_id["service.metabase"].status,
            DependencyReadinessStatus.MISSING_REQUIRED,
        )
        self.assertEqual(
            by_id["database.metabase-application"].status,
            DependencyReadinessStatus.DISABLED,
        )

    def test_doctor_reports_dependency_readiness_for_enabled_profiles(self):
        config = _config_with_profiles("maya-core", "maya-documents")
        with mock.patch("project_maya.dependencies.shutil.which", return_value=None):
            report = run_doctor(
                config,
                HermesRuntimeAdapter(factory_path="missing.hermes:factory"),
                lifecycle_state=AgentState.CREATED,
            )

        checks = {check.name: check for check in report.checks}
        self.assertIn("dependencies.profile.maya-documents", checks)
        self.assertIn("dependencies.python.reportlab", checks)
        self.assertIn("dependencies.command.pdftoppm", checks)
        self.assertIn("dependencies.application.ms-office", checks)
        self.assertEqual(
            checks["dependencies.command.pdftoppm"].status,
            DoctorStatus.WARN,
        )
        self.assertNotIn("secret://", checks["dependencies.profile.maya-documents"].message)

    def test_doctor_reports_metabase_dependency_readiness(self):
        config = _config_with_profiles("maya-core", "maya-metabase")
        with mock.patch("project_maya.dependencies.shutil.which", return_value=None):
            report = run_doctor(
                config,
                HermesRuntimeAdapter(factory_path="missing.hermes:factory"),
                lifecycle_state=AgentState.CREATED,
            )

        checks = {check.name: check for check in report.checks}
        self.assertIn("dependencies.profile.maya-metabase", checks)
        self.assertIn("dependencies.runtime.java", checks)
        self.assertIn("dependencies.service.metabase", checks)
        self.assertIn("dependencies.database.metabase-application", checks)
        self.assertIn("dependencies.database.metabase-analytics-sources", checks)
        self.assertEqual(checks["dependencies.runtime.java"].status, DoctorStatus.FAIL)
        self.assertEqual(checks["dependencies.service.metabase"].status, DoctorStatus.PASS)
        self.assertNotIn("secret://metabase", checks["dependencies.database.metabase-application"].message)

    def test_connector_service_dependencies_use_redacted_validation(self):
        data = valid_config_mapping()
        data["runtime"]["enabled_profiles"] = ["maya-core", "maya-messaging"]
        data["integrations"]["google"]["enabled"] = True
        data["deployment"]["data_dir"] = str(Path.cwd() / "maya-data")
        config = config_from_mapping(data)
        report = run_doctor(
            config,
            HermesRuntimeAdapter(factory_path="missing.hermes:factory"),
            lifecycle_state=AgentState.CREATED,
        )

        checks = {check.name: check for check in report.checks}
        self.assertIn("dependencies.service.google", checks)
        self.assertNotIn("secret://integrations/google", checks["dependencies.service.google"].message)
        self.assertIn("credential_ref=configured", checks["dependencies.service.google"].message)

    def test_local_model_dependency_uses_phase2_local_mode_contract(self):
        data = valid_config_mapping()
        data["runtime"]["enabled_profiles"] = ["maya-core", "maya-local-models"]
        data["llm"] = {
            "mode": "local",
            "provider": "openai-compatible",
            "model": "llama-local",
            "endpoint": "http://127.0.0.1:11434/v1",
            "credential_ref": None,
        }
        data["deployment"]["data_dir"] = str(Path.cwd() / "maya-data")
        config = config_from_mapping(data)

        readiness = evaluate_profile_readiness(
            config,
            ComponentProfile.LOCAL_MODELS,
        )

        by_id = {
            dependency.contract.dependency_id: dependency
            for dependency in readiness.dependencies
        }
        self.assertEqual(
            by_id["endpoint.local-model"].status,
            DependencyReadinessStatus.CUSTOMER_MANAGED,
        )
        self.assertIn("family=ollama", by_id["endpoint.local-model"].message)

    def test_install_hints_are_not_machine_specific(self):
        for contract in dependency_contracts():
            hint = contract.install_hint("Windows")
            self.assertNotIn("C:\\Users\\", hint)
            self.assertNotIn("/home/", hint)
            self.assertNotIn("/opt/data", hint)


if __name__ == "__main__":
    unittest.main()
