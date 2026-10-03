"""Candidate intake contract fixtures, plus real native SQLite refusal.

No Telegram network/SDK dispatcher or complete connector loop is qualified.
"""
import asyncio
from dataclasses import replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest

from project_maya.audit import LocalJsonlAuditSink, NullAuditSink
from project_maya.hermes_plugins import governance
from project_maya.hermes_plugins.session_requests import ACKNOWLEDGEMENT
from project_maya.hermes_plugins.telegram_intake import CandidateTelegramPollingIntake
from tests import test_hermes_authenticated_session_requests as requests


class TestTelegramIntake(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.audit = LocalJsonlAuditSink(Path(self.temp.name) / 'audit.jsonl')
        self.bot = NS(id=123, base_url='https://api.telegram.org/botsynthetic')
        self.application = NS(bot=self.bot)
        self.adapter = NS(_bot=self.bot, _app=self.application, _webhook_mode=False)
        self.context = NS(bot=self.bot, application=self.application)
        self.owner = governance.RequestIdentity('alice', 'confidential')
        self.seen = []
        self.owners = {(456, 789): self.owner}
        self.intake = self.build()

    def build(self, **changes):
        async def consume(request):
            self.seen.append((request, governance._identity.get()))
        kwargs = dict(adapter=self.adapter, bot_id=123, owners=self.owners,
                      audit_sink=self.audit, consume=consume, acknowledgement=ACKNOWLEDGEMENT)
        kwargs.update(changes)
        return CandidateTelegramPollingIntake(**kwargs)

    def update(self, number=1, **changes):
        message = NS(from_user=NS(id=456, is_bot=False), chat=NS(id=789, type='private'), text='safe input')
        for key, value in changes.items():
            setattr(message, key, value)
        return NS(update_id=number, message=message)

    async def test_host_identity_and_classification_not_message_authority(self):
        update = self.update(actor_id='mallory', session_id='other', verified=True)
        await self.intake(update, self.context)
        request, identity = self.seen[0]
        self.assertEqual(identity, self.owner)
        self.assertEqual(request.identity, self.owner)
        self.assertEqual(request.text, 'safe input')
        self.assertEqual(request.qualification, 'source_candidate_only')
        self.assertNotIn('safe input', repr(request))
        self.assertIsNone(governance._identity.get())
        self.assertIsNone(governance._session_write.get())

    async def test_exact_user_and_chat_mapping_required(self):
        for changes in (dict(from_user=NS(id=999, is_bot=False)), dict(chat=NS(id=999, type='private'))):
            with self.assertRaisesRegex(governance.GovernanceBoundaryError, 'owner_unmapped'):
                await self.intake(self.update(**changes), self.context)
        self.assertEqual(self.seen, [])

    async def test_unsupported_messages_never_dispatch(self):
        cases = [dict(chat=NS(id=789, type='group')), dict(from_user=None),
                 dict(from_user=NS(id=True, is_bot=False)), dict(from_user=NS(id=456, is_bot=True)),
                 dict(text='/new'), dict(text=' '), dict(text='x' * 65537)]
        cases.extend({name: object()} for name in ('sender_chat', 'forward_origin', 'reply_to_message',
                                                 'document', 'message_thread_id', 'external_reply'))
        for changes in cases:
            with self.assertRaises(governance.GovernanceBoundaryError):
                await self.intake(self.update(**changes), self.context)
        self.assertEqual(self.seen, [])
        self.assertFalse(self.audit.path.exists())

    async def test_synthetic_and_nonmessage_updates_rejected(self):
        for update in (NS(verified=True, source=NS(user_id='456')), NS(update_id=True, message=self.update().message),
                       NS(update_id=1, message=self.update().message, callback_query=object())):
            with self.assertRaises(governance.GovernanceBoundaryError):
                await self.intake(update, self.context)
        self.assertEqual(self.seen, [])

    async def test_exact_transport_and_bot_identity_required(self):
        for context in (None, NS(bot=self.bot, application=NS(bot=self.bot)), NS(bot=NS(id=123), application=self.application)):
            with self.assertRaisesRegex(governance.GovernanceBoundaryError, 'transport_unqualified'):
                await self.intake(self.update(), context)
        self.adapter._webhook_mode = True
        with self.assertRaises(governance.GovernanceBoundaryError):
            await self.intake(self.update(), self.context)
        self.assertEqual(self.seen, [])

    async def test_replaced_connection_revokes_callback(self):
        self.adapter._bot = NS(id=123, base_url=self.bot.base_url)
        with self.assertRaises(governance.GovernanceBoundaryError):
            await self.intake(self.update(), self.context)

    async def test_replay_and_out_of_order_updates_refused(self):
        await self.intake(self.update(2), self.context)
        for number in (2, 1):
            with self.assertRaises(governance.GovernanceBoundaryError):
                await self.intake(self.update(number), self.context)
        await self.intake(self.update(3), self.context)
        self.assertEqual(len(self.seen), 2)
        self.assertNotEqual(self.seen[0][0].request_id, self.seen[1][0].request_id)

    async def test_owner_mapping_is_frozen_against_caller_mutation(self):
        self.owners[(456, 789)] = replace(self.owner, actor_id='mallory')
        await self.intake(self.update(), self.context)
        self.assertEqual(self.seen[0][1], self.owner)

    async def test_audit_secret_safe_and_fail_closed(self):
        await self.intake(self.update(text='private customer contents'), self.context)
        record = json.loads(self.audit.path.read_text())
        self.assertEqual(record['actor_id'], 'alice')
        self.assertTrue(record['target'].startswith('sha256:'))
        self.assertTrue(record['idempotency_key'].startswith('sha256:'))
        self.assertNotIn('private customer contents', self.audit.path.read_text())
        class BrokenAudit:
            def write(self, record):
                raise RuntimeError('raw-secret-diagnostic')
        intake = self.build(audit_sink=BrokenAudit())
        with self.assertRaisesRegex(governance.GovernanceBoundaryError, 'audit_unavailable') as caught:
            await intake(self.update(), self.context)
        self.assertNotIn('raw-secret', str(caught.exception))
        self.assertEqual(len(self.seen), 1)

    async def test_failure_revokes_identity_and_does_not_retry(self):
        async def broken(request):
            raise RuntimeError('raw-secret-diagnostic')
        intake = self.build(consume=broken)
        with self.assertRaisesRegex(governance.GovernanceBoundaryError, 'dispatch_failed'):
            await intake(self.update(), self.context)
        self.assertIsNone(governance._identity.get())
        with self.assertRaisesRegex(governance.GovernanceBoundaryError, 'update_unqualified'):
            await intake(self.update(), self.context)

    async def test_overlap_and_cancellation_release_scope(self):
        entered, release = asyncio.Event(), asyncio.Event()
        async def waiting(request):
            entered.set()
            await release.wait()
        intake = self.build(consume=waiting)
        task = asyncio.create_task(intake(self.update(), self.context))
        await entered.wait()
        with self.assertRaisesRegex(governance.GovernanceBoundaryError, 'intake_busy'):
            await intake(self.update(2), self.context)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        release.set()
        await intake(self.update(2), self.context)
        self.assertIsNone(governance._identity.get())

    def test_invalid_host_configuration_refused(self):
        for changes in (dict(acknowledgement=''), dict(bot_id=True), dict(bot_id=999), dict(owners={}),
                        dict(owners={(True, 789): self.owner}), dict(audit_sink=NullAuditSink())):
            with self.assertRaises(governance.GovernanceBoundaryError):
                self.build(**changes)


class TestTelegramIntakeNativeSQLite(unittest.TestCase):
    def test_authenticated_intake_does_not_grant_session_writes(self):
        native = requests.TestAuthenticatedSessionRequests()
        self.addCleanup(native.doCleanups)
        native.setUp()
        bot = NS(id=123, base_url='https://api.telegram.org/botsynthetic')
        application = NS(bot=bot)
        async def consume(request):
            native.db.append_message('synthetic-session', 'user', request.text)
        intake = CandidateTelegramPollingIntake(adapter=NS(_bot=bot, _app=application, _webhook_mode=False),
            bot_id=123, owners={(456, 789): native.owner}, audit_sink=native.audit, consume=consume,
            acknowledgement=ACKNOWLEDGEMENT)
        update = NS(update_id=1, message=NS(from_user=NS(id=456, is_bot=False),
            chat=NS(id=789, type='private'), text='safe input'))
        with self.assertRaises(governance.GovernanceBoundaryError):
            asyncio.run(intake(update, NS(bot=bot, application=application)))
        self.assertEqual(native.rows(), [])
