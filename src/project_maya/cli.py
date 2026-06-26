"""Command-line entry points for minimal Project MAYA operations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .bootstrap import build_local_product
from .config import config_from_mapping, config_to_mapping
from .doctor import DoctorStatus, run_doctor
from .local_api import build_local_api_http_server
from .secrets import (
    SecretRef,
    SecretReferenceError,
    SecretStoreError,
    build_platform_secret_store,
)


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
    rotate_parser = subparsers.add_parser(
        "rotate-secret",
        help="Store or rotate a secret value in the configured platform store.",
    )
    rotate_parser.add_argument(
        "name",
        help="Secret name, for example local-api/token or secret://local-api/token.",
    )
    rotate_parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to a JSON Maya configuration file.",
    )
    rotate_parser.add_argument(
        "--value-stdin",
        action="store_true",
        required=True,
        help="Read the new secret value from standard input.",
    )
    export_parser = subparsers.add_parser(
        "export-config",
        help="Validate and print a normalized Maya configuration.",
    )
    export_parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to a JSON Maya configuration file.",
    )
    import_parser = subparsers.add_parser(
        "import-config",
        help="Validate and optionally write a normalized Maya configuration.",
    )
    import_parser.add_argument(
        "--from",
        dest="from_path",
        type=Path,
        required=True,
        help="Source JSON Maya configuration file.",
    )
    import_parser.add_argument(
        "--to",
        dest="to_path",
        type=Path,
        required=True,
        help="Destination JSON Maya configuration file.",
    )
    import_parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the normalized config. Default is dry-run.",
    )
    import_parser.add_argument(
        "--allow-overwrite",
        action="store_true",
        help="Allow replacing an existing destination when used with --apply.",
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
    if args.command == "rotate-secret":
        return _rotate_secret(args.config, args.name)
    if args.command == "export-config":
        return _export_config(args.config)
    if args.command == "import-config":
        return _import_config(
            args.from_path,
            args.to_path,
            apply=args.apply,
            allow_overwrite=args.allow_overwrite,
        )
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


def _rotate_secret(config_path: Path, name: str) -> int:
    try:
        config = _load_config(config_path)
        ref = _secret_ref_from_name(name)
        value = sys.stdin.read().rstrip("\r\n")
        if not value:
            raise ValueError("secret value is required")
        store = build_platform_secret_store(config.deployment.data_dir)
        store.write(ref, value)
    except (SecretReferenceError, SecretStoreError, ValueError, OSError):
        print(
            json.dumps(
                {
                    "error": {
                        "code": "secret_rotation_failed",
                        "message": "secret rotation failed",
                    }
                },
                sort_keys=True,
            )
        )
        return 1
    print(
        json.dumps(
            {
                "status": "rotated",
                "secret": str(ref),
            },
            sort_keys=True,
        )
    )
    return 0


def _secret_ref_from_name(name: str) -> SecretRef:
    value = name if name.startswith("secret://") else f"secret://{name}"
    return SecretRef.parse(value)


def _export_config(config_path: Path) -> int:
    try:
        config = _load_config(config_path)
        print(_config_json(config))
    except Exception:
        print(
            json.dumps(
                {
                    "error": {
                        "code": "config_export_failed",
                        "message": "config export failed",
                    }
                },
                sort_keys=True,
            )
        )
        return 1
    return 0


def _import_config(
    from_path: Path,
    to_path: Path,
    *,
    apply: bool = False,
    allow_overwrite: bool = False,
) -> int:
    try:
        config = _load_config(from_path)
        normalized = _config_json(config)
        if not apply:
            print(
                json.dumps(
                    {
                        "status": "dry_run",
                        "valid": True,
                        "to": str(to_path),
                    },
                    sort_keys=True,
                )
            )
            return 0
        if to_path.exists() and not allow_overwrite:
            raise FileExistsError("destination exists")
        to_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = to_path.with_suffix(to_path.suffix + ".tmp")
        temporary.write_text(normalized + "\n", encoding="utf-8")
        temporary.replace(to_path)
    except Exception:
        print(
            json.dumps(
                {
                    "error": {
                        "code": "config_import_failed",
                        "message": "config import failed",
                    }
                },
                sort_keys=True,
            )
        )
        return 1
    print(
        json.dumps(
            {
                "status": "imported",
                "to": str(to_path),
            },
            sort_keys=True,
        )
    )
    return 0


def _load_config(config_path: Path):
    return config_from_mapping(json.loads(config_path.read_text(encoding="utf-8")))


def _config_json(config) -> str:
    return json.dumps(config_to_mapping(config), indent=2, sort_keys=True)


def _jsonable(value: Any) -> Any:
    try:
        json.dumps(value)
    except TypeError:
        return str(value)
    return value


if __name__ == "__main__":
    raise SystemExit(main())
