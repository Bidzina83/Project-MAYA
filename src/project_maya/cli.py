"""Command-line entry points for minimal Project MAYA operations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .bootstrap import build_local_product
from .config import config_from_mapping
from .doctor import DoctorStatus, run_doctor
from .local_api import build_local_api_http_server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="maya")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor_parser = subparsers.add_parser("doctor", help="Validate local Maya setup")
    doctor_parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to a JSON Maya configuration file.",
    )
    run_parser = subparsers.add_parser(
        "run",
        help="Run one request through the local Maya runtime.",
    )
    run_parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to a JSON Maya configuration file.",
    )
    run_parser.add_argument(
        "--input",
        required=True,
        help="Input text to send through the governed Maya runtime.",
    )
    run_parser.add_argument(
        "--idempotency-key",
        default=None,
        help="Optional idempotency key for the governed runtime request.",
    )
    run_parser.add_argument(
        "--data-classification",
        default="internal",
        help="Data classification label for governance and model-egress audit.",
    )
    serve_parser = subparsers.add_parser(
        "serve-local-api",
        help="Serve the authenticated local Maya API on configured loopback.",
    )
    serve_parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to a JSON Maya configuration file.",
    )

    args = parser.parse_args(argv)
    if args.command == "doctor":
        return _doctor(args.config)
    if args.command == "run":
        return _run(
            args.config,
            args.input,
            args.idempotency_key,
            args.data_classification,
        )
    if args.command == "serve-local-api":
        return _serve_local_api(args.config)
    parser.error(f"unknown command: {args.command}")
    return 2


def _doctor(config_path: Path) -> int:
    config = _load_config(config_path)
    try:
        product = build_local_product(config)
    except Exception as exc:
        print(f"{DoctorStatus.FAIL.value}\truntime.assembly\t{exc}")
        return 1
    report = run_doctor(
        config,
        product.runtime,
        lifecycle_state=product.agent.state,
        secret_store=product.secret_store,
    )
    for check in report.checks:
        print(f"{check.status.value}\t{check.name}\t{check.message}")
    return 0 if report.healthy else 1


def _run(
    config_path: Path,
    input_text: str,
    idempotency_key: str | None = None,
    data_classification: str = "internal",
) -> int:
    config = _load_config(config_path)
    try:
        with build_local_product(config) as product:
            result = product.run(
                input_text,
                idempotency_key=idempotency_key,
                data_classification=data_classification,
            )
    except Exception:
        print(
            json.dumps(
                {
                    "error": {
                        "code": "runtime_failed",
                        "message": "request failed",
                    }
                },
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps({"result": _jsonable(result)}, sort_keys=True))
    return 0


def _serve_local_api(config_path: Path) -> int:
    config = _load_config(config_path)
    try:
        with build_local_product(config) as product:
            server = build_local_api_http_server(
                product.local_api,
                bind=config.local_api.bind,
                port=config.local_api.port or 0,
                remote_access=config.local_api.remote_access,
            )
            try:
                print(
                    json.dumps(
                        {
                            "status": "listening",
                            "bind": config.local_api.bind,
                            "port": server.server_port,
                        },
                        sort_keys=True,
                    )
                )
                server.serve_forever()
            except KeyboardInterrupt:
                return 0
            finally:
                server.server_close()
    except Exception:
        print(
            json.dumps(
                {
                    "error": {
                        "code": "local_api_failed",
                        "message": "local API failed",
                    }
                },
                sort_keys=True,
            )
        )
        return 1
    return 0


def _load_config(config_path: Path):
    return config_from_mapping(json.loads(config_path.read_text(encoding="utf-8")))


def _jsonable(value: Any) -> Any:
    try:
        json.dumps(value)
    except TypeError:
        return str(value)
    return value


if __name__ == "__main__":
    raise SystemExit(main())
