import unittest

from scripts.verify_phase1_package import main as verify_phase1_package


class TestPhase1PackageInstall(unittest.TestCase):
    def test_built_wheel_installs_project_maya_and_cli(self):
        self.assertEqual(verify_phase1_package([]), 0)


if __name__ == "__main__":
    unittest.main()
