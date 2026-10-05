"""Actual native ordinary lazy initialization on patched/unpatched source."""
import json
from pathlib import Path
import sys
from unittest.mock import Mock

import pytest
import hermes_state
import run_agent
from hermes_cli import middleware

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from prepare_governance_g2_recognition import verify_stage
        from prepare_governance_security_checkpoint import effective_files
        from prepare_governance_baseline import PIN, CONTRACT, digest
        source = Path(run_agent.__file__).resolve().parent
        stage = source.parent
        if (stage / "g2-recognition-manifest.json").exists():
            assert verify_stage(stage)[0] == source
        else:
            data = json.loads((stage / "baseline-manifest.json").read_text())
            assert data["pin"] == PIN and data["patches_applied"] is False
            assert data["contract_sha256"] == digest(CONTRACT.read_bytes())
            effective_files(stage, data, {"effective_native_sha256": {}})
        assert Path(hermes_state.__file__).resolve().parent == source
    finally:
        sys.path.pop(0)


@pytest.fixture
def ordinary(tmp_path, monkeypatch):
    if hasattr(middleware, "_mandatory_enabled"):
        monkeypatch.setattr(middleware, "_mandatory_enabled", False)
    db = hermes_state.SessionDB(tmp_path / "native.db")
    agent = object.__new__(run_agent.AIAgent)
    agent._session_db = db
    agent._session_db_created = False
    agent.session_id = "ordinary-fixture"
    agent.platform = "cli"
    agent.model = "synthetic-model"
    agent._session_init_model_config = {}
    agent._cached_system_prompt = "Synthetic ordinary prompt"
    agent._parent_session_id = None
    yield agent, db
    db.close()


def test_ordinary_lazy_create_and_repeat(ordinary):
    agent, db = ordinary
    agent._ensure_db_session()
    assert agent._session_db_created
    assert db.get_session(agent.session_id) is not None
    before = list(db._conn.iterdump())
    agent._ensure_db_session()
    assert list(db._conn.iterdump()) == before


def test_ordinary_missing_database_remains_noop(ordinary):
    agent, db = ordinary
    agent._session_db = None
    agent._ensure_db_session()
    assert not agent._session_db_created and db.get_session(agent.session_id) is None


def test_ordinary_transient_failure_can_retry(ordinary, monkeypatch):
    agent, db = ordinary
    create = db.create_session
    monkeypatch.setattr(db, "create_session", Mock(side_effect=OSError("synthetic fixture failure")))
    agent._ensure_db_session()
    assert agent._session_db is db and not agent._session_db_created
    assert db.get_session(agent.session_id) is None
    monkeypatch.setattr(db, "create_session", create)
    agent._ensure_db_session()
    assert agent._session_db_created and db.get_session(agent.session_id) is not None
