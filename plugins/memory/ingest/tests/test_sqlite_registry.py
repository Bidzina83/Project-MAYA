import os
import tempfile
import shutil
import json
import importlib.util


def load_module_from_path(path, name):
    # If tests reference absolute /opt/hermes paths (CI), prefer the repo copy when available.
    if not os.path.exists(path):
        # map /opt/hermes/... to repository-relative path and common workspace locations
        if path.startswith('/opt/hermes/'):
            rel = path[len('/opt/hermes/'):].lstrip('/')
            candidates = []
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
            candidates.append(os.path.join(repo_root, rel))
            gw = os.environ.get('GITHUB_WORKSPACE')
            if gw:
                candidates.append(os.path.join(gw, rel))
            # also try current working directory root
            cwd = os.getcwd()
            candidates.append(os.path.join(cwd, rel))
            for alt in candidates:
                if os.path.exists(alt):
                    path = alt
                    break
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_sqlite_bulk_import_empty():
    tmp = tempfile.mkdtemp(prefix="maya_sqlite_")
    try:
        # load modules directly from file paths to avoid package import issues
        reg_mod = load_module_from_path("/opt/hermes/plugins/memory/ingest/registry.py", "reg_mod")
        sql_mod = load_module_from_path("/opt/hermes/plugins/memory/ingest/sqlite_registry.py", "sql_mod")

        # ensure no JSON exists
        reg_json = os.path.join(tmp, "registry", "memory_registry.json")
        os.makedirs(os.path.dirname(reg_json), exist_ok=True)
        if os.path.exists(reg_json):
            os.remove(reg_json)

        # create sqlite registry and bulk import empty dict
        s = sql_mod.SQLiteMemoryRegistry(tmp)
        s.bulk_import({})

        # DB should exist and have zero rows
        assert os.path.exists(s.db_path)
        assert s.list_entries() == {}
    finally:
        shutil.rmtree(tmp)


def test_sqlite_bulk_import_nonempty_and_upsert():
    tmp = tempfile.mkdtemp(prefix="maya_sqlite_")
    try:
        reg_mod = load_module_from_path("/opt/hermes/plugins/memory/ingest/registry.py", "reg_mod")
        sql_mod = load_module_from_path("/opt/hermes/plugins/memory/ingest/sqlite_registry.py", "sql_mod")

        s = sql_mod.SQLiteMemoryRegistry(tmp)
        # prepare sample entries
        entries = {
            "cid1": {
                "chunk_id": "cid1",
                "embedding_path": "/tmp/emb/cid1.json",
                "source_path": "/tmp/src1.txt",
                "source_hash": "h1",
                "model": "m1",
                "extractor_version": "v0",
                "embedding_timestamp": "2026-01-01T00:00:00Z",
            },
            "cid2": {
                "chunk_id": "cid2",
                "embedding_path": "/tmp/emb/cid2.json",
                "source_path": "/tmp/src2.txt",
                "source_hash": "h2",
                "model": "m1",
                "extractor_version": "v0",
                "embedding_timestamp": "2026-01-02T00:00:00Z",
            },
        }
        s.bulk_import(entries)

        listed = s.list_entries(limit=10)
        # should contain two entries
        assert len(listed) == 2
        e1 = s.get_entry("cid1")
        assert e1 is not None
        assert e1["model"] == "m1"

        # upsert behavior: change model for cid1
        entries["cid1"]["model"] = "m2"
        entries["cid1"]["embedding_timestamp"] = "2026-06-01T00:00:00Z"
        s.bulk_import({"cid1": entries["cid1"]})
        e1b = s.get_entry("cid1")
        assert e1b["model"] == "m2"
        assert e1b["embedding_timestamp"] == "2026-06-01T00:00:00Z"
    finally:
        shutil.rmtree(tmp)


def test_migrate_dryrun_reads_json_and_imports_to_sqlite():
    tmp = tempfile.mkdtemp(prefix="maya_sqlite_")
    try:
        # create a registry JSON file with a couple entries
        reg_dir = os.path.join(tmp, "registry")
        os.makedirs(reg_dir, exist_ok=True)
        json_path = os.path.join(reg_dir, "memory_registry.json")
        entries = {
            "a": {"chunk_id": "a", "embedding_path": "/tmp/a.json", "model": "m"},
            "b": {"chunk_id": "b", "embedding_path": "/tmp/b.json", "model": "m"},
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(entries, f)

        # load modules
        reg_mod = load_module_from_path("/opt/hermes/plugins/memory/ingest/registry.py", "reg_mod")
        sql_mod = load_module_from_path("/opt/hermes/plugins/memory/ingest/sqlite_registry.py", "sql_mod")

        # use the JSON registry reader implementation to load entries
        reg = reg_mod.MemoryRegistry(tmp)
        data = reg.list_entries()
        assert len(data) == 2

        # import into sqlite
        s = sql_mod.SQLiteMemoryRegistry(tmp)
        s.bulk_import(data)
        # verify
        assert len(s.list_entries(limit=10)) == 2
    finally:
        shutil.rmtree(tmp)
