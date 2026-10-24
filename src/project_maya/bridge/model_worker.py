"""Trusted offline worker protocol candidate. Not a provider/network service."""
from __future__ import annotations

import importlib.metadata
import os
from pathlib import Path
import re
import sys

from project_maya.governance import PolicyAuthorizationGateway, PolicyRule

from .audit import RequiredAudit
from .host_files import open_private
from .model_native import native_request
from .model_service import OfflineModelBridge, TARGET, digest
from .protocol import ProtocolError, decode
from .service import HostBinding
from .transport import PrivateChannel


def _command(channel, binding: HostBinding, kind: str, *fields: str) -> dict:
    message = channel.receive()
    if (type(message) is not dict or set(message) != {"v", "type", "attempt", "request_id", *fields}
            or type(message["v"]) is not int or message["v"] != 1 or message["type"] != kind
            or message["attempt"] != binding.attempt or type(message["request_id"]) is not str
            or not re.fullmatch(r"[0-9a-f]{32}", message["request_id"])):
        raise ProtocolError()
    return message


def serve_model(channel: PrivateChannel, config: dict, policy: dict, literals: bytes,
                audit: RequiredAudit, write_expected) -> dict:
    """Only the coordinator owns this endpoint and its delivery confirmations.

    write_expected is a trusted fixed open-existing private-file writer, never
    a child-specified path. No native case matrix/VM invocation is authorized
    merely by this protocol candidate. A failure terminates this worker attempt.
    """
    if (type(config) is not dict or set(config) !=
            {"operator_sid", "attempt", "channel_id", "utc_day", "canary", "fixture_text"}
            or type(config["fixture_text"]) is not str
            or not re.fullmatch(r"MAYA_OFFLINE_MODEL_OK:[0-9a-f]{32}", config["fixture_text"])):
        raise ProtocolError()
    binding = HostBinding(config["operator_sid"], config["attempt"], config["channel_id"])
    expected_rules = [dict(capability=cap, target=TARGET, operation=operation,
                           actor_id="windows:"+binding.operator_sid)
                      for cap, operation in (("model.egress", "infer"), ("model.output", "disclose"))]
    if policy != {"allow": expected_rules}:
        raise ProtocolError()
    expected = native_request(literals, binding.attempt, config["utc_day"], config["canary"])
    count = write_expected(expected)
    if type(count) is not int or count != len(expected):
        raise ProtocolError()
    service = OfflineModelBridge(binding, PolicyAuthorizationGateway(tuple(PolicyRule(**rule) for rule in expected_rules)),
                                 audit, expected, config["fixture_text"])
    seen = set()

    def command(kind, *fields):
        message = _command(channel, binding, kind, *fields)
        if message["request_id"] in seen:
            raise ProtocolError()
        seen.add(message["request_id"])
        return message

    def send(kind, command_id, **values):
        channel.send(dict(v=1, type=kind, attempt=binding.attempt, request_id=command_id, **values))

    try:
        channel.send(dict(v=1, type="model_worker_ready", attempt=binding.attempt, pid=os.getpid(),
                          request_sha256=digest(expected), request_bytes=len(expected),
                          service_request_id=service.request_id, real_inference=False))
        message = command("model_issue")
        send("model_grant_reply", message["request_id"], grant=service.issue())
        message = command("model_dispatch", "request")
        reply = service.prepare_runtime(message["request"], binding.channel_id)
        send("model_dispatch_reply", message["request_id"], response=reply,
             dispatches=service.dispatches, prepared_runtime_releases=service.prepared_runtime_releases,
             confirmed_runtime_releases=service.confirmed_runtime_releases)
        message = command("model_runtime_delivered", "response_sha256")
        service.confirm_runtime_delivery(message["response_sha256"], message["request_id"])
        send("model_runtime_ack", message["request_id"], confirmed_runtime_releases=service.confirmed_runtime_releases)
        message = command("model_prepare_final", "text")
        text = service.prepare_operator(message["text"])
        send("model_final_prepared", message["request_id"], text=text,
             prepared_operator_releases=service.prepared_operator_releases,
             confirmed_operator_releases=service.confirmed_operator_releases)
        message = command("model_operator_delivered", "text_sha256")
        service.confirm_operator_delivery(message["text_sha256"], message["request_id"])
        send("model_operator_ack", message["request_id"], confirmed_operator_releases=service.confirmed_operator_releases)
        message = command("model_shutdown")
        result = dict(dispatches=service.dispatches, confirmed_runtime_releases=service.confirmed_runtime_releases,
                      confirmed_operator_releases=service.confirmed_operator_releases, real_inference=False)
        send("model_worker_complete", message["request_id"], effects=result)
        return result
    finally:
        service.close()


def main() -> int:
    if (os.name != "nt" or sys.version_info[:3] != (3, 13, 14) or not all(
            (sys.flags.isolated, sys.flags.no_site, sys.flags.dont_write_bytecode))):
        return 2
    root = Path.cwd()
    try:
        runtime = Path(__file__).resolve().parents[2]
        if root != runtime.parent / "host" or runtime.name != "runtime":
            raise ProtocolError()
        for name, version in (("cryptography", "46.0.7"), ("cffi", "2.0.0"), ("pycparser", "3.0")):
            dist = importlib.metadata.distribution(name)
            if dist.version != version or not Path(dist.locate_file("")).resolve().is_relative_to(runtime):
                raise ProtocolError()
        from project_maya import broker
        if broker.Ed25519PrivateKey is None or "run_agent" in sys.modules or "openai" in sys.modules:
            raise ProtocolError()
        with open_private(root/"worker.json", root, limit=8192) as stream:
            config = decode(stream.read(8193))
        with open_private(root/"policy.json", root, limit=8192) as stream:
            policy = decode(stream.read(8193))
        literals = (runtime/"model-native-literals.json").read_bytes()

        def write_expected(raw):
            with open_private(root/"request.json", root, writable=True, limit=0) as stream:
                count = stream.write(raw)
                if count != len(raw):
                    raise ProtocolError()
                stream.flush(); os.fsync(stream.fileno())
                return count

        with open_private(root/"audit.jsonl", root, writable=True, limit=0) as stream:
            serve_model(PrivateChannel(sys.stdin.buffer, sys.stdout.buffer), config, policy, literals,
                        RequiredAudit(stream), write_expected)
        return 0
    except Exception:
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
