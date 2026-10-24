"""Private trusted worker entry. No listening socket, Hermes or model imports."""
from __future__ import annotations

import json
import importlib.metadata
import os
from pathlib import Path
import re
import sys

from project_maya.governance import PolicyAuthorizationGateway, PolicyRule

from .audit import RequiredAudit
from .host_files import HostDocument, open_private
from .protocol import ProtocolError, decode
from .service import BridgeDenied, DocumentBridge, HostBinding
from .transport import PrivateChannel

CASES = ("N01", "N02", "N03", "N04", "N05", "N06", "N07", "N08", "N10", "N12")


def _shape(message: dict, fields: set[str], kind: str, attempt: str) -> None:
    if (set(message) != fields or type(message.get("v")) is not int or message["v"] != 1
            or message.get("type") != kind or message.get("attempt") != attempt):
        raise ProtocolError()


def serve(channel: PrivateChannel, root: Path, config: dict, audit: RequiredAudit) -> int:
    """Only the coordinator owns this channel and its fixed case schedule."""
    if (set(config) != {"operator_sid", "attempt", "channel_id", "document_sha256"}
            or not all(type(value) is str for value in config.values())
            or not re.fullmatch(r"[0-9a-f]{64}", config["document_sha256"])):
        raise ProtocolError()
    binding = HostBinding(config["operator_sid"], config["attempt"], config["channel_id"])
    policy_path = root / "policy.json"
    # Required private path/handle verification precedes the existing loader.
    # The directory ACL prevents child replacement between verification and load.
    with open_private(policy_path, root, limit=8192) as stream:
        policy_bytes = stream.read(8193)
        policy = decode(policy_bytes)
    expected_rules = [dict(capability="file.read", target="maya.synthetic.document.v1", operation="read",
                           actor_id="windows:" + binding.operator_sid),
                      dict(capability="file.disclose", target="runtime:" + binding.attempt,
                           operation="release", actor_id="windows:" + binding.operator_sid)]
    if policy != {"allow": expected_rules}:
        raise ProtocolError()
    gateway = PolicyAuthorizationGateway(tuple(PolicyRule(**rule) for rule in policy["allow"]))
    document = HostDocument(root, config["document_sha256"])
    service = DocumentBridge(binding, gateway, audit, document.read)
    original_gateway = gateway
    channel.send(dict(v=1, type="ready", attempt=binding.attempt, pid=os.getpid()))
    results = []
    try:
        for case in CASES:
            command = channel.receive()
            _shape(command, {"v", "type", "attempt", "request_id", "case"}, "issue", binding.attempt)
            if command["case"] != case or not re.fullmatch(r"[0-9a-f]{32}", command["request_id"]):
                raise ProtocolError()
            # These are exact host schedule fixtures, not runtime-controlled
            # policy changes or an alternate policy engine.
            if case in ("N03", "N10"):
                service._gateway = PolicyAuthorizationGateway(tuple(
                    rule for rule in tuple(PolicyRule(**item) for item in expected_rules)
                    if case == "N10" and rule.capability == "file.read"))
            else:
                service._gateway = original_gateway
            grant = service.issue()
            if case == "N08":
                service.revoke()
            channel.send(dict(v=1, type="grant_reply", attempt=binding.attempt,
                              request_id=command["request_id"], grant=grant))
            before = (document.opens, service.reads, service.sent, service.bytes_sent)
            message = channel.receive()
            if case == "N02":
                _shape(message, {"v", "type", "attempt", "request_id"}, "no_request", binding.attempt)
                if message["request_id"] != command["request_id"]:
                    raise ProtocolError()
                service.revoke()
                response = None
            else:
                _shape(message, {"v", "type", "attempt", "request_id", "request"}, "dispatch", binding.attempt)
                if message["request_id"] != command["request_id"]:
                    raise ProtocolError()
                frames = []
                try:
                    def collect(raw):
                        frames.append(raw)
                        return len(raw)
                    service.handle(message["request"], binding.channel_id, collect)
                    from .protocol import Decoder
                    decoder = Decoder()
                    parsed = decoder.feed(frames[0])
                    decoder.eof()
                    if len(parsed) != 1:
                        raise ProtocolError()
                    response = parsed[0]
                except BridgeDenied as error:
                    response = dict(v=1, type="response", attempt=binding.attempt,
                                    seq=grant["next_seq"], status="denied", code=error.code, data=None)
            after = (document.opens, service.reads, service.sent, service.bytes_sent)
            delta = [end-start for start, end in zip(before, after)]
            results.append(dict(case=case, opens=delta[0], reads=delta[1],
                                prepared_releases=delta[2], prepared_content_bytes=delta[3]))
            channel.send(dict(v=1, type="dispatch_reply", attempt=binding.attempt,
                              request_id=command["request_id"], response=response, effects=results[-1]))
            observed = channel.receive()
            _shape(observed, {"v","type","attempt","request_id","case","delivered"}, "delivery_result", binding.attempt)
            if (observed["request_id"] != command["request_id"] or observed["case"] != case or
                    type(observed["delivered"]) is not bool or observed["delivered"] != (case == "N01")):
                raise ProtocolError()
            service.delivery_observed(observed["delivered"], command["request_id"])
            channel.send(dict(v=1,type="delivery_ack",attempt=binding.attempt,request_id=command["request_id"]))
        message = channel.receive()
        _shape(message, {"v", "type", "attempt"}, "shutdown", binding.attempt)
        channel.send(dict(v=1, type="worker_complete", attempt=binding.attempt, results=results))
        return 0
    finally:
        service.close()


def main() -> int:
    if os.name != "nt" or sys.version_info[:3] != (3, 13, 14) or not all(
            (sys.flags.isolated, sys.flags.no_site, sys.flags.dont_write_bytecode)):
        return 2
    root = Path.cwd()
    try:
        runtime = Path(__file__).resolve().parents[2]
        if root != runtime.parent / 'host' or runtime.name != 'runtime':
            raise ProtocolError()
        for name, expected in (('cryptography','46.0.7'),('cffi','2.0.0'),('pycparser','3.0')):
            distribution = importlib.metadata.distribution(name)
            if distribution.version != expected or not Path(distribution.locate_file('')).resolve().is_relative_to(runtime):
                raise ProtocolError()
        from project_maya import broker
        if broker.Ed25519PrivateKey is None or 'run_agent' in sys.modules or 'openai' in sys.modules:
            raise ProtocolError()
        with open_private(root / "worker.json", root, limit=8192) as stream:
            config = decode(stream.read(8193))
        with open_private(root / "audit.jsonl", root, writable=True, limit=0) as stream:
            return serve(PrivateChannel(sys.stdin.buffer, sys.stdout.buffer), root, config, RequiredAudit(stream))
    except Exception:
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
