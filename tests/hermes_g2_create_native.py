"""Native create/SQLite/publication diagnostics; no frontend qualification."""
import json
from pathlib import Path
import sys
from unittest.mock import patch

import pytest

from gateway.config import GatewayConfig
from gateway.session import SessionStore
from hermes_cli import middleware, plugins
import hermes_state
from project_maya.audit import LocalJsonlAuditSink
from project_maya.config import config_from_mapping
from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins.governance import MayaGovernancePlugin, RequestIdentity
from project_maya.hermes_plugins.session_requests import ACKNOWLEDGEMENT
from project_maya.hermes_plugins.session_transitions import CandidateCreateSessionBinding
from project_maya.hermes_plugins.session_creation import CandidateNativeSessionCreate, projection_bytes, _digest

ROOT = Path(__file__).resolve().parents[1]
with patch.object(sys, "path", [str(ROOT / "scripts"), *sys.path]):
    from prepare_governance_g2_create import verify_create_stage


SCHEMA = """
CREATE TABLE maya_session_owners_v1 (
 session_id TEXT PRIMARY KEY REFERENCES sessions(id), instance_id TEXT NOT NULL,
 database_id TEXT NOT NULL, principal TEXT NOT NULL, classification TEXT NOT NULL,
 binding_version INTEGER NOT NULL, lifecycle_status TEXT NOT NULL,
 parent_session_id TEXT REFERENCES sessions(id), UNIQUE(session_id,principal));
CREATE TABLE maya_session_routes_v1 (
 route_slot TEXT PRIMARY KEY, principal TEXT NOT NULL, session_id TEXT NOT NULL,
 route_version INTEGER NOT NULL, correlation_id TEXT NOT NULL,
 FOREIGN KEY(session_id,principal) REFERENCES maya_session_owners_v1(session_id,principal));
CREATE TABLE maya_session_transitions_v1 (
 correlation_id TEXT PRIMARY KEY, descriptor_digest TEXT NOT NULL, principal TEXT NOT NULL,
 binding_version INTEGER NOT NULL, operation TEXT NOT NULL, target_session TEXT REFERENCES sessions(id),
 expected_route_version INTEGER NOT NULL, result_route_version INTEGER NOT NULL, state TEXT NOT NULL,
 generation INTEGER NOT NULL, projection_hash TEXT NOT NULL, policy_decision_ref TEXT NOT NULL);
CREATE TABLE maya_session_projection_v1 (
 singleton INTEGER PRIMARY KEY CHECK(singleton=1), schema_version INTEGER NOT NULL,
 instance_id TEXT NOT NULL, database_id TEXT NOT NULL, generation INTEGER NOT NULL,
 projection_hash TEXT NOT NULL, index_path TEXT NOT NULL);
"""


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    source = Path(hermes_state.__file__).resolve().parent
    verified, _ = verify_create_stage(source.parent)
    assert source == verified.resolve()


@pytest.fixture
def host(tmp_path, monkeypatch):
    monkeypatch.setattr(middleware, "_mandatory_enabled", False)
    monkeypatch.setattr(middleware, "_mandatory_callbacks", {})
    db = hermes_state.SessionDB(tmp_path / "native.db")
    # Explicit isolated fixture provisioning, never conversation authority.
    db._conn.executescript(SCHEMA)
    raw = projection_bytes("g2-test", str(db.db_path.resolve()), 0, {})
    db._conn.execute("INSERT INTO maya_session_projection_v1 VALUES (1,1,?,?,0,?,?)",
                     ("g2-test", str(db.db_path.resolve()), _digest(raw), str(tmp_path / "sessions/sessions.json")))
    db._conn.commit()
    directory = tmp_path / "sessions"
    directory.mkdir()
    (directory / "sessions.json").write_bytes(raw)
    (directory / "maya-session-projection.lock").write_bytes(b"0")
    monkeypatch.setattr(hermes_state, "SessionDB", lambda: db)
    store = SessionStore(directory, GatewayConfig())
    # Restore the native class for coordinator type validation.
    monkeypatch.undo()
    audit = LocalJsonlAuditSink(tmp_path / "audit.jsonl")
    gateway = PolicyAuthorizationGateway((
        PolicyRule("session.read", operation="route_state", actor_id="alice"),
        PolicyRule("session.transition", operation="create", actor_id="alice"),
        PolicyRule("session.write", operation="create", actor_id="alice"),
    ))
    owner = RequestIdentity("alice", "confidential")
    binding = CandidateCreateSessionBinding(owner=owner, instance_id="g2-test", database=db.db_path,
        route_slot="telegram:fixture", binding_version=1, gateway=gateway,
        audit_sink=audit, acknowledgement=ACKNOWLEDGEMENT)
    config = config_from_mapping({
        "schema_version": 2, "product": {"edition": "enterprise", "instance_id": "g2-test"},
        "deployment": {"class": "desktop", "network_policy": "standard", "data_dir": str(tmp_path)},
        "runtime": {"hermes_compatibility": ">=0.1", "enabled_profiles": ["maya-core"]},
        "broker": {"mode": "disabled"},
        "llm": {"mode": "customer_owned", "provider": "openai", "model": "synthetic-model",
                "credential_ref": "secret://llm/test", "endpoint": "https://api.openai.com/v1"},
        "memory": {"hermes_provider": "local", "retriever": "local_vector", "registry": "sqlite", "governance_enabled": True},
        "governance": {"policy_file": str(tmp_path / "policy.json"), "default_action": "deny", "minimum_memory_trust": 0.7},
        "metabase": {"enabled": False, "deployment": "managed_local"},
    })
    plugin = MayaGovernancePlugin(config, gateway, audit)
    manager = plugins.get_plugin_manager()
    monkeypatch.setattr(manager, "_middleware", {})
    monkeypatch.setattr(middleware, "_mandatory_enabled", False)
    monkeypatch.setattr(middleware, "_mandatory_callbacks", {})
    context = plugins.PluginContext(plugins.PluginManifest(name="maya-g2-create-test"), manager)
    for kind, callback in (("llm_execution", plugin.model_execution), ("tool_execution", plugin.tool_execution),
                           ("tool_result", plugin.tool_result), ("model_output", plugin.model_output),
                           ("session_write", plugin.session_write)):
        context.register_middleware(kind, callback)
        middleware.require_middleware(kind, callback)
    coordinator = CandidateNativeSessionCreate(store, binding, acknowledgement=ACKNOWLEDGEMENT)
    yield store, db, binding, coordinator
    monkeypatch.setattr(middleware, "_mandatory_enabled", False)
    db.close()


def snapshot(host):
    store, db, _, _ = host
    return list(db._conn.iterdump()), (store.sessions_dir / "sessions.json").read_bytes()


def create(host):
    store, _, binding, _ = host
    with binding.authenticated_create(binding.owner) as authority:
        return store.create_owned_session_candidate(authority)


def test_allowed_native_create_commits_and_publishes_without_dispatch_or_cache(host):
    store, db, binding, _ = host
    result = create(host)
    assert result["state"] == "published" and result["dispatch_allowed"] is False
    assert tuple(db._conn.execute("SELECT id,user_id FROM sessions").fetchone()) == (result["session_id"], "alice")
    assert db._conn.execute("SELECT state FROM maya_session_transitions_v1").fetchone()[0] == "published"
    raw = (store.sessions_dir / "sessions.json").read_bytes()
    projection = json.loads(raw)
    assert projection["generation"] == 1
    assert projection["routes"][binding.route_slot]["session_id"] == result["session_id"]
    assert db._conn.execute("SELECT projection_hash FROM maya_session_projection_v1").fetchone()[0] == _digest(raw)
    assert store._entries == {} and not store._loaded
    assert "outcome.session_transition" in binding.audit.path.read_text()


@pytest.mark.parametrize("damage", ["schema", "foreign_owner", "projection", "binding_version", "audit", "policy", "gate"])
def test_denied_native_create_preserves_both_stores(host, damage, monkeypatch):
    store, db, binding, _ = host
    if damage == "schema":
        db._conn.execute("DROP TABLE maya_session_routes_v1")
        db._conn.commit()
    elif damage == "foreign_owner":
        db._conn.execute("INSERT INTO sessions(id,source,started_at) VALUES ('legacy','fixture',1)")
        db._conn.commit()
    elif damage == "projection":
        (store.sessions_dir / "sessions.json").write_bytes(b'{"forged":true}')
    elif damage == "binding_version":
        db._conn.execute("UPDATE maya_session_projection_v1 SET schema_version=2")
        db._conn.commit()
    before = snapshot(host)
    with binding.authenticated_create(binding.owner) as authority:
        if damage == "audit":
            monkeypatch.setattr(binding.audit, "write", lambda record: (_ for _ in ()).throw(RuntimeError("private-value")))
        elif damage == "policy":
            binding.gateway = PolicyAuthorizationGateway(())
        elif damage == "gate":
            middleware._mandatory_callbacks.pop("session_write")
        with pytest.raises(middleware.MandatoryMiddlewareError):
            store.create_owned_session_candidate(authority)
    assert snapshot(host) == before
    assert store._entries == {} and not store._loaded


def test_publication_failure_retains_pending_commit_and_old_index(host, monkeypatch):
    store, db, _, coordinator = host
    old = snapshot(host)[1]
    monkeypatch.setattr(coordinator, "_publish", lambda raw: (_ for _ in ()).throw(OSError("private-path")))
    with pytest.raises(middleware.MandatoryMiddlewareError):
        create(host)
    assert (store.sessions_dir / "sessions.json").read_bytes() == old
    assert db._conn.execute("SELECT count(*) FROM sessions").fetchone()[0] == 1
    assert db._conn.execute("SELECT state FROM maya_session_transitions_v1").fetchone()[0] == "committed_pending_projection"
    before = snapshot(host)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        create(host)
    assert snapshot(host) == before


def test_outcome_audit_failure_leaves_quarantined_receipt(host, monkeypatch):
    _, db, binding, _ = host
    write = binding.audit.write
    def fail_outcome(record):
        if record.event_type == "outcome.session_transition":
            raise RuntimeError("synthetic-private-value")
        write(record)
    monkeypatch.setattr(binding.audit, "write", fail_outcome)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        create(host)
    assert db._conn.execute("SELECT state FROM maya_session_transitions_v1").fetchone()[0] == "projection_verified"
    before = snapshot(host)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        create(host)
    assert snapshot(host) == before


def test_revoked_authority_never_mutates_native_state(host):
    store, _, binding, _ = host
    before = snapshot(host)
    with binding.authenticated_create(binding.owner) as authority:
        authority.revoke()
        with pytest.raises(middleware.MandatoryMiddlewareError):
            store.create_owned_session_candidate(authority)
    assert snapshot(host) == before


def test_repeat_create_does_not_replace_existing_owned_route(host):
    create(host)
    before = snapshot(host)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        create(host)
    assert snapshot(host) == before


def test_native_sql_failure_rolls_back_all_rows_and_consumes_attempt(host):
    store, db, binding, _ = host
    db._conn.execute("CREATE TRIGGER fixture_abort_owner BEFORE INSERT ON maya_session_owners_v1 "
                     "BEGIN SELECT RAISE(ABORT,'fixture-failure'); END")
    db._conn.commit()
    before = snapshot(host)
    with binding.authenticated_create(binding.owner) as authority:
        with pytest.raises(middleware.MandatoryMiddlewareError):
            store.create_owned_session_candidate(authority)
        assert snapshot(host) == before
        db._conn.execute("DROP TRIGGER fixture_abort_owner")
        db._conn.commit()
        after_drop = snapshot(host)
        with pytest.raises(middleware.MandatoryMiddlewareError):
            store.create_owned_session_candidate(authority)
        assert snapshot(host) == after_drop


def test_unknown_commit_outcome_is_quarantined_not_replayed(host, monkeypatch):
    _, db, _, coordinator = host
    old = snapshot(host)[1]
    def ambiguous_commit(conn):
        conn.commit()
        raise OSError("fixture lost commit acknowledgement")
    monkeypatch.setattr(coordinator, "_commit", ambiguous_commit)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        create(host)
    assert snapshot(host)[1] == old
    assert db._conn.execute("SELECT state FROM maya_session_transitions_v1").fetchone()[0] == "committed_pending_projection"
    before = snapshot(host)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        create(host)
    assert snapshot(host) == before


def test_strict_replace_failure_never_copies_over_index(host, monkeypatch):
    import project_maya.hermes_plugins.session_creation as module
    _, db, _, _ = host
    old = snapshot(host)[1]
    monkeypatch.setattr(module.os, "replace", lambda *args: (_ for _ in ()).throw(OSError("busy-file")))
    with pytest.raises(middleware.MandatoryMiddlewareError):
        create(host)
    assert snapshot(host)[1] == old
    assert db._conn.execute("SELECT state FROM maya_session_transitions_v1").fetchone()[0] == "committed_pending_projection"
    assert not list(host[0].sessions_dir.glob(".maya-projection-*"))


def test_busy_cross_process_lock_denies_without_native_effects(host):
    import portalocker
    _, _, _, coordinator = host
    before = snapshot(host)
    with portalocker.Lock(coordinator.lockfile, mode="r+b", timeout=0):
        with pytest.raises(middleware.MandatoryMiddlewareError):
            create(host)
    assert snapshot(host) == before


def test_replaced_native_coordinator_denies_before_handler(host):
    from types import SimpleNamespace
    store, _, _, coordinator = host
    calls = []
    store._maya_create_coordinator = SimpleNamespace(contract=coordinator.contract, create=lambda *args: calls.append(args))
    before = snapshot(host)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        create(host)
    assert calls == [] and snapshot(host) == before
