import os
import tempfile
import unittest
from pathlib import Path

from project_maya import (
    SecretRef,
    SecretReferenceError,
    SecretStoreError,
    SecretStoreStatus,
    WindowsDPAPISecretStore,
    build_local_product,
    build_platform_secret_store,
    config_from_mapping,
    run_doctor,
)
from project_maya.adapters import HermesRuntimeAdapter
from tests.test_phase0_contracts import valid_config_mapping


class TestPhase1Secrets(unittest.TestCase):
    def test_platform_secret_store_reports_unavailable_when_not_supported(self):
        if os.name == "nt":
            self.skipTest("non-Windows fallback is not used on Windows")

        with tempfile.TemporaryDirectory() as tmp:
            store = build_platform_secret_store(Path(tmp))
            health = store.health()

        self.assertEqual(health.status, SecretStoreStatus.UNAVAILABLE)
        self.assertFalse(store.contains(SecretRef.parse("secret://llm/openai")))
        with self.assertRaises(SecretStoreError):
            store.read(SecretRef.parse("secret://llm/openai"))

    @unittest.skipUnless(os.name == "nt", "Windows DPAPI is Windows-only")
    def test_windows_dpapi_store_round_trips_without_plaintext_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = WindowsDPAPISecretStore(Path(tmp) / "secrets")
            ref = SecretRef.parse("secret://integrations/google")

            store.write(ref, "super-secret-token")
            stored_path = Path(tmp) / "secrets" / "integrations" / "google.secret"

            self.assertTrue(store.contains(ref))
            self.assertEqual(store.read(ref), "super-secret-token")
            self.assertNotIn("super-secret-token", stored_path.read_text("ascii"))

            store.delete(ref)
            self.assertFalse(store.contains(ref))

    @unittest.skipUnless(os.name == "nt", "Windows DPAPI is Windows-only")
    def test_windows_dpapi_store_preserves_dotted_secret_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = WindowsDPAPISecretStore(Path(tmp) / "secrets")
            ref = SecretRef.parse("secret://integrations/google.oauth")

            store.write(ref, "token")

            self.assertTrue(
                (Path(tmp) / "secrets" / "integrations" / "google.oauth.secret")
                .is_file()
            )

    def test_secret_reference_rejects_unsafe_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = build_platform_secret_store(Path(tmp))
            with self.assertRaises(SecretReferenceError):
                store.contains(SecretRef.parse("secret://../escape"))

    def test_build_local_product_assembles_secret_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_data = valid_config_mapping()
            config_data["deployment"]["data_dir"] = str(Path(tmp) / "maya-data")
            config_data["runtime"]["enabled_profiles"] = ["maya-core"]
            config_data["memory"]["retriever"] = "local_json"

            product = build_local_product(config_from_mapping(config_data))
            health = product.secret_store.health()

        if os.name == "nt":
            self.assertEqual(health.status, SecretStoreStatus.HEALTHY)
            self.assertEqual(health.backend, "windows-dpapi")
        else:
            self.assertEqual(health.status, SecretStoreStatus.UNAVAILABLE)

    def test_doctor_reports_secret_backend_without_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_data = valid_config_mapping()
            config_data["deployment"]["data_dir"] = str(Path(tmp) / "maya-data")
            config_data["runtime"]["enabled_profiles"] = ["maya-core"]
            config = config_from_mapping(config_data)
            store = build_platform_secret_store(config.deployment.data_dir)
            runtime = HermesRuntimeAdapter(factory_path="missing.hermes:factory")

            report = run_doctor(config, runtime, secret_store=store)

        checks = {check.name: check for check in report.checks}
        self.assertIn("secrets.backend", checks)
        self.assertNotIn("secret://llm/openai", checks["secrets.backend"].message)
        self.assertNotIn("super-secret-token", checks["secrets.backend"].message)


if __name__ == "__main__":
    unittest.main()
