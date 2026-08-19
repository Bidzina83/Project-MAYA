import tempfile
import json
import hashlib
import unittest
from pathlib import Path
from unittest.mock import patch

from project_maya import (
    ActionRequest,
    AuthorizationResult,
    DoctorStatus,
    GovernanceDecision,
    GovernedMemoryRetriever,
    LocalSQLiteVectorRetriever,
    MayaHermesMemoryPlugin,
    MemoryRetriever,
    build_local_product,
    config_from_mapping,
    inspect_local_vector_store,
    run_doctor,
)
from project_maya.memory import (
    BusinessMemoryService,
    EmbeddingModelError,
    PinnedOnnxEmbeddingModel,
)
from project_maya.adapters import HermesRuntimeAdapter
from project_maya.cli import main as maya_cli
from tests.test_phase0_contracts import valid_config_mapping


class AllowGateway:
    def __init__(self):
        self.requests = []

    def authorize(self, request: ActionRequest):
        self.requests.append(request)
        return AuthorizationResult(
            decision=GovernanceDecision.ALLOW,
            reason_code="test.allow",
        )


class FakeEmbeddingModel:
    model_id = "test/local-semantic"
    dimension = 2

    def embed(self, texts):
        vectors = []
        for text in texts:
            lowered = text.lower()
            vectors.append(
                [1.0, 0.0]
                if any(word in lowered for word in ("invoice", "billing", "month"))
                else [0.0, 1.0]
            )
        return vectors


class TestPhase1SQLiteVectorMemory(unittest.TestCase):
    def test_business_memory_cli_ingest_search_and_rebuild_readiness(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            policy_path = data_dir / "governance" / "policies" / "default.json"
            policy_path.parent.mkdir(parents=True)
            policy_path.write_text(
                json.dumps(
                    {
                        "allow": [
                            {"actor_id": "local-user", "capability": "memory.read"},
                            {"actor_id": "local-user", "capability": "memory.ingest"},
                            {"actor_id": "local-user", "capability": "memory.write"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            config_data = valid_config_mapping()
            config_data["deployment"]["data_dir"] = str(data_dir)
            config_data["governance"]["policy_file"] = str(policy_path)
            config_path = data_dir / "config" / "maya.json"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(json.dumps(config_data), encoding="utf-8")
            source = data_dir / "documents" / "operations.md"
            source.parent.mkdir(parents=True)
            source.write_text("Quarterly operations review", encoding="utf-8")

            with patch("builtins.print") as printed:
                ingest_exit = maya_cli(
                    ["memory", "ingest", "--config", str(config_path), "--source", str(source)]
                )
                search_exit = maya_cli(
                    ["memory", "search", "--config", str(config_path), "--query", "quarterly", "--include-content"]
                )
                rebuild_exit = maya_cli(
                    ["memory", "rebuild-embeddings", "--config", str(config_path)]
                )
                outputs = [str(call.args[0]) for call in printed.call_args_list]

        self.assertEqual(ingest_exit, 0)
        self.assertEqual(search_exit, 0)
        self.assertEqual(rebuild_exit, 1)
        self.assertTrue(any("Quarterly operations review" in item for item in outputs))
        self.assertTrue(any("business_memory_operation_failed" in item for item in outputs))

    def test_hermes_plugin_uses_governed_sqlite_for_business_memory_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            policy_path = data_dir / "governance" / "policies" / "default.json"
            policy_path.parent.mkdir(parents=True)
            policy_path.write_text(
                json.dumps(
                    {
                        "default_action": "deny",
                        "allow": [
                            {
                                "actor_id": "local-user",
                                "capability": "memory.read",
                                "target": "*",
                                "operation": "*",
                            },
                            {
                                "actor_id": "local-user",
                                "capability": "memory.ingest",
                                "target": "*",
                                "operation": "*",
                            },
                            {
                                "actor_id": "local-user",
                                "capability": "memory.write",
                                "target": "*",
                                "operation": "*",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            config_data = valid_config_mapping()
            config_data["deployment"]["data_dir"] = str(data_dir)
            config_data["governance"]["policy_file"] = str(policy_path)
            config_path = data_dir / "config" / "maya.json"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(json.dumps(config_data), encoding="utf-8")
            plugin = MayaHermesMemoryPlugin(config_path)
            document = data_dir / "documents" / "northwind.txt"
            document.parent.mkdir(parents=True)
            document.write_text(
                "Northwind requested monthly PDF reports.", encoding="utf-8"
            )

            self.assertTrue(plugin.is_available())
            plugin.initialize("session-1", platform="project_maya")
            ingest = json.loads(
                plugin.handle_tool_call(
                    "maya_business_memory_ingest", {"path": str(document)}
                )
            )
            plugin.sync_turn(
                "What did Northwind request?",
                "A conversation that belongs to Hermes session storage.",
            )
            context = plugin.prefetch("Northwind monthly")
            tools = {item["name"] for item in plugin.get_tool_schemas()}
            plugin.shutdown()

            status = inspect_local_vector_store(
                data_dir / "memory" / "memory.sqlite3"
            )
            audit = (
                data_dir / "governance" / "audit" / "runtime.jsonl"
            ).read_text(encoding="utf-8")

        self.assertEqual(ingest["chunks"], 1)
        self.assertIn("Northwind requested monthly PDF reports", context)
        self.assertEqual(
            tools,
            {
                "maya_business_memory_search",
                "maya_business_memory_ingest",
                "maya_business_memory_rebuild_embeddings",
            },
        )
        self.assertEqual(status["records"], 1)
        self.assertIn('"capability": "memory.write"', audit)
        self.assertIn('"capability": "memory.read"', audit)

    def test_business_memory_hybrid_search_and_embedding_rebuild(self):
        with tempfile.TemporaryDirectory() as tmp:
            retriever = LocalSQLiteVectorRetriever(Path(tmp) / "memory.sqlite3")
            gateway = AllowGateway()
            governed = GovernedMemoryRetriever(
                MemoryRetriever(retriever),
                gateway,
                actor_id="operator",
            )
            service = BusinessMemoryService(
                retriever, governed, FakeEmbeddingModel()
            )
            service.ingest_text(
                "The customer prefers invoices at the end of every month.",
                source_path="customers/northwind.md",
            )

            results = service.search("What is the billing schedule?")
            rebuilt = service.rebuild_embeddings()
            retriever.close()

        self.assertEqual(len(results), 1)
        self.assertIn("invoices", results[0]["content"])
        self.assertEqual(rebuilt["records"], 1)
        self.assertTrue(
            all(
                request.capability in {"memory.read", "memory.write"}
                for request in gateway.requests
            )
        )

    def test_pinned_embedding_manifest_rejects_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            files = {
                "model.onnx": b"model",
                "tokenizer.json": b"{}",
            }
            for name, content in files.items():
                (root / name).write_bytes(content)
            (root / "embedding-model-manifest.json").write_text(
                json.dumps(
                    {
                        "model_id": "sentence-transformers/all-MiniLM-L6-v2",
                        "revision": "pinned-test-revision",
                        "license": "apache-2.0",
                        "source": "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2",
                        "dimension": 384,
                        "max_length": 256,
                        "files": {
                            name: hashlib.sha256(content).hexdigest()
                            for name, content in files.items()
                        },
                    }
                ),
                encoding="utf-8",
            )
            model = PinnedOnnxEmbeddingModel(root)
            self.assertEqual(model.dimension, 384)
            (root / "model.onnx").write_bytes(b"tampered")
            with self.assertRaisesRegex(EmbeddingModelError, "checksum"):
                PinnedOnnxEmbeddingModel(root)

    def test_embedding_rebuild_atomically_allows_a_new_dimension(self):
        with tempfile.TemporaryDirectory() as tmp:
            retriever = LocalSQLiteVectorRetriever(Path(tmp) / "memory.sqlite3")
            retriever.bulk_upsert(
                [
                    {"id": "one", "content": "one", "embedding": [1.0, 0.0]},
                    {"id": "two", "content": "two", "embedding": [0.0, 1.0]},
                ]
            )
            retriever.replace_embeddings(
                {"one": [1.0, 0.0, 0.0], "two": [0.0, 1.0, 0.0]}
            )

            results = retriever.query_vector([1.0, 0.0, 0.0])
            stats = retriever.stats()
            retriever.close()

        self.assertEqual(results[0]["id"], "one")
        self.assertEqual(stats["vectors"], 2)

    def test_embedding_rebuild_rejects_partial_replacement_without_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            retriever = LocalSQLiteVectorRetriever(Path(tmp) / "memory.sqlite3")
            retriever.bulk_upsert(
                [
                    {"id": "one", "content": "one", "embedding": [1.0, 0.0]},
                    {"id": "two", "content": "two", "embedding": [0.0, 1.0]},
                ]
            )
            with self.assertRaisesRegex(ValueError, "every memory record"):
                retriever.replace_embeddings({"one": [1.0, 0.0, 0.0]})

            results = retriever.query_vector([1.0, 0.0])
            retriever.close()

        self.assertEqual([item["id"] for item in results], ["one", "two"])

    def test_records_persist_and_upsert_without_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "memory.sqlite3"
            retriever = LocalSQLiteVectorRetriever(path)
            retriever.upsert(
                {
                    "id": "customer-1",
                    "content": "Northwind prefers quarterly PDF reports",
                    "category": "customer",
                    "trust_score": 0.9,
                    "source_path": "customers/northwind.md",
                    "source_hash": "sha256:one",
                    "extractor_version": "maya-test-v1",
                    "embedding": [1.0, 0.0],
                }
            )
            retriever.upsert(
                {
                    "id": "customer-1",
                    "content": "Northwind prefers monthly PDF reports",
                    "category": "customer",
                    "trust_score": 0.95,
                    "source_path": "customers/northwind.md",
                    "source_hash": "sha256:two",
                    "extractor_version": "maya-test-v1",
                    "embedding": [1.0, 0.0],
                }
            )
            retriever.close()

            reopened = LocalSQLiteVectorRetriever(path)
            record = reopened.get("customer-1")
            stats = reopened.stats()
            reopened.close()

        self.assertEqual(record["content"], "Northwind prefers monthly PDF reports")
        self.assertEqual(stats["records"], 1)
        self.assertEqual(stats["vectors"], 1)
        self.assertEqual(stats["journal_mode"], "wal")

    def test_full_text_category_filter_and_vector_ranking(self):
        with tempfile.TemporaryDirectory() as tmp:
            retriever = LocalSQLiteVectorRetriever(Path(tmp) / "memory.sqlite3")
            retriever.bulk_upsert(
                [
                    {
                        "id": "customer-1",
                        "content": "Northwind quarterly finance report",
                        "category": "customer",
                        "embedding": [1.0, 0.0],
                    },
                    {
                        "id": "policy-1",
                        "content": "Northwind retention policy",
                        "category": "policy",
                        "embedding": [0.0, 1.0],
                    },
                ]
            )

            search = retriever.search("Northwind", category="customer")
            vectors = retriever.query_vector([0.9, 0.1], top_k=2)
            retriever.close()

        self.assertEqual([item["id"] for item in search], ["customer-1"])
        self.assertEqual([item["id"] for item in vectors], ["customer-1", "policy-1"])
        self.assertGreater(vectors[0]["similarity"], vectors[1]["similarity"])

    def test_rejects_invalid_vectors_and_trust_scores(self):
        with tempfile.TemporaryDirectory() as tmp:
            retriever = LocalSQLiteVectorRetriever(Path(tmp) / "memory.sqlite3")
            with self.assertRaisesRegex(ValueError, "finite"):
                retriever.upsert({"id": "bad-vector", "embedding": [float("nan")]})
            with self.assertRaisesRegex(ValueError, "trust_score"):
                retriever.upsert({"id": "bad-trust", "trust_score": 2.0})
            retriever.upsert({"id": "dimension-2", "embedding": [1.0, 0.0]})
            with self.assertRaisesRegex(ValueError, "dimension must be 2"):
                retriever.upsert(
                    {"id": "dimension-3", "embedding": [1.0, 0.0, 0.0]}
                )
            with self.assertRaisesRegex(ValueError, "dimension must be 2"):
                retriever.query_vector([1.0, 0.0, 0.0])
            retriever.close()

    def test_product_routes_sqlite_memory_through_governance(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            config_data = valid_config_mapping()
            config_data["deployment"]["data_dir"] = str(data_dir)
            config_data["runtime"]["enabled_profiles"] = ["maya-core"]
            config_data["governance"]["policy_file"] = str(
                data_dir / "governance" / "missing-policy.json"
            )
            gateway = AllowGateway()
            product = build_local_product(
                config_from_mapping(config_data),
                gateway=gateway,
                actor_id="operator",
            )

            product.memory.remember(
                {"id": "briefing-1", "content": "Approved SMB briefing"}
            )
            result = product.memory.search("briefing")
            product.stop()

            status = inspect_local_vector_store(
                data_dir / "memory" / "memory.sqlite3"
            )

        self.assertEqual(result[0]["id"], "briefing-1")
        self.assertEqual(
            [request.capability for request in gateway.requests],
            ["memory.write", "memory.read"],
        )
        self.assertEqual(status["status"], "ready")
        self.assertEqual(status["records"], 1)

    def test_doctor_reports_sqlite_integrity_and_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            path = data_dir / "memory" / "memory.sqlite3"
            retriever = LocalSQLiteVectorRetriever(path)
            retriever.upsert({"id": "one", "content": "one"})
            retriever.close()
            config_data = valid_config_mapping()
            config_data["deployment"]["data_dir"] = str(data_dir)
            config_data["runtime"]["enabled_profiles"] = ["maya-core"]
            config = config_from_mapping(config_data)

            report = run_doctor(
                config,
                HermesRuntimeAdapter(factory_path="missing.hermes:factory"),
            )

        memory_check = {check.name: check for check in report.checks}["memory.store"]
        self.assertEqual(memory_check.status, DoctorStatus.PASS)
        self.assertIn("records=1", memory_check.message)
        self.assertIn("schema=1", memory_check.message)


if __name__ == "__main__":
    unittest.main()
