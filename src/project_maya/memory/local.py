"""Small persistent local retriever for the minimal Maya runtime."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


class LocalJsonRetriever:
    """File-backed Retriever implementation using portable JSON.

    This is intentionally simple: records are authoritative JSON documents,
    search is deterministic substring matching, and vector query is explicitly
    unsupported until a vector backend is configured.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._records: dict[str, dict[str, Any]] = {}
        self._load()

    def upsert(self, doc: dict[str, Any]) -> None:
        doc_id = _document_id(doc)
        self._records[doc_id] = dict(doc)
        self._flush()

    def bulk_upsert(self, docs: list[dict[str, Any]]) -> None:
        for doc in docs:
            self._records[_document_id(doc)] = dict(doc)
        self._flush()

    def get(self, id: str) -> dict[str, Any] | None:
        record = self._records.get(id)
        return dict(record) if record is not None else None

    def query_vector(
        self,
        vector: list[float],
        top_k: int = 10,
        metric: str = "cosine",
    ) -> list[dict[str, Any]]:
        return []

    def search(
        self,
        query: str,
        category: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        if limit < 1:
            raise ValueError("limit must be positive")
        needle = query.casefold()
        matches: list[dict[str, Any]] = []
        for record in self._records.values():
            if category is not None and record.get("category") != category:
                continue
            haystack = json.dumps(record, sort_keys=True).casefold()
            if needle in haystack:
                matches.append(dict(record))
            if len(matches) >= limit:
                break
        return matches

    def probe(
        self, entity: str, category: str | None = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        return self.search(entity, category=category, limit=limit)

    def related(
        self, entity: str, category: str | None = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        return self.search(entity, category=category, limit=limit)

    def reason(
        self,
        entities: list[str],
        category: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        seen: set[str] = set()
        results: list[dict[str, Any]] = []
        for entity in entities:
            for record in self.search(entity, category=category, limit=limit):
                doc_id = _document_id(record)
                if doc_id in seen:
                    continue
                seen.add(doc_id)
                results.append(record)
                if len(results) >= limit:
                    return results
        return results

    def contradict(
        self,
        category: str | None = None,
        threshold: float = 0.3,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        return []

    def stats(self) -> dict[str, Any]:
        return {
            "backend": "local_json",
            "path": str(self._path),
            "records": len(self._records),
        }

    def _load(self) -> None:
        if not self._path.exists():
            return
        data = json.loads(self._path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("local retriever store must contain a JSON list")
        self._records = {_document_id(record): dict(record) for record in data}

    def _flush(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{self._path.name}.",
            suffix=".tmp",
            dir=str(self._path.parent),
            text=True,
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(
                    list(self._records.values()),
                    handle,
                    indent=2,
                    sort_keys=True,
                )
                handle.write("\n")
            os.replace(tmp_name, self._path)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)


def _document_id(doc: dict[str, Any]) -> str:
    for key in ("id", "chunk_id", "embedding_id"):
        value = doc.get(key)
        if value:
            return str(value)
    raise ValueError("document requires id, chunk_id, or embedding_id")
