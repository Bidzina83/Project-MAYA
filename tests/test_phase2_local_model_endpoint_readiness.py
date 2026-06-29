import tempfile
import unittest
from pathlib import Path

from project_maya import (
    ActionRequest,
    AuthorizationResult,
    ConfigError,
    GovernanceDecision,
    LocalModelEndpointStatus,
    ModelConfigStatus,
    build_local_product,
    config_from_mapping,
    load_config_profile,
    validate_local_model_endpoint,
    validate_model_config,
)

from tests.test_phase2_model_config import enterprise_broker_disabled_mapping


class AllowGateway:
    def __init__(self):
        self.requests = []

    def authorize(self, request: ActionRequest):
        self.requests.append(request)
        return AuthorizationResult(
            decision=GovernanceDecision.ALLOW,
            reason_code="test.allow",
        )


class TestPhase2LocalModelEndpointReadiness(unittest.TestCase):
    def test_common_openai_compatible_local_endpoint_families_are_ready(self):
        cases = (
            ("http://127.0.0.1:11434/v1", "ollama"),
            ("http://localhost:1234/v1", "lm_studio"),
            ("http://127.0.0.1:8000/v1", "vllm"),
        )
        for endpoint, family in cases:
            with self.subTest(endpoint=endpoint):
                config = self._local_config(endpoint=endpoint)

                readiness = validate_local_model_endpoint(config)
                validation = validate_model_config(config)

                self.assertEqual(readiness.status, LocalModelEndpointStatus.READY)
                self.assertTrue(readiness.ready)
                self.assertEqual(readiness.endpoint_family, family)
                self.assertEqual(readiness.endpoint_state, "local_configured")
                self.assertTrue(readiness.openai_compatible)
                self.assertFalse(readiness.network_used)
                self.assertEqual(validation.status, ModelConfigStatus.VALID)
                self.assertNotIn(endpoint, readiness.redacted_summary())

    def test_customer_hosted_openai_compatible_endpoint_is_config_ready(self):
        config = self._local_config(endpoint="https://models.customer.example/v1")

        readiness = validate_local_model_endpoint(config)

        self.assertEqual(readiness.status, LocalModelEndpointStatus.READY)
        self.assertEqual(
            readiness.endpoint_family,
            "openai_compatible_customer_hosted",
        )
        self.assertEqual(readiness.endpoint_state, "customer_hosted_configured")
        self.assertFalse(readiness.network_used)

    def test_local_mode_requires_openai_compatible_provider(self):
        config_data = enterprise_broker_disabled_mapping()
        config_data["llm"] = {
            "mode": "local",
            "provider": "openai",
            "model": "llama-local",
            "endpoint": "http://127.0.0.1:11434/v1",
        }
        config = config_from_mapping(config_data)

        readiness = validate_local_model_endpoint(config)
        validation = validate_model_config(config)

        self.assertEqual(readiness.status, LocalModelEndpointStatus.INVALID)
        self.assertEqual(validation.status, ModelConfigStatus.INVALID)
        self.assertIn("provider=openai-compatible", readiness.message)
        with self.assertRaisesRegex(ConfigError, "provider=openai-compatible"):
            build_local_product(config)

    def test_non_local_model_reports_not_configured(self):
        config = config_from_mapping(enterprise_broker_disabled_mapping())

        readiness = validate_local_model_endpoint(config)

        self.assertEqual(
            readiness.status,
            LocalModelEndpointStatus.NOT_CONFIGURED,
        )
        self.assertFalse(readiness.ready)
        self.assertFalse(readiness.network_used)

    def test_local_endpoint_profile_builds_hermes_base_url_without_model_egress(self):
        events = []

        class FakeLocalRuntime:
            def __init__(self, **kwargs):
                events.append(("init", kwargs))

            def attach_memory(self, memory_provider):
                events.append(("memory", type(memory_provider).__name__))

            def start(self, *, agent_name):
                events.append(("start", agent_name))

            def run(self, request, **kwargs):
                events.append(("run", request, kwargs))
                return "local model response"

            def stop(self):
                events.append(("stop",))

        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-local-model"
            config = load_config_profile(
                Path("docs/config/enterprise-local-model-broker-disabled.json"),
                data_dir=data_dir,
                instance_id="local-model-runtime",
            )
            config_data = self._as_mapping_with_factory(
                config,
                f"{__name__}:FakeLocalRuntime",
            )
            globals()["FakeLocalRuntime"] = FakeLocalRuntime
            try:
                gateway = AllowGateway()
                product = build_local_product(
                    config_from_mapping(config_data),
                    gateway=gateway,
                )
                product.start()
                result = product.run("use local model")
                product.stop()
            finally:
                globals().pop("FakeLocalRuntime", None)

        self.assertEqual(result, "local model response")
        init_kwargs = events[0][1]
        self.assertEqual(init_kwargs["provider"], "openai-compatible")
        self.assertEqual(init_kwargs["model"], "local-model")
        self.assertEqual(init_kwargs["base_url"], "http://127.0.0.1:11434/v1")
        self.assertEqual(init_kwargs["request_overrides"]["timeout_seconds"], 120)
        capabilities = [
            request.capability
            for request in gateway.requests
        ]
        self.assertIn("runtime.execute", capabilities)
        self.assertNotIn("model.egress", capabilities)

    def _local_config(self, *, endpoint: str):
        config_data = enterprise_broker_disabled_mapping()
        config_data["llm"] = {
            "mode": "local",
            "provider": "openai-compatible",
            "model": "llama-local",
            "endpoint": endpoint,
        }
        return config_from_mapping(config_data)

    def _as_mapping_with_factory(self, config, factory_path):
        from project_maya import config_to_mapping

        data = config_to_mapping(config)
        data["runtime"]["hermes_factory"] = factory_path
        data["governance"]["policy_file"] = str(
            config.deployment.data_dir / "governance" / "missing-policy.json"
        )
        return data


if __name__ == "__main__":
    unittest.main()
