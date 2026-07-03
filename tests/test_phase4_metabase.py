import json
import tempfile
import unittest
from pathlib import Path

from project_maya import (
    ActionRequest,
    AuthorizationResult,
    GovernanceDecision,
    LocalJsonlAuditSink,
    MetabaseCapabilityError,
    apply_metabase_provisioning,
    config_from_mapping,
    inspect_metabase_lifecycle,
    plan_metabase_provisioning,
    run_doctor,
    validate_metabase_health,
    write_metabase_provisioning_plan,
)
from project_maya.adapters import HermesRuntimeAdapter
from tests.test_phase0_contracts import valid_config_mapping


class Gateway:
    def __init__(self, decision=GovernanceDecision.ALLOW):
        self.decision = decision
        self.requests = []

    def authorize(self, request: ActionRequest):
        self.requests.append(request)
        return AuthorizationResult(
            decision=self.decision,
            reason_code=f"test.{self.decision.value}",
        )


def _config(data_dir: Path, *, deployment: str = "customer_managed"):
    data = valid_config_mapping()
    data["runtime"]["enabled_profiles"] = ["maya-core", "maya-metabase"]
    data["deployment"]["data_dir"] = str(data_dir)
    data["governance"]["policy_file"] = str(data_dir / "governance" / "policy.json")
    data["metabase"] = {
        "enabled": True,
        "deployment": deployment,
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
    }
    return config_from_mapping(data)


class TestPhase4Metabase(unittest.TestCase):
    def test_customer_managed_health_is_redacted_and_no_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = _config(Path(tmp) / "maya-data")

            health = validate_metabase_health(config)
            summary = json.dumps(health.redacted_summary(), sort_keys=True)

        self.assertEqual(health.status, "ready")
        self.assertEqual(health.deployment, "customer_managed")
        self.assertFalse(health.network_used)
        self.assertNotIn("secret://metabase", summary)
        self.assertIn('"memory_exposed": "false"', summary)

    def test_customer_managed_lifecycle_reports_customer_owned_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            lifecycle = inspect_metabase_lifecycle(_config(Path(tmp) / "maya-data"))
            summary = json.dumps(lifecycle.redacted_summary(), sort_keys=True)

        self.assertEqual(lifecycle.status, "customer_managed")
        self.assertTrue(lifecycle.customer_managed)
        self.assertNotIn(str(Path(tmp)), summary)

    def test_managed_local_lifecycle_reports_missing_artifact_without_failure_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            lifecycle = inspect_metabase_lifecycle(
                _config(data_dir, deployment="managed_local")
            )

        self.assertEqual(lifecycle.status, "managed_local_artifact_missing")
        self.assertEqual(lifecycle.service_artifact, "missing")

    def test_live_health_is_deferred_without_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            health = validate_metabase_health(_config(Path(tmp) / "maya-data"), live=True)

        self.assertEqual(health.status, "live_check_deferred")
        self.assertFalse(health.network_used)

    def test_provisioning_plan_excludes_memory_prompts_secrets_and_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = plan_metabase_provisioning(_config(Path(tmp) / "maya-data"))
            summary = json.dumps(plan.redacted_summary(), sort_keys=True)

        self.assertEqual(plan.status, "planned")
        self.assertIn('"raw_memory": "excluded"', summary)
        self.assertIn('"prompts": "excluded"', summary)
        self.assertIn('"secrets": "excluded"', summary)
        self.assertIn('"files": "excluded"', summary)
        self.assertNotIn("secret://metabase", summary)

    def test_write_provisioning_plan_persists_redacted_metadata_under_maya_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            config = _config(data_dir)
            plan = plan_metabase_provisioning(config)

            path = write_metabase_provisioning_plan(config, plan)
            text = path.read_text(encoding="utf-8")

        self.assertEqual(path.name, "latest-plan.json")
        self.assertIn("metabase", path.parts)
        self.assertIn("provisioning", path.parts)
        self.assertNotIn("secret://metabase", text)
        self.assertIn('"raw_memory": "excluded"', text)

    def test_write_provisioning_plan_rejects_unsafe_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = _config(Path(tmp) / "maya-data")
            plan = plan_metabase_provisioning(config)

            with self.assertRaises(MetabaseCapabilityError):
                write_metabase_provisioning_plan(
                    config,
                    plan,
                    filename="../escape.json",
                )

    def test_apply_requires_governance_and_audits_without_secret_refs(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            audit_path = data_dir / "governance" / "audit" / "runtime.jsonl"
            gateway = Gateway()

            result = apply_metabase_provisioning(
                _config(data_dir),
                gateway=gateway,
                audit_sink=LocalJsonlAuditSink(audit_path),
            )

            audit_text = audit_path.read_text(encoding="utf-8")
            record = json.loads(audit_text.splitlines()[0])
            applied_path = (
                data_dir
                / "metabase"
                / "provisioning"
                / "last-applied-plan.json"
            )
            applied_exists = applied_path.is_file()

        self.assertEqual(result.status, "applied")
        self.assertTrue(applied_exists)
        self.assertEqual(gateway.requests[0].capability, "metabase.apply-provision")
        self.assertEqual(record["event_type"], "authorization.metabase")
        self.assertNotIn("secret://metabase", audit_text)

    def test_apply_denial_prevents_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(PermissionError):
                apply_metabase_provisioning(
                    _config(Path(tmp) / "maya-data"),
                    gateway=Gateway(GovernanceDecision.DENY),
                )

    def test_apply_blocked_plan_reports_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = valid_config_mapping()
            data["runtime"]["enabled_profiles"] = ["maya-core", "maya-metabase"]
            data["deployment"]["data_dir"] = str(Path(tmp) / "maya-data")
            data["metabase"] = {
                "enabled": True,
                "deployment": "customer_managed",
                "endpoint": None,
                "application_database": {
                    "engine": "sqlite",
                    "credential_ref": "secret://metabase/application-db",
                },
                "analytics_sources": [],
            }
            config = config_from_mapping(data)

            with self.assertRaises(MetabaseCapabilityError):
                apply_metabase_provisioning(config, gateway=Gateway())

    def test_doctor_reports_phase4_metabase_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = run_doctor(
                _config(Path(tmp) / "maya-data"),
                HermesRuntimeAdapter(factory_path="missing.hermes:factory"),
            )

        checks = {check.name: check for check in report.checks}
        self.assertIn("metabase.health", checks)
        self.assertIn("metabase.lifecycle", checks)
        self.assertIn("metabase.provisioning", checks)
        self.assertNotIn("secret://metabase", checks["metabase.health"].message)


if __name__ == "__main__":
    unittest.main()
