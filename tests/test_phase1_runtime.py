import unittest

from project_maya import (
    ActionRequest,
    AuthorizationResult,
    ComponentProfile,
    DoctorStatus,
    GovernanceDecision,
    GovernedAgentRuntime,
    create_agent,
    run_doctor,
)
from project_maya.adapters import HermesRuntimeAdapter
from project_maya.agent.contracts import RuntimeHealthState
from tests.test_phase0_contracts import valid_config_mapping
from project_maya import config_from_mapping


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
        return {"ok": True, "request": request}

    def stop(self):
        self.events.append(("stop",))


class AllowGateway:
    def __init__(self):
        self.requests = []

    def authorize(self, request: ActionRequest):
        self.requests.append(request)
        return AuthorizationResult(
            decision=GovernanceDecision.ALLOW,
            reason_code="test.allow",
        )


class TestPhase1Runtime(unittest.TestCase):
    def test_hermes_adapter_reports_missing_runtime_as_unhealthy(self):
        adapter = HermesRuntimeAdapter(factory_path="missing.hermes:factory")

        compatibility = adapter.compatibility()
        health = adapter.health()

        self.assertFalse(compatibility.compatible)
        self.assertEqual(health.state, RuntimeHealthState.UNHEALTHY)
        self.assertIn("Hermes runtime factory unavailable", compatibility.reason)

    def test_hermes_adapter_preserves_startup_order(self):
        runtime = RuntimeDouble()
        adapter = HermesRuntimeAdapter(factory=lambda **kwargs: runtime)
        memory = object()
        plugin = object()

        adapter.attach_memory(memory)
        adapter.load_plugin("maya.identity", plugin)
        adapter.start(agent_name="maya")
        result = adapter.run("hello")
        adapter.stop()

        self.assertEqual(result["ok"], True)
        self.assertEqual(
            runtime.events,
            [
                ("memory", memory),
                ("plugin", "maya.identity", plugin),
                ("start", "maya"),
                ("run", "hello", {}),
                ("stop",),
            ],
        )

    def test_public_agent_executes_through_governed_hermes_adapter(self):
        runtime = RuntimeDouble()
        gateway = AllowGateway()
        adapter = HermesRuntimeAdapter(factory=lambda **kwargs: runtime)
        governed = GovernedAgentRuntime(adapter, gateway, actor_id="operator")
        agent = create_agent("maya", runtime=governed)

        agent.start()
        result = agent.run("prepare briefing", idempotency_key="turn-1")
        agent.stop()

        self.assertEqual(result["request"], "prepare briefing")
        self.assertEqual(gateway.requests[0].capability, "runtime.execute")
        self.assertEqual(gateway.requests[0].target, "hermes-agent")

    def test_doctor_reports_missing_hermes_as_failure(self):
        config_data = valid_config_mapping()
        config_data["runtime"]["enabled_profiles"] = [ComponentProfile.CORE.value]
        config = config_from_mapping(config_data)
        adapter = HermesRuntimeAdapter(factory_path="missing.hermes:factory")

        report = run_doctor(config, adapter)

        self.assertFalse(report.healthy)
        statuses = {check.name: check.status for check in report.checks}
        self.assertEqual(statuses["config"], DoctorStatus.PASS)
        self.assertEqual(statuses["hermes.compatibility"], DoctorStatus.FAIL)
        self.assertEqual(statuses["hermes.health"], DoctorStatus.FAIL)


if __name__ == "__main__":
    unittest.main()
