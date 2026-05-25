import json
import os
import random
import time
from multiprocessing import Process


def writer(base_dir: str, chunk_id: str, writer_id: int, iterations: int = 10):
    # local import to pick up repo layout under pytest
    from plugins.memory.indexer import Indexer

    idx = Indexer(base_dir=base_dir)
    for i in range(iterations):
        entry = {
            "chunk_id": chunk_id,
            "writer_id": writer_id,
            "iter": i,
            "payload": f"data-{writer_id}-{i}",
        }
        idx.write_index_entry(entry)
        # small jitter to increase overlap
        time.sleep(random.random() * 0.01)


def test_atomic_write_under_concurrent_writers(tmp_path):
    base_dir = str(tmp_path / "index_base")
    chunk_id = "atomic-test-chunk"

    # spawn multiple processes that concurrently write the same chunk_id
    procs = []
    num_writers = 6
    iterations = 10
    for wid in range(num_writers):
        p = Process(target=writer, args=(base_dir, chunk_id, wid, iterations))
        p.start()
        procs.append(p)

    for p in procs:
        p.join(timeout=30)
        assert not p.exitcode is None
        assert p.exitcode == 0, f"writer process failed: exitcode={p.exitcode}"

    # find the final file (should be exactly one)
    matches = []
    for root, dirs, files in os.walk(base_dir):
        for fn in files:
            if fn == f"{chunk_id}.json":
                matches.append(os.path.join(root, fn))

    assert len(matches) == 1, f"expected exactly one final file, found: {matches}"
    final_path = matches[0]

    # file must be valid JSON and contain expected keys
    with open(final_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "writer_id" in data, "final JSON missing writer_id"
    assert "payload" in data, "final JSON missing payload"

    # no leftover temporary files
    tmp_leftovers = []
    for root, dirs, files in os.walk(os.path.dirname(final_path)):
        for fn in files:
            if fn.startswith(".tmp_index_"):
                tmp_leftovers.append(os.path.join(root, fn))
    assert tmp_leftovers == [], f"found leftover temp files: {tmp_leftovers}"
