"""Actual source/target native cancellation and late executors; synthetic SDK."""
import asyncio
import importlib.util
import json
from pathlib import Path
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
spec = importlib.util.spec_from_file_location("switch_late_descriptor_fixture", ROOT / "tests/hermes_g2_switch_descriptors_native.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
for name in ("host", "caller_host", "loop_host", "recognition_host", "cache_host", "reset_host", "switch_host", "composed_host"):
    globals()[name] = getattr(base, name)


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    sys.path.insert(0, str(ROOT / "scripts"))
    from verify_governance_g2_switch_callers import verify_worker_stage
    source, host = verify_worker_stage(Path(hermes_state.__file__).resolve().parent.parent)
    assert Path(run_agent.__file__).resolve().is_relative_to(source)
    assert Path(governance.__file__).resolve().is_relative_to(host)


def audit(h):
    return [json.loads(line) for line in h.binding.audit.path.read_text().splitlines()]


@pytest.fixture
def late_host(composed_host, monkeypatch):
    h = composed_host
    h.entered = [threading.Event() for _ in range(3)]
    h.release = [threading.Event() for _ in range(3)]
    h.finished = [threading.Event() for _ in range(3)]
    h.contexts, h.client_calls, h.late_denials, h.probe_errors = [], [], [], []
    h.probe_late, h.old_position = False, 0
    constructor = run_agent.AIAgent.__init__
    conversation = run_agent.AIAgent.run_conversation

    def construct(agent, *args, **kwargs):
        constructor(agent, *args, **kwargs)
        scope = governance._session_write.get()
        assert scope.thread_id == threading.get_ident() and scope.task is None and scope.lease.is_active
        h.contexts.append(scope)

    def probe():
        bound = governance._session_write.get()
        assert bound is h.contexts[h.old_position] and bound.session_id == h.old_session
        assert not bound.lease.is_active and h.reader._active.session_id == h.fresh_session
        assert h.reader._active.lease.is_active and h.reader._active.request_id != bound.request_id
        transport, handler = Mock(), Mock()
        def prepare():
            with h.store.prepare_owned_switch_candidate(h.binding.owner, h.source):
                pytest.fail("late switch caller entered")
        for name, effect in (
            ("model", lambda: middleware.run_llm_execution_middleware(
                {"model": "synthetic-model", "messages": []}, transport,
                provider="openai", base_url="https://api.openai.com/v1")),
            ("tool", lambda: middleware.run_tool_execution_middleware("read_file", {"path": "synthetic.txt"}, handler)),
            ("output", lambda: middleware.run_model_output_middleware("SYNTHETIC_LATE_PRIVATE_OUTPUT",
                provider="openai", model="synthetic-model", base_url="https://api.openai.com/v1")),
            ("old_write", lambda: h.db.append_message(h.old_session, "user", "SYNTHETIC_LATE_PRIVATE_WRITE")),
            ("fresh_write", lambda: h.db.append_message(h.fresh_session, "user", "SYNTHETIC_LATE_PRIVATE_WRITE")),
            ("route", lambda: h.store.switch_session(h.binding.route_slot, h.source)),
            ("switch_prepare", prepare),
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
                if position == h.old_position and h.probe_late:
                    probe()
            except BaseException as error:
                h.probe_errors.append(type(error).__name__)
                raise
            finally:
                h.finished[position].set()

    def respond(request):
        position = len(h.requests)
        assert position < 3
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
@pytest.mark.parametrize("side", ["source", "target"])
@pytest.mark.parametrize("race", ["cancel", "repeated_cancellation", "swallowed_child"])
async def test_cancelled_executor_cannot_borrow_fresh_request(late_host, monkeypatch, capsys, caplog, side, race):
    h = late_host
    guards = pytest.MonkeyPatch()
    base.guard_sockets(guards)  # Windows event-loop wake-up socket already exists.
    roots, children = [], []
    child_caught, child_release, cleanup_entered = asyncio.Event(), asyncio.Event(), asyncio.Event()
    factory = h.runner._maya_conversation_executor_factory
    schedule = factory.schedule
    def scheduled(*args):
        task = schedule(*args)
        children.append(task)
        return task
    monkeypatch.setattr(factory, "schedule", scheduled)
    old, fresh = None, None
    try:
        if side == "target":
            h.release[0].set()
            result = await call(h, roots)
            assert result["final_response"] == "Synthetic approved response"
            base.base.prepare(h)
            h.old_position = 1
        position = h.old_position
        h.old_session = h.child if side == "source" else h.source
        h.fresh_session = h.source
        if race == "repeated_cancellation":
            original_wait = asyncio.wait
            async def wait(*args, **kwargs):
                scope = governance._session_write.get()
                if (scope is not None and len(roots) > position
                        and scope.request_id == roots[position].request_id
                        and scope.lease.parent is None and not scope.lease.is_active):
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
                    if not len(roots) > position or handoff._source.request_id != roots[position].request_id:
                        raise
                    child_caught.set()
                    await child_release.wait()
                    assert not governance._session_write.get().lease.is_active
                    with pytest.raises(governance.GovernanceBoundaryError):
                        h.plugin._actor()
                    return None
            monkeypatch.setattr(CandidateSessionExecutorHandoff, "execute", swallowed)

        old = asyncio.create_task(call(h, roots))
        await wait_signal(h.entered[position], old)
        assert roots[position].session_id == h.old_session and roots[position].lease.is_active
        old.cancel()
        if race == "repeated_cancellation":
            await wait_signal(cleanup_entered, old)
            assert not roots[position].lease.is_active
            old.cancel()
        elif race == "swallowed_child":
            await wait_signal(child_caught, old)
            assert not roots[position].lease.is_active
        with pytest.raises(asyncio.CancelledError):
            await old
        assert roots[position].lease.termination == "cancelled" and not roots[position].lease.is_active
        assert not h.finished[position].is_set() and h.reader._active is None and not h.store._entries
        assert h.runner._running_agents == {}
        if side == "source":
            base.base.prepare(h)
        retained_child = h.db.get_messages(h.child)
        historical = list(h.db._conn.execute("SELECT * FROM maya_session_transitions_v1 ORDER BY correlation_id"))
        fresh = asyncio.create_task(call(h, roots))
        await wait_signal(h.entered[position + 1], fresh)
        assert roots[position + 1].session_id == h.fresh_session and roots[position + 1].lease.is_active
        assert roots[position + 1].request_id != roots[position].request_id
        assert h.agents[position] is not h.agents[position + 1]
        assert "SYNTHETIC_OLD_HISTORY" in json.dumps(h.wire[position + 1])
        assert "SYNTHETIC_CHILD_HISTORY" not in json.dumps(h.wire[position + 1])
        before, audit_before = base.snapshot(h), audit(h)
        cache, running = dict(h.store._entries), dict(h.runner._running_agents)
        h.probe_late = True
        h.release[position].set()
        await wait_signal(h.finished[position])
        assert not h.probe_errors
        assert h.late_denials == ["model", "tool", "output", "old_write", "fresh_write", "route", "switch_prepare"]
        assert base.snapshot(h) == before and h.store._entries == cache
        assert h.runner._running_agents == running
        assert h.reader._active is roots[position + 1] and roots[position + 1].lease.is_active
        suffix = audit(h)[len(audit_before):]
        assert audit(h)[:len(audit_before)] == audit_before and suffix
        assert all(row["decision"] == "deny" for row in suffix)
        assert len(h.requests) == position + 2
        child_release.set()
        await asyncio.gather(children[position], return_exceptions=True)
        h.release[position + 1].set()
        result = await fresh
        assert result["final_response"] == "Synthetic approved response"
        assert h.db.get_messages(h.child) == retained_child and h.db.get_messages(h.source)
        assert list(h.db._conn.execute("SELECT * FROM maya_session_transitions_v1 ORDER BY correlation_id")) == historical
        assert h.db._conn.execute("SELECT route_version FROM maya_session_routes_v1").fetchone()[0] == 3
        assert h.db._conn.execute("SELECT state FROM maya_session_transitions_v1 WHERE operation='switch'").fetchone()[0] == "caller_acknowledged"
        assert h.db._conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert h.db._conn.execute("PRAGMA foreign_key_check").fetchone() is None
        assert h.original[3].index.read_bytes() == h.original[3]._state(h.db._conn)[2]
        count = position + 2
        assert len(h.clients) == count * 2 and all(sdk.max_retries == 0 for sdk in h.clients)
        assert sorted(calls[0] for calls in h.client_calls) == [0] * count + [1] * count
        assert len(h.agents) == count and not h.runner._running_agents
        assert not roots[position + 1].lease.is_active and h.reader._active is None and not h.store._entries
        output = capsys.readouterr()
        assert "SYNTHETIC_LATE_PRIVATE" not in output.out + output.err + caplog.text
        assert "SYNTHETIC_LATE_PRIVATE" not in h.binding.audit.path.read_text()
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
