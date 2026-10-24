"""Native Hermes tool adapter over a bound, non-network Maya bridge channel."""
from __future__ import annotations

import json
import re

from project_maya.bridge.protocol import ProtocolError
from project_maya.bridge.service import RESOURCE
from project_maya.bridge.transport import PrivateChannel

TOOL = "maya_document_read"
SCHEMA = {"name": TOOL, "description": "Read the exact Maya-authorized document.",
          "parameters": {"type": "object", "properties": {"resource": {"type": "string", "enum": [RESOURCE]}},
                         "required": ["resource"], "additionalProperties": False}}


class BridgeClient:
    def __init__(self, channel: PrivateChannel, attempt: str) -> None:
        if type(attempt) is not str or not re.fullmatch(r"[0-9a-f]{32}", attempt):
            raise ProtocolError()
        self.channel, self.attempt = channel, attempt
        self._grant: dict | None = None

    def bind_grant(self, grant: dict) -> None:
        if (set(grant) != {"v", "type", "attempt", "lease", "ttl_ms", "next_seq", "operation", "resource"}
                or type(grant["v"]) is not int or grant["v"] != 1 or grant["type"] != "grant"
                or grant["attempt"] != self.attempt or grant["operation"] != "document.read"
                or grant["resource"] != RESOURCE or type(grant["next_seq"]) is not int
                or not 1 <= grant["next_seq"] <= 16 or type(grant["ttl_ms"]) is not int
                or grant["ttl_ms"] != 2000 or type(grant["lease"]) is not str
                or not re.fullmatch(r"[0-9a-f]{64}", grant["lease"])):
            raise ProtocolError()
        self._grant = grant.copy()

    def request(self) -> dict:
        if self._grant is None:
            raise ProtocolError()
        grant, self._grant = self._grant, None
        return dict(v=1, type="request", attempt=self.attempt, lease=grant["lease"],
                    seq=grant["next_seq"], operation="document.read", resource=RESOURCE)

    def call(self, request: dict) -> dict:
        self.channel.send(request)
        response = self.channel.receive()
        if (set(response) != {"v", "type", "attempt", "seq", "status", "code", "data"}
                or type(response["v"]) is not int or response["v"] != 1 or response["type"] != "response"
                or response["attempt"] != self.attempt or type(response["seq"]) is not int
                or response["seq"] != request["seq"]):
            raise ProtocolError()
        if response["status"] == "ok":
            if (response["code"] != "bridge.document_read" or type(response["data"]) is not dict
                    or set(response["data"]) != {"text"} or type(response["data"]["text"]) is not str
                    or not 1 <= len(response["data"]["text"].encode("utf-8")) <= 1024):
                raise ProtocolError()
        elif (response["status"] != "denied" or response["code"] not in
              ("bridge.denied", "bridge.unavailable", "bridge.uncertain") or response["data"] is not None):
            raise ProtocolError()
        return response

    def handle(self, args: dict, **kwargs) -> str:
        try:
            if type(args) is not dict or args != {"resource": RESOURCE}:
                return '{"error":"bridge.denied"}'
            response = self.call(self.request())
            return json.dumps(response, ensure_ascii=True, separators=(",", ":"))
        except Exception:
            return '{"error":"bridge.unavailable"}'

    def register(self, registry) -> None:
        if registry.get_entry(TOOL) is not None:
            raise ProtocolError()
        registry.register(name=TOOL, toolset="maya_bridge", schema=SCHEMA,
                          handler=self.handle, override=False)
        entry = registry.get_entry(TOOL)
        if entry is None or entry.handler != self.handle or entry.toolset != "maya_bridge":
            raise ProtocolError()
