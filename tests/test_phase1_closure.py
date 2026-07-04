import unittest
from pathlib import Path

from scripts.verify_phase1_package import REQUIRED_COMMANDS


class TestPhase1Closure(unittest.TestCase):
    def test_phase1_closure_evidence_files_exist(self):
        root = Path(__file__).resolve().parents[1]
        evidence = [
            "docs/architecture/phase1_closure.md",
            "docs/architecture/phase1_package_verification.md",
            "docs/architecture/hermes_runtime_binding.md",
            "docs/architecture/governed_memory.md",
            "docs/architecture/hermes_memory_provider.md",
            "docs/architecture/local_authorization_policy.md",
            "docs/architecture/model_egress_governance.md",
            "docs/architecture/local_api_boundary.md",
            "docs/architecture/local_secret_store.md",
            "docs/architecture/local_doctor_checks.md",
            "docs/architecture/local_repair.md",
            "docs/architecture/local_integration_reset.md",
            "docs/architecture/local_backup.md",
            "docs/architecture/local_migration_cli.md",
            "docs/architecture/local_update_status.md",
            "scripts/validate_project_maya_context.py",
            "scripts/verify_phase1_package.py",
        ]

        missing = [path for path in evidence if not (root / path).is_file()]

        self.assertEqual(missing, [])

    def test_package_verifier_covers_required_v2_command_surface(self):
        expected = (
            "doctor",
            "repair",
            "reset-integration",
            "run",
            "serve-local-api",
            "rotate-secret",
            "export-config",
            "import-config",
            "backup",
            "restore",
            "migrate",
            "update",
            "documents",
            "metabase",
            "setup",
            "health",
        )

        self.assertEqual(REQUIRED_COMMANDS, expected)
