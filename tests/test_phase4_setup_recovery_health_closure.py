import unittest
from pathlib import Path


class TestPhase4SetupRecoveryHealthClosure(unittest.TestCase):
    def test_phase4_scope_records_boundaries(self):
        scope = Path(
            "docs/architecture/phase4_setup_recovery_health_scope.md"
        ).read_text(encoding="utf-8")

        for expected in (
            "Windows-first",
            "does not",
            "production installer",
            "automatic updates",
            "claim full Windows",
        ):
            self.assertIn(expected, scope)

    def test_phase4_closure_maps_approved_steps(self):
        closure = Path(
            "docs/architecture/phase4_setup_recovery_health_closure.md"
        ).read_text(encoding="utf-8")

        for expected in (
            "1. Scope gate",
            "2. Setup contract",
            "3. Setup CLI",
            "4. Health summary",
            "5. Recovery UX",
            "6. Backup/restore hardening",
            "7. Update readiness hardening",
            "8. Windows installed-package smoke",
            "9. Package verification",
            "10. Closure",
            "tests/test_phase4_setup_recovery_health_package_verification.py",
        ):
            self.assertIn(expected, closure)


if __name__ == "__main__":
    unittest.main()
