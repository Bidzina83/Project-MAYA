"""Two real host processes; native conversation state, synthetic SDK transport."""
import asyncio
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SENTINEL = "SYNTHETIC_STALE_PRIVATE_SNAPSHOT_MUST_NOT_BE_SENT"


def fixture_module():
    spec = importlib.util.spec_from_file_location("restart_cache_fixture", ROOT / "tests/hermes_g2_prompt_cache_native.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resume_host(directory, patcher):
    """Rebind existing native records; no fixture schema/projection provisioning."""
    import hermes_state
    from gateway.config import GatewayConfig
    from gateway.session import SessionStore
    from hermes_cli import middleware, plugins
    from project_maya.audit import LocalJsonlAuditSink
    from project_maya.config import config_from_mapping
    from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
    from project_maya.hermes_plugins.caller_preparation import CandidateCallerPreparation
    from project_maya.hermes_plugins.governance import MayaGovernancePlugin, RequestIdentity
    from project_maya.hermes_plugins.session_creation import CandidateNativeSessionCreate
    from project_maya.hermes_plugins.session_readers import CandidatePublishedSessionReader
    from project_maya.hermes_plugins.session_requests import ACKNOWLEDGEMENT
    from project_maya.hermes_plugins.session_transitions import CandidateCreateSessionBinding

    assert (directory / "native.db").is_file()
    # Native existing-fixture reopen, not production schema/repair qualification.
    db = hermes_state.SessionDB(directory / "native.db")
    with pytest.MonkeyPatch.context() as construction:
        construction.setattr(hermes_state, "SessionDB", lambda: db)
        store = SessionStore(directory / "sessions", GatewayConfig())
    audit = LocalJsonlAuditSink(directory / "restart-audit.jsonl")
    gateway = PolicyAuthorizationGateway(())
    owner = RequestIdentity("alice", "confidential")  # Fresh trusted fixture authentication, not row-derived identity.
    binding = CandidateCreateSessionBinding(owner=owner, instance_id="g2-test", database=db.db_path,
        route_slot="telegram:fixture", binding_version=1, gateway=gateway,
        audit_sink=audit, acknowledgement=ACKNOWLEDGEMENT)
    config = config_from_mapping({
        "schema_version": 2, "product": {"edition": "enterprise", "instance_id": "g2-test"},
        "deployment": {"class": "desktop", "network_policy": "standard", "data_dir": str(directory)},
        "runtime": {"hermes_compatibility": ">=0.1", "enabled_profiles": ["maya-core"]},
        "broker": {"mode": "disabled"},
        "llm": {"mode": "customer_owned", "provider": "openai", "model": "synthetic-model",
                "credential_ref": "secret://llm/test", "endpoint": "https://api.openai.com/v1"},
        "memory": {"hermes_provider": "local", "retriever": "local_vector", "registry": "sqlite", "governance_enabled": True},
        "governance": {"policy_file": str(directory / "policy.json"), "default_action": "deny", "minimum_memory_trust": 0.7},
        "metabase": {"enabled": False, "deployment": "managed_local"},
    })
    plugin = MayaGovernancePlugin(config, gateway, audit)
    context = plugins.PluginContext(plugins.PluginManifest(name="maya-restart-loop-test"), plugins.get_plugin_manager())
    for kind, callback in (("llm_execution", plugin.model_execution), ("tool_execution", plugin.tool_execution),
                           ("tool_result", plugin.tool_result), ("model_output", plugin.model_output),
                           ("session_write", plugin.session_write)):
        context.register_middleware(kind, callback)
        middleware.require_middleware(kind, callback)
    coordinator = CandidateNativeSessionCreate(store, binding, acknowledgement=ACKNOWLEDGEMENT)
    caller = CandidateCallerPreparation(coordinator, acknowledgement=ACKNOWLEDGEMENT)
    reader = CandidatePublishedSessionReader(coordinator, acknowledgement=ACKNOWLEDGEMENT)
    return (store, db, binding, coordinator), caller, reader


def persisted(directory):
    with sqlite3.connect((directory / "native.db").resolve().as_uri() + "?mode=ro", uri=True) as connection:
        return list(connection.iterdump())


def worker(stage, directory, scenario):
    if scenario not in {"create", "resume", "wrong_owner", "mode_denied", "stale_projection"}:
        raise ValueError("g2.restart_scenario_invalid")
    sys.path[:0] = [str(stage / "host/src"), str(stage / "source"), str(ROOT / "scripts")]
    from verify_governance_g2_restart import contract, verify_worker_stage
    source, host_source = verify_worker_stage(stage)
    marker = directory / "g2-restart-fixture.json"
    fixture_marker = {"schema_version": 1, "qualification": "isolated_restart_loop_fixture",
                      "parent_inputs_sha256": contract()["parent_inputs_sha256"]}
    if scenario == "create":
        assert directory.is_dir() and not any(directory.iterdir())
        marker.write_text(json.dumps(fixture_marker, sort_keys=True), encoding="utf-8")
    else:
        assert json.loads(marker.read_text(encoding="utf-8")) == fixture_marker
    import hermes_state
    import run_agent
    from agent import conversation_loop
    from hermes_cli import middleware
    from project_maya.hermes_plugins import governance
    from project_maya.governance import PolicyAuthorizationGateway, PolicyRule

    assert Path(run_agent.__file__).resolve().is_relative_to(source)
    assert Path(governance.__file__).resolve().is_relative_to(host_source)
    module = fixture_module()
    patcher = pytest.MonkeyPatch()
    initial = scenario == "create"
    root_generator = None
    if initial:
        root_generator = module.host.__wrapped__(directory, patcher)
        original = next(root_generator)
        caller_host = module.caller_host.__wrapped__(original)
    else:
        before_open = persisted(directory)
        caller_host = resume_host(directory, patcher)
        original = caller_host[0]
        assert persisted(directory) == before_open
    loop_generator = module.loop_host.__wrapped__(caller_host, patcher, directory)
    host = module.cache_host.__wrapped__(module.recognition_host.__wrapped__(next(loop_generator)), patcher)
    # Resumed conversation authority has no create/acknowledgement permission.
    if not initial:
        host.binding.gateway = PolicyAuthorizationGateway(tuple(
            PolicyRule("session.read", operation=operation, actor_id="alice")
            for operation in ("route_state", "history", "existing_session", "prompt_cache_rebuild_without_snapshot")))
    if initial:
        receipt = module.base.prepare(host)
        host.db._conn.execute("UPDATE sessions SET system_prompt=? WHERE id=?", (SENTINEL, receipt["session_id"]))
        host.db._conn.commit()
    else:
        receipt = {"session_id": host.db._conn.execute("SELECT id FROM sessions").fetchone()[0]}
    session_id = receipt["session_id"]
    before_rows = host.db.get_messages(session_id)
    projection_path = directory / "sessions/sessions.json"
    if scenario == "stale_projection":
        projection = json.loads(projection_path.read_text())
        projection["generation"] += 1
        projection_path.write_text(json.dumps(projection), encoding="utf-8")  # Isolated attack fixture, never repair.
    before_db = list(host.db._conn.iterdump())
    before_projection = projection_path.read_bytes()
    if scenario == "mode_denied":
        original_authorize = host.binding.gateway.authorize
        patcher.setattr(host.binding.gateway, "authorize", lambda action:
            PolicyAuthorizationGateway(()).authorize(action)
            if action.operation == "prompt_cache_rebuild_without_snapshot" else original_authorize(action))

    def forbidden(*args, **kwargs):
        raise AssertionError("g2.unexpected_snapshot_or_transport")

    patcher.setattr(host.db, "update_system_prompt", forbidden)
    patcher.setattr(conversation_loop, "_stored_prompt_matches_runtime", forbidden)
    original_read = host.db.get_session

    def read(session):
        import traceback
        assert "_restore_or_build_system_prompt" not in {frame.name for frame in traceback.extract_stack()}
        return original_read(session)

    patcher.setattr(host.db, "get_session", read)

    async def conversation():
        # Install after asyncio's native self-pipe creation; SDK uses MockTransport.
        patcher.setattr(socket, "create_connection", forbidden)
        patcher.setattr(socket.socket, "connect", forbidden)
        patcher.setattr(socket.socket, "connect_ex", forbidden)
        patcher.setattr(socket.socket, "sendto", forbidden)
        if scenario == "wrong_owner":
            from dataclasses import replace
            with pytest.raises(middleware.MandatoryMiddlewareError):
                with host.store.authenticated_owned_session_candidate(replace(host.binding.owner, actor_id="mallory")):
                    raise AssertionError("foreign owner reached conversation")
        elif scenario in {"mode_denied", "stale_projection"}:
            with pytest.raises(middleware.MandatoryMiddlewareError):
                await module.execute(host)
        else:
            result = await module.execute(host)
            assert result["final_response"] == "Synthetic approved response"

    try:
        asyncio.run(conversation())
        denied = scenario not in {"create", "resume"}
        assert host.reader._active is None and not host.store._entries
        assert all(client.max_retries == 0 for client in host.clients)
        assert host.db._conn.execute("SELECT system_prompt FROM sessions WHERE id=?", (session_id,)).fetchone()[0] == SENTINEL
        assert projection_path.read_bytes() == before_projection
        assert host.db._conn.execute("SELECT state FROM maya_session_transitions_v1").fetchone()[0] == "caller_acknowledged"
        assert host.db._conn.execute("SELECT count(*) FROM sessions").fetchone()[0] == 1
        if denied:
            assert not host.requests and not host.wire
            assert list(host.db._conn.iterdump()) == before_db
            if scenario != "mode_denied":
                assert not host.agents
            else:
                records = [json.loads(line) for line in host.binding.audit.path.read_text().splitlines()]
                assert any(row.get("operation") == "prompt_cache_rebuild_without_snapshot"
                           and row.get("decision") == "deny" for row in records)
                assert not any(row.get("capability") == "model.egress" for row in records)
                assert "_restore_or_build_system_prompt" in {name for name, _ in host.fixture_errors[0][1]}
        else:
            assert len(host.requests) == len(host.agents) == 1
            assert host.mode_counts == [1]  # New process, new audit, new mode approval.
            assert SENTINEL not in json.dumps(host.wire)
            assert len(host.db.get_messages(session_id)) > len(before_rows)
            if not initial:
                assert before_rows and any(row["role"] == "assistant" for row in host.wire[0]["messages"])
        assert host.db._conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        report = {"status": "passed", "scenario": scenario, "pid": os.getpid(), "session_id": session_id,
                  "requests": len(host.requests), "agents": len(host.agents), "history_before": len(before_rows),
                  "history_after": len(host.db.get_messages(session_id)), "projection_unchanged": True,
                  "snapshot_unchanged": True, "production_qualified": False}
    finally:
        try:
            next(loop_generator)
        except StopIteration:
            pass
        if root_generator is not None:
            try:
                next(root_generator)
            except StopIteration:
                pass
        else:
            middleware._mandatory_enabled = False
            host.db.close()
        patcher.undo()
    return report


@pytest.fixture(scope="module")
def verified_stage():
    import hermes_state
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from verify_governance_g2_restart import verify_stage
        stage = Path(hermes_state.__file__).resolve().parent.parent
        verify_stage(stage)
        return stage
    finally:
        sys.path.pop(0)


@pytest.mark.parametrize("scenario", ["resume", "wrong_owner", "mode_denied", "stale_projection"])
def test_new_process_rebinds_and_qualifies_conversation(verified_stage, tmp_path, scenario):
    environment = os.environ.copy()
    environment.update(PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
    environment["HERMES_HOME"] = str(tmp_path / "home")
    environment.pop("PYTHONPATH", None)

    def run(selected):
        result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(Path(__file__).resolve()),
                                 "--worker", str(verified_stage), str(tmp_path), selected],
                                cwd=verified_stage, env=environment, capture_output=True, timeout=180)
        assert result.returncode == 0, "g2.restart_worker_failed"
        assert SENTINEL.encode() not in result.stdout + result.stderr
        return json.loads(result.stdout)

    first = run("create")  # Waits for process termination before starting the new host.
    second = run(scenario)
    assert first["pid"] != second["pid"] and first["session_id"] == second["session_id"]
    assert first["requests"] == 1 and first["history_before"] == 0
    assert second["history_before"] == first["history_after"] > 0
    assert second["requests"] == int(scenario == "resume")
    if scenario == "resume":
        assert second["history_after"] > second["history_before"]
    else:
        assert second["history_after"] == second["history_before"]
    assert second["projection_unchanged"] and second["snapshot_unchanged"]


if __name__ == "__main__":
    if len(sys.argv) != 5 or sys.argv[1] != "--worker":
        raise SystemExit(2)
    # Arguments are fixture paths/scenario, never production mode or identity selectors.
    captured = io.StringIO()
    try:
        with redirect_stdout(captured), redirect_stderr(captured):
            report = worker(Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve(), sys.argv[4])
        assert SENTINEL not in captured.getvalue()
    except BaseException:
        print(json.dumps({"status": "failed", "reason_code": "g2.restart_worker_failed"}))
        raise SystemExit(1) from None
    print(json.dumps(report, sort_keys=True))
