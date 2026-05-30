import os
import shutil
import tempfile
import json

import pytest

from plugins.memory.ingest.registry import MemoryRegistry


def test_registry_add_and_reload():
    tmp = tempfile.mkdtemp(prefix="maya_reg_")
    try:
        reg = MemoryRegistry(tmp)
        entry = {
            "chunk_id": "abc123",
            "embedding_path": os.path.join(tmp, "embeddings", "abc123.json"),
            "source_path": "/tmp/sample.txt",
            "source_hash": "deadbeef",
            "model": "m",
            "extractor_version": "v0.test",
            "embedding_timestamp": "2026-01-01T00:00:00Z",
        }
        # ensure registry file does not exist yet
        assert not os.path.exists(reg.path)
        reg.add_entry(entry)
        # registry file now exists
        assert os.path.exists(reg.path)
        # reload registry by creating a new object
        reg2 = MemoryRegistry(tmp)
        loaded = reg2.get_entry("abc123")
        assert loaded is not None
        assert loaded["chunk_id"] == "abc123"
        assert loaded["model"] == "m"
        # check content on disk
        with open(reg.path, "r", encoding="utf-8") as f:
            d = json.load(f)
        assert "abc123" in d

    finally:
        shutil.rmtree(tmp)


def test_registry_idempotent_update():
    tmp = tempfile.mkdtemp(prefix="maya_reg_")
    try:
        reg = MemoryRegistry(tmp)
        entry = {
            "chunk_id": "dup",
            "embedding_path": os.path.join(tmp, "embeddings", "dup.json"),
            "model": "m1",
            "extractor_version": "v0.1",
            "embedding_timestamp": "2026-01-01T00:00:00Z",
        }
        reg.add_entry(entry)
        e1 = reg.get_entry("dup")
        assert e1["model"] == "m1"
        # update with new model
        entry2 = entry.copy()
        entry2["model"] = "m2"
        entry2["embedding_timestamp"] = "2026-06-01T00:00:00Z"
        reg.add_entry(entry2)
        e2 = reg.get_entry("dup")
        assert e2["model"] == "m2"
        assert e2["embedding_timestamp"] == "2026-06-01T00:00:00Z"
    finally:
        shutil.rmtree(tmp)
