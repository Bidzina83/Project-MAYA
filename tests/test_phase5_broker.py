import json
import tempfile
import unittest
from pathlib import Path

from project_maya.broker import (
    BrokerOperationError,
    BrokerProtocolError,
    ReplayCache,
    complete_oauth_session,
    generate_instance_identity,
    model_proxy_readiness,
    refresh_token,
    register_broker_instance,
    revoke_token,
    run_mock_broker_conformance,
    sign_broker_request,
    start_oauth_session,
    token_status,
    verify_broker_request,
)
from project_maya.config import config_from_mapping
from project_maya.secrets import InMemoryEnterpriseSecretBackend


class TestPhase5Broker(unittest.TestCase):
    def test_signed_request_rejects_tampering_replay_and_expiry(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = _standard_config(Path(tmp))
            identity, private_key = generate_instance_identity(config)
            body = {"provider": "google"}
            request = sign_broker_request(
                identity=identity,
                private_key=private_key,
                method="POST",
                path="/oauth/start",
                body=body,
            )
            cache = ReplayCache()
            verify_broker_request(
                request,
                public_key=identity.public_key,
                body=body,
                replay_cache=cache,
            )
            with self.assertRaises(BrokerProtocolError):
                verify_broker_request(
                    request,
                    public_key=identity.public_key,
                    body=body,
                    replay_cache=cache,
                )
            with self.assertRaises(BrokerProtocolError):
                verify_broker_request(
                    request,
                    public_key=identity.public_key,
                    body={"provider": "slack"},
                )

    def test_mock_broker_conformance_is_network_free(self):
        report = run_mock_broker_conformance()

        self.assertTrue(report.passed)
        self.assertFalse(report.network_used)
        names = {check["name"] for check in report.checks}
        self.assertIn("replay_rejected", names)
        self.assertIn("tampered_body_rejected", names)
        self.assertIn("expired_request_rejected", names)

    def test_oauth_and_token_lifecycle_are_secret_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = _standard_config(Path(tmp))
            store = InMemoryEnterpriseSecretBackend()
            register_broker_instance(config, store, apply=True)

            session = start_oauth_session(config, "slack", apply=True)
            callback = (
                "http://127.0.0.1/oauth/maya/callback"
                f"?state={session.state}&code=mock-code"
            )
            result = complete_oauth_session(
                config,
                store,
                provider="slack",
                session_id=session.session_id,
                callback_url=callback,
                apply=True,
            )
            payload = json.dumps(result.redacted_summary(), sort_keys=True)
            self.assertNotIn("access_token", payload)
            self.assertNotIn("refresh_token", payload)
            self.assertIn("broker-token-envelope", payload)

            status = token_status(config, "slack")
            self.assertEqual(status.state.value, "active")
            self.assertEqual(status.refresh_owner, "broker_assisted")
            refreshed = refresh_token(config, store, "slack", apply=True)
            self.assertEqual(
                refreshed.redacted_summary()["token"]["rotation_count"],
                1,
            )
            revoked = revoke_token(config, store, "slack", apply=True)
            self.assertEqual(
                revoked.redacted_summary()["token"]["state"],
                "revoked",
            )

    def test_oauth_rejects_wrong_state_and_telegram(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = _standard_config(Path(tmp))
            store = InMemoryEnterpriseSecretBackend()
            session = start_oauth_session(config, "google", apply=True)
            with self.assertRaises(BrokerOperationError):
                complete_oauth_session(
                    config,
                    store,
                    provider="google",
                    session_id=session.session_id,
                    callback_url=(
                        "http://127.0.0.1/oauth/maya/callback"
                        "?state=wrong&code=mock-code"
                    ),
                    apply=True,
                )
            with self.assertRaises(BrokerOperationError):
                start_oauth_session(config, "telegram", apply=True)

    def test_broker_modes_and_enterprise_boundaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            disabled = _standard_config(Path(tmp), broker_mode="disabled")
            with self.assertRaises(BrokerOperationError):
                start_oauth_session(disabled, "google", apply=False)

        with tempfile.TemporaryDirectory() as tmp:
            enterprise = _standard_config(Path(tmp), edition="enterprise")
            with self.assertRaises(BrokerOperationError):
                start_oauth_session(enterprise, "google", apply=False)

    def test_model_proxy_readiness_is_status_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = _standard_config(Path(tmp), llm_mode="maya_managed")
            store = InMemoryEnterpriseSecretBackend()
            pending = model_proxy_readiness(config, store)
            self.assertEqual(pending.status.value, "pending")
            register_broker_instance(config, store, apply=True)
            ready = model_proxy_readiness(config, store)
            self.assertEqual(ready.status.value, "ready")
            self.assertTrue(ready.governance_required)


def _standard_config(
    data_dir: Path,
    *,
    edition: str = "standard",
    broker_mode: str = "runtime",
    llm_mode: str = "customer_owned",
):
    data_dir.mkdir(parents=True, exist_ok=True)
    connector_mode = "broker" if broker_mode != "disabled" else "customer_owned"
    return config_from_mapping(
        {
            "schema_version": 2,
            "product": {"edition": edition, "instance_id": "test-instance"},
            "deployment": {
                "class": "desktop",
                "network_policy": "standard",
                "data_dir": str(data_dir),
            },
            "runtime": {
                "hermes_compatibility": ">=0.0",
                "enabled_profiles": ["maya-core", "maya-messaging"],
            },
            "broker": {
                "mode": broker_mode,
                "endpoint": (
                    "https://broker.maya.example"
                    if broker_mode != "disabled"
                    else None
                ),
            },
            "llm": {
                "mode": llm_mode,
                "provider": "openai",
                "model": "gpt-test",
                "credential_ref": (
                    "secret://models/customer"
                    if llm_mode == "customer_owned"
                    else None
                ),
                "endpoint": None,
                "timeout_seconds": 60,
            },
            "integrations": {
                "google": {
                    "enabled": True,
                    "credential_mode": connector_mode,
                    "credential_ref": "secret://integrations/google",
                },
                "slack": {
                    "enabled": True,
                    "credential_mode": connector_mode,
                    "credential_ref": "secret://integrations/slack",
                },
                "telegram": {
                    "enabled": False,
                    "credential_mode": "customer_owned",
                    "credential_ref": "secret://integrations/telegram",
                },
            },
            "memory": {
                "hermes_provider": "local",
                "retriever": "local_vector",
                "registry": "sqlite",
                "governance_enabled": True,
            },
            "governance": {
                "policy_file": str(data_dir / "governance" / "policy.yaml"),
                "audit_enabled": True,
                "default_action": "deny",
                "minimum_memory_trust": 0.7,
            },
            "metabase": {
                "enabled": False,
                "deployment": "customer_managed",
                "endpoint": None,
                "application_database": None,
                "analytics_sources": [],
            },
            "local_api": {
                "bind": "127.0.0.1",
                "port": None,
                "remote_access": False,
            },
        }
    )


if __name__ == "__main__":
    unittest.main()
