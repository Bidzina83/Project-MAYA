import unittest

from project_maya import (
    EnterpriseSecretBackend,
    InMemoryEnterpriseSecretBackend,
    SecretBackendDescriptor,
    SecretBackendKind,
    SecretRef,
    SecretStoreError,
    SecretStoreStatus,
)


class TestPhase2SecretBackendExtension(unittest.TestCase):
    def test_in_memory_enterprise_backend_satisfies_redacted_contract(self):
        descriptor = SecretBackendDescriptor(
            kind=SecretBackendKind.EXTERNAL_VAULT,
            name="customer-vault",
            location="https://vault.customer.example",
            key_ref=SecretRef.parse("secret://vault/unseal-key"),
        )
        backend = InMemoryEnterpriseSecretBackend(descriptor)
        ref = SecretRef.parse("secret://integrations/google")

        backend.write(ref, "super-secret-token")

        self.assertIsInstance(backend, EnterpriseSecretBackend)
        self.assertTrue(backend.contains(ref))
        self.assertEqual(backend.read(ref), "super-secret-token")
        health = backend.health()
        self.assertEqual(health.status, SecretStoreStatus.HEALTHY)
        self.assertEqual(health.backend, "customer-vault")
        self.assertIn("kind=external_vault", health.message)
        self.assertIn("location=configured", health.message)
        self.assertIn("key_ref=configured", health.message)
        self.assertNotIn("super-secret-token", health.message)
        self.assertNotIn("https://vault.customer.example", health.message)
        self.assertNotIn("secret://vault/unseal-key", health.message)

    def test_in_memory_enterprise_backend_delete_and_missing_secret(self):
        backend = InMemoryEnterpriseSecretBackend()
        ref = SecretRef.parse("secret://llm/openai")
        backend.write(ref, "value")
        backend.delete(ref)

        self.assertFalse(backend.contains(ref))
        with self.assertRaisesRegex(SecretStoreError, "secret not found"):
            backend.read(ref)

    def test_secret_backend_descriptor_summary_is_secret_safe(self):
        descriptor = SecretBackendDescriptor(
            kind=SecretBackendKind.MASTER_KEY,
            name="customer-master-key",
            location="C:/sensitive/path/master.key",
            key_ref=SecretRef.parse("secret://enterprise/master-key"),
        )

        summary = descriptor.redacted_summary()

        self.assertEqual(
            summary,
            (
                "kind=master_key; name=customer-master-key; "
                "location=configured; key_ref=configured"
            ),
        )
        self.assertNotIn("C:/sensitive/path/master.key", summary)
        self.assertNotIn("secret://enterprise/master-key", summary)


if __name__ == "__main__":
    unittest.main()
