"""Actual old/new native callers and executor threads; synthetic SDK only."""
import asyncio
import importlib.util
import json
from pathlib import Path
import socket
import sys
import threading
from time import monotonic
from unittest.mock import Mock

import hermes_state
import httpx
from openai import OpenAI
import pytest
import run_agent
from gateway.config import Platform
from gateway.session import SessionSource
from hermes_cli import middleware
from project_maya.hermes_plugins import governance
from project_maya.hermes_plugins.candidate_transport import completion_response
from project_maya.hermes_plugins.session_handoff import CandidateSessionExecutorHandoff

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("late_reset_fixture", ROOT / "tests/hermes_g2_reset_contention_native.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
reset_host = base.reset_host


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    sys.path.insert(0, str(ROOT / "scripts"))
    from verify_governance_g2_reset_late_executor import verify_stage
    source, host = verify_stage(Path(hermes_state.__file__).resolve().parent.parent)
    assert Path(run_agent.__file__).resolve().is_relative_to(source)
    assert Path(governance.__file__).resolve().is_relative_to(host)


@pytest.fixture
def late_host(reset_host, monkeypatch):
    h = reset_host
    h.entered = [threading.Event(), threading.Event()]
    h.release = [threading.Event(), threading.Event()]
    h.finished = [threading.Event(), threading.Event()]
    h.contexts = []
    h.client_calls = []
    h.late_denials = []
    h.probe_errors = []
    h.probe_late = False
    constructor = run_agent.AIAgent.__init__
    conversation = run_agent.AIAgent.run_conversation

    def construct(agent, *args, **kwargs):
        constructor(agent, *args, **kwargs)
        scope = governance._session_write.get()
        assert scope.thread_id == threading.get_ident() and scope.task is None and scope.lease.is_active
        h.contexts.append(scope)

    def probe():
        bound = governance._session_write.get()
        assert bound is h.contexts[0] and bound.session_id == h.source and not bound.lease.is_active
        assert h.reader._active.session_id == h.target and h.reader._active.lease.is_active
        transport, handler = Mock(), Mock()
        def prepare():
            with h.store.prepare_owned_reset_candidate(h.binding.owner):
                pytest.fail("late reset body entered")
        for name, effect in (
            ("model", lambda: middleware.run_llm_execution_middleware(
                {"model": "synthetic-model", "messages": []}, transport,
                provider="openai", base_url="https://api.openai.com/v1")),
            ("tool", lambda: middleware.run_tool_execution_middleware("read_file", {"path": "synthetic.txt"}, handler)),
            ("output", lambda: middleware.run_model_output_middleware("SYNTHETIC_LATE_PRIVATE_OUTPUT",
                provider="openai", model="synthetic-model", base_url="https://api.openai.com/v1")),
            ("old_write", lambda: h.db.append_message(h.source, "user", "SYNTHETIC_LATE_PRIVATE_WRITE")),
            ("new_write", lambda: h.db.append_message(h.target, "user", "SYNTHETIC_LATE_PRIVATE_WRITE")),
            ("route", lambda: h.store.reset_session(h.binding.route_slot)),
            ("reset_prepare", prepare),
        ):
            with pytest.raises((governance.GovernanceBoundaryError, middleware.MandatoryMiddlewareError)):
                effect()
            h.late_denials.append(name)
        transport.assert_not_called()
        handler.assert_not_called()

    def run(agent, *args, **kwargs):
        position = h.agents.index(agent)
        try:
            return conversation(agent, *args, **kwargs)
        finally:
            try:
                if position == 0 and h.probe_late:
                    probe()
            except BaseException as error:
                h.probe_errors.append(type(error).__name__)
                raise
            finally:
                h.finished[position].set()

    def respond(request):
        position = len(h.requests)
        assert position < 2
        records = audit(h)
        assert sum(row.get("capability") == "model.egress" and row.get("decision") == "allow"
                   for row in records) == position + 1
        assert any(row.get("operation") == "prompt_cache_rebuild_without_snapshot" and row.get("decision") == "allow"
                   for row in records)
        h.requests.append(request.url.path)
        h.wire.append(json.loads(request.content))
        h.entered[position].set()
        assert h.release[position].wait(60), "synthetic transport release not received"
        return completion_response(request, tool=False)

    def client(**kwargs):
        calls = [0]
        h.client_calls.append(calls)
        def tracked(request):
            calls[0] += 1
            return respond(request)
        kwargs["max_retries"] = 0
        kwargs["http_client"] = httpx.Client(transport=httpx.MockTransport(tracked), trust_env=False)
        sdk = OpenAI(**kwargs)
        h.clients.append(sdk)
        return sdk

    monkeypatch.setattr(run_agent, "OpenAI", client)
    monkeypatch.setattr(run_agent.AIAgent, "__init__", construct)
    monkeypatch.setattr(run_agent.AIAgent, "run_conversation", run)
    yield h
    for event in h.release:
        event.set()
    for entered, finished in zip(h.entered, h.finished):
        if entered.is_set():
            assert finished.wait(15), "native executor did not finish before fixture cleanup"


def audit(h):
    return [json.loads(line) for line in h.binding.audit.path.read_text().splitlines()]


async def wait_signal(signal, task=None):
    deadline = monotonic() + 30
    while not signal.is_set():
        if task is not None and task.done():
            await task
            raise AssertionError("native caller finished before the observed boundary")
        assert monotonic() < deadline, "native boundary not reached"
        await asyncio.sleep(0.01)


async def call(h, roots):
    with h.store.authenticated_owned_session_candidate(h.binding.owner) as entry:
        h.session_id = entry.session_id
        roots.append(governance._session_write.get())
        history = h.store.load_transcript(entry.session_id)
        return await h.runner._run_agent("Synthetic current question", "", history,
            SessionSource(platform=Platform.LOCAL, chat_id="fixture", user_id="alice"),
            entry.session_id, session_key=h.binding.route_slot)


@pytest.mark.asyncio
@pytest.mark.parametrize("race", ["cancel", "repeated_cancellation", "swallowed_child"])
async def test_cancelled_old_executor_cannot_borrow_reset_authority(late_host, monkeypatch, tmp_path, capsys, caplog, race):
    h = late_host
    # Windows asyncio creates its internal wake-up socket before entering this test.
    guards = pytest.MonkeyPatch()
    def forbidden(*args, **kwargs):
        raise AssertionError("g2.reset_late_executor_unexpected_socket")
    guards.setattr(socket, "create_connection", forbidden)
    guards.setattr(socket.socket, "connect", forbidden)
    roots, children = [], []
    child_caught, child_release, cleanup_entered = asyncio.Event(), asyncio.Event(), asyncio.Event()
    factory = h.runner._maya_conversation_executor_factory
    schedule = factory.schedule
    def scheduled(*args):
        task = schedule(*args)
        children.append(task)
        return task
    monkeypatch.setattr(factory, "schedule", scheduled)
    if race == "repeated_cancellation":
        original_wait = asyncio.wait
        async def wait(*args, **kwargs):
            scope = governance._session_write.get()
            if scope is not None and scope.session_id == h.source and scope.lease.parent is None and not scope.lease.is_active:
                cleanup_entered.set()
                await asyncio.Event().wait()
            return await original_wait(*args, **kwargs)
        monkeypatch.setattr(asyncio, "wait", wait)
    elif race == "swallowed_child":
        execute = CandidateSessionExecutorHandoff.execute
        async def swallowed(handoff, *args):
            try:
                return await execute(handoff, *args)
            except asyncio.CancelledError:
                if handoff._source.session_id != h.source:
                    raise
                # Hold the actual selected receiver after its native handoff revoked authority.
                child_caught.set()
                await child_release.wait()
                assert not governance._session_write.get().lease.is_active
                with pytest.raises(governance.GovernanceBoundaryError):
                    h.plugin._actor()
                return None
        monkeypatch.setattr(CandidateSessionExecutorHandoff, "execute", swallowed)

    old = asyncio.create_task(call(h, roots))
    fresh = None
    try:
        await wait_signal(h.entered[0], old)
        assert len(h.agents) == 1 and len(h.requests) == 1 and roots[0].lease.is_active
        old.cancel()
        if race == "repeated_cancellation":
            await wait_signal(cleanup_entered, old)
            assert not roots[0].lease.is_active
            old.cancel()
        elif race == "swallowed_child":
            await wait_signal(child_caught, old)
            assert not roots[0].lease.is_active
        with pytest.raises(asyncio.CancelledError):
            await old
        assert roots[0].lease.termination == "cancelled" and not roots[0].lease.is_active
        assert not h.finished[0].is_set() and h.reader._active is None and not h.store._entries
        assert h.runner._running_agents == {}
        retained = h.db.get_messages(h.source)
        with h.store.prepare_owned_reset_candidate(h.binding.owner) as receipt:
            h.target = receipt["session_id"]
        assert h.target != h.source and h.db.get_messages(h.target) == []
        assert h.db.get_messages(h.source) == retained
        fresh = asyncio.create_task(call(h, roots))
        await wait_signal(h.entered[1], fresh)
        assert roots[1].session_id == h.target and roots[1].lease.is_active
        assert roots[1].request_id != roots[0].request_id and h.contexts[0].session_id == h.source
        assert h.agents[0] is not h.agents[1]
        assert "SYNTHETIC_OLD_HISTORY" not in json.dumps(h.wire[1])
        before = base.persisted(tmp_path)
        audit_before = audit(h)
        cache = dict(h.store._entries)
        h.probe_late = True
        h.release[0].set()
        await wait_signal(h.finished[0])
        assert not h.probe_errors
        assert h.late_denials == ["model", "tool", "output", "old_write", "new_write", "route", "reset_prepare"]
        assert base.persisted(tmp_path) == before and h.store._entries == cache
        assert h.reader._active is roots[1] and roots[1].lease.is_active
        suffix = audit(h)[len(audit_before):]
        assert audit(h)[:len(audit_before)] == audit_before and suffix
        assert all(row["decision"] == "deny" for row in suffix)
        assert h.requests == ["/v1/chat/completions", "/v1/chat/completions"]
        child_release.set()
        await asyncio.gather(children[0], return_exceptions=True)
        h.release[1].set()
        result = await fresh
        assert result["final_response"] == "Synthetic approved response"
        assert h.db.get_messages(h.source) == retained and h.db.get_messages(h.target)
        assert h.db._conn.execute("SELECT route_version FROM maya_session_routes_v1").fetchone()[0] == 2
        assert h.db._conn.execute("SELECT state FROM maya_session_transitions_v1 WHERE operation='reset'").fetchone()[0] == "caller_acknowledged"
        assert h.db._conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert h.db._conn.execute("PRAGMA foreign_key_check").fetchone() is None
        # Each native agent has an idle initialization client and one stream-request client.
        assert len(h.clients) == 4 and all(sdk.max_retries == 0 for sdk in h.clients)
        assert sorted(calls[0] for calls in h.client_calls) == [0, 0, 1, 1]
        assert len(h.agents) == 2 and not h.runner._running_agents
        assert not roots[1].lease.is_active and h.reader._active is None and not h.store._entries
        output = capsys.readouterr()
        assert "SYNTHETIC_LATE_PRIVATE" not in output.out + output.err + caplog.text
    finally:
        try:
            for event in h.release:
                event.set()
            child_release.set()
            for task in (old, fresh):
                if task is not None and not task.done():
                    task.cancel()
            await asyncio.gather(*(task for task in (old, fresh, *children) if task is not None), return_exceptions=True)
            for entered, finished in zip(h.entered, h.finished):
                if entered.is_set():
                    await wait_signal(finished)
        finally:
            guards.undo()
