"""Native cleanup-method probes, not complete AIAgent-loop qualification."""
import asyncio
import ast
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest
import gateway.run as native
from hermes_cli import middleware
from project_maya.hermes_plugins import governance
from tests.hermes_g1_caller_entry_native import host


@pytest.mark.asyncio
@pytest.mark.parametrize("reason", ["cancelled", "failed", "completed", "timeout"])
async def test_native_cleanup_revokes_before_receiver_cleanup_await(host, reason):
    host.runner._draining = False
    release_state = Mock()
    host.runner._release_running_agent_state = release_state
    entered, cleanup_seen = asyncio.Event(), asyncio.Event()
    denied = []
    transport, handler = Mock(), Mock()
    async def receiver():
        with governance._bind_session_handoff(root, governance._SessionWriteLease(parent=root.lease)):
            assert governance.MayaGovernancePlugin._actor(None) == host.owner
            entered.set()
            try:
                await asyncio.Event().wait()
            finally:
                assert not governance._session_write.get().lease.is_active
                for effect in (
                    lambda: governance.MayaGovernancePlugin._actor(None),
                    lambda: host.db.append_message("fixed-session", "user", "late synthetic write"),
                    lambda: middleware.run_llm_execution_middleware(
                        {"model": "synthetic-model", "messages": []}, transport,
                        provider="openai", base_url="https://api.openai.com/v1"),
                    lambda: middleware.run_tool_execution_middleware(
                        "read_file", {"path": "synthetic.txt"}, handler),
                ):
                    try:
                        effect()
                    except (governance.GovernanceBoundaryError, middleware.MandatoryMiddlewareError):
                        denied.append(True)
                cleanup_seen.set()
                await asyncio.sleep(0)
    with host.binding.authenticated_request(host.owner):
        root = governance._session_write.get()
        with host.factory.caller_scope(host.runner, root.session_id):
            task = asyncio.create_task(receiver())
            await asyncio.wait_for(entered.wait(), 2)
            error = (asyncio.CancelledError() if reason == "cancelled" else
                     RuntimeError("synthetic private diagnostic") if reason == "failed" else None)
            if reason == "timeout":
                host.factory.revoke_caller(host.runner, root.session_id, "timeout")
            await host.runner._maya_finish_caller(host.factory, root.session_id, [task], None,
                                                  "fixed-key", 7, error)
            assert cleanup_seen.is_set() and task.cancelled()
            assert root.lease.termination == reason
    assert denied == [True, True, True, True]
    transport.assert_not_called()
    handler.assert_not_called()
    assert host.db.get_messages("fixed-session") == []
    release_state.assert_called_once_with("fixed-key", run_generation=7)


@pytest.mark.asyncio
@pytest.mark.parametrize("typed", [False, True])
async def test_cleanup_failure_observed_and_slot_released(host, typed):
    host.runner._draining = False
    release = Mock()
    host.runner._release_running_agent_state = release
    async def fail():
        raise RuntimeError("synthetic private cleanup marker")
    with host.binding.authenticated_request(host.owner):
        root = governance._session_write.get()
        with host.factory.caller_scope(host.runner, root.session_id):
            task = asyncio.create_task(fail())
            await asyncio.wait({task}, timeout=2)
            error = middleware.MandatoryMiddlewareError("caller_entry_excluded") if typed else None
            if typed:
                await host.runner._maya_finish_caller(host.factory, root.session_id, [task], None,
                                                      "fixed-key", 1, error)
            else:
                with pytest.raises(middleware.MandatoryMiddlewareError) as exc:
                    await host.runner._maya_finish_caller(host.factory, root.session_id, [task], None,
                                                          "fixed-key", 1, error)
                assert str(exc.value) == "mandatory_middleware.caller_cleanup_failed"
            assert not root.lease.is_active
    release.assert_called_once()


@pytest.mark.asyncio
async def test_host_deadline_interrupts_native_caller_scope(host):
    host.binding = replace(host.binding, timeout_seconds=0.02)
    with host.binding.authenticated_request(host.owner):
        root = governance._session_write.get()
        with pytest.raises(asyncio.CancelledError):
            with host.runner._maya_caller_scope("fixed-session"):
                await asyncio.sleep(2)
        assert not root.lease.is_active and root.lease.termination == "timeout"


@pytest.mark.asyncio
async def test_scope_error_before_inner_cleanup_revokes_root(host):
    with host.binding.authenticated_request(host.owner):
        root = governance._session_write.get()
        with pytest.raises(RuntimeError):
            with host.runner._maya_caller_scope("fixed-session"):
                raise RuntimeError("synthetic construction failure")
        assert not root.lease.is_active and root.lease.termination == "failed"


@pytest.mark.asyncio
async def test_swallowed_cancellation_has_bounded_cleanup_and_no_late_authority(host):
    host.runner._draining = False
    host.runner._release_running_agent_state = Mock()
    entered, release = asyncio.Event(), asyncio.Event()
    late = []
    async def stubborn():
        with governance._bind_session_handoff(root, governance._SessionWriteLease(parent=root.lease)):
            entered.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                await release.wait()
                with pytest.raises(governance.GovernanceBoundaryError):
                    governance.MayaGovernancePlugin._actor(None)
                late.append("denied")
    with host.binding.authenticated_request(host.owner):
        root = governance._session_write.get()
        with host.factory.caller_scope(host.runner, root.session_id):
            task = asyncio.create_task(stubborn())
            try:
                await asyncio.wait_for(entered.wait(), 2)
                with pytest.raises(middleware.MandatoryMiddlewareError, match="caller_cleanup_failed"):
                    await asyncio.wait_for(host.runner._maya_finish_caller(
                        host.factory, root.session_id, [task], None, "fixed-key", 1, None), 3)
                assert not root.lease.is_active
                host.runner._release_running_agent_state.assert_called_once()
            finally:
                release.set()
                await asyncio.wait_for(task, 2)
    assert late == ["denied"]


@pytest.mark.asyncio
async def test_native_inactivity_timeout_is_terminal_and_cancels_selected_task(host):
    with host.binding.authenticated_request(host.owner):
        root = governance._session_write.get()
        with host.factory.caller_scope(host.runner, root.session_id):
            task = asyncio.create_task(asyncio.sleep(60))
            with pytest.raises(middleware.MandatoryMiddlewareError) as exc:
                host.runner._maya_timeout_caller(host.factory, root.session_id, task)
            assert str(exc.value) == "mandatory_middleware.caller_request_timeout"
            assert root.lease.termination == "timeout" and not root.lease.is_active
            with pytest.raises(asyncio.CancelledError):
                await task


def test_complete_native_caller_has_cleanup_and_timeout_wiring():
    # Structural coverage proves connection sites, not complete-loop behavior.
    tree = ast.parse(Path(native.__file__).read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "GatewayRunner")
    method = next(n for n in cls.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "_run_agent_inner")
    cleanup = [n for n in ast.walk(method) if isinstance(n, ast.Try) and any(
        isinstance(x, ast.Attribute) and x.attr == "_maya_finish_caller"
        for s in n.finalbody for x in ast.walk(s))]
    assert len(cleanup) == 1
    timeout = next(n for n in ast.walk(method) if isinstance(n, ast.If)
                   and isinstance(n.test, ast.Name) and n.test.id == "_inactivity_timeout")
    guarded = timeout.body[1]
    assert isinstance(guarded, ast.If)
    calls = [n for n in ast.walk(guarded) if isinstance(n, ast.Attribute)]
    assert any(n.attr == "_maya_timeout_caller" for n in calls)
    supports = [n for n in ast.walk(method) if isinstance(n, ast.Attribute)
                and n.attr == "_maya_support_delivery_task"]
    assert len(supports) == 4


@pytest.mark.asyncio
@pytest.mark.parametrize("mandatory", [False, True])
async def test_native_support_delivery_task_exclusion_and_ordinary_control(host, monkeypatch, mandatory):
    monkeypatch.setattr(middleware, "_mandatory_enabled", mandatory)
    sends = []
    async def delivery():
        sends.append("synthetic status")
    task = host.runner._maya_support_delivery_task(delivery())
    if mandatory:
        assert task is None
    else:
        await task
    assert sends == ([] if mandatory else ["synthetic status"])
