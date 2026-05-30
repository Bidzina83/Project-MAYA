"""Registry writer for persistent memory embeddings (T1.1 registry component).

Provides MemoryRegistry which stores an index at
STORAGE_ROOT/registry/memory_registry.json mapping chunk_id -> metadata.

Metadata fields stored per entry include:
- chunk_id
- embedding_path
- source_path
- source_hash
- model
- extractor_version
- embedding_timestamp

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
            # if tmp still exists, remove it
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
        # normalize/trim large fields if present
        entry = {
            "chunk_id": cid,
            "embedding_path": metadata.get("embedding_path"),
            "source_path": metadata.get("source_path"),
            "source_hash": metadata.get("source_hash"),
            "model": metadata.get("model"),
            # optional fields added: provider and vector_dim for completeness
            "provider": metadata.get("provider"),
            "vector_dim": metadata.get("vector_dim"),
            "extractor_version": metadata.get("extractor_version"),
            "embedding_timestamp": metadata.get("embedding_timestamp"),
        }
        # Use an advisory file lock to serialize concurrent writers on this registry directory.
        # This prevents lost updates when multiple processes/threads read-modify-write concurrently.
        os.makedirs(self.registry_dir, exist_ok=True)
        with open(self.lock_path, "w") as lockf:
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
        # shared lock for readers
        if not os.path.exists(self.lock_path):
            # no lock file yet; safe to read
            return self._load().get(chunk_id)
        with open(self.lock_path, "r") as lockf:
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
        if not os.path.exists(self.lock_path):
            return self._load()
        with open(self.lock_path, "r") as lockf:
            fcntl.flock(lockf, fcntl.LOCK_SH)
            try:
                return self._load()
            finally:
                try:
                    fcntl.flock(lockf, fcntl.LOCK_UN)
                except Exception:
                    pass

    def exists(self, chunk_id: str) -> bool:
        if not os.path.exists(self.lock_path):
            return chunk_id in self._load()
        with open(self.lock_path, "r") as lockf:
            fcntl.flock(lockf, fcntl.LOCK_SH)
            try:
                return chunk_id in self._load()
            finally:
                try:
                    fcntl.flock(lockf, fcntl.LOCK_UN)
                except Exception:
                    pass
