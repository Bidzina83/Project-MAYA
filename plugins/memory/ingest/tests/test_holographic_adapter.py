import pytest

from plugins.memory.holographic.store import MemoryStore
from plugins.memory.adapters.holographic_adapter import HolographicAdapter, RetrieverError


def test_holographic_adapter_search_and_probe(tmp_path):
    dbpath = tmp_path / "holo.db"
    # create store and seed facts
    store = MemoryStore(db_path=str(dbpath))

    # Insert a couple of facts
    fid1 = store.add_fact("Alice went to the market.", category="narrative", tags="test")
    fid2 = store.add_fact("Bob likes Python programming.", category="tech", tags="test")

    # Attempt to initialize the adapter around the store
    try:
        adapter = HolographicAdapter(store)
    except RetrieverError:
        pytest.skip("Holographic FactRetriever not available in this environment")

    # Basic search should return results (FTS fallback works even without numpy)
    res = adapter.search("market", limit=5)
    assert isinstance(res, list)
    assert any(r.get("fact_id") == fid1 for r in res)

    # Probe should work (may fallback to search if HRR disabled)
    p = adapter.probe("Alice", limit=5)
    assert isinstance(p, list)

    # related/reason APIs should not raise
    r = adapter.related("Alice", limit=5)
    assert isinstance(r, list)

    rr = adapter.reason(["Alice"], limit=5)
    assert isinstance(rr, list)
