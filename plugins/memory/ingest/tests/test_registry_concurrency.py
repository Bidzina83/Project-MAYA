import multiprocessing
from plugins.memory.ingest.registry import MemoryRegistry


def _worker(args):
    storage_root, chunk_id = args
    reg = MemoryRegistry(storage_root)
    # each worker adds a unique entry
    reg.add_entry({"chunk_id": chunk_id, "embedding_path": f"emb/{chunk_id}.npy"})
    return chunk_id


def test_registry_concurrent_writes(tmp_path):
    """Concurrent writers should not lose distinct entries.

    This test spawns multiple processes which each add a unique entry to the
    same MemoryRegistry on disk. If the registry suffers a read-modify-write
    race, some entries will be missing after all writers complete and the
    test will fail — surfacing the concurrency bug.
    """
    storage = tmp_path / "storage"
    storage.mkdir()
    storage_root = str(storage)

    # warm-up
    MemoryRegistry(storage_root)

    workers = 20
    ids = [f"cid_{i}" for i in range(workers)]

    ctx = multiprocessing.get_context("spawn")
    with ctx.Pool(processes=min(8, workers)) as p:
        p.map(_worker, [(storage_root, cid) for cid in ids])

    reg = MemoryRegistry(storage_root)
    data = reg.list_entries()
    missing = [cid for cid in ids if cid not in data]
    assert not missing, f"Missing entries after concurrent writes: {missing}"
