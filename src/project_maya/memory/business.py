"""Governed SMB business-memory ingestion and hybrid retrieval."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .embedding import EmbeddingModel
from .retriever import GovernedMemoryRetriever
from .sqlite_vector import LocalSQLiteVectorRetriever


class BusinessMemoryService:
    def __init__(
        self,
        retriever: LocalSQLiteVectorRetriever,
        governed: GovernedMemoryRetriever,
        embedding_model: EmbeddingModel | None = None,
    ) -> None:
        self._retriever = retriever
        self._governed = governed
        self._embedding_model = embedding_model

    @property
    def semantic_ready(self) -> bool:
        return self._embedding_model is not None

    def ingest_text(
        self,
        text: str,
        *,
        source_path: str,
        category: str = "business_document",
        max_chars: int = 1200,
    ) -> dict[str, Any]:
        if not text.strip():
            raise ValueError("document text is required")
        source_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        chunks = _chunks(text, max_chars)
        vectors = (
            self._embedding_model.embed(chunks) if self._embedding_model else [None] * len(chunks)
        )
        for index, (chunk, vector) in enumerate(zip(chunks, vectors)):
            record = {
                "id": f"business:{source_hash}:{index}",
                "content": chunk,
                "category": category,
                "trust_score": 0.8,
                "source_path": source_path,
                "source_hash": source_hash,
                "extractor_version": "project-maya.business-memory.v1",
            }
            if vector is not None:
                record["embedding"] = vector
            self._governed.remember(record)
        return {
            "status": "ingested",
            "chunks": len(chunks),
            "embedded": self.semantic_ready,
            "source_hash": source_hash,
        }

    def ingest_document(self, path: Path, documents_root: Path) -> dict[str, Any]:
        source = path.resolve()
        root = documents_root.resolve()
        if source != root and root not in source.parents:
            raise ValueError("document is outside the governed documents root")
        if source.suffix.lower() not in {".txt", ".md", ".csv", ".json"}:
            raise ValueError("business-memory ingestion supports txt, md, csv, and json")
        source_ref = source.relative_to(root).as_posix()
        self._governed.authorize_ingest(source_ref)
        return self.ingest_text(
            source.read_text(encoding="utf-8-sig"),
            source_path=source_ref,
        )

    def search(self, query: str, *, category: str | None = None, limit: int = 10):
        vector = self._embedding_model.embed([query])[0] if self._embedding_model else None
        return self._governed.search_hybrid(
            query, query_vector=vector, category=category, limit=limit
        )

    def rebuild_embeddings(self) -> dict[str, Any]:
        if self._embedding_model is None:
            raise RuntimeError("local embedding model is unavailable")
        documents = self._retriever.documents()
        vectors = self._embedding_model.embed(
            [str(document.get("content") or document.get("text") or "") for document in documents]
        )
        if len(vectors) != len(documents):
            raise RuntimeError("embedding model returned an incomplete rebuild")
        identifiers = [str(document["id"]) for document in documents]
        self._governed.authorize_embedding_rebuild(identifiers)
        self._retriever.replace_embeddings(dict(zip(identifiers, vectors)))
        return {"status": "rebuilt", "records": len(documents)}


def _chunks(text: str, max_chars: int) -> list[str]:
    if max_chars < 100:
        raise ValueError("max_chars must be at least 100")
    paragraphs = [part.strip() for part in text.replace("\r\n", "\n").split("\n\n") if part.strip()]
    result: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                result.append(current)
                current = ""
            result.extend(paragraph[index : index + max_chars] for index in range(0, len(paragraph), max_chars))
        elif not current:
            current = paragraph
        elif len(current) + 2 + len(paragraph) <= max_chars:
            current += "\n\n" + paragraph
        else:
            result.append(current)
            current = paragraph
    if current:
        result.append(current)
    return result
