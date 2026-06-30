"""Command-line entry points for minimal Project MAYA operations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .backup import BackupError, RestoreError, create_local_backup, restore_local_backup
from .bootstrap import build_local_product
from .config import config_from_mapping, config_to_mapping
from .doctor import DoctorStatus, run_doctor
from .integrations import IntegrationResetError, reset_integration_state
from .local_api import build_local_api_http_server
from .repair import RepairError, repair_local_state
from .secrets import (
    SecretRef,
    SecretReferenceError,
    SecretStoreError,
    build_platform_secret_store,
)
from .update import UpdateError, check_updates, rollback_update


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
    repair_parser = subparsers.add_parser(
        "repair",
        help="Plan or apply safe local Maya state repairs.",
    )
    repair_parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to a JSON Maya configuration file.",
    )
    repair_parser.add_argument(
        "--apply",
        action="store_true",
        help="Create missing local state directories. Default is dry-run.",
    )
    reset_integration_parser = subparsers.add_parser(
        "reset-integration",
        help="Plan or apply a local integration state reset.",
    )
    reset_integration_parser.add_argument(
        "name",
        help="Configured integration name to reset, for example google.",
    )
    reset_integration_parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to a JSON Maya configuration file.",
    )
    reset_mode = reset_integration_parser.add_mutually_exclusive_group()
    reset_mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan the reset without deleting local state. This is the default.",
    )
    reset_mode.add_argument(
        "--apply",
        action="store_true",
        help="Delete local integration state. Provider tokens are not revoked.",
    )
    reset_integration_parser.add_argument(
        "--revoke-provider",
        action="store_true",
        help=(
            "Request provider-token revocation. Reports unavailable until a "
            "provider-specific revoker exists."
        ),
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
    backup_parser = subparsers.add_parser(
        "backup",
        help="Create a local backup archive of Maya state.",
    )
    backup_parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to a JSON Maya configuration file.",
    )
    backup_parser.add_argument(
        "--to",
        dest="destination",
        type=Path,
        default=None,
        help="Optional explicit backup archive path.",
    )
    restore_parser = subparsers.add_parser(
        "restore",
        help="Validate and optionally restore a local Maya backup archive.",
    )
    restore_parser.add_argument(
        "--from",
        dest="archive_path",
        type=Path,
        required=True,
        help="Backup archive to restore.",
    )
    restore_parser.add_argument(
        "--to",
        dest="destination",
        type=Path,
        required=True,
        help="Destination Maya data directory.",
    )
    restore_parser.add_argument(
        "--apply",
        action="store_true",
        help="Write restored files. Default is dry-run.",
    )
    restore_parser.add_argument(
        "--allow-overwrite",
        action="store_true",
        help="Allow replacing existing destination files when used with --apply.",
    )
    migrate_parser = subparsers.add_parser(
        "migrate",
        help="Migrate legacy memory storage with dry-run safety defaults.",
    )
    migrate_parser.add_argument(
        "--from",
        dest="from_src",
        type=Path,
        required=True,
        help="Legacy SQLite database containing memory_kv.",
    )
    migrate_parser.add_argument(
        "--to",
        dest="to_dest",
        type=Path,
        required=True,
        help="Destination SQLite database.",
    )
    migrate_parser.add_argument(
        "--target-schema",
        choices=("memory_entries", "registry"),
        default="registry",
        help="Destination schema shape.",
    )
    migrate_mode = migrate_parser.add_mutually_exclusive_group()
    migrate_mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate migration without writing. This is the default.",
    )
    migrate_mode.add_argument(
        "--apply",
        action="store_true",
        help="Apply migration. Default is dry-run.",
    )
    migrate_parser.add_argument(
        "--allow-modify",
        action="store_true",
        help="Required with --apply to acknowledge destination writes.",
    )
    migrate_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing destination rows. Requires explicit backup handling.",
    )
    migrate_parser.add_argument(
        "--backup",
        dest="backup_path",
        type=Path,
        default=None,
        help="Backup path required when applying to an existing destination.",
    )
    migrate_parser.add_argument(
        "--report",
        dest="report_path",
        type=Path,
        default=None,
        help="Optional migration report path.",
    )
    update_parser = subparsers.add_parser(
        "update",
        help="Inspect local update and rollback readiness.",
    )
    update_parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to a JSON Maya configuration file.",
    )
    update_mode = update_parser.add_mutually_exclusive_group(required=True)
    update_mode.add_argument(
        "--check",
        action="store_true",
        help="Check local signed update metadata without network access.",
    )
    update_mode.add_argument(
        "--rollback",
        action="store_true",
        help="Check local signed rollback metadata without changing files.",
    )

    args = parser.parse_args(argv)
    if args.command == "doctor":
        return _doctor(args.config)
    if args.command == "repair":
        return _repair(args.config, apply=args.apply)
    if args.command == "reset-integration":
        return _reset_integration(
            args.config,
            args.name,
            apply=args.apply,
            revoke_provider=args.revoke_provider,
        )
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
    if args.command == "backup":
        return _backup(args.config, args.destination)
    if args.command == "restore":
        return _restore(
            args.archive_path,
            args.destination,
            apply=args.apply,
            allow_overwrite=args.allow_overwrite,
        )
    if args.command == "migrate":
        return _migrate(
            args.from_src,
            args.to_dest,
            target_schema=args.target_schema,
            dry_run=args.dry_run or not args.apply,
            allow_modify=args.allow_modify,
            overwrite=args.overwrite,
            backup_path=args.backup_path,
            report_path=args.report_path,
        )
    if args.command == "update":
        return _update(args.config, rollback=args.rollback)
    parser.error(f"unknown command: {args.command}")
    return 2


def _doctor(config_path: Path) -> int:
    try:
        config = _load_config(config_path)
    except Exception:
        print(f"{DoctorStatus.FAIL.value}\tconfig\tconfiguration invalid")
        return 1
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


def _repair(config_path: Path, *, apply: bool = False) -> int:
    try:
        config = _load_config(config_path)
        result = repair_local_state(config, apply=apply)
    except (RepairError, OSError, ValueError):
        print(
            json.dumps(
                {
                    "error": {
                        "code": "repair_failed",
                        "message": "repair failed",
                    }
                },
                sort_keys=True,
            )
        )
        return 1
    print(
        json.dumps(
            {
                "status": "dry_run" if result.dry_run else "repaired",
                "actions": [
                    {
                        "action": action.action,
                        "path": str(action.path),
                        "status": action.status,
                    }
                    for action in result.actions
                ],
            },
            sort_keys=True,
        )
    )
    return 0


def _reset_integration(
    config_path: Path,
    name: str,
    *,
    apply: bool = False,
    revoke_provider: bool = False,
) -> int:
    try:
        config = _load_config(config_path)
        result = reset_integration_state(
            config,
            name,
            apply=apply,
            revoke_provider=revoke_provider,
        )
    except (IntegrationResetError, OSError, ValueError):
        print(
            json.dumps(
                {
                    "error": {
                        "code": "integration_reset_failed",
                        "message": "integration reset failed",
                    }
                },
                sort_keys=True,
            )
        )
        return 1
    print(
        json.dumps(
            {
                "status": "dry_run" if result.dry_run else "reset",
                "integration": result.name,
                "local_state_path": str(result.local_state_path),
                "local_state_exists": result.local_state_exists,
                "files": result.files,
                "credential_ref_present": result.credential_ref_present,
                "external_revocation_performed": (
                    result.external_revocation_performed
                ),
                "provider_revocation_requested": (
                    result.provider_revocation_requested
                ),
                "provider_revocation_status": (
                    result.provider_revocation_status.value
                ),
                "provider_revocation_reason": result.provider_revocation_reason,
            },
            sort_keys=True,
        )
    )
    return 0


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


def _backup(config_path: Path, destination: Path | None = None) -> int:
    try:
        config = _load_config(config_path)
        result = create_local_backup(config, destination=destination)
    except (BackupError, OSError, ValueError):
        print(
            json.dumps(
                {
                    "error": {
                        "code": "backup_failed",
                        "message": "backup failed",
                    }
                },
                sort_keys=True,
            )
        )
        return 1
    print(
        json.dumps(
            {
                "status": "backed_up",
                "archive": str(result.archive_path),
                "files": result.files,
            },
            sort_keys=True,
        )
    )
    return 0


def _restore(
    archive_path: Path,
    destination: Path,
    *,
    apply: bool = False,
    allow_overwrite: bool = False,
) -> int:
    try:
        result = restore_local_backup(
            archive_path,
            destination,
            apply=apply,
            allow_overwrite=allow_overwrite,
        )
    except (RestoreError, OSError, ValueError):
        print(
            json.dumps(
                {
                    "error": {
                        "code": "restore_failed",
                        "message": "restore failed",
                    }
                },
                sort_keys=True,
            )
        )
        return 1
    print(
        json.dumps(
            {
                "status": "dry_run" if result.dry_run else "restored",
                "archive": str(result.archive_path),
                "destination": str(result.destination),
                "files": result.files,
            },
            sort_keys=True,
        )
    )
    return 0


def _migrate(
    from_src: Path,
    to_dest: Path,
    *,
    target_schema: str = "registry",
    dry_run: bool = True,
    allow_modify: bool = False,
    overwrite: bool = False,
    backup_path: Path | None = None,
    report_path: Path | None = None,
) -> int:
    try:
        from .migration import migrate

        result = migrate(
            str(from_src),
            str(to_dest),
            dry_run=dry_run,
            target_schema=target_schema,
            allow_modify=allow_modify,
            overwrite=overwrite,
            backup_path=str(backup_path) if backup_path is not None else None,
            report_path=str(report_path) if report_path is not None else None,
        )
    except Exception:
        print(
            json.dumps(
                {
                    "error": {
                        "code": "migration_failed",
                        "message": "migration failed",
                    }
                },
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(_jsonable(result), sort_keys=True))
    return 0


def _update(config_path: Path, *, rollback: bool = False) -> int:
    try:
        config = _load_config(config_path)
        result = rollback_update(config) if rollback else check_updates(config)
    except (UpdateError, OSError, ValueError):
        print(
            json.dumps(
                {
                    "error": {
                        "code": "update_status_failed",
                        "message": "update status failed",
                    }
                },
                sort_keys=True,
            )
        )
        return 1
    print(
        json.dumps(
            {
                "operation": result.operation,
                "supported": result.supported,
                "status": result.status,
                "metadata_path": str(result.metadata_path),
                "current_version": result.current_version,
                "available_version": result.available_version,
                "rollback_version": result.rollback_version,
                "signed_manifest": result.signed_manifest,
                "network_used": result.network_used,
                "action_required": result.action_required,
            },
            sort_keys=True,
        )
    )
    return 0


def _load_config(config_path: Path):
    return config_from_mapping(json.loads(config_path.read_text(encoding="utf-8-sig")))


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
