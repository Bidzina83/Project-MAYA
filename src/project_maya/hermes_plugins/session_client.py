"""Explicit source-candidate CLI over the authenticated bound Local API."""
from __future__ import annotations

import argparse
from http.client import HTTPConnection
from ipaddress import ip_address
import json
from pathlib import Path
import re
import sys
from typing import Mapping

from ..config import MayaConfig, config_from_mapping
from .governance import _checked_payload
from .session_requests import ACKNOWLEDGEMENT, REQUEST_BINDING_CONTRACT

MAX_RESPONSE_BYTES = 1_048_576


class CandidateSessionClientError(RuntimeError):
    """Fixed client failure; never interpolate tokens, payloads or exceptions."""

    def __init__(self, code: str) -> None:
        allowed = {"acknowledgement_required", "loopback_endpoint_required", "invalid_local_api_token",
                   "invalid_request", "request_too_large", "request_rejected", "response_rejected",
                   "binding_required", "request_failed", "invalid_arguments"}
        super().__init__(code if code in allowed else "request_failed")


def run_authenticated_cli_request(config: MayaConfig, *, token: str, message: str,
                                  acknowledgement: str) -> object:
    if acknowledgement != ACKNOWLEDGEMENT:
        raise CandidateSessionClientError("acknowledgement_required")
    try:
        config.validate()
        host = config.local_api.bind
        host = "127.0.0.1" if host == "localhost" else host
        port = config.local_api.port
        if (config.local_api.remote_access or not ip_address(host).is_loopback
                or type(port) is not int or not 1 <= port <= 65535):
            raise ValueError
    except Exception:
        raise CandidateSessionClientError("loopback_endpoint_required") from None
    if (not isinstance(token, str) or not 1 <= len(token) <= 4096
            or not re.fullmatch(r"[A-Za-z0-9._~+/-]+={0,2}", token)):
        raise CandidateSessionClientError("invalid_local_api_token")
    if not isinstance(message, str) or not message.strip():
        raise CandidateSessionClientError("invalid_request")
    body = json.dumps({"input": message}).encode("utf-8")
    if len(body) > 65536:
        raise CandidateSessionClientError("request_too_large")
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json",
               "X-Maya-Session-Binding": REQUEST_BINDING_CONTRACT}

    def exchange(method: str, path: str, payload: bytes | None = None) -> Mapping[str, object]:
        # HTTPConnection has no proxy discovery, redirects or automatic retries.
        connection = HTTPConnection(host, port, timeout=5)
        try:
            connection.request(method, path, body=payload, headers=headers)
            response = connection.getresponse()
            if response.status != 200:
                raise CandidateSessionClientError("request_rejected")
            data = response.read(MAX_RESPONSE_BYTES + 1)
            if len(data) > MAX_RESPONSE_BYTES or token.encode() in data:
                raise CandidateSessionClientError("response_rejected")
            parsed = json.loads(data)
            pending = [parsed]
            while pending:
                item = pending.pop()
                if isinstance(item, str) and token in item:
                    raise CandidateSessionClientError("response_rejected")
                if isinstance(item, Mapping):
                    pending.extend(item.keys())
                    pending.extend(item.values())
                elif isinstance(item, list):
                    pending.extend(item)
            if (not isinstance(parsed, Mapping)
                    or parsed.get("session_binding_contract") != REQUEST_BINDING_CONTRACT
                    or parsed.get("qualification") != "source_candidate_only"):
                raise CandidateSessionClientError("binding_required")
            _checked_payload(parsed)
            return parsed
        except CandidateSessionClientError:
            raise
        except Exception:
            raise CandidateSessionClientError("request_failed") from None
        finally:
            connection.close()

    exchange("GET", "/v1/session-binding")
    result = exchange("POST", "/v1/run", body)
    if "result" not in result:
        raise CandidateSessionClientError("response_rejected")
    return result["result"]


class _SafeParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CandidateSessionClientError("invalid_arguments")


def main(argv: list[str] | None = None) -> int:
    parser = _SafeParser(description="Source-candidate authenticated Maya CLI; not production qualification")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--request-file", type=Path, required=True)
    parser.add_argument("--api-token-stdin", action="store_true", required=True)
    parser.add_argument("--acknowledge", choices=[ACKNOWLEDGEMENT], required=True)
    try:
        args = parser.parse_args(argv)
        config = config_from_mapping(json.loads(args.config.read_text(encoding="utf-8-sig")))
        token = sys.stdin.readline(4098).rstrip("\r\n")
        message = args.request_file.read_text(encoding="utf-8-sig")
        result = run_authenticated_cli_request(config, token=token, message=message,
                                                acknowledgement=args.acknowledge)
        print(json.dumps({"result": result, "qualification": "source_candidate_only", "production_qualified": False}))
        return 0
    except CandidateSessionClientError as error:
        print(json.dumps({"status": "blocked", "reason_code": str(error)}))
    except Exception:
        print(json.dumps({"status": "blocked", "reason_code": "request_failed"}))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
