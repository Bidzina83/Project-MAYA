"""Bounded source-only no-snapshot qualification; no external sockets."""
import importlib.util
from dataclasses import replace
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import hermes_state
import run_agent
from agent import conversation_loop
from gateway.config import Platform
from gateway.session import SessionSource
from hermes_cli import middleware
from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins import governance
from project_maya.hermes_plugins.session_handoff import CandidateSessionExecutorHandoff
from project_maya.hermes_plugins.session_requests import ACKNOWLEDGEMENT

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cache_recognition_fixture", ROOT / "tests/hermes_g2_recognition_native.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
host = base.host
caller_host = base.caller_host
loop_host = base.loop_host
recognition_host = base.recognition_host


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from prepare_governance_g2_prompt_cache import verify_stage
        source, staged = verify_stage(Path(hermes_state.__file__).resolve().parent.parent)
        assert Path(run_agent.__file__).resolve().is_relative_to(source)
        assert Path(governance.__file__).resolve().is_relative_to(staged)
    finally:
        sys.path.pop(0)


@pytest.fixture
def cache_host(recognition_host, monkeypatch):
    host = recognition_host
    host.binding.gateway = PolicyAuthorizationGateway(tuple(
        PolicyRule(capability, operation=operation, actor_id="alice")
        for capability, operation in (("session.read", "route_state"), ("session.read", "history"),
            ("session.read", "existing_session"), ("session.read", "prompt_cache_rebuild_without_snapshot"),
            ("session.transition", "create"), ("session.transition", "acknowledge_create"),
            ("session.write", "create"))))
    host.wire = []
    host.mode_counts = []
    original = base.base.completion_response

    def response(request, **kwargs):
        records = [json.loads(line) for line in host.binding.audit.path.read_text().splitlines()]
        assert any(row.get("operation") == "prompt_cache_rebuild_without_snapshot"
                   and row.get("decision") == "allow" for row in records)
        host.mode_counts.append(sum(row.get("operation") == "prompt_cache_rebuild_without_snapshot"
                                    and row.get("decision") == "allow" for row in records))
        host.wire.append(json.loads(request.content))
        return original(request, **kwargs)

    monkeypatch.setattr(base.base, "completion_response", response)
    return host


async def execute(host):
    with host.store.authenticated_owned_session_candidate(host.binding.owner) as entry:
        host.session_id = entry.session_id
        history = host.store.load_transcript(entry.session_id)
        return await host.runner._run_agent("Synthetic current question", "", history,
            SessionSource(platform=Platform.LOCAL, chat_id="fixture", user_id="alice"),
            entry.session_id, session_key=host.binding.route_slot)


@pytest.mark.asyncio
async def test_first_and_resumed_fresh_agents_omit_snapshot(cache_host, monkeypatch, capsys):
    host = cache_host
    receipt = base.prepare(host)
    sentinel = "SYNTHETIC_STALE_PRIVATE_SNAPSHOT_MUST_NOT_BE_SENT"
    # Fixture provisioning only, outside all conversation authority.
    host.db._conn.execute("UPDATE sessions SET system_prompt=? WHERE id=?", (sentinel, receipt["session_id"]))
    host.db._conn.commit()
    update = Mock(side_effect=AssertionError("snapshot write forbidden"))
    monkeypatch.setattr(host.db, "update_system_prompt", update)
    matches = Mock(side_effect=AssertionError("snapshot restore forbidden"))
    monkeypatch.setattr(conversation_loop, "_stored_prompt_matches_runtime", matches)
    original_read = host.db.get_session

    def read(session_id):
        import traceback
        assert "_restore_or_build_system_prompt" not in {frame.name for frame in traceback.extract_stack()}
        return original_read(session_id)

    monkeypatch.setattr(host.db, "get_session", read)
    for _ in range(2):
        result = await execute(host)
        assert result["final_response"] == "Synthetic approved response"
    assert len(host.agents) == 2 and host.agents[0] is not host.agents[1]
    assert len(host.wire) == 2
    assert host.mode_counts == [1, 2]
    assert all(sdk.max_retries == 0 for sdk in host.clients)
    assert sentinel not in json.dumps(host.wire)
    assert all(any(row["role"] == "system" and row["content"] for row in request["messages"])
               for request in host.wire)
    assert any(row["role"] == "assistant" for row in host.wire[1]["messages"])
    update.assert_not_called()
    matches.assert_not_called()
    assert host.db._conn.execute("SELECT system_prompt FROM sessions WHERE id=?", (receipt["session_id"],)).fetchone()[0] == sentinel
    assert len(host.db.get_messages(receipt["session_id"])) >= 4
    assert host.reader._active is None and not host.store._entries
    assert host.db._conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    output = capsys.readouterr()
    assert sentinel not in output.out + output.err


@pytest.mark.asyncio
@pytest.mark.parametrize("damage", ["missing", "replaced", "contract", "method", "unknown", "import", "policy", "audit", "revocation"])
async def test_mode_denial_stops_native_helper(cache_host, monkeypatch, damage):
    host = cache_host
    receipt = base.prepare(host)
    with host.store.authenticated_owned_session_candidate(host.binding.owner):
        agent = SimpleNamespace(_session_db=host.db, session_id=receipt["session_id"],
                                _cached_system_prompt="old in-process prompt")
        agent._build_system_prompt = Mock(side_effect=AssertionError("build after denial"))

        def attempt():
            if damage == "missing":
                del host.db._maya_existing_session_reader
            elif damage == "replaced":
                host.db._maya_existing_session_reader = object()
            elif damage == "contract":
                monkeypatch.setattr(host.reader, "prompt_cache_contract", "unknown")
            elif damage == "method":
                monkeypatch.setattr(host.reader, "prompt_cache_mode", lambda *args: "rebuild_without_snapshot")
            elif damage == "unknown":
                monkeypatch.setattr(type(host.reader), "prompt_cache_mode", lambda *args: "unknown")
            elif damage == "import":
                import builtins
                original = builtins.__import__

                def broken_import(name, *args, **kwargs):
                    if name == "project_maya.hermes_plugins.session_readers":
                        raise ImportError("synthetic-private-detail")
                    return original(name, *args, **kwargs)

                monkeypatch.setattr(builtins, "__import__", broken_import)
            elif damage == "policy":
                original = host.binding.gateway.authorize
                monkeypatch.setattr(host.binding.gateway, "authorize", lambda action:
                    PolicyAuthorizationGateway(()).authorize(action)
                    if action.operation == "prompt_cache_rebuild_without_snapshot" else original(action))
            elif damage in ("audit", "revocation"):
                original = host.binding.audit.write

                def audit(record):
                    if record.operation == "prompt_cache_rebuild_without_snapshot":
                        if damage == "audit":
                            raise RuntimeError("synthetic-private-detail")
                        governance._session_write.get().lease.revoke_request("cancelled")
                    return original(record)

                monkeypatch.setattr(host.binding.audit, "write", audit)
            with pytest.raises(middleware.MandatoryMiddlewareError) as error:
                conversation_loop._restore_or_build_system_prompt(agent, "", [])
            assert str(error.value) == "mandatory_middleware.callback_failed"
            agent._build_system_prompt.assert_not_called()

        handoff = CandidateSessionExecutorHandoff(attempt, audit_sink=host.binding.audit,
                                                  acknowledgement=ACKNOWLEDGEMENT)
        await handoff.execute(attempt)
    assert not host.requests


@pytest.mark.asyncio
async def test_model_denial_remains_independent(cache_host):
    host = cache_host
    base.prepare(host)
    host.plugin.gateway = PolicyAuthorizationGateway(tuple(
        PolicyRule(capability, actor_id="alice") for capability in ("session.write", "model.output")))
    with pytest.raises(middleware.MandatoryMiddlewareError):
        await execute(host)
    assert not host.requests and not host.wire


@pytest.mark.asyncio
@pytest.mark.parametrize("damage", ["policy", "audit", "contract"])
async def test_mode_denial_stops_actual_native_loop(cache_host, monkeypatch, damage, capsys):
    host = cache_host
    base.prepare(host)
    if damage == "contract":
        monkeypatch.setattr(host.reader, "prompt_cache_contract", "unknown")
    elif damage == "policy":
        original = host.binding.gateway.authorize
        monkeypatch.setattr(host.binding.gateway, "authorize", lambda action:
            PolicyAuthorizationGateway(()).authorize(action)
            if action.operation == "prompt_cache_rebuild_without_snapshot" else original(action))
    else:
        original = host.binding.audit.write

        def audit(record):
            if record.operation == "prompt_cache_rebuild_without_snapshot":
                raise RuntimeError("synthetic-private-detail")
            return original(record)

        monkeypatch.setattr(host.binding.audit, "write", audit)
    with pytest.raises(middleware.MandatoryMiddlewareError) as error:
        await execute(host)
    # Frozen executor/gateway callers map the native error to their fixed code.
    assert str(error.value) == "mandatory_middleware.session_write_failed"
    assert host.fixture_errors[0][0] == "MandatoryMiddlewareError"
    assert "_restore_or_build_system_prompt" in {name for name, _ in host.fixture_errors[0][1]}
    assert not host.requests and not host.wire
    assert host.reader._active is None and not host.store._entries
    output = capsys.readouterr()
    assert "synthetic-private-detail" not in output.out + output.err


@pytest.mark.asyncio
@pytest.mark.parametrize("damage", ["identity", "request", "session", "database", "operations", "thread", "task", "expired", "revoked"])
async def test_mode_requires_exact_live_executor_authority(cache_host, damage):
    host = cache_host
    receipt = base.prepare(host)
    with host.store.authenticated_owned_session_candidate(host.binding.owner):
        agent = SimpleNamespace(_session_db=host.db, session_id=receipt["session_id"],
                                _cached_system_prompt="existing native in-process prompt")

        def attempt():
            scope = governance._session_write.get()
            changes = {"identity": {"identity": replace(scope.identity, actor_id="mallory")},
                       "request": {"request_id": "foreign"}, "session": {"session_id": "foreign"},
                       "database": {"database": scope.database.parent / "foreign.db"},
                       "operations": {"operations": frozenset({"append", "metadata"})},
                       "thread": {"thread_id": -1}, "task": {"task": object()}}
            token = None
            if damage in changes:
                token = governance._session_write.set(replace(scope, **changes[damage]))
            elif damage == "expired":
                scope.lease.deadline = 0
            else:
                scope.lease.revoke_request("cancelled")
            try:
                with pytest.raises(middleware.MandatoryMiddlewareError):
                    conversation_loop._restore_or_build_system_prompt(agent, "", [])
            finally:
                if token is not None:
                    governance._session_write.reset(token)

        handoff = CandidateSessionExecutorHandoff(attempt, audit_sink=host.binding.audit,
                                                  acknowledgement=ACKNOWLEDGEMENT)
        await handoff.execute(attempt)
    assert not host.requests


@pytest.mark.asyncio
async def test_in_process_prompt_kept_only_after_fresh_decisions(cache_host):
    host = cache_host
    receipt = base.prepare(host)
    with host.store.authenticated_owned_session_candidate(host.binding.owner):
        agent = SimpleNamespace(_session_db=host.db, session_id=receipt["session_id"],
                                _cached_system_prompt="existing native in-process prompt",
                                _build_system_prompt=Mock(side_effect=AssertionError("duplicate native session start")))

        def attempt():
            for _ in range(2):
                conversation_loop._restore_or_build_system_prompt(agent, "", [])
            agent._build_system_prompt.assert_not_called()

        handoff = CandidateSessionExecutorHandoff(attempt, audit_sink=host.binding.audit,
                                                  acknowledgement=ACKNOWLEDGEMENT)
        await handoff.execute(attempt)
    records = [json.loads(line) for line in host.binding.audit.path.read_text().splitlines()]
    assert sum(row.get("operation") == "prompt_cache_rebuild_without_snapshot" for row in records) == 2


@pytest.mark.parametrize("sink", ["read", "write"])
def test_touched_catches_propagate_typed_denial_without_logging(monkeypatch, sink, caplog):
    # Source catch probe: enable mandatory mode at the failing sink. This is not
    # an authorized snapshot profile or full-loop qualification.
    monkeypatch.setattr(middleware, "mandatory_middleware_enabled", Mock(side_effect=[False, True]))
    error = middleware.MandatoryMiddlewareError("synthetic-private-detail")
    db = SimpleNamespace(get_session=Mock(side_effect=error), update_system_prompt=Mock(side_effect=error))
    agent = SimpleNamespace(_session_db=db, session_id="fixture", model="fixture",
                            _cached_system_prompt=None, _build_system_prompt=Mock(return_value="fixture prompt"))
    import agent.credits_tracker as credits
    import hermes_cli.plugins as plugins
    monkeypatch.setattr(credits, "seed_credits_at_session_start", lambda *args: None)
    monkeypatch.setattr(plugins, "invoke_hook", lambda *args, **kwargs: None)
    with pytest.raises(middleware.MandatoryMiddlewareError) as caught:
        conversation_loop._restore_or_build_system_prompt(agent, "", [{}] if sink == "read" else [])
    assert str(caught.value) == "mandatory_middleware.callback_failed"
    assert "synthetic-private-detail" not in caplog.text
