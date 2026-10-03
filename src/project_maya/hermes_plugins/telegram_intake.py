"""Explicit source-candidate Telegram polling intake; not production activation.

The trusted host registers this callback with the existing polling application.
An arbitrary MessageEvent, verified flag, or serialized request is not an intake
credential. Like the session contract, this is not a sandbox against Python code.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from threading import Lock
from types import MappingProxyType
from typing import Awaitable, Callable, Mapping
from uuid import uuid4

from ..audit import AuditRecord, AuditSink, NullAuditSink
from .governance import GovernanceBoundaryError, RequestIdentity, bind_request_identity
from .session_requests import ACKNOWLEDGEMENT

TELEGRAM_INTAKE_CONTRACT = "project-maya.telegram-polling-intake.v1"
TELEGRAM_REGISTRATION_CONTRACT = "project-maya.telegram-polling-registration.v1"


def _positive_id(value: object) -> bool:
    return type(value) is int and value > 0


@dataclass(frozen=True)
class TelegramIntakeRequest:
    identity: RequestIdentity
    request_id: str
    text: str = field(repr=False)
    qualification: str = field(default="source_candidate_only", init=False)


class CandidateTelegramPollingIntake:
    """Host-installed callback with exact bot/user/chat mapping, no session grant.

Only the configured application's polling dispatcher may supply updates. The
host must not expose this callable through a plugin, tool or public API. Transport
origin is the trusted registration boundary, not a field on the supplied update.
"""

    def __init__(self, *, adapter: object, bot_id: int,
                 owners: Mapping[tuple[int, int], RequestIdentity], audit_sink: AuditSink,
                 consume: Callable[[TelegramIntakeRequest], Awaitable[None]],
                 acknowledgement: str) -> None:
        if (acknowledgement != ACKNOWLEDGEMENT or not _positive_id(bot_id)
                or not owners or not callable(consume) or not isinstance(audit_sink, AuditSink)
                or isinstance(audit_sink, NullAuditSink)):
            raise GovernanceBoundaryError("governance.telegram_intake_invalid")
        selected = dict(owners)
        for key, owner in selected.items():
            if (type(key) is not tuple or len(key) != 2
                    or not all(_positive_id(value) for value in key)
                    or not isinstance(owner, RequestIdentity)):
                raise GovernanceBoundaryError("governance.telegram_intake_invalid")
            with bind_request_identity(owner.actor_id, owner.data_classification):
                pass
        self._adapter = adapter
        self._application = getattr(adapter, "_app", None)
        self._bot = getattr(adapter, "_bot", None)
        self._bot_id = bot_id
        self._owners = MappingProxyType(selected)
        self._audit = audit_sink
        self._consume = consume
        self._lock = Lock()
        self._last_update = -1
        self._validate_transport()

    def _validate_transport(self, context: object | None = None) -> None:
        # No webhook/proxy/custom Bot API admission in this first contract.
        if (self._application is None or self._bot is None
                or getattr(self._adapter, "_webhook_mode", None) is not False
                or getattr(self._adapter, "_app", None) is not self._application
                or getattr(self._adapter, "_bot", None) is not self._bot
                or getattr(self._application, "bot", None) is not self._bot
                or type(getattr(self._bot, "id", None)) is not int
                or self._bot.id != self._bot_id
                or not isinstance(getattr(self._bot, "base_url", None), str)
                or not self._bot.base_url.startswith("https://api.telegram.org/bot")
                or (context is not None and (
                    getattr(context, "application", None) is not self._application
                    or getattr(context, "bot", None) is not self._bot))):
            raise GovernanceBoundaryError("governance.telegram_transport_unqualified")

    async def __call__(self, update: object, context: object) -> None:
        if context is None:
            raise GovernanceBoundaryError("governance.telegram_transport_unqualified")
        self._validate_transport(context)
        if not self._lock.acquire(blocking=False):
            raise GovernanceBoundaryError("governance.telegram_intake_busy")
        try:
            update_id = getattr(update, "update_id", None)
            message = getattr(update, "message", None)
            if (type(update_id) is not int or update_id < 0 or update_id <= self._last_update
                    or message is None or any(getattr(update, name, None) is not None for name in (
                        "edited_message", "channel_post", "edited_channel_post", "callback_query",
                        "business_message", "edited_business_message"))):
                raise GovernanceBoundaryError("governance.telegram_update_unqualified")
            user = getattr(message, "from_user", None)
            chat = getattr(message, "chat", None)
            text = getattr(message, "text", None)
            user_id = getattr(user, "id", None)
            chat_id = getattr(chat, "id", None)
            if (not _positive_id(user_id) or not _positive_id(chat_id)
                    or getattr(user, "is_bot", None) is not False
                    or getattr(chat, "type", None) != "private"
                    or not isinstance(text, str) or not text.strip()
                    or len(text.encode("utf-8")) > 65536 or text.lstrip().startswith("/")
                    or any(getattr(message, name, None) for name in (
                        "sender_chat", "forward_origin", "forward_from", "forward_from_chat",
                        "reply_to_message", "external_reply", "message_thread_id", "is_topic_message",
                        "photo", "video", "audio", "voice", "document", "sticker", "caption"))):
                raise GovernanceBoundaryError("governance.telegram_message_unqualified")
            owner = self._owners.get((user_id, chat_id))
            if owner is None:
                raise GovernanceBoundaryError("governance.telegram_owner_unmapped")
            request_id = uuid4().hex
            try:
                self._audit.write(AuditRecord(
                    event_type="authentication.telegram_intake", decision="allow",
                    reason_code="authentication.identity_bound", actor_id=owner.actor_id,
                    capability="telegram.request", operation="bind",
                    target="sha256:" + hashlib.sha256(
                        f"{self._bot_id}:{user_id}:{chat_id}".encode()).hexdigest(),
                    data_classification=owner.data_classification,
                    idempotency_key="sha256:" + hashlib.sha256(
                        f"{self._bot_id}:{update_id}".encode()).hexdigest(),
                    metadata={"contract": TELEGRAM_INTAKE_CONTRACT,
                              "qualification": "source_candidate_only"},
                ))
            except Exception:
                raise GovernanceBoundaryError("governance.audit_unavailable") from None
            # Consume once even on failure; do not replay an uncertain side effect.
            self._last_update = update_id
            with bind_request_identity(owner.actor_id, owner.data_classification):
                try:
                    await self._consume(TelegramIntakeRequest(owner, request_id, text))
                except GovernanceBoundaryError:
                    raise
                except Exception:
                    raise GovernanceBoundaryError("governance.telegram_dispatch_failed") from None
        finally:
            self._lock.release()


@dataclass(frozen=True)
class CandidateTelegramPollingRegistration:
    """Trusted host factory invoked by native connect before Application.start.

This replaces ordinary dispatch for the candidate, rather than allowing native
text batching to inherit unqualified identity. It grants no worker authority.
"""

    bot_id: int
    owners: Mapping[tuple[int, int], RequestIdentity] = field(repr=False)
    audit_sink: AuditSink = field(repr=False)
    consume: Callable[[TelegramIntakeRequest], Awaitable[None]] = field(repr=False)
    acknowledgement: str = field(repr=False)
    contract: str = field(default=TELEGRAM_REGISTRATION_CONTRACT, init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "owners", MappingProxyType(dict(self.owners)))

    def __call__(self, adapter: object) -> str:
        try:
            import telegram
            from telegram.ext import Application, ApplicationHandlerStop, TypeHandler
            app = getattr(adapter, "_app", None)
            if (telegram.__version__ != "22.6" or not isinstance(app, Application)
                    or app.running or app.updater is None or app.updater.running
                    or app.persistence is not None or app.concurrent_updates > 1
                    or getattr(adapter, "_maya_polling_registration", None) is not None):
                raise ValueError
            intake = CandidateTelegramPollingIntake(
                adapter=adapter, bot_id=self.bot_id, owners=self.owners,
                audit_sink=self.audit_sink, consume=self.consume,
                acknowledgement=self.acknowledgement,
            )
            # Own the candidate's handler catalogue: no preceding handler or
            # reconfigured block=False callback can leak into ordinary dispatch.
            async def dispatch(update, context):
                try:
                    if (type(update) is not telegram.Update
                            or app.handlers != {0: [handler]} or handler.block is not True
                            or handler.callback is not dispatch
                            or getattr(adapter, "_maya_polling_registration", None) is not handler):
                        raise GovernanceBoundaryError("governance.telegram_registration_changed")
                    await intake(update, context)
                except Exception:
                    # A fixed local rejection audit, not SDK process_error (which
                    # can retain raw updates or continue to the next handler group).
                    try:
                        self.audit_sink.write(AuditRecord(
                            event_type="authentication.telegram_rejected", decision="deny",
                            reason_code="authentication.intake_rejected", actor_id="unmapped",
                            capability="telegram.request", target="telegram:intake", operation="bind",
                            data_classification="confidential",
                        ))
                    finally:
                        raise ApplicationHandlerStop() from None
                raise ApplicationHandlerStop()

            handler = TypeHandler(object, dispatch, block=True)
            # Existing callbacks are intentionally inaccessible in this source
            # candidate. Host composition must not restore them after registration.
            app.handlers.clear()
            app.add_handler(handler, group=0)
            setattr(adapter, "_maya_polling_registration", handler)
            return self.contract
        except GovernanceBoundaryError:
            raise
        except Exception:
            raise GovernanceBoundaryError("governance.telegram_registration_unqualified") from None
