import os
import json
import hashlib
from importlib import import_module, util

# Simple unit test to validate pipeline writes registry entries with provider/vector_dim

def test_pipeline_writes_registry(tmp_path, monkeypatch):
    # prepare sample file
    src = tmp_path / "sample.md"
    src.write_text("A.\n\nB.\n")
    storage = tmp_path / "storage"
    storage.mkdir()

    # load pipeline module from repo path
    pipeline = import_module('plugins.memory.ingest.pipeline') if False else None
    # load by file for isolation
    repo_pipeline = util.spec_from_file_location('repo_pipeline', os.path.join(os.path.dirname(__file__), '..', 'pipeline.py'))
    pipeline_mod = util.module_from_spec(repo_pipeline)
    repo_pipeline.loader.exec_module(pipeline_mod)

    # mock chunker
    class Chunk:
        def __init__(self, text, start, end, metadata):
            self.text = text
            self.start = start
            self.end = end
            self.metadata = metadata

    def mock_chunk_file(path, max_chars=1000, extractor_version='v0.1'):
        content = open(path, 'r', encoding='utf-8').read()
        paras = [p.strip() for p in content.split('\n\n') if p.strip()]
        src_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        out = []
        off = 0
        for p in paras:
            out.append(Chunk(p, off, off+len(p), {'source_path': str(path), 'source_hash': src_hash, 'extractor_version': extractor_version}))
            off += len(p)+2
        return out

    monkeypatch.setattr(pipeline_mod, 'chunk_file', mock_chunk_file)

    # mock embedder
    class MockEmbedder:
        def __init__(self, backend='mock', model=None, batch_size=32):
            pass
        def embed(self, texts):
            return [[0.1, 0.2] for _ in texts]

    monkeypatch.setattr(pipeline_mod, 'Embedder', MockEmbedder)
    import hashlib as _hashlib
    monkeypatch.setattr(pipeline_mod, 'compute_chunk_id', lambda t: _hashlib.sha256(t.encode('utf-8')).hexdigest())

    pl = pipeline_mod.IngestionPipeline(backend='mock', model='mymodel')
    written = pl.process_file(str(src), str(storage), force=True)
    # assert registry exists
    reg_path = storage / 'registry' / 'memory_registry.json'
    assert reg_path.exists()
    reg = json.loads(reg_path.read_text(encoding='utf-8'))
    assert len(reg) == 2
    for cid, meta in reg.items():
        assert meta.get('provider') == 'mock'
        assert meta.get('vector_dim') == 2
        assert meta.get('model') == 'mymodel'
