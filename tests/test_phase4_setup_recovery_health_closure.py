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
            "Restore planning",
            "Migration dry-run",
        ):
            self.assertIn(expected, scope)

    def test_phase4_closure_maps_approved_steps(self):
        closure = Path(
            "docs/architecture/phase4_setup_recovery_health_closure.md"
        ).read_text(encoding="utf-8")

        for expected in (
            "1. Scope gate",
            "2. Edition-aware setup contract",
            "3. Setup CLI",
            "4. Health summary",
            "5. Recovery UX",
            "6. Backup/restore hardening",
            "7. Migration and update readiness hardening",
            "8. Windows installed-package smoke",
            "9. Package verification",
            "10. Closure",
            "tests/test_phase4_setup_recovery_health_package_verification.py",
            "Restore planning reports manifest status",
            "Migration remains dry-run by default",
            "create customer tenant resources",
        ):
            self.assertIn(expected, closure)

    def test_phase4_closure_does_not_claim_later_phase_work(self):
        closure = Path(
            "docs/architecture/phase4_setup_recovery_health_closure.md"
        ).read_text(encoding="utf-8")

        for forbidden in (
            "production OAuth is complete",
            "broker protocol is complete",
            "automatic update is complete",
            "signed installer is complete",
            "Windows is supported",
            "silently installs",
        ):
            self.assertNotIn(forbidden, closure)


if __name__ == "__main__":
    unittest.main()
