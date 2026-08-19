"""Hermes memory-plugin implementation backed by governed Maya memory."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from ..audit import LocalJsonlAuditSink
from ..config import config_from_mapping
from ..governance import load_policy_gateway
from .business import BusinessMemoryService
from .embedding import EmbeddingModelError, PinnedOnnxEmbeddingModel
from .provider import HermesMemoryProvider
from .retriever import GovernedMemoryRetriever, MemoryRetriever
from .sqlite_vector import LocalSQLiteVectorRetriever


class MayaHermesMemoryPlugin:
    """Hermes-compatible provider using Maya's authoritative local store."""

    name = "maya"

    def __init__(self, config_path: Path | None = None) -> None:
        self._config_path = config_path
        self._provider: HermesMemoryProvider | None = None
        self._retriever: LocalSQLiteVectorRetriever | None = None
        self._session_id = ""
        self._business: BusinessMemoryService | None = None
        self._config = None

    def is_available(self) -> bool:
        try:
            config = self._load_config()
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return False
        return (
            config.memory.hermes_provider == "local"
            and config.memory.retriever == "local_vector"
            and config.memory.registry == "sqlite"
            and config.memory.governance_enabled
            and config.governance.policy_file.is_file()
        )

    def initialize(self, session_id: str, **kwargs: Any) -> None:
        if not session_id:
            raise ValueError("session_id is required")
        self.shutdown()
        config = self._load_config()
        if not self.is_available():
            raise RuntimeError("Maya governed local_vector memory is unavailable")
        retriever = LocalSQLiteVectorRetriever(
            config.deployment.data_dir / "memory" / "memory.sqlite3"
        )
        memory = GovernedMemoryRetriever(
            MemoryRetriever(retriever),
            load_policy_gateway(config.governance.policy_file),
            actor_id="local-user",
            audit_sink=LocalJsonlAuditSink(
                config.deployment.data_dir / "governance" / "audit" / "runtime.jsonl"
            ),
        )
        provider = HermesMemoryProvider(memory)
        provider.begin_session(session_id, metadata=_safe_session_metadata(kwargs))
        embedding_model = None
        model_dir = os.environ.get("MAYA_EMBEDDING_MODEL_DIR")
        if model_dir:
            try:
                embedding_model = PinnedOnnxEmbeddingModel(Path(model_dir))
            except EmbeddingModelError:
                embedding_model = None
        self._retriever = retriever
        self._provider = provider
        self._business = BusinessMemoryService(retriever, memory, embedding_model)
        self._config = config
        self._session_id = session_id

    def system_prompt_block(self) -> str:
        return (
            "Maya governed local memory is authoritative for SMB business and "
            "operational information. Hermes MEMORY.md, USER.md, and sessions "
            "remain the agent's own memory."
        )

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        records = self._require_business().search(query, limit=5)
        if not records:
            return ""
        return json.dumps(records, sort_keys=True, ensure_ascii=True)

    def queue_prefetch(self, query: str, *, session_id: str = "") -> None:
        return None

    def sync_turn(
        self,
        user_content: str,
        assistant_content: str,
        *,
        session_id: str = "",
        messages: list[dict[str, Any]] | None = None,
    ) -> None:
        # Hermes owns conversation/session persistence, MEMORY.md, and USER.md.
        # Maya business memory changes only through explicit governed workflows.
        return None

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "maya_business_memory_search",
                "description": "Search governed SMB operational and business memory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "category": {"type": "string"},
                        "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "maya_business_memory_ingest",
                "description": "Ingest a document from Maya's governed documents folder.",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            },
            {
                "name": "maya_business_memory_rebuild_embeddings",
                "description": "Rebuild local embeddings for governed business memory.",
                "parameters": {"type": "object", "properties": {}},
            },
        ]

    def handle_tool_call(
        self, tool_name: str, args: dict[str, Any], **kwargs: Any
    ) -> str:
        business = self._require_business()
        if tool_name == "maya_business_memory_search":
            result = business.search(
                str(args.get("query", "")),
                category=(str(args["category"]) if args.get("category") else None),
                limit=max(1, min(int(args.get("limit", 5)), 20)),
            )
        elif tool_name == "maya_business_memory_ingest":
            config = self._require_config()
            result = business.ingest_document(
                Path(str(args.get("path", ""))),
                config.deployment.data_dir / "documents",
            )
        elif tool_name == "maya_business_memory_rebuild_embeddings":
            result = business.rebuild_embeddings()
        else:
            raise ValueError("unsupported Maya memory tool")
        return json.dumps(result, sort_keys=True, ensure_ascii=True)

    def shutdown(self) -> None:
        if self._provider is not None:
            self._provider.end_session(self._session_id)
        if self._retriever is not None:
            self._retriever.close()
        self._provider = None
        self._retriever = None
        self._business = None
        self._config = None
        self._session_id = ""

    def _load_config(self):
        path = self._config_path or _default_config_path()
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
        return config_from_mapping(raw)

    def _require_provider(self) -> HermesMemoryProvider:
        if self._provider is None:
            raise RuntimeError("Maya memory provider is not initialized")
        return self._provider

    def _require_business(self) -> BusinessMemoryService:
        if self._business is None:
            raise RuntimeError("Maya business memory is not initialized")
        return self._business

    def _require_config(self):
        if self._config is None:
            raise RuntimeError("Maya business memory configuration is unavailable")
        return self._config


def _default_config_path() -> Path:
    configured = os.environ.get("MAYA_CONFIG")
    if configured:
        return Path(configured)
    data_dir = os.environ.get("MAYA_DATA_DIR")
    if not data_dir:
        raise RuntimeError("MAYA_CONFIG or MAYA_DATA_DIR is required")
    return Path(data_dir) / "config" / "maya.json"


def _safe_session_metadata(values: dict[str, Any]) -> dict[str, str]:
    allowed = ("platform", "agent_context", "agent_identity", "agent_workspace")
    return {key: str(values[key]) for key in allowed if values.get(key) is not None}
