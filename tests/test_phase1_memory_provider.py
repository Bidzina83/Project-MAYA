import tempfile
import unittest
from pathlib import Path

from project_maya import (
    ActionDeniedError,
    ActionRequest,
    AuthorizationResult,
    GovernanceDecision,
    GovernedMemoryRetriever,
    HermesMemoryProvider,
    MemoryRetriever,
    build_local_product,
    config_from_mapping,
)
from project_maya.memory import LocalJsonRetriever
from tests.test_phase0_contracts import valid_config_mapping


class Gateway:
    def __init__(self, decision):
        self.decision = decision
        self.requests = []

    def authorize(self, request: ActionRequest):
        self.requests.append(request)
        return AuthorizationResult(
            decision=self.decision,
            reason_code=f"test.{self.decision.value}",
        )


class TestPhase1MemoryProvider(unittest.TestCase):
    def test_prefetch_reads_through_governed_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = MemoryRetriever(LocalJsonRetriever(Path(tmp) / "records.json"))
            base.remember(
                {
                    "id": "note-1",
                    "category": "briefing",
                    "text": "Maya remembers durable context.",
                }
            )
            gateway = Gateway(GovernanceDecision.ALLOW)
            memory = GovernedMemoryRetriever(
                base,
                gateway,
                actor_id="operator",
            )
            provider = HermesMemoryProvider(memory)

            matches = provider.prefetch("durable context", category="briefing")

        self.assertEqual(matches[0]["id"], "note-1")
        self.assertEqual(gateway.requests[0].capability, "memory.read")
        self.assertEqual(gateway.requests[0].operation, "search")

    def test_prefetch_denial_blocks_memory_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory = GovernedMemoryRetriever(
                MemoryRetriever(LocalJsonRetriever(Path(tmp) / "records.json")),
                Gateway(GovernanceDecision.DENY),
                actor_id="operator",
            )
            provider = HermesMemoryProvider(memory)

            with self.assertRaises(ActionDeniedError):
                provider.prefetch("blocked")

    def test_synchronize_turn_writes_through_governed_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            gateway = Gateway(GovernanceDecision.ALLOW)
            retriever = LocalJsonRetriever(Path(tmp) / "records.json")
            memory = GovernedMemoryRetriever(
                MemoryRetriever(retriever),
                gateway,
                actor_id="operator",
            )
            provider = HermesMemoryProvider(memory)

            result = provider.synchronize_turn(
                [{"id": "turn-1", "text": "approved memory"}]
            )

        self.assertEqual(result, {"stored": 1})
        self.assertEqual(retriever.get("turn-1")["text"], "approved memory")
        self.assertEqual(gateway.requests[0].capability, "memory.write")

    def test_local_product_attaches_provider_to_hermes_runtime(self):
        events = []

        class FakeAIAgent:
            def __init__(self, **kwargs):
                events.append(("init", kwargs))

            def attach_memory(self, memory_provider):
                events.append(("memory", type(memory_provider).__name__))

            def chat(self, message):
                events.append(("chat", message))
                return "ok"

        with tempfile.TemporaryDirectory() as tmp:
            module_path = "tests.test_phase1_memory_provider:FakeAIAgent"
            config_data = valid_config_mapping()
            config_data["deployment"]["data_dir"] = str(Path(tmp) / "maya-data")
            config_data["runtime"]["enabled_profiles"] = ["maya-core"]
            config_data["runtime"]["hermes_factory"] = module_path
            config_data["memory"]["retriever"] = "local_json"

            globals()["FakeAIAgent"] = FakeAIAgent
            try:
                product = build_local_product(
                    config_from_mapping(config_data),
                    gateway=Gateway(GovernanceDecision.ALLOW),
                    actor_id="operator",
                )
                product.start()
                product.stop()
            finally:
                globals().pop("FakeAIAgent", None)

        self.assertIsInstance(product.memory_provider, HermesMemoryProvider)
        self.assertIn(("memory", "HermesMemoryProvider"), events)


if __name__ == "__main__":
    unittest.main()
