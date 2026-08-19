import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from project_maya import (
    LocalAPIRequest,
    SecretRef,
    SecretStoreHealth,
    SecretStoreStatus,
    build_local_product,
    config_from_mapping,
)

from tests.test_phase2_model_config import enterprise_broker_disabled_mapping


class StaticSecretStore:
    def __init__(self):
        self._values = {}

    def read(self, ref):
        return self._values[str(ref)]

    def write(self, ref, value):
        self._values[str(ref)] = value

    def delete(self, ref):
        self._values.pop(str(ref), None)

    def contains(self, ref):
        return str(ref) in self._values

    def health(self):
        return SecretStoreHealth(
            backend="test-static",
            status=SecretStoreStatus.HEALTHY,
            message="test store",
        )


class BrokerDisabledRuntime:
    events = []

    def __init__(self, **kwargs):
        type(self).events.append(("init", kwargs))
        self._memory_provider = None
        self._started = False

    def attach_memory(self, memory_provider):
        type(self).events.append(("attach_memory", type(memory_provider).__name__))
        self._memory_provider = memory_provider

    def load_plugin(self, name, plugin=None):
        type(self).events.append(("load_plugin", name, plugin))

    def start(self, *, agent_name):
        type(self).events.append(("start", agent_name))
        self._started = True

    def run(self, request, **kwargs):
        type(self).events.append(("run", request, kwargs))
        return {"reply": "enterprise broker-disabled response"}

    def health(self):
        from project_maya.agent.contracts import RuntimeHealth, RuntimeHealthState

        state = (
            RuntimeHealthState.HEALTHY
            if self._started
            else RuntimeHealthState.UNHEALTHY
        )
        return RuntimeHealth(state=state, components={"runtime": state})

    def stop(self):
        type(self).events.append(("stop",))
        self._started = False


class TestPhase2BrokerDisabledRuntimePath(unittest.TestCase):
    def test_openai_secret_is_supplied_with_direct_api_endpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            config_data = enterprise_broker_disabled_mapping()
            config_data["deployment"]["data_dir"] = str(data_dir)
            config_data["runtime"]["enabled_profiles"] = ["maya-core"]
            config_data["runtime"]["hermes_factory"] = (
                f"{__name__}:BrokerDisabledRuntime"
            )
            config_data["memory"]["retriever"] = "local_json"
            config_data["governance"]["policy_file"] = str(
                data_dir / "governance" / "missing-policy.json"
            )
            secret_store = StaticSecretStore()
            secret_store.write(
                SecretRef.parse("secret://llm/openai"),
                "test-openai-key",
            )

            BrokerDisabledRuntime.events = []
            with patch(
                "project_maya.bootstrap.build_platform_secret_store",
                return_value=secret_store,
            ):
                product = build_local_product(config_from_mapping(config_data))
            product.start()
            product.stop()

        init_kwargs = BrokerDisabledRuntime.events[0][1]
        self.assertEqual(init_kwargs["provider"], "openai")
        self.assertEqual(init_kwargs["base_url"], "https://api.openai.com/v1")
        self.assertEqual(init_kwargs["api_key"], "test-openai-key")

    def test_enterprise_broker_disabled_runs_memory_audit_and_local_api(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            policy_path = data_dir / "governance" / "policy.json"
            policy_path.parent.mkdir(parents=True)
            policy_path.write_text(
                json.dumps(
                    {
                        "allow": [
                            {
                                "actor_id": "operator",
                                "capability": "runtime.execute",
                                "target": "hermes-agent",
                                "operation": "run",
                            },
                            {
                                "actor_id": "operator",
                                "capability": "model.egress",
                                "target": "model:openai",
                                "operation": "infer",
                            },
                            {
                                "actor_id": "operator",
                                "capability": "memory.write",
                                "target": "*",
                                "operation": "remember",
                            },
                            {
                                "actor_id": "operator",
                                "capability": "memory.read",
                                "target": "*",
                                "operation": "*",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            config_data = enterprise_broker_disabled_mapping()
            config_data["deployment"]["data_dir"] = str(data_dir)
            config_data["runtime"]["enabled_profiles"] = ["maya-core"]
            config_data["runtime"]["hermes_factory"] = (
                f"{__name__}:BrokerDisabledRuntime"
            )
            config_data["runtime"]["hermes_runtime_version"] = "test-hermes"
            config_data["memory"]["retriever"] = "local_json"
            config_data["governance"]["policy_file"] = str(policy_path)
            config = config_from_mapping(config_data)
            secret_store = StaticSecretStore()

            BrokerDisabledRuntime.events = []
            with patch(
                "project_maya.bootstrap.build_platform_secret_store",
                return_value=secret_store,
            ):
                product = build_local_product(config, actor_id="operator")
            product.secret_store.write(
                SecretRef.parse("secret://local-api/token"),
                "local-token",
            )

            try:
                product.start()
                product.memory_provider.synchronize_turn(
                    [
                        {
                            "id": "phase2-runtime-note",
                            "category": "phase2",
                            "text": "broker-disabled Enterprise uses local memory",
                        }
                    ]
                )
                prefetched = product.memory_provider.prefetch(
                    "local memory",
                    category="phase2",
                )
                direct_result = product.run(
                    "prepare broker-disabled briefing",
                    idempotency_key="phase2-turn",
                    data_classification="confidential",
                )
                health_response = product.local_api.handle(
                    LocalAPIRequest(
                        method="GET",
                        path="/v1/health",
                        headers={"Authorization": "Bearer local-token"},
                    )
                )
                run_response = product.local_api.handle(
                    LocalAPIRequest(
                        method="POST",
                        path="/v1/run",
                        headers={"Authorization": "Bearer local-token"},
                        body=json.dumps(
                            {
                                "input": "local api broker-disabled run",
                                "idempotency_key": "phase2-api-turn",
                                "data_classification": "restricted",
                            }
                        ).encode("utf-8"),
                    )
                )
            finally:
                product.stop()

            audit_path = data_dir / "governance" / "audit" / "runtime.jsonl"
            audit_records = [
                json.loads(line)
                for line in audit_path.read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual(config.product.edition.value, "enterprise")
        self.assertEqual(config.broker.mode.value, "disabled")
        self.assertIsNone(config.broker.endpoint)
        self.assertEqual(direct_result["reply"], "enterprise broker-disabled response")
        self.assertEqual(prefetched[0]["id"], "phase2-runtime-note")
        self.assertEqual(health_response.status_code, 200)
        self.assertEqual(health_response.body["runtime"], "healthy")
        self.assertEqual(run_response.status_code, 200)
        self.assertEqual(
            run_response.body["result"]["reply"],
            "enterprise broker-disabled response",
        )

        init_event = BrokerDisabledRuntime.events[0]
        self.assertEqual(init_event[0], "init")
        self.assertEqual(init_event[1]["model"], "gpt-test")
        self.assertEqual(init_event[1]["provider"], "openai")
        self.assertNotIn("broker", init_event[1])
        self.assertNotIn("credential", init_event[1])
        self.assertIn(("attach_memory", "HermesMemoryProvider"), BrokerDisabledRuntime.events)
        self.assertIn(("stop",), BrokerDisabledRuntime.events)

        capabilities = [record["capability"] for record in audit_records]
        self.assertIn("memory.write", capabilities)
        self.assertIn("memory.read", capabilities)
        self.assertEqual(capabilities.count("runtime.execute"), 2)
        self.assertEqual(capabilities.count("model.egress"), 2)
        for record in audit_records:
            serialized = json.dumps(record, sort_keys=True)
            self.assertNotIn("secret://", serialized)
            self.assertNotIn("local-token", serialized)
            self.assertNotIn("https://broker.example", serialized)


if __name__ == "__main__":
    unittest.main()
