"""Host-owned expected bytes for one pinned, tool-free Windows conversation.

This is a narrow synthetic request oracle, not a prompt builder for the product.
It neither imports Hermes nor learns authority from a child's first request.
"""
from __future__ import annotations

from datetime import date
import hashlib
import json
import re

from .model_service import MODEL, checked_request
from .protocol import ProtocolError, decode, encode

LITERALS_SHA256 = "df19fbdf99f3ee18661f19c47408514e65525b68ad718da9a0540fb010d9ade3"


def native_request(literals: bytes, attempt: str, utc_day: str, canary: str) -> bytes:
    """All arguments must be loaded/generated in trusted product setup."""
    values = decode(literals)
    canonical = json.dumps(values, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    if hashlib.sha256(canonical).hexdigest() != LITERALS_SHA256:
        raise ProtocolError()
    if (type(attempt) is not str or not re.fullmatch(r"[0-9a-f]{32}", attempt)
            or type(canary) is not str or not re.fullmatch(r"[0-9a-f]{64}", canary)
            or type(utc_day) is not str or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", utc_day)):
        raise ProtocolError()
    try:
        day = date.fromisoformat(utc_day)
    except ValueError:
        raise ProtocolError() from None
    state = "C:\\ProgramData\\MayaProtectedPython-Startup1\\" + attempt + "\\state"
    environment = ("Host: Windows (11)\nUser home directory: " + state
        + "\nCurrent working directory: " + state + "\n" + values["windows_username_note"]
        + "\n\n" + values["_WINDOWS_BASH_SHELL_HINT"])
    weekdays = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
    months = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")
    stamp = (f"Conversation started: {weekdays[day.weekday()]}, {months[day.month-1]} {day.day:02d}, {day.year}"
             + "\nModel: " + MODEL + "\nProvider: custom")
    system = "\n\n".join((values["DEFAULT_AGENT_IDENTITY"], values["HERMES_AGENT_HELP_GUIDANCE"],
                             environment, values["default_profile"], stamp))
    # Match the pinned SDK's body-field ordering and httpx 0.28.1 JSON encoding.
    raw = json.dumps(dict(messages=[dict(role="system", content=system),
                         dict(role="user", content="MAYA_OFFLINE_MODEL_REQUEST:"+canary)],
                         model=MODEL, max_tokens=32, stream=False),
                         ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    checked_request(raw)
    # Body wrapping must still fit the unchanged coordinator frame budget.
    encode(dict(v=1, type="model_request", attempt=attempt, route="maya.offline.model.v1",
                lease="0"*64, seq=1, method="POST", path="/v1/chat/completions", body=raw.decode("utf-8")))
    return raw
