"""Single-use source-candidate executor handoff, not general worker authority."""
from __future__ import annotations

import asyncio
import hashlib
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from inspect import isawaitable, iscoroutine, isgenerator
from pathlib import Path
from threading import Lock, get_ident
from time import monotonic
from typing import Callable

from ..audit import AuditRecord, AuditSink, NullAuditSink
from .governance import (
    GovernanceBoundaryError, _SessionWriteLease, _bind_session_handoff,
    _current_task, _identity, _session_write,
)
from .session_requests import ACKNOWLEDGEMENT

SESSION_HANDOFF_CONTRACT = "project-maya.session-executor-handoff.v1"
CONVERSATION_SCHEDULE_CONTRACT = "project-maya.conversation-executor-schedule.v1"
CALLER_ENTRY_CONTRACT = "project-maya.native-caller-entry.v1"


@dataclass
class _CallerEntry:
    source: object
    factory: object
    active: bool = True


_caller_entry: ContextVar[_CallerEntry | None] = ContextVar("maya_native_caller_entry", default=None)


@dataclass
class _ExecutorSelection:
    source: object
    function: Callable
    factory: object
    consumed: bool = False


_executor_selection: ContextVar[_ExecutorSelection | None] = ContextVar(
    "maya_candidate_executor_selection", default=None,
)


class _LeasedRequestTask(asyncio.Task):
    """Use the native Task API, revoking authority before cancellation delivery."""

    def __init__(self, coroutine, lease):
        self._maya_lease = lease
        super().__init__(coroutine, loop=asyncio.get_running_loop())
        self.add_done_callback(self._observe_completion)

    def cancel(self, msg=None):
        if self.done():
            return False
        self._maya_lease.revoke_request("cancelled")
        return super().cancel(msg)

    def _observe_completion(self, task):
        # Retrieve abandoned failures without printing worker/provider details.
        # exception() does not consume the exception for a later awaiter.
        if task.cancelled():
            self._maya_lease.revoke_request("cancelled")
        elif task.exception() is not None:
            self._maya_lease.revoke_request("failed")


class CandidateSessionExecutorHandoff:
    """Capture a trusted request's limits for one selected synchronous callable.

Construct only in the authenticated host scope, not from a model/tool argument.
The receiver cannot select identity, path, session, operations or another job.
Nested delegation, arbitrary workers and inherited context remain unqualified.
"""

    contract = SESSION_HANDOFF_CONTRACT

    def __init__(self, function: Callable, *, audit_sink: AuditSink, acknowledgement: str):
        source = _session_write.get()
        selection = _executor_selection.get()
        selected_task = (selection is not None and selection.source is source
                         and selection.function is function and not selection.consumed)
        if (acknowledgement != ACKNOWLEDGEMENT or not callable(function)
                or asyncio.iscoroutinefunction(function) or source is None
                or not source.lease.is_active
                or (source.lease.parent is not None and not selected_task)
                or source.thread_id != get_ident() or source.task is not _current_task()
                or source.identity != _identity.get() or not isinstance(audit_sink, AuditSink)
                or isinstance(audit_sink, NullAuditSink)):
            raise GovernanceBoundaryError("governance.session_handoff_invalid")
        if selected_task:
            selection.consumed = True
        self._source = source
        self._function = function
        self._audit = audit_sink
        self._lease = _SessionWriteLease(parent=source.lease)
        self._lock = Lock()
        self._used = False
        self._receiver_started = False

    async def execute(self, function: Callable, *args):
        source = self._source
        if (function is not self._function or _session_write.get() is not source
                or source.thread_id != get_ident() or source.task is not _current_task()
                or source.identity != _identity.get() or not self._lease.is_active):
            raise GovernanceBoundaryError("governance.session_handoff_invalid")
        with self._lock:
            if self._used:
                raise GovernanceBoundaryError("governance.session_handoff_consumed")
            self._used = True
        try:
            try:
                self._audit.write(AuditRecord(
                    event_type="authentication.session_executor_handoff", decision="allow",
                    reason_code="authentication.request_handoff", actor_id=source.identity.actor_id,
                    capability="session.executor", operation="handoff",
                    target="sha256:" + hashlib.sha256(source.session_id.encode()).hexdigest(),
                    data_classification=source.identity.data_classification,
                    idempotency_key="sha256:" + hashlib.sha256(source.request_id.encode()).hexdigest(),
                    metadata={"contract": self.contract, "qualification": "source_candidate_only"},
                ))
            except Exception:
                raise GovernanceBoundaryError("governance.audit_unavailable") from None
            return await asyncio.get_running_loop().run_in_executor(None, self._invoke, *args)
        except GovernanceBoundaryError:
            raise
        except Exception:
            raise GovernanceBoundaryError("governance.session_executor_failed") from None
        finally:
            # Cancellation cannot kill a running thread, but no later write may
            # use its lease. Already-authorized transactions are not rolled back.
            self._lease.active = False

    def _invoke(self, *args):
        with self._lock:
            if (not self._used or self._receiver_started
                    or get_ident() == self._source.thread_id or _current_task() is not None):
                raise GovernanceBoundaryError("governance.session_handoff_invalid")
            self._receiver_started = True
        with _bind_session_handoff(self._source, self._lease):
            result = self._function(*args)
            if isawaitable(result) or isgenerator(result):
                if iscoroutine(result) or isgenerator(result):
                    result.close()
                raise GovernanceBoundaryError("governance.session_executor_result_unqualified")
            return result


class _CandidateExecutorResolver:
    contract = SESSION_HANDOFF_CONTRACT

    def __init__(self, factory):
        self._factory = factory

    async def execute(self, function, *args):
        selection = _executor_selection.get()
        if (selection is None or selection.factory is not self._factory
                or selection.source is not _session_write.get()
                or selection.function is not function or args):
            raise GovernanceBoundaryError("governance.session_handoff_invalid")
        handoff = CandidateSessionExecutorHandoff(
            function, audit_sink=self._factory._audit, acknowledgement=ACKNOWLEDGEMENT,
        )
        return await handoff.execute(function)


class CandidateConversationExecutorFactory:
    """One native main-loop closure per authenticated scope, not generic workers.

    Install once on a trusted candidate runner. Native Patch 23 selects the
    synchronous closure; no request fields or tool arguments select authority.
    """

    contract = CONVERSATION_SCHEDULE_CONTRACT
    caller_contract = CALLER_ENTRY_CONTRACT

    def __init__(self, runner, *, audit_sink: AuditSink, acknowledgement: str):
        helper = getattr(runner, "_run_in_executor_with_context", None)
        if (acknowledgement != ACKNOWLEDGEMENT or not asyncio.iscoroutinefunction(helper)
                or getattr(helper, "__self__", None) is not runner
                or not isinstance(audit_sink, AuditSink) or isinstance(audit_sink, NullAuditSink)
                or getattr(runner, "_maya_request_executor", None) is not None
                or getattr(runner, "_maya_conversation_executor_factory", None) is not None):
            raise GovernanceBoundaryError("governance.session_handoff_invalid")
        self._runner = runner
        self._helper = helper
        self._audit = audit_sink
        self._lock = Lock()
        self._claimed = []
        self._caller_claimed = []
        self._resolver = _CandidateExecutorResolver(self)
        runner._maya_request_executor = self._resolver
        runner._maya_conversation_executor_factory = self

    def _validate_caller(self, runner, session_id):
        source = _session_write.get()
        if (runner is not self._runner
                or getattr(runner, "_maya_request_executor", None) is not self._resolver
                or getattr(runner, "_maya_conversation_executor_factory", None) is not self
                or getattr(runner, "_run_in_executor_with_context", None) != self._helper
                or source is None or source.lease.parent is not None
                or source.lease.deadline is None or not source.lease.is_active
                or source.thread_id != get_ident() or source.task is None
                or source.task is not _current_task() or source.identity != _identity.get()
                or session_id != source.session_id):
            raise GovernanceBoundaryError("governance.caller_entry_invalid")
        try:
            database = Path(runner._session_db.db_path).resolve(strict=True)
        except Exception:
            raise GovernanceBoundaryError("governance.caller_entry_invalid") from None
        if database != source.database:
            raise GovernanceBoundaryError("governance.caller_entry_invalid")
        return source

    @contextmanager
    def caller_scope(self, runner, session_id):
        """One authenticated native caller per root request, never a worker grant."""
        source = self._validate_caller(runner, session_id)
        if _caller_entry.get() is not None:
            raise GovernanceBoundaryError("governance.caller_entry_invalid")
        with self._lock:
            self._caller_claimed = [item for item in self._caller_claimed if item[1].is_active]
            if any(item[0] == source.request_id for item in self._caller_claimed):
                raise GovernanceBoundaryError("governance.caller_entry_consumed")
            self._caller_claimed.append((source.request_id, source.lease))
        try:
            self._audit.write(AuditRecord(
                event_type="authentication.native_caller", decision="allow",
                reason_code="authentication.identity_bound", actor_id=source.identity.actor_id,
                capability="runtime.caller", operation="enter",
                target="sha256:" + hashlib.sha256(source.session_id.encode()).hexdigest(),
                data_classification=source.identity.data_classification,
                idempotency_key="sha256:" + hashlib.sha256(source.request_id.encode()).hexdigest(),
                metadata={"contract": self.caller_contract, "qualification": "source_candidate_only"},
            ))
        except Exception:
            raise GovernanceBoundaryError("governance.audit_unavailable") from None
        entry = _CallerEntry(source, self)
        token = _caller_entry.set(entry)
        loop = asyncio.get_running_loop()
        def expire():
            if entry.active and source.lease.active:
                source.lease.revoke("timeout")
                source.task.cancel()
        timer = None
        try:
            timer = loop.call_later(max(0, source.lease.deadline - monotonic()), expire)
            yield
        except asyncio.CancelledError:
            source.lease.revoke("cancelled")
            raise
        except BaseException:
            source.lease.revoke("failed")
            raise
        finally:
            if timer is not None:
                timer.cancel()
            source.lease.revoke("completed")
            entry.active = False
            _caller_entry.reset(token)

    def require_caller(self, runner, session_id):
        source = self._validate_caller(runner, session_id)
        entry = _caller_entry.get()
        if (entry is None or not entry.active or entry.factory is not self or entry.source is not source):
            raise GovernanceBoundaryError("governance.caller_entry_invalid")
        return True

    def revoke_caller(self, runner, session_id, reason):
        """Synchronous cleanup boundary; expired authority may still be revoked."""
        entry = _caller_entry.get()
        source = _session_write.get()
        if (runner is not self._runner or source is None or entry is None or not entry.active
                or entry.factory is not self or entry.source is not source
                or source.lease.parent is not None
                or source.thread_id != get_ident() or source.task is not _current_task()
                or source.identity != _identity.get() or source.session_id != session_id):
            raise GovernanceBoundaryError("governance.caller_entry_invalid")
        source.lease.revoke_request(reason)

    def schedule(self, runner, function):
        source = _session_write.get()
        if (runner is not self._runner
                or getattr(runner, "_maya_request_executor", None) is not self._resolver
                or getattr(runner, "_maya_conversation_executor_factory", None) is not self
                or getattr(runner, "_run_in_executor_with_context", None) != self._helper
                or source is None or not source.lease.is_active or source.lease.parent is not None
                or source.task is None
                or source.thread_id != get_ident() or source.task is not _current_task()
                or source.identity != _identity.get() or not callable(function)
                or asyncio.iscoroutinefunction(function)):
            raise GovernanceBoundaryError("governance.session_handoff_invalid")
        # The existing host request UUID is unique; retain it only while its
        # source scope is live. Concurrent requests never share a runner slot.
        with self._lock:
            self._claimed = [item for item in self._claimed if item[1].is_active]
            if any(item[0] == source.request_id for item in self._claimed):
                raise GovernanceBoundaryError("governance.session_handoff_consumed")
            self._claimed.append((source.request_id, source.lease))
        lease = _SessionWriteLease(parent=source.lease)
        try:
            self._audit.write(AuditRecord(
                event_type="authentication.session_task_handoff", decision="allow",
                reason_code="authentication.request_handoff", actor_id=source.identity.actor_id,
                capability="session.task", operation="handoff",
                target="sha256:" + hashlib.sha256(source.session_id.encode()).hexdigest(),
                data_classification=source.identity.data_classification,
                idempotency_key="sha256:" + hashlib.sha256(source.request_id.encode()).hexdigest(),
                metadata={"contract": self.contract, "qualification": "source_candidate_only"},
            ))
        except Exception:
            lease.active = False
            raise GovernanceBoundaryError("governance.audit_unavailable") from None
        coroutine = self._receive(source, lease, function)
        try:
            return _LeasedRequestTask(coroutine, lease)
        except Exception:
            lease.active = False
            coroutine.close()
            raise GovernanceBoundaryError("governance.session_task_failed") from None

    async def _receive(self, source, lease, function):
        try:
            with _bind_session_handoff(source, lease):
                selection = _ExecutorSelection(_session_write.get(), function, self)
                token = _executor_selection.set(selection)
                try:
                    return await self._helper(function)
                finally:
                    _executor_selection.reset(token)
        except asyncio.CancelledError:
            lease.revoke_request("cancelled")
            raise
        except BaseException:
            lease.revoke_request("failed")
            raise
        finally:
            lease.active = False
