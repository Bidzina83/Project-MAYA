from __future__ import annotations
import os, json
from datetime import datetime, timezone
from typing import List
import hashlib

# Import submodules with fallback to absolute names so module works when executed
# via importlib.spec_from_file_location (no parent package) or normal package import.
try:
    from .chunker import chunk_file
    from .embedder import Embedder
    from .registry import MemoryRegistry
    from .sqlite_registry import SQLiteMemoryRegistry
except Exception:
    from plugins.memory.ingest.chunker import chunk_file
    from plugins.memory.ingest.embedder import Embedder
    from plugins.memory.ingest.registry import MemoryRegistry
    from plugins.memory.ingest.sqlite_registry import SQLiteMemoryRegistry


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def compute_chunk_id(text: str) -> str:
    """Compute a deterministic chunk id for given text. Exposed so tests can monkeypatch it.

    Default: sha256 hex digest of the text.
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


class IngestionPipeline:
    def __init__(self, backend: str = "mock", model: str | None = None, batch_size: int = 32, dual_write: bool = False):
        self.backend = backend
        self.model = model
        self.batch_size = batch_size
        self.dual_write = dual_write
        self.embedder = Embedder(backend=self.backend, model=self.model, batch_size=self.batch_size)

    def process_file(self, path: str, storage_root: str, force: bool = False, max_chars: int = 1000, extractor_version: str | None = None) -> List[str]:
        """Process file: chunk -> embed -> persist embedding files and update registry.

        Returns list of embedding file paths written.
        """
        os.makedirs(storage_root, exist_ok=True)
        emb_dir = os.path.join(storage_root, 'embeddings')
        os.makedirs(emb_dir, exist_ok=True)
        reg = MemoryRegistry(storage_root)
        sqlite = SQLiteMemoryRegistry(storage_root) if self.dual_write else None

        # produce chunks (Chunk objects from chunker)
        chunks = chunk_file(path, max_chars=max_chars, extractor_version=(extractor_version or 'v0.auto'))
        texts = [c.text for c in chunks]
        # embed texts preserving order
        vectors = self.embedder.embed(texts)
        written_paths = []
        ts = _now_iso()
        for c, v in zip(chunks, vectors):
            chunk_id = getattr(c, 'id', None) or compute_chunk_id(c.text)
            # prepare embedding record
            emb_obj = {
                'chunk_id': chunk_id,
                'embedding': v,
                'model': self.model,
                'provider': self.backend,
                'extractor_version': c.metadata.get('extractor_version', extractor_version),
                'source_path': c.metadata.get('source_path'),
                'source_hash': c.metadata.get('source_hash'),
                'chunk_start': c.start,
                'chunk_end': c.end,
                'chunk_text': c.text[:max_chars],
                'embedding_timestamp': ts,
            }
            emb_path = os.path.join(emb_dir, f"{chunk_id}.json")
            # idempotence: skip if exists and not force
            if os.path.exists(emb_path) and not force:
                written_paths.append(emb_path)
                # ensure registry entry exists
                continue
            # write atomically
            tmp = emb_path + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(emb_obj, f, ensure_ascii=False)
            os.replace(tmp, emb_path)
            written_paths.append(emb_path)

            # update JSON registry
            meta = {
                'chunk_id': chunk_id,
                'embedding_path': emb_path,
                'source_path': emb_obj['source_path'],
                'source_hash': emb_obj['source_hash'],
                'model': emb_obj['model'],
                'provider': emb_obj['provider'],
                'extractor_version': emb_obj['extractor_version'],
                'embedding_timestamp': emb_obj['embedding_timestamp'],
            }
            reg.add_entry(meta)
            if sqlite is not None:
                sqlite.add_entry(meta)

        return written_paths
