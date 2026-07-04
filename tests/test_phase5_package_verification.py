import unittest
from pathlib import Path


class TestPhase5PackageVerification(unittest.TestCase):
    def test_clean_package_verifier_covers_phase5_operator_surfaces(self):
        verifier = Path("scripts/verify_phase1_package.py").read_text(
            encoding="utf-8"
        )

        for expected in (
            "_verify_installed_phase5_operator_surfaces",
            "phase5-operator-surfaces-importable",
            "setup",
            "health",
            "backup",
            "inspect",
            "restore",
            "mutation",
        ):
            self.assertIn(expected, verifier)


if __name__ == "__main__":
    unittest.main()
