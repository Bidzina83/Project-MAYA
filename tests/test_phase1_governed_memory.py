import json
import tempfile
import unittest
from pathlib import Path

from project_maya import (
    ActionDeniedError,
    ActionRequest,
    AuthorizationResult,
    GovernanceDecision,
    GovernedMemoryRetriever,
    LocalJsonlAuditSink,
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


class TestPhase1GovernedMemory(unittest.TestCase):
    def test_remember_is_authorized_and_audited_without_memory_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            audit_path = Path(tmp) / "audit.jsonl"
            gateway = Gateway(GovernanceDecision.ALLOW)
            memory = GovernedMemoryRetriever(
                MemoryRetriever(LocalJsonRetriever(Path(tmp) / "records.json")),
                gateway,
                actor_id="operator",
                audit_sink=LocalJsonlAuditSink(audit_path),
            )

            memory.remember(
                {
                    "id": "note-1",
                    "text": "sensitive memory body",
                    "category": "general",
                }
            )
            audit_text = audit_path.read_text(encoding="utf-8")
            audit_record = json.loads(audit_text)

        self.assertEqual(gateway.requests[0].capability, "memory.write")
        self.assertEqual(gateway.requests[0].operation, "remember")
        self.assertEqual(audit_record["event_type"], "authorization.memory")
        self.assertEqual(audit_record["decision"], "allow")
        self.assertEqual(audit_record["metadata"]["memory_id"], "note-1")
        self.assertNotIn("sensitive memory body", audit_text)

    def test_recall_is_authorized(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = MemoryRetriever(LocalJsonRetriever(Path(tmp) / "records.json"))
            base.remember({"id": "note-1", "text": "hello"})
            gateway = Gateway(GovernanceDecision.ALLOW)
            memory = GovernedMemoryRetriever(
                base,
                gateway,
                actor_id="operator",
                audit_sink=LocalJsonlAuditSink(Path(tmp) / "audit.jsonl"),
            )

            record = memory.recall("note-1")

        self.assertEqual(record["text"], "hello")
        self.assertEqual(gateway.requests[0].capability, "memory.read")
        self.assertEqual(gateway.requests[0].operation, "recall")

    def test_denied_memory_write_does_not_persist_document(self):
        with tempfile.TemporaryDirectory() as tmp:
            store_path = Path(tmp) / "records.json"
            memory = GovernedMemoryRetriever(
                MemoryRetriever(LocalJsonRetriever(store_path)),
                Gateway(GovernanceDecision.DENY),
                actor_id="operator",
                audit_sink=LocalJsonlAuditSink(Path(tmp) / "audit.jsonl"),
            )

            with self.assertRaises(ActionDeniedError):
                memory.remember({"id": "note-1", "text": "do not persist"})

            reopened = LocalJsonRetriever(store_path)

        self.assertIsNone(reopened.get("note-1"))

    def test_assembled_product_uses_governed_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_data = valid_config_mapping()
            config_data["deployment"]["data_dir"] = str(Path(tmp) / "maya-data")
            config_data["runtime"]["enabled_profiles"] = ["maya-core"]
            config_data["memory"]["retriever"] = "local_json"
            gateway = Gateway(GovernanceDecision.ALLOW)
            product = build_local_product(
                config_from_mapping(config_data),
                gateway=gateway,
                actor_id="operator",
            )

            product.memory.remember({"id": "note-1", "text": "hello"})

        self.assertEqual(gateway.requests[0].capability, "memory.write")
        self.assertEqual(product.memory.recall("note-1")["text"], "hello")


if __name__ == "__main__":
    unittest.main()
