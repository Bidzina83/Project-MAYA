"""Registry writer for persistent memory embeddings (T1.1 registry component).

Provides MemoryRegistry which stores an index at
STORAGE_ROOT/registry/memory_registry.json mapping chunk_id -> metadata.

Writes are atomic via tempfile + os.replace to avoid partial writes.
"""
from __future__ import annotations
import json
import os
import tempfile
import fcntl
from typing import Dict, Any, Optional


class MemoryRegistry:
    def __init__(self, storage_root: str):
        self.storage_root = storage_root
        self.registry_dir = os.path.join(storage_root, "registry")
        os.makedirs(self.registry_dir, exist_ok=True)
        self.path = os.path.join(self.registry_dir, "memory_registry.json")
        self.lock_path = os.path.join(self.registry_dir, ".memory_registry.lock")

    def _load(self) -> Dict[str, Dict[str, Any]]:
        if not os.path.exists(self.path):
            return {}
        with open(self.path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                # treat corrupt file as empty registry
                return {}

    def _save(self, data: Dict[str, Dict[str, Any]]):
        # atomic write
        fd, tmp = tempfile.mkstemp(dir=self.registry_dir, prefix=".tmp_registry_")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except Exception:
                    pass

    def add_entry(self, metadata: Dict[str, Any]) -> None:
        """Add or update a registry entry. Expects metadata to contain 'chunk_id' and 'embedding_path'."""
        if "chunk_id" not in metadata:
            raise ValueError("metadata must include chunk_id")
        if "embedding_path" not in metadata:
            raise ValueError("metadata must include embedding_path")
        cid = metadata["chunk_id"]
        entry = {
            "chunk_id": cid,
            "embedding_path": metadata.get("embedding_path"),
            "source_path": metadata.get("source_path"),
            "source_hash": metadata.get("source_hash"),
            "model": metadata.get("model"),
            "provider": metadata.get("provider"),
            "vector_dim": metadata.get("vector_dim"),
            "extractor_version": metadata.get("extractor_version"),
            "embedding_timestamp": metadata.get("embedding_timestamp"),
        }
        os.makedirs(self.registry_dir, exist_ok=True)
        with open(self.lock_path, "a+") as lockf:
            fcntl.flock(lockf, fcntl.LOCK_EX)
            try:
                data = self._load()
                data[cid] = entry
                self._save(data)
            finally:
                try:
                    fcntl.flock(lockf, fcntl.LOCK_UN)
                except Exception:
                    pass

    def get_entry(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        os.makedirs(self.registry_dir, exist_ok=True)
        with open(self.lock_path, "a+") as lockf:
            fcntl.flock(lockf, fcntl.LOCK_SH)
            try:
                data = self._load()
                return data.get(chunk_id)
            finally:
                try:
                    fcntl.flock(lockf, fcntl.LOCK_UN)
                except Exception:
                    pass

    def list_entries(self) -> Dict[str, Dict[str, Any]]:
        os.makedirs(self.registry_dir, exist_ok=True)
        with open(self.lock_path, "a+") as lockf:
            fcntl.flock(lockf, fcntl.LOCK_SH)
            try:
                return self._load()
            finally:
                try:
                    fcntl.flock(lockf, fcntl.LOCK_UN)
                except Exception:
                    pass

    def exists(self, chunk_id: str) -> bool:
        os.makedirs(self.registry_dir, exist_ok=True)
        with open(self.lock_path, "a+") as lockf:
            fcntl.flock(lockf, fcntl.LOCK_SH)
            try:
                return chunk_id in self._load()
            finally:
                try:
                    fcntl.flock(lockf, fcntl.LOCK_UN)
                except Exception:
                    pass
