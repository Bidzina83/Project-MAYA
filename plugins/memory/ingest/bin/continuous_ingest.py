#!/usr/bin/env python3
"""Continuous ingest processor: process incoming text files, embed, and register.

Usage: continuous_ingest.py --storage-root /opt/data/Project-MAYA --incoming incoming --processed processed

Behavior:
- Scans storage_root/<incoming> for files (txt, md, json).
- For each file: reads text, computes embedding via EmbeddingClient, writes embedding JSON to storage_root/embeddings/{chunk_id}.json,
  adds registry entry via MemoryRegistry.add_entry, and inserts into LocalVectorStore (sqlite).
- Moves processed files to storage_root/<processed> to avoid reprocessing.
"""
import argparse, os, json, shutil, hashlib, time
from datetime import datetime
from pathlib import Path

# Ensure repo importable
import sys
repo_root = Path(__file__).resolve().parents[4]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from plugins.memory.ingest.embedder_wrapper import EmbeddingClient
from plugins.memory.ingest.registry import MemoryRegistry
from plugins.memory.indexer import LocalVectorStore


def compute_sha256(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def process_file(path: Path, storage_root: Path, embed_client: EmbeddingClient, registry: MemoryRegistry, store: LocalVectorStore):
    text = None
    metadata = {}
    try:
        if path.suffix.lower() == '.json':
            obj = json.loads(path.read_text(encoding='utf-8'))
            if 'text' in obj:
                text = obj['text']
                metadata = {k:v for k,v in obj.items() if k!='text'}
            else:
                # fallback: stringify
                text = json.dumps(obj)
        else:
            text = path.read_text(encoding='utf-8')
    except Exception as e:
        print('failed to read', path, e)
        return False
    if not text or not text.strip():
        print('empty text; skipping', path)
        return False
    # embed
    try:
        out = embed_client.embed_documents([text])
    except Exception as e:
        print('embed failed for', path, e)
        return False
    if not out:
        print('no embedding returned for', path)
        return False
    item = out[0]
    chunk_id = item['id']
    vector = item['vector']
    embedding_id = 'emb-' + chunk_id
    # write embedding file
    emb_dir = storage_root / 'embeddings'
    emb_dir.mkdir(parents=True, exist_ok=True)
    emb_path = emb_dir / f"{chunk_id}.json"
    emb_obj = {
        'chunk_id': chunk_id,
        'embedding_id': embedding_id,
        'vector': vector,
        'vector_dim': len(vector),
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'source_path': str(path),
    }
    try:
        with open(emb_path, 'w', encoding='utf-8') as f:
            json.dump(emb_obj, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print('failed write embedding', emb_path, e)
        return False
    # registry metadata
    meta = {
        'chunk_id': chunk_id,
        'embedding_path': str(emb_path),
        'source_path': str(path),
        'source_hash': compute_sha256(text),
        'model': metadata.get('model', 'local-mock'),
        'provider': metadata.get('provider', 'local-mock'),
        'vector_dim': len(vector),
        'extractor_version': metadata.get('extractor_version', 'v0.1'),
        'embedding_timestamp': emb_obj['created_at'],
    }
    try:
        registry.add_entry(meta)
    except Exception as e:
        print('registry.add_entry failed', e)
        return False
    # local vector store insert
    try:
        store.add_entry(embedding_id=embedding_id, chunk_id=chunk_id, vector=vector, created_at=emb_obj['created_at'], source_path=str(path), score_meta={})
    except Exception as e:
        print('LocalVectorStore.add_entry failed', e)
        return False
    return True


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--storage-root', default='/opt/data/Project-MAYA')
    p.add_argument('--incoming', default='incoming')
    p.add_argument('--processed', default='processed')
    p.add_argument('--db', default=None, help='Optional explicit sqlite db path')
    p.add_argument('--backend', default='mock')
    args = p.parse_args()

    storage_root = Path(args.storage_root)
    incoming = storage_root / args.incoming
    processed = storage_root / args.processed
    incoming.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)

    registry = MemoryRegistry(str(storage_root))
    db_path = args.db or str(storage_root / 'registry' / 'memory_registry.sqlite')
    store = LocalVectorStore(db_path)
    embed_client = EmbeddingClient(backend=args.backend, model=None)

    # process all files in incoming
    patterns = ('*.txt', '*.md', '*.json')
    files = []
    for pat in patterns:
        files.extend(sorted(incoming.glob(pat)))
    if not files:
        print('no files to process in', incoming)
        return
    for f in files:
        print('processing', f)
        ok = process_file(f, storage_root, embed_client, registry, store)
        if ok:
            dest = processed / f.name
            try:
                shutil.move(str(f), str(dest))
            except Exception as e:
                print('failed to move processed file', e)
    store.close()

if __name__ == '__main__':
    main()
