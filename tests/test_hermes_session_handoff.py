"""Bounded executor authority with real native SQLite and native helper."""
import asyncio
from contextvars import copy_context
from pathlib import Path
import subprocess
from threading import Event, Thread, get_ident
import unittest
from unittest.mock import patch

from project_maya.hermes_plugins import governance
from project_maya.hermes_plugins.session_handoff import (
    CandidateConversationExecutorFactory, CandidateSessionExecutorHandoff,
)
from project_maya.hermes_plugins.session_requests import ACKNOWLEDGEMENT
from tests import test_hermes_authenticated_session_requests as requests

ROOT = Path(__file__).resolve().parents[1]


class TestSessionHandoff(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.native = requests.TestAuthenticatedSessionRequests()
        self.addCleanup(self.native.doCleanups)
        self.native.setUp()
        target = self.native.native.target / 'executor-fixture'
        (target / 'gateway').mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', str(target)], check=True, capture_output=True)
        (target / 'gateway/run.py').write_bytes((ROOT / 'tests/fixtures/hermes_gateway_executor.py').read_bytes())
        applied = subprocess.run(['git', 'apply', '--whitespace=error', str(ROOT / 'patches/hermes/0022-bounded-request-executor-handoff.patch')],
                                 cwd=target, capture_output=True, text=True)
        self.assertEqual(applied.returncode, 0, applied.stderr)
        applied = subprocess.run(['git', 'apply', '--whitespace=error', str(ROOT / 'patches/hermes/0023-bound-conversation-request-task.patch')],
                                 cwd=target, capture_output=True, text=True)
        self.assertEqual(applied.returncode, 0, applied.stderr)
        namespace = {}
        exec(compile((target / 'gateway/run.py').read_text(), str(target / 'gateway/run.py'), 'exec'), namespace)
        self.runner = namespace['GatewayRunner']()
        self.calls = []

    def job(self, text='safe input'):
        self.calls.append(get_ident())
        self.native.db.append_message('synthetic-session', 'user', text)
        return 'accepted'

    def handoff(self, job):
        return CandidateSessionExecutorHandoff(job, audit_sink=self.native.audit, acknowledgement=ACKNOWLEDGEMENT)

    def conversation_factory(self):
        return CandidateConversationExecutorFactory(
            self.runner, audit_sink=self.native.audit, acknowledgement=ACKNOWLEDGEMENT,
        )

    async def test_native_conversation_scheduling_hops_task_then_executor(self):
        self.conversation_factory()
        source = []
        def job():
            source.append(governance._session_write.get())
            return self.job()
        with self.native.binding.authenticated_request(self.native.owner):
            root = governance._session_write.get()
            task = self.runner.scheduling_seam(job)
            self.assertIsInstance(task, asyncio.Task)
            self.assertIsNot(task, asyncio.current_task())
            self.assertEqual(await task, 'accepted')
            with self.assertRaises(self.native.engine.MandatoryMiddlewareError):
                self.runner.scheduling_seam(job)
        self.assertEqual(len(self.native.rows()), 1)
        self.assertEqual(source[0].identity, root.identity)
        self.assertEqual(source[0].database, root.database)
        self.assertEqual(source[0].operations, root.operations)
        self.assertEqual(source[0].session_id, root.session_id)
        self.assertFalse(source[0].lease.is_active)

    async def test_factory_missing_unbound_and_changed_runner_are_denied(self):
        with self.assertRaises(self.native.engine.MandatoryMiddlewareError):
            self.runner.scheduling_seam(self.job)
        factory = self.conversation_factory()
        with self.assertRaises(self.native.engine.MandatoryMiddlewareError):
            self.runner.scheduling_seam(self.job)
        with self.native.binding.authenticated_request(self.native.owner):
            with self.assertRaises(governance.GovernanceBoundaryError):
                factory.schedule(object(), self.job)
            self.runner._maya_request_executor = object()
            with self.assertRaises(self.native.engine.MandatoryMiddlewareError):
                self.runner.scheduling_seam(self.job)
        self.assertEqual(self.calls, [])

    async def test_root_exit_before_task_execution_revokes_authority(self):
        self.conversation_factory()
        with self.native.binding.authenticated_request(self.native.owner):
            task = self.runner.scheduling_seam(self.job)
        with self.assertRaises(governance.GovernanceBoundaryError):
            await task
        self.assertEqual(self.native.rows(), [])

    async def test_conversation_cancel_before_start_and_next_request(self):
        self.conversation_factory()
        with self.native.binding.authenticated_request(self.native.owner):
            task = self.runner.scheduling_seam(self.job)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        self.assertEqual(self.calls, [])
        with self.native.binding.authenticated_request(self.native.owner):
            self.assertEqual(await self.runner.scheduling_seam(self.job), 'accepted')
        self.assertEqual(len(self.native.rows()), 1)

    async def test_conversation_cancel_revokes_running_worker_immediately(self):
        self.conversation_factory()
        entered, release, done = Event(), Event(), Event()
        self.addCleanup(release.set)
        denied = []
        def job():
            entered.set()
            try:
                if not release.wait(5):
                    raise AssertionError('worker timed out')
                self.job('late')
            except self.native.engine.MandatoryMiddlewareError:
                denied.append(True)
            finally:
                done.set()
        with self.native.binding.authenticated_request(self.native.owner):
            task = self.runner.scheduling_seam(job)
            while not entered.is_set():
                await asyncio.sleep(0.01)
            task.cancel()
            release.set()
            with self.assertRaises(asyncio.CancelledError):
                await task
            while not done.is_set():
                await asyncio.sleep(0.01)
        self.assertEqual(denied, [True])
        self.assertEqual(self.native.rows(), [])

    async def test_unrelated_background_executor_has_no_selection(self):
        self.conversation_factory()
        with self.native.binding.authenticated_request(self.native.owner):
            with self.assertRaises(self.native.engine.MandatoryMiddlewareError):
                await asyncio.create_task(self.runner._run_in_executor_with_context(self.job))
            self.assertEqual(await self.runner.scheduling_seam(self.job), 'accepted')

    async def test_conversation_wrong_session_still_requires_per_write_policy(self):
        self.conversation_factory()
        def job():
            self.native.db.append_message('not-authorized', 'user', 'safe')
        with self.native.binding.authenticated_request(self.native.owner):
            with self.assertRaises(self.native.engine.MandatoryMiddlewareError):
                await self.runner.scheduling_seam(job)
        self.assertEqual(self.native.rows(), [])

    async def test_task_audit_failure_prevents_scheduling(self):
        self.conversation_factory()
        with self.native.binding.authenticated_request(self.native.owner):
            with patch.object(self.native.audit, 'write', side_effect=RuntimeError('raw sensitive detail')):
                with self.assertRaises(self.native.engine.MandatoryMiddlewareError) as failure:
                    self.runner.scheduling_seam(self.job)
            self.assertNotIn('raw sensitive detail', str(failure.exception))
        self.assertEqual(self.calls, [])

    async def test_ordinary_conversation_scheduling_retains_native_task(self):
        with patch.object(self.native.engine, 'mandatory_middleware_enabled', return_value=False):
            task = self.runner.scheduling_seam(lambda: 'ordinary')
            self.assertIsInstance(task, asyncio.Task)
            self.assertEqual(await task, 'ordinary')

    async def test_task_cancellation_cannot_be_swallowed_to_keep_authority(self):
        from project_maya.hermes_plugins.session_handoff import _LeasedRequestTask
        entered = asyncio.Event()
        denied = []
        async def receiver(source, lease):
            with governance._bind_session_handoff(source, lease):
                entered.set()
                try:
                    await asyncio.sleep(60)
                except asyncio.CancelledError:
                    try:
                        governance.MayaGovernancePlugin._actor(None)
                    except governance.GovernanceBoundaryError:
                        denied.append(True)
                    return 'cancellation suppressed, authority revoked'
        with self.native.binding.authenticated_request(self.native.owner):
            source = governance._session_write.get()
            lease = governance._SessionWriteLease(parent=source.lease)
            task = _LeasedRequestTask(receiver(source, lease), lease)
            await entered.wait()
            task.cancel()
            self.assertFalse(lease.is_active)
            await task
        self.assertEqual(denied, [True])

    async def test_conversation_worker_cannot_delegate_another_executor(self):
        self.conversation_factory()
        def job():
            with self.assertRaises(governance.GovernanceBoundaryError):
                self.handoff(self.job)
            return self.job()
        with self.native.binding.authenticated_request(self.native.owner):
            self.assertEqual(await self.runner.scheduling_seam(job), 'accepted')
        self.assertEqual(len(self.native.rows()), 1)

    async def test_allowed_selected_callable_rebinds_and_uses_native_policy(self):
        job = self.job
        with self.native.binding.authenticated_request(self.native.owner):
            self.runner._maya_request_executor = self.handoff(job)
            self.assertEqual(await self.runner._run_in_executor_with_context(job), 'accepted')
        self.assertNotEqual(self.calls[0], get_ident())
        self.assertEqual(len(self.native.rows()), 1)
        self.assertIsNone(governance._session_write.get())

    async def test_missing_handoff_and_other_callable_are_denied(self):
        job = self.job
        with self.native.binding.authenticated_request(self.native.owner):
            with self.assertRaises(self.native.engine.MandatoryMiddlewareError):
                await self.runner._run_in_executor_with_context(job)
            self.runner._maya_request_executor = self.handoff(job)
            with self.assertRaises(self.native.engine.MandatoryMiddlewareError):
                await self.runner._run_in_executor_with_context(lambda: self.job())
        self.assertEqual(self.calls, [])

    async def test_handoff_single_use_and_source_expiration(self):
        job = self.job
        with self.native.binding.authenticated_request(self.native.owner):
            handoff = self.handoff(job)
            with self.assertRaises(governance.GovernanceBoundaryError):
                handoff._invoke()
            await handoff.execute(job)
            with self.assertRaises(governance.GovernanceBoundaryError):
                await handoff.execute(job)
            unused = self.handoff(job)
        with self.assertRaises(governance.GovernanceBoundaryError):
            await unused.execute(job)
        self.assertEqual(len(self.native.rows()), 1)

    async def test_other_async_task_cannot_take_source_authority(self):
        job = self.job
        with self.native.binding.authenticated_request(self.native.owner):
            handoff = self.handoff(job)
            with self.assertRaises(governance.GovernanceBoundaryError):
                await asyncio.create_task(handoff.execute(job))
        self.assertEqual(self.calls, [])

    async def test_wrong_session_and_operations_remain_denied(self):
        def wrong_session():
            self.native.db.append_message('other-session', 'user', 'safe')
        def wrong_operation():
            self.native.db.clear_messages('synthetic-session')
        with self.native.binding.authenticated_request(self.native.owner):
            for job in (wrong_session, wrong_operation):
                self.runner._maya_request_executor = self.handoff(job)
                with self.assertRaises(self.native.engine.MandatoryMiddlewareError):
                    await self.runner._run_in_executor_with_context(job)
        self.assertEqual(self.native.rows(), [])

    async def test_captured_worker_context_expires_on_return(self):
        captured = []
        def job():
            captured.append(copy_context())
            return self.job()
        with self.native.binding.authenticated_request(self.native.owner):
            await self.handoff(job).execute(job)
            with self.assertRaises(self.native.engine.MandatoryMiddlewareError):
                captured[0].run(self.native.db.append_message, 'synthetic-session', 'user', 'late')
        self.assertEqual(len(self.native.rows()), 1)

    async def test_nested_delegation_and_descendant_thread_are_denied(self):
        denied = []
        def job():
            try:
                self.handoff(self.job)
            except governance.GovernanceBoundaryError:
                denied.append('nested')
            context = copy_context()
            def descendant():
                try:
                    context.run(self.native.db.append_message, 'synthetic-session', 'user', 'descendant')
                except self.native.engine.MandatoryMiddlewareError:
                    denied.append('thread')
            thread = Thread(target=descendant)
            thread.start()
            thread.join(5)
            self.assertFalse(thread.is_alive())
        with self.native.binding.authenticated_request(self.native.owner):
            await self.handoff(job).execute(job)
        self.assertEqual(denied, ['nested', 'thread'])
        self.assertEqual(self.native.rows(), [])

    async def test_cancelled_request_revokes_later_thread_write(self):
        entered, release, done = Event(), Event(), Event()
        denied = []
        self.addCleanup(release.set)
        def job():
            entered.set()
            try:
                if not release.wait(5):
                    raise AssertionError('worker release timed out')
                try:
                    governance.MayaGovernancePlugin._actor(None)
                except governance.GovernanceBoundaryError:
                    denied.append('identity')
                self.native.db.append_message('synthetic-session', 'user', 'late')
            except self.native.engine.MandatoryMiddlewareError:
                denied.append(True)
            finally:
                done.set()
        async def request():
            with self.native.binding.authenticated_request(self.native.owner):
                await self.handoff(job).execute(job)
        task = asyncio.create_task(request())
        self.assertTrue(await asyncio.to_thread(entered.wait, 5))
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        release.set()
        self.assertTrue(await asyncio.to_thread(done.wait, 5))
        self.assertEqual(denied, ['identity', True])
        self.assertEqual(self.native.rows(), [])

    async def test_audit_failure_and_raw_executor_errors_are_secret_safe(self):
        class BrokenAudit:
            def write(self, record):
                raise RuntimeError('raw-secret-diagnostic')
        job = self.job
        with self.native.binding.authenticated_request(self.native.owner):
            handoff = CandidateSessionExecutorHandoff(job, audit_sink=BrokenAudit(), acknowledgement=ACKNOWLEDGEMENT)
            with self.assertRaisesRegex(governance.GovernanceBoundaryError, 'audit_unavailable'):
                await handoff.execute(job)
            def broken():
                raise RuntimeError('raw-secret-diagnostic')
            with self.assertRaisesRegex(governance.GovernanceBoundaryError, 'executor_failed') as caught:
                await self.handoff(broken).execute(broken)
        self.assertNotIn('raw-secret', str(caught.exception))
        self.assertEqual(self.calls, [])

    async def test_no_authenticated_scope_cannot_create_handoff(self):
        with self.assertRaises(governance.GovernanceBoundaryError):
            self.handoff(self.job)

    async def test_ordinary_native_context_copy_behavior_preserved(self):
        with patch.object(self.native.engine, 'mandatory_middleware_enabled', return_value=False):
            self.assertEqual(await self.runner._run_in_executor_with_context(lambda: 'ordinary'), 'ordinary')

    async def test_lazy_async_result_cannot_escape_executor_scope(self):
        async def delayed():
            return self.job()
        def job():
            return delayed()
        with self.native.binding.authenticated_request(self.native.owner):
            with self.assertRaisesRegex(governance.GovernanceBoundaryError, 'result_unqualified'):
                await self.handoff(job).execute(job)
        self.assertEqual(self.calls, [])
