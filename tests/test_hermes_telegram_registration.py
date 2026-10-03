"""Real pinned Telegram SDK dispatcher, synthetic HTTP and no live sockets."""
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import os
import sys
import textwrap
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from project_maya.audit import LocalJsonlAuditSink
from project_maya.hermes_plugins.governance import GovernanceBoundaryError, RequestIdentity
from project_maya.hermes_plugins.session_requests import ACKNOWLEDGEMENT
from project_maya.hermes_plugins.telegram_intake import CandidateTelegramPollingRegistration

try:
    import telegram
    from telegram import Chat, Message, Update, User
    from telegram.ext import Application, TypeHandler
    from telegram.request import BaseRequest
except ImportError:
    telegram = None
    BaseRequest = object


class SyntheticRequest(BaseRequest):
    @property
    def read_timeout(self):
        return 5

    async def initialize(self):
        pass

    async def shutdown(self):
        pass

    async def do_request(self, url, method, request_data=None, **kwargs):
        if not url.endswith('/getMe'):
            raise AssertionError('Unexpected Telegram transport call')
        return 200, json.dumps({'ok': True, 'result': {
            'id': 123, 'is_bot': True, 'first_name': 'Synthetic', 'username': 'synthetic_bot',
        }}).encode()


@unittest.skipUnless(telegram is not None and telegram.__version__ == '22.6', 'requires pinned Telegram SDK 22.6')
class TestTelegramRegistration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.audit = LocalJsonlAuditSink(Path(self.temp.name) / 'audit.jsonl')
        self.seen, self.ordinary, self.errors = [], [], []
        self.net = patch('socket.socket.connect', side_effect=AssertionError('Live network forbidden'))
        self.net.start()
        self.addCleanup(self.net.stop)
        self.app = (Application.builder().token('123:synthetic')
                    .request(SyntheticRequest()).get_updates_request(SyntheticRequest()).build())
        await self.app.initialize()
        self.addAsyncCleanup(self.app.shutdown)
        self.adapter = NS(_app=self.app, _bot=self.app.bot, _webhook_mode=False)
        async def ordinary(update, context):
            self.ordinary.append(update)
        async def error(update, context):
            self.errors.append(context.error)
        self.app.add_handler(TypeHandler(object, ordinary), group=-10)
        self.app.add_error_handler(error)
        async def consume(request):
            self.seen.append(request)
        self.factory = CandidateTelegramPollingRegistration(bot_id=123,
            owners={(456, 789): RequestIdentity('alice', 'confidential')},
            audit_sink=self.audit, consume=consume, acknowledgement=ACKNOWLEDGEMENT)

    def update(self, number=1, user=456, chat_type='private', text='safe input'):
        return Update(number, message=Message(message_id=number, date=datetime.now(timezone.utc),
            chat=Chat(789, chat_type), from_user=User(user, 'Untrusted display name', False), text=text))

    async def test_real_dispatcher_maps_identity_and_stops_native_handlers(self):
        self.assertEqual(self.factory(self.adapter), self.factory.contract)
        await self.app.process_update(self.update())
        self.assertEqual(self.seen[0].identity.actor_id, 'alice')
        self.assertEqual(self.seen[0].text, 'safe input')
        self.assertEqual(self.ordinary, [])
        self.assertEqual(self.errors, [])

    async def test_denied_messages_do_not_fall_through_or_reach_sdk_errors(self):
        self.factory(self.adapter)
        for update in (self.update(user=999), self.update(chat_type='group'), self.update(text='/new'),
                       NS(update_id=1, message=self.update().message, verified=True)):
            await self.app.process_update(update)
        self.assertEqual(self.seen, [])
        self.assertEqual(self.ordinary, [])
        self.assertEqual(self.errors, [])
        self.assertNotIn('safe input', self.audit.path.read_text())
        self.assertEqual(len(self.audit.path.read_text().splitlines()), 4)

    async def test_handler_removal_and_catalogue_mutation_never_authorize_intake(self):
        self.factory(self.adapter)
        handler = self.adapter._maya_polling_registration
        self.app.remove_handler(handler)
        await self.app.process_update(self.update())
        self.assertEqual(self.seen, [])
        self.app.add_handler(handler)
        async def fallback(update, context):
            self.ordinary.append(update)
        self.app.add_handler(TypeHandler(object, fallback), group=1)
        await self.app.process_update(self.update())
        self.assertEqual(self.seen, [])
        self.assertEqual(self.ordinary, [])

    async def test_changed_connection_and_unsupported_mode_rejected(self):
        self.factory(self.adapter)
        self.adapter._webhook_mode = True
        await self.app.process_update(self.update())
        self.assertEqual(self.seen, [])
        self.assertEqual(self.errors, [])

    async def test_failure_and_replay_never_run_ordinary_dispatch(self):
        async def broken(request):
            raise RuntimeError('secret-diagnostic')
        factory = CandidateTelegramPollingRegistration(bot_id=123, owners=self.factory.owners,
            audit_sink=self.audit, consume=broken, acknowledgement=ACKNOWLEDGEMENT)
        factory(self.adapter)
        await self.app.process_update(self.update())
        await self.app.process_update(self.update())
        self.assertEqual(self.errors, [])
        self.assertEqual(self.ordinary, [])
        self.assertNotIn('secret-diagnostic', self.audit.path.read_text())

    async def test_double_registration_is_refused(self):
        self.factory(self.adapter)
        with self.assertRaises(GovernanceBoundaryError):
            self.factory(self.adapter)

    async def test_ordinary_sdk_dispatch_unchanged_without_factory(self):
        await self.app.process_update(self.update())
        self.assertEqual(len(self.ordinary), 1)
        self.assertEqual(self.seen, [])

    async def test_native_registration_seam_runs_before_start_and_blocks_missing_factory(self):
        # Execute the exact added native block; this is not complete connect()
        # qualification and does not make a network call or start an updater.
        patch_path = Path(__file__).resolve().parents[1] / 'patches/hermes/0021-telegram-polling-intake-registration.patch'
        added = '\n'.join(line[1:] for line in patch_path.read_text().splitlines()
                          if line.startswith('+') and not line.startswith('+++'))
        scope = {'os': os}
        code = 'async def seam(self):\n' + textwrap.indent(textwrap.dedent(added), '    ')
        code += '\n    self.started_after_registration = hasattr(self, "_maya_polling_registration")\n'
        exec(compile(code, str(patch_path), 'exec'), scope)
        class MandatoryError(RuntimeError):
            pass
        middleware = NS(MandatoryMiddlewareError=MandatoryError, mandatory_middleware_enabled=lambda: True)
        with patch.dict(sys.modules, {'hermes_cli.middleware': middleware}), patch.dict(os.environ, {'TELEGRAM_WEBHOOK_URL': ''}):
            with self.assertRaises(MandatoryError):
                await scope['seam'](self.adapter)
            self.assertFalse(hasattr(self.adapter, 'started_after_registration'))
            self.adapter._maya_polling_intake_factory = self.factory
            await scope['seam'](self.adapter)
            self.assertTrue(self.adapter.started_after_registration)
            await self.app.process_update(self.update())
        self.assertEqual(len(self.seen), 1)
        self.assertEqual(self.ordinary, [])

    async def test_native_registration_seam_denies_webhook_before_factory(self):
        patch_path = Path(__file__).resolve().parents[1] / 'patches/hermes/0021-telegram-polling-intake-registration.patch'
        added = '\n'.join(line[1:] for line in patch_path.read_text().splitlines()
                          if line.startswith('+') and not line.startswith('+++'))
        scope = {'os': os}
        exec('async def seam(self):\n' + textwrap.indent(textwrap.dedent(added), '    '), scope)
        middleware = NS(MandatoryMiddlewareError=RuntimeError, mandatory_middleware_enabled=lambda: True)
        self.adapter._maya_polling_intake_factory = self.factory
        with patch.dict(sys.modules, {'hermes_cli.middleware': middleware}), patch.dict(os.environ, {'TELEGRAM_WEBHOOK_URL': 'https://invalid.example'}):
            with self.assertRaises(RuntimeError):
                await scope['seam'](self.adapter)
        self.assertFalse(hasattr(self.adapter, '_maya_polling_registration'))
