"""Pinned offline ONNX embedding model for Maya business memory."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Protocol, Sequence, runtime_checkable


class EmbeddingModelError(RuntimeError):
    """Raised when the managed embedding model is absent or invalid."""


@runtime_checkable
class EmbeddingModel(Protocol):
    model_id: str
    dimension: int

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class PinnedOnnxEmbeddingModel:
    """Run a disclosed, hashed sentence-embedding model without network use."""

    def __init__(self, model_dir: Path) -> None:
        self.model_dir = model_dir.resolve()
        manifest_path = self.model_dir / "embedding-model-manifest.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise EmbeddingModelError("embedding model manifest is unavailable") from exc
        self.model_id = str(manifest.get("model_id", ""))
        self.revision = str(manifest.get("revision", ""))
        self.license = str(manifest.get("license", ""))
        self.source = str(manifest.get("source", ""))
        self.dimension = int(manifest.get("dimension", 0))
        self.max_length = int(manifest.get("max_length", 256))
        if (
            not self.model_id
            or not self.revision
            or not self.license
            or not self.source.startswith("https://")
            or self.dimension < 1
        ):
            raise EmbeddingModelError("embedding model is not pinned")
        files = manifest.get("files")
        if not isinstance(files, dict):
            raise EmbeddingModelError("embedding model file manifest is invalid")
        self._model_path = self._verified_file(files, "model.onnx")
        self._tokenizer_path = self._verified_file(files, "tokenizer.json")
        self._session = None
        self._tokenizer = None

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        values = [str(text) for text in texts]
        if not values:
            return []
        self._load_runtime()
        import numpy as np

        encodings = self._tokenizer.encode_batch(values)
        id_rows = [item.ids[: self.max_length] for item in encodings]
        mask_rows = [item.attention_mask[: self.max_length] for item in encodings]
        width = max(len(row) for row in id_rows)
        input_ids = np.asarray(
            [row + [0] * (width - len(row)) for row in id_rows], dtype=np.int64
        )
        attention = np.asarray(
            [row + [0] * (width - len(row)) for row in mask_rows], dtype=np.int64
        )
        available = {item.name for item in self._session.get_inputs()}
        inputs = {"input_ids": input_ids, "attention_mask": attention}
        if "token_type_ids" in available:
            inputs["token_type_ids"] = np.zeros_like(input_ids)
        output = self._session.run(None, inputs)[0]
        mask = attention[..., None].astype(np.float32)
        pooled = (output * mask).sum(axis=1) / np.maximum(mask.sum(axis=1), 1.0)
        vectors = []
        for row in pooled:
            vector = [float(value) for value in row]
            if len(vector) != self.dimension:
                raise EmbeddingModelError("embedding model dimension mismatch")
            norm = math.sqrt(sum(value * value for value in vector))
            vectors.append([value / norm for value in vector] if norm else vector)
        return vectors

    def _load_runtime(self) -> None:
        if self._session is not None:
            return
        try:
            import onnxruntime
            from tokenizers import Tokenizer
        except ImportError as exc:
            raise EmbeddingModelError(
                "onnxruntime and tokenizers are required for local embeddings"
            ) from exc
        self._tokenizer = Tokenizer.from_file(str(self._tokenizer_path))
        self._tokenizer.enable_padding()
        self._tokenizer.enable_truncation(max_length=self.max_length)
        self._session = onnxruntime.InferenceSession(
            str(self._model_path), providers=["CPUExecutionProvider"]
        )

    def _verified_file(self, files: dict, name: str) -> Path:
        expected = files.get(name)
        path = self.model_dir / name
        if not isinstance(expected, str) or len(expected) != 64 or not path.is_file():
            raise EmbeddingModelError(f"embedding model lacks pinned {name}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise EmbeddingModelError(f"embedding model checksum mismatch: {name}")
        return path


def inspect_embedding_model(model_dir: Path | None) -> dict[str, object]:
    if model_dir is None or not model_dir.is_dir():
        return {"status": "missing"}
    try:
        model = PinnedOnnxEmbeddingModel(model_dir)
    except EmbeddingModelError as exc:
        return {"status": "blocked", "reason": str(exc)}
    return {
        "status": "ready",
        "model_id": model.model_id,
        "revision": model.revision,
        "license": model.license,
        "source": model.source,
        "dimension": model.dimension,
    }
