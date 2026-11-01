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
from .model_service import ModelDenied, OfflineModelBridge, TARGET, digest
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
                audit: RequiredAudit, write_expected, *, deny_egress: bool = False, wrong_model: bool = False,
                startup=None, wrong_route: bool = False, wrong_attempt: bool = False, wrong_body: bool = False, expire_grant: bool = False, revoke_grant: bool = False, replay_grant: bool = False, same_client_budget: bool = False, recreated_client_budget: bool = False) -> dict:
    """Only the coordinator owns this endpoint and its delivery confirmations.

    write_expected is a trusted fixed open-existing private-file writer, never
    a child-specified path. No native case matrix/VM invocation is authorized
    merely by this protocol candidate. A failure terminates this worker attempt.
    """
    if startup is not None: startup.mark('service_config')
    if (any(type(mode) is not bool for mode in (deny_egress, wrong_model, wrong_route, wrong_attempt, wrong_body, expire_grant, revoke_grant, replay_grant, same_client_budget, recreated_client_budget))
            or sum((deny_egress, wrong_model, wrong_route, wrong_attempt, wrong_body, expire_grant, revoke_grant, replay_grant, same_client_budget, recreated_client_budget)) > 1
            or type(config) is not dict or set(config) !=
            {"operator_sid", "attempt", "channel_id", "utc_day", "canary", "fixture_text"}
            or type(config["fixture_text"]) is not str
            or not re.fullmatch(r"MAYA_OFFLINE_MODEL_OK:[0-9a-f]{32}", config["fixture_text"])):
        raise ProtocolError()
    binding = HostBinding(config["operator_sid"], config["attempt"], config["channel_id"])
    expected_rules = [dict(capability=cap, target=TARGET, operation=operation,
                           actor_id="windows:"+binding.operator_sid)
                      for cap, operation in (("model.egress", "infer"), ("model.output", "disclose"))]
    if deny_egress:
        expected_rules = expected_rules[1:]
    if policy != {"allow": expected_rules}:
        raise ProtocolError()
    if startup is not None: startup.mark('request_build')
    expected = native_request(literals, binding.attempt, config["utc_day"], config["canary"])
    count = write_expected(expected)
    if startup is not None: startup.mark('request_write_checked')
    if type(count) is not int or count != len(expected):
        raise ProtocolError()
    service_type = OfflineModelBridge
    if wrong_model:
        if startup is not None: startup.mark('service_import')
        from .model_validation import WrongModelBridge
        service_type = WrongModelBridge
    if wrong_route:
        if startup is not None: startup.mark('service_import')
        from .model_route_validation import WrongRouteBridge
        service_type = WrongRouteBridge
    if wrong_attempt:
        if startup is not None: startup.mark('service_import')
        from .model_attempt_validation import WrongAttemptBridge
        service_type = WrongAttemptBridge
    if wrong_body:
        if startup is not None: startup.mark('service_import')
        from .model_body_validation import WrongBodyBridge
        service_type = WrongBodyBridge
    if expire_grant:
        if startup is not None: startup.mark('service_import')
        from .model_lease_expiry import ExpiredGrantBridge
        service_type = ExpiredGrantBridge
    if revoke_grant:
        if startup is not None: startup.mark('service_import')
        from .model_lease_revocation import RevokedGrantBridge
        service_type = RevokedGrantBridge
    if replay_grant:
        if startup is not None: startup.mark('service_import')
        from .model_lease_replay import ConsumedGrantBridge
        service_type = ConsumedGrantBridge
    if startup is not None: startup.mark('service_construct')
    service = service_type(binding, PolicyAuthorizationGateway(tuple(PolicyRule(**rule) for rule in expected_rules)),
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
        if startup is not None: startup.mark('ready_send')
        channel.send(dict(v=1, type="model_worker_ready", attempt=binding.attempt, pid=os.getpid(),
                          request_sha256=digest(expected), request_bytes=len(expected),
                          service_request_id=service.request_id, real_inference=False))
        if startup is not None: startup.mark('ready_sent')
        message = command("model_issue")
        send("model_grant_reply", message["request_id"], grant=service.issue())
        if revoke_grant:
            message = command("model_revoke", "lease")
            evidence = service.revoke_issued(message["lease"], message["request_id"])
            send("model_revoke_ack", message["request_id"], evidence=evidence)
        message = command("model_dispatch", "request")
        if replay_grant:
            service.bind_first(message["request_id"])
        if wrong_model or wrong_route or wrong_attempt or wrong_body or expire_grant or revoke_grant:
            service.bind_command(message["request_id"])
        try:
            reply = service.prepare_runtime(message["request"], binding.channel_id)
        except ModelDenied:
            if revoke_grant:
                evidence = service.evidence()
                send("model_lease_revoked", message["request_id"], evidence=evidence)
                return evidence
            if expire_grant:
                evidence = service.evidence()
                send("model_lease_expired", message["request_id"], evidence=evidence)
                return evidence
            if wrong_body:
                evidence = service.evidence()
                send("model_body_rejected", message["request_id"], evidence=evidence)
                return evidence
            if wrong_attempt:
                evidence = service.evidence()
                send("model_attempt_rejected", message["request_id"], evidence=evidence)
                return evidence
            if wrong_route:
                evidence = service.evidence()
                send("model_route_rejected", message["request_id"], evidence=evidence)
                return evidence
            if wrong_model:
                evidence = service.evidence()
                send("model_validation_rejected", message["request_id"], evidence=evidence)
                return evidence
            if not deny_egress:
                raise
            from .model_denial import denial_evidence
            effects = denial_evidence(service, audit)
            send("model_egress_denied", message["request_id"], effects=effects)
            return effects
        if deny_egress or wrong_model or wrong_route or wrong_attempt or wrong_body or expire_grant or revoke_grant:
            raise ProtocolError()
        send("model_dispatch_reply", message["request_id"], response=reply,
             dispatches=service.dispatches, prepared_runtime_releases=service.prepared_runtime_releases,
             confirmed_runtime_releases=service.confirmed_runtime_releases)
        message = command("model_runtime_delivered", "response_sha256")
        delivery_age = service.confirm_runtime_delivery(message["response_sha256"], message["request_id"])
        if replay_grant:
            send("model_runtime_ack", message["request_id"], confirmed_runtime_releases=service.confirmed_runtime_releases,
                 delivery_elapsed_ms=delivery_age)
            message = command("model_dispatch", "request")
            service.bind_replay(message["request_id"])
            try:
                service.prepare_runtime(message["request"], binding.channel_id)
            except ModelDenied:
                evidence = service.evidence()
                send("model_lease_consumed", message["request_id"], evidence=evidence)
                return evidence
            raise ProtocolError()
        send("model_runtime_ack", message["request_id"], confirmed_runtime_releases=service.confirmed_runtime_releases)
        if same_client_budget or recreated_client_budget:
            from .model_adapter_budget import finish_adapter_budget
            delivery_id = message["request_id"]
            message = command("model_adapter_finish", "delivery_command_id")
            if message["delivery_command_id"] != delivery_id:
                raise ProtocolError()
            effects = finish_adapter_budget(service, delivery_id)
            if recreated_client_budget:
                effects = dict(effects, case="M05b")
            send("model_adapter_complete", message["request_id"], effects=effects)
            return effects
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


def main(*, deny_egress: bool = False, wrong_model: bool = False, startup=None, wrong_route: bool = False, wrong_attempt: bool = False, wrong_body: bool = False, expire_grant: bool = False, revoke_grant: bool = False, replay_grant: bool = False, same_client_budget: bool = False, recreated_client_budget: bool = False) -> int:
    if startup is not None: startup.mark('worker_preflight')
    if (os.name != "nt" or sys.version_info[:3] != (3, 13, 14) or not all(
            (sys.flags.isolated, sys.flags.no_site, sys.flags.dont_write_bytecode))):
        if startup is not None: startup.fail()
        return 2
    if startup is not None: startup.mark('worker_root')
    root = Path.cwd()
    try:
        runtime = Path(__file__).resolve().parents[2]
        if root != runtime.parent / "host" or runtime.name != "runtime":
            raise ProtocolError()
        if startup is not None: startup.mark('dependency_readback')
        for name, version in (("cryptography", "46.0.7"), ("cffi", "2.0.0"), ("pycparser", "3.0")):
            dist = importlib.metadata.distribution(name)
            if dist.version != version or not Path(dist.locate_file("")).resolve().is_relative_to(runtime):
                raise ProtocolError()
        if startup is not None: startup.mark('canonical_preflight')
        from project_maya import broker
        if broker.Ed25519PrivateKey is None or "run_agent" in sys.modules or "openai" in sys.modules:
            raise ProtocolError()
        if startup is not None: startup.mark('config_read')
        with open_private(root/"worker.json", root, limit=8192) as stream:
            config = decode(stream.read(8193))
        if startup is not None: startup.mark('policy_read')
        with open_private(root/"policy.json", root, limit=8192) as stream:
            policy = decode(stream.read(8193))
        if startup is not None: startup.mark('literals_read')
        literals = (runtime/"model-native-literals.json").read_bytes()

        def write_expected(raw):
            if startup is not None: startup.mark('request_open')
            with open_private(root/"request.json", root, writable=True, limit=0) as stream:
                if startup is not None: startup.mark('request_write')
                count = stream.write(raw)
                if count != len(raw):
                    raise ProtocolError()
                if startup is not None: startup.mark('request_flush')
                stream.flush()
                if startup is not None: startup.mark('request_sync')
                os.fsync(stream.fileno())
                if startup is not None: startup.mark('request_close')
            return count

        if startup is not None: startup.mark('audit_open')
        with open_private(root/"audit.jsonl", root, writable=True, limit=0) as stream:
            serve_model(PrivateChannel(sys.stdin.buffer, sys.stdout.buffer), config, policy, literals,
                        RequiredAudit(stream), write_expected, deny_egress=deny_egress, wrong_model=wrong_model,
                        wrong_route=wrong_route, wrong_attempt=wrong_attempt, wrong_body=wrong_body, expire_grant=expire_grant, revoke_grant=revoke_grant, replay_grant=replay_grant, same_client_budget=same_client_budget, recreated_client_budget=recreated_client_budget, startup=startup)
        return 0
    except Exception as error:
        if startup is not None: startup.fail(error)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
