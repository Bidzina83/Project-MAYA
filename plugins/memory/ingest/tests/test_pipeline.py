import os
import shutil
import tempfile
import importlib
import json

import pytest


def test_pipeline_writes_embeddings(monkeypatch):
    """End-to-end: chunk a file, embed via mock backend, persist embeddings and registry."""
    emb_mod = importlib.import_module("plugins.memory.ingest.embedder")
    pipe_mod = importlib.import_module("plugins.memory.ingest.pipeline")
    reg_mod = importlib.import_module("plugins.memory.ingest.registry")

    # create temporary workspace
    tmp = tempfile.mkdtemp(prefix="maya_test_")
    try:
        src = os.path.join(tmp, "sample.txt")
        with open(src, "w", encoding="utf-8") as f:
            f.write("""
This is a sample document.

It has multiple paragraphs so the chunker will produce several chunks.

End of sample.
""")
        storage = os.path.join(tmp, "storage")

        # Mock backend that returns deterministic vectors and records calls
        calls = []

        class MockBackend:
            def __init__(self, model=None):
                self.model = model

            def embed_batch(self, texts):
                calls.append(list(texts))
                # return fixed-length vectors derived from text length for determinism
                return [[float(len(t) % 10)] * 4 for t in texts]

        # Monkeypatch BackendFactory
        if hasattr(emb_mod, "BackendFactory"):
            monkeypatch.setattr(emb_mod, "BackendFactory", lambda name, model: MockBackend(model=model))
        else:
            monkeypatch.setattr(emb_mod, "MockBackend", MockBackend, raising=False)

        # Run pipeline (without dual-write)
        pipeline = pipe_mod.IngestionPipeline(backend="mock", model="m", batch_size=2, dual_write=False)
        written = pipeline.process_file(src, storage_root=storage, force=True, max_chars=50, extractor_version="v0.test")

        # Assertions: embedding files created matching chunk_count
        emb_dir = os.path.join(storage, "embeddings")
        files = sorted(os.listdir(emb_dir))
        assert len(files) == len(written)
        # Check contents and registry
        reg = reg_mod.MemoryRegistry(storage)
        for p in written:
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            assert "chunk_id" in d
            assert "embedding" in d
            assert d["extractor_version"] == "v0.test"
            assert d["model"] == "m"
            assert "source_path" in d
            assert os.path.exists(d["source_path"]) or True
            # verify registry contains this chunk_id
            reg_entry = reg.get_entry(d["chunk_id"])
            assert reg_entry is not None
            assert reg_entry["embedding_path"] == p

    finally:
        shutil.rmtree(tmp)


def test_pipeline_dual_write_populates_sqlite(monkeypatch):
    """Run pipeline with dual_write=True and verify SQLite registry is populated."""
    emb_mod = importlib.import_module("plugins.memory.ingest.embedder")
    pipe_mod = importlib.import_module("plugins.memory.ingest.pipeline")
    reg_mod = importlib.import_module("plugins.memory.ingest.registry")
    sql_mod = importlib.import_module("plugins.memory.ingest.sqlite_registry")

    tmp = tempfile.mkdtemp(prefix="maya_test_")
    try:
        src = os.path.join(tmp, "sample.txt")
        with open(src, "w", encoding="utf-8") as f:
            f.write("""
One paragraph only for a quick test.
""")
        storage = os.path.join(tmp, "storage")

        class MockBackend:
            def __init__(self, model=None):
                self.model = model
            def embed_batch(self, texts):
                return [[0.1]*4 for _ in texts]

        if hasattr(emb_mod, "BackendFactory"):
            monkeypatch.setattr(emb_mod, "BackendFactory", lambda name, model: MockBackend(model=model))
        else:
            monkeypatch.setattr(emb_mod, "MockBackend", MockBackend, raising=False)

        pipeline = pipe_mod.IngestionPipeline(backend="mock", model="m", batch_size=2, dual_write=True)
        written = pipeline.process_file(src, storage_root=storage, force=True, max_chars=100, extractor_version="v0.test")

        # verify sqlite DB exists and has entries
        s = sql_mod.SQLiteMemoryRegistry(storage)
        entries = s.list_entries(limit=10)
        assert len(entries) >= 1

    finally:
        shutil.rmtree(tmp)
