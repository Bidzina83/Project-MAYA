from pathlib import Path
import unittest


class TestPhase2PackageVerification(unittest.TestCase):
    def test_phase2_package_verification_documents_enterprise_byo_surface(self):
        doc = Path("docs/architecture/phase2_package_verification.md").read_text(
            encoding="utf-8"
        )
        script = Path("scripts/verify_phase1_package.py").read_text(encoding="utf-8")

        for expected in (
            "Enterprise BYO",
            "`broker.mode=disabled`",
            "customer-owned",
            "`load_config_profile`",
            "`validate_local_model_endpoint`",
            "`InMemoryEnterpriseSecretBackend`",
            "reset-integration --revoke-provider",
            "without printing secret",
        ):
            self.assertIn(expected, doc)
        for expected in (
            "_verify_installed_enterprise_byo_surfaces",
            "_verify_installed_phase2_profile_model_and_secret_surfaces",
            "_write_enterprise_byo_config",
            "_write_enterprise_local_model_profile",
            "ProviderRevocationStatus",
            "InMemoryEnterpriseSecretBackend",
            "load_config_profile",
            "validate_local_model_endpoint",
            "validate_configured_connectors",
            "validate_model_config",
        ):
            self.assertIn(expected, script)


if __name__ == "__main__":
    unittest.main()
