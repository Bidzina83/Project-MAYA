import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from project_maya import (
    ActionRequest,
    AuthorizationResult,
    BearerTokenAuthenticator,
    GovernanceDecision,
    GovernedAgentRuntime,
    LocalAPI,
    LocalAPIError,
    LocalAPIRequest,
    SecretRef,
    SecretStoreHealth,
    SecretStoreStatus,
    build_local_api_http_server,
    build_local_product,
    config_from_mapping,
    create_agent,
    run_doctor,
)
from project_maya.adapters import HermesRuntimeAdapter
from project_maya.agent.contracts import RuntimeHealth, RuntimeHealthState
from tests.test_phase0_contracts import valid_config_mapping


class StaticSecretStore:
    def __init__(self, values):
        self._values = values

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


class RuntimeDouble:
    def __init__(self):
        self.events = []

    def attach_memory(self, memory_provider):
        self.events.append(("memory", memory_provider))

    def load_plugin(self, name, plugin=None):
        self.events.append(("plugin", name, plugin))

    def start(self, *, agent_name):
        self.events.append(("start", agent_name))

    def run(self, request, **kwargs):
        self.events.append(("run", request, kwargs))
        return "runtime response"

    def stop(self):
        self.events.append(("stop",))

    def health(self):
        return RuntimeHealth(
            state=RuntimeHealthState.HEALTHY,
            components={"runtime": RuntimeHealthState.HEALTHY},
        )


class AllowGateway:
    def __init__(self):
        self.requests = []

    def authorize(self, request: ActionRequest):
        self.requests.append(request)
        return AuthorizationResult(
            decision=GovernanceDecision.ALLOW,
            reason_code="test.allow",
        )


class TestPhase1LocalAPI(unittest.TestCase):
    def test_health_requires_bearer_auth(self):
        api = self._api()[0]

        response = api.handle(LocalAPIRequest(method="GET", path="/v1/health"))

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.body["error"]["code"], "unauthorized")

    def test_health_reports_runtime_without_secrets(self):
        api, _, _, agent = self._api()
        agent.start()
        try:
            response = api.handle(
                LocalAPIRequest(
                    method="GET",
                    path="/v1/health",
                    headers={"authorization": "Bearer local-token"},
                )
            )
        finally:
            agent.stop()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body["runtime"], "healthy")
        self.assertNotIn("local-token", response.json_bytes().decode("utf-8"))

    def test_run_executes_through_governed_agent(self):
        api, runtime, gateway, agent = self._api()
        agent.start()
        try:
            response = api.handle(
                LocalAPIRequest(
                    method="POST",
                    path="/v1/run",
                    headers={"Authorization": "Bearer local-token"},
                    body=json.dumps(
                        {
                            "input": "prepare briefing",
                            "idempotency_key": "turn-1",
                            "data_classification": "confidential",
                        }
                    ).encode("utf-8"),
                )
            )
        finally:
            agent.stop()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body["result"], "runtime response")
        self.assertEqual(gateway.requests[0].capability, "runtime.execute")
        self.assertEqual(gateway.requests[0].data_classification, "confidential")
        self.assertEqual(runtime.events[-2], ("run", "prepare briefing", {}))

    def test_run_rejects_invalid_data_classification(self):
        api = self._api()[0]

        response = api.handle(
            LocalAPIRequest(
                method="POST",
                path="/v1/run",
                headers={"authorization": "Bearer local-token"},
                body=json.dumps(
                    {"input": "prepare briefing", "data_classification": ""}
                ).encode("utf-8"),
            )
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.body["error"]["code"], "invalid_request")
        self.assertEqual(
            response.body["error"]["message"],
            "data_classification must be a string",
        )

    def test_run_rejects_invalid_json(self):
        api = self._api()[0]

        response = api.handle(
            LocalAPIRequest(
                method="POST",
                path="/v1/run",
                headers={"authorization": "Bearer local-token"},
                body=b"not-json",
            )
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.body["error"]["code"], "invalid_json")

    def test_request_size_limit_is_enforced(self):
        api = self._api(max_body_bytes=2)[0]

        response = api.handle(
            LocalAPIRequest(
                method="POST",
                path="/v1/run",
                headers={"authorization": "Bearer local-token"},
                body=b"{}{}",
            )
        )

        self.assertEqual(response.status_code, 413)

    def test_build_local_product_assembles_locked_local_api(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_data = valid_config_mapping()
            config_data["deployment"]["data_dir"] = str(Path(tmp) / "maya-data")
            config_data["runtime"]["enabled_profiles"] = ["maya-core"]
            config_data["memory"]["retriever"] = "local_json"
            product = build_local_product(config_from_mapping(config_data))

            response = product.local_api.handle(
                LocalAPIRequest(method="GET", path="/v1/health")
            )

        self.assertEqual(response.status_code, 401)

    def test_doctor_reports_local_api_binding(self):
        config = config_from_mapping(valid_config_mapping())
        runtime = HermesRuntimeAdapter(factory_path="missing.hermes:factory")

        report = run_doctor(config, runtime)

        checks = {check.name: check for check in report.checks}
        self.assertIn("local_api.binding", checks)
        self.assertIn("authentication=required", checks["local_api.binding"].message)

    def test_http_server_requires_auth_and_serves_routes_on_loopback(self):
        api, runtime, gateway, agent = self._api()
        agent.start()
        server = build_local_api_http_server(api, bind="127.0.0.1", port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        try:
            with self.assertRaises(urllib.error.HTTPError) as denied:
                urllib.request.urlopen(base_url + "/v1/health", timeout=5)
            self.assertEqual(denied.exception.code, 401)

            request = urllib.request.Request(
                base_url + "/v1/health",
                headers={"Authorization": "Bearer local-token"},
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))

            run_request = urllib.request.Request(
                base_url + "/v1/run",
                data=json.dumps(
                    {
                        "input": "prepare briefing",
                        "idempotency_key": "turn-http",
                        "data_classification": "restricted",
                    }
                ).encode("utf-8"),
                headers={
                    "Authorization": "Bearer local-token",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(run_request, timeout=5) as response:
                run_payload = json.loads(response.read().decode("utf-8"))
        finally:
            server.shutdown()
            server.server_close()
            agent.stop()
            thread.join(timeout=5)

        self.assertEqual(payload["runtime"], "healthy")
        self.assertEqual(run_payload["result"], "runtime response")
        self.assertEqual(gateway.requests[-1].capability, "runtime.execute")
        self.assertEqual(gateway.requests[-1].data_classification, "restricted")
        self.assertEqual(runtime.events[-2], ("run", "prepare briefing", {}))

    def test_http_server_rejects_non_loopback_phase1_binding(self):
        api = self._api()[0]

        with self.assertRaises(LocalAPIError):
            build_local_api_http_server(api, bind="0.0.0.0", port=0)

    def _api(self, max_body_bytes=65536):
        runtime = RuntimeDouble()
        gateway = AllowGateway()
        adapter = HermesRuntimeAdapter(factory=lambda **kwargs: runtime)
        governed = GovernedAgentRuntime(adapter, gateway, actor_id="operator")
        agent = create_agent("maya", runtime=governed)
        store = StaticSecretStore(
            {str(SecretRef.parse("secret://local-api/token")): "local-token"}
        )
        api = LocalAPI(
            agent=agent,
            runtime=governed,
            authenticator=BearerTokenAuthenticator(store),
            max_body_bytes=max_body_bytes,
        )
        return api, runtime, gateway, agent


if __name__ == "__main__":
    unittest.main()
