import unittest

from project_maya import (
    AgentNotRunningError,
    RuntimeCompatibilityError,
    AgentStartError,
    AgentState,
    RuntimeNotConfiguredError,
    create_agent,
)
from project_maya.agent.contracts import (
    RuntimeCompatibility,
    RuntimeHealth,
    RuntimeHealthState,
)


class FakeRuntime:
    def __init__(self, *, fail_plugin=None, compatible=True):
        self.events = []
        self.fail_plugin = fail_plugin
        self.compatible = compatible

    def compatibility(self):
        self.events.append(("compatibility",))
        return RuntimeCompatibility(
            runtime_name="fake-hermes",
            runtime_version="test",
            supported_contract="phase-0",
            compatible=self.compatible,
            reason=None if self.compatible else "unsupported runtime contract",
        )

    def attach_memory(self, memory_provider):
        self.events.append(("memory", memory_provider))

    def load_plugin(self, name, plugin=None):
        self.events.append(("plugin", name, plugin))
        if name == self.fail_plugin:
            raise RuntimeError("plugin initialization failed")

    def start(self, *, agent_name):
        self.events.append(("start", agent_name))

    def run(self, request, **kwargs):
        self.events.append(("run", request, kwargs))
        return {"request": request, "kwargs": kwargs}

    def health(self):
        return RuntimeHealth(
            state=RuntimeHealthState.HEALTHY,
            components={"runtime": RuntimeHealthState.HEALTHY},
        )

    def stop(self):
        self.events.append(("stop",))


class TestAgentPublicAPI(unittest.TestCase):
    def test_runtime_is_required_for_start(self):
        agent = create_agent()

        with self.assertRaises(RuntimeNotConfiguredError):
            agent.start()

        self.assertEqual(agent.state, AgentState.CREATED)

    def test_start_wires_components_before_runtime_and_runs(self):
        runtime = FakeRuntime()
        memory = object()
        plugin = object()
        agent = create_agent("employee", runtime=runtime)
        agent.attach_memory(memory)
        agent.load_plugin("calendar", plugin)

        agent.start()
        result = agent.run("prepare briefing", audience="owner")
        agent.stop()
        agent.stop()

        self.assertEqual(agent.state, AgentState.STOPPED)
        self.assertEqual(
            runtime.events,
            [
                ("compatibility",),
                ("memory", memory),
                ("plugin", "calendar", plugin),
                ("start", "employee"),
                ("run", "prepare briefing", {"audience": "owner"}),
                ("stop",),
            ],
        )
        self.assertIs(agent.plugins["calendar"], plugin)

    def test_plugin_failure_rolls_back_and_is_not_reported_loaded(self):
        runtime = FakeRuntime(fail_plugin="broken")
        agent = create_agent(runtime=runtime)
        agent.load_plugin("broken", object())

        with self.assertRaises(AgentStartError) as raised:
            agent.start()

        self.assertIsInstance(raised.exception.__cause__, RuntimeError)
        self.assertEqual(agent.state, AgentState.FAILED)
        self.assertNotIn("broken", agent.plugins)
        self.assertEqual(runtime.events[-1], ("stop",))

    def test_run_before_start_is_rejected(self):
        agent = create_agent(runtime=FakeRuntime())

        with self.assertRaises(AgentNotRunningError):
            agent.run("too early")

    def test_incompatible_runtime_rolls_back_and_fails_start(self):
        runtime = FakeRuntime(compatible=False)
        agent = create_agent(runtime=runtime)

        with self.assertRaises(AgentStartError) as raised:
            agent.start()

        self.assertIsInstance(raised.exception.__cause__, RuntimeCompatibilityError)
        self.assertEqual(agent.state, AgentState.FAILED)
        self.assertEqual(runtime.events, [("compatibility",), ("stop",)])


if __name__ == "__main__":
    unittest.main()
