"""Command-line entry points for minimal Project MAYA operations."""

from __future__ import annotations

import argparse
import builtins
import json
import sys
from pathlib import Path
from typing import Any

from .backup import (
    BackupError,
    RestoreError,
    create_local_backup,
    inspect_backup_archive,
    plan_restore_backup,
    restore_local_backup,
)
from .bootstrap import build_local_product
from .broker import (
    BrokerOperationError,
    broker_status,
    complete_oauth_session,
    model_proxy_readiness,
    refresh_token,
    register_broker_instance,
    revoke_token,
    run_mock_broker_conformance,
    start_oauth_session,
    token_status,
)
from .config import config_from_mapping, config_to_mapping
from .doctor import DoctorStatus, run_doctor
from .documents import (
    DocumentCapabilityError,
    DocumentDependencyUnavailable,
    convert_document,
    create_pdf,
    extract_pdf_text,
    inspect_document,
)
from .governance import DenyByDefaultGateway, load_policy_gateway
from .integrations import IntegrationResetError, reset_integration_state
from .local_api import build_local_api_http_server
from .audit import LocalJsonlAuditSink
from .metabase import (
    MetabaseCapabilityError,
    apply_metabase_provisioning,
    inspect_metabase_lifecycle,
    plan_metabase_provisioning,
    validate_metabase_health,
    write_metabase_provisioning_plan,
)
from .repair import RepairError, repair_local_state
from .health import summarize_health
from .secrets import (
    SecretRef,
    SecretReferenceError,
    SecretStoreError,
    build_platform_secret_store,
)
from .update import UpdateError, check_updates, rollback_update
from .setup import plan_setup
from .skills import packaged_document_skill_status


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
    setup_parser = subparsers.add_parser(
        "setup",
        help="Plan or initialize safe local Maya setup.",
    )
    setup_subparsers = setup_parser.add_subparsers(
        dest="setup_command",
        required=True,
    )
    for setup_command in ("plan", "init"):
        setup_child = setup_subparsers.add_parser(
            setup_command,
            help=(
                "Report setup requirements."
                if setup_command == "plan"
                else "Initialize safe Maya-owned local state."
            ),
        )
        setup_child.add_argument("--config", type=Path, required=True)
        setup_child.add_argument(
            "--format",
            choices=("json", "text"),
            default="json",
        )
        if setup_command == "init":
            setup_child.add_argument(
                "--apply",
                action="store_true",
                help="Create safe Maya-owned directories. Default is dry-run.",
            )
    health_parser = subparsers.add_parser(
        "health",
        help="Report operator-oriented Maya health.",
    )
    health_subparsers = health_parser.add_subparsers(
        dest="health_command",
        required=True,
    )
    health_summary = health_subparsers.add_parser(
        "summary",
        help="Summarize Maya health from existing diagnostics.",
    )
    health_summary.add_argument("--config", type=Path, required=True)
    health_summary.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
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
        "backup_command",
        nargs="?",
        default="create",
        help="Use 'inspect' to inspect an existing backup archive.",
    )
    backup_parser.add_argument(
        "--config",
        type=Path,
        required=False,
        help="Path to a JSON Maya configuration file.",
    )
    backup_parser.add_argument(
        "--from",
        dest="archive_path",
        type=Path,
        default=None,
        help="Backup archive to inspect.",
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
    documents_parser = subparsers.add_parser(
        "documents",
        help="Run governed local document operations.",
    )
    documents_subparsers = documents_parser.add_subparsers(
        dest="documents_command",
        required=True,
    )
    documents_inspect = documents_subparsers.add_parser(
        "inspect",
        help="Inspect redacted local document metadata.",
    )
    documents_inspect.add_argument("--config", type=Path, required=True)
    documents_inspect.add_argument("--source", type=Path, required=True)
    documents_inspect.add_argument("--data-classification", default="internal")
    documents_extract = documents_subparsers.add_parser(
        "extract-text",
        help="Extract text from a governed local PDF.",
    )
    documents_extract.add_argument("--config", type=Path, required=True)
    documents_extract.add_argument("--source", type=Path, required=True)
    documents_extract.add_argument(
        "--include-text",
        action="store_true",
        help="Include extracted text in stdout. Audit remains redacted.",
    )
    documents_extract.add_argument(
        "--to",
        dest="output",
        type=Path,
        default=None,
        help=(
            "Optional governed .txt output path. A bare filename is written "
            "under maya-data/documents/outputs."
        ),
    )
    documents_extract.add_argument("--data-classification", default="internal")
    documents_create = documents_subparsers.add_parser(
        "create-pdf",
        help="Create a governed local PDF from plain text or Markdown.",
    )
    documents_create.add_argument("--config", type=Path, required=True)
    documents_create.add_argument(
        "--output",
        type=Path,
        required=True,
        help=(
            "Governed PDF output path. A bare filename is written under "
            "maya-data/documents/outputs."
        ),
    )
    documents_create.add_argument(
        "--text",
        required=True,
        help="Source text. The value is not written to audit records.",
    )
    documents_create.add_argument(
        "--source-format",
        choices=("plain", "markdown"),
        default="plain",
    )
    documents_create.add_argument("--data-classification", default="internal")
    documents_convert = documents_subparsers.add_parser(
        "convert",
        help="Convert a governed document through LibreOffice.",
    )
    documents_convert.add_argument("--config", type=Path, required=True)
    documents_convert.add_argument("--source", type=Path, required=True)
    documents_convert.add_argument(
        "--to",
        dest="output",
        type=Path,
        required=True,
        help="Output filename or path under maya-data/documents/outputs.",
    )
    documents_convert.add_argument(
        "--format",
        choices=("pdf", "txt", "docx"),
        required=True,
    )
    documents_convert.add_argument("--data-classification", default="internal")
    metabase_parser = subparsers.add_parser(
        "metabase",
        help="Validate and plan governed Metabase integration.",
    )
    metabase_subparsers = metabase_parser.add_subparsers(
        dest="metabase_command",
        required=True,
    )
    metabase_health = metabase_subparsers.add_parser(
        "health",
        help="Report secret-safe Metabase health.",
    )
    metabase_health.add_argument("--config", type=Path, required=True)
    metabase_health.add_argument(
        "--live",
        action="store_true",
        help="Request a live check. Phase 4 reports this as deferred.",
    )
    metabase_lifecycle = metabase_subparsers.add_parser(
        "lifecycle",
        help="Report managed-local or customer-managed Metabase lifecycle state.",
    )
    metabase_lifecycle.add_argument("--config", type=Path, required=True)
    metabase_plan = metabase_subparsers.add_parser(
        "plan-provision",
        help="Create a redacted Metabase provisioning plan.",
    )
    metabase_plan.add_argument("--config", type=Path, required=True)
    metabase_plan.add_argument(
        "--write",
        action="store_true",
        help="Write the redacted plan to maya-data/metabase/provisioning.",
    )
    metabase_apply = metabase_subparsers.add_parser(
        "apply-provision",
        help="Apply an approved Metabase provisioning plan.",
    )
    metabase_apply.add_argument("--config", type=Path, required=True)
    metabase_apply.add_argument(
        "--apply",
        action="store_true",
        required=True,
        help="Required confirmation for Phase 4 provisioning apply.",
    )
    metabase_apply.add_argument("--data-classification", default="internal")
    skills_parser = subparsers.add_parser(
        "skills",
        help="Report packaged Maya skill artifact status.",
    )
    skills_subparsers = skills_parser.add_subparsers(
        dest="skills_command",
        required=True,
    )
    skills_status = skills_subparsers.add_parser(
        "status",
        help="Report packaged and allowlisted skill status.",
    )
    skills_status.add_argument("--config", type=Path, required=True)
    skills_status.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
    )
    broker_parser = subparsers.add_parser(
        "broker",
        help="Manage Phase 5 broker and Standard OAuth readiness.",
    )
    broker_subparsers = broker_parser.add_subparsers(
        dest="broker_command",
        required=True,
    )
    for broker_command in ("status", "conformance", "model-proxy-status"):
        broker_child = broker_subparsers.add_parser(
            broker_command,
            help=f"Run broker {broker_command}.",
        )
        broker_child.add_argument("--config", type=Path, required=True)
        broker_child.add_argument(
            "--format",
            choices=("json", "text"),
            default="json",
        )
    broker_register = broker_subparsers.add_parser(
        "register",
        help="Plan or store a local broker instance identity.",
    )
    broker_register.add_argument("--config", type=Path, required=True)
    broker_register.add_argument("--apply", action="store_true")
    broker_register.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
    )
    broker_oauth_start = broker_subparsers.add_parser(
        "oauth-start",
        help="Plan or create a broker-assisted OAuth session.",
    )
    broker_oauth_start.add_argument("--config", type=Path, required=True)
    broker_oauth_start.add_argument(
        "--provider",
        choices=("google", "slack"),
        required=True,
    )
    broker_oauth_start.add_argument("--apply", action="store_true")
    broker_oauth_start.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
    )
    broker_oauth_complete = broker_subparsers.add_parser(
        "oauth-complete",
        help="Complete a broker-assisted OAuth session.",
    )
    broker_oauth_complete.add_argument("--config", type=Path, required=True)
    broker_oauth_complete.add_argument(
        "--provider",
        choices=("google", "slack"),
        required=True,
    )
    broker_oauth_complete.add_argument("--session", required=True)
    broker_oauth_complete.add_argument("--callback-url", required=True)
    broker_oauth_complete.add_argument("--apply", action="store_true", required=True)
    broker_oauth_complete.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
    )
    for broker_command in ("token-status", "token-refresh", "token-revoke"):
        broker_child = broker_subparsers.add_parser(
            broker_command,
            help=f"Run broker {broker_command}.",
        )
        broker_child.add_argument("--config", type=Path, required=True)
        broker_child.add_argument(
            "--provider",
            choices=("google", "slack"),
            required=True,
        )
        if broker_command != "token-status":
            broker_child.add_argument("--apply", action="store_true", required=True)
        broker_child.add_argument(
            "--format",
            choices=("json", "text"),
            default="json",
        )

    args = parser.parse_args(argv)
    if args.command == "doctor":
        return _doctor(args.config)
    if args.command == "repair":
        return _repair(args.config, apply=args.apply)
    if args.command == "setup":
        return _setup(
            args.config,
            command=args.setup_command,
            apply=getattr(args, "apply", False),
            output_format=args.format,
        )
    if args.command == "health":
        return _health_summary(args.config, output_format=args.format)
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
        if args.backup_command == "inspect":
            return _backup_inspect(args.archive_path, output_format="json")
        if args.config is None:
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
    if args.command == "documents":
        return _documents(args)
    if args.command == "metabase":
        return _metabase(args)
    if args.command == "skills":
        return _skills(args)
    if args.command == "broker":
        return _broker(args)
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
                        "category": action.category,
                        "hint": action.hint,
                        "target": _repair_target_ref(config, action.path),
                        "severity": action.severity,
                        "status": action.status,
                    }
                    for action in result.actions
                ],
            },
            sort_keys=True,
        )
    )
    return 0


def _setup(
    config_path: Path,
    *,
    command: str,
    apply: bool = False,
    output_format: str = "json",
) -> int:
    try:
        config = _load_config(config_path)
        result = plan_setup(config, apply=apply if command == "init" else False)
    except (RepairError, OSError, ValueError):
        print(
            json.dumps(
                {
                    "error": {
                        "code": "setup_failed",
                        "message": "setup failed",
                    }
                },
                sort_keys=True,
            )
        )
        return 1
    payload = result.redacted_summary()
    payload["operation"] = command
    _print_payload(payload, output_format=output_format)
    return 0


def _health_summary(config_path: Path, *, output_format: str = "json") -> int:
    try:
        config = _load_config(config_path)
        product = build_local_product(config)
        result = summarize_health(
            config,
            product.runtime,
            lifecycle_state=product.agent.state,
            secret_store=product.secret_store,
        )
    except Exception:
        print(
            json.dumps(
                {
                    "error": {
                        "code": "health_summary_failed",
                        "message": "health summary failed",
                    }
                },
                sort_keys=True,
            )
        )
        return 1
    _print_payload(result.redacted_summary(), output_format=output_format)
    return 0 if result.status.value in {"ready", "degraded"} else 1


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
            _redact_payload_for_output(
                {
                    "status": "rotated",
                    "secret_ref_state": "configured",
                }
            ),
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
                "manifest": result.manifest.redacted_summary(),
            },
            sort_keys=True,
        )
    )
    return 0


def _backup_inspect(
    archive_path: Path | None,
    *,
    output_format: str = "json",
) -> int:
    try:
        if archive_path is None:
            raise RestoreError("backup archive is required")
        result = inspect_backup_archive(archive_path)
    except (RestoreError, OSError, ValueError):
        print(
            json.dumps(
                {
                    "error": {
                        "code": "backup_inspect_failed",
                        "message": "backup inspect failed",
                    }
                },
                sort_keys=True,
            )
        )
        return 1
    _print_payload(result.redacted_summary(), output_format=output_format)
    return 0


def _restore(
    archive_path: Path,
    destination: Path,
    *,
    apply: bool = False,
    allow_overwrite: bool = False,
) -> int:
    try:
        plan = plan_restore_backup(
            archive_path,
            destination,
            allow_overwrite=allow_overwrite,
        )
        if plan.overwrite_required and not (apply and allow_overwrite):
            raise RestoreError("restore destination contains existing files")
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
    payload = result.redacted_summary()
    payload["status"] = "dry_run" if result.dry_run else "restored"
    _print_payload(payload)
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
                "mutation": result.mutation,
            },
            sort_keys=True,
        )
    )
    return 0


def _repair_target_ref(config, path: Path) -> str:
    root = config.deployment.data_dir.resolve()
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(root).as_posix()
    except ValueError:
        return "maya-data" if resolved == root else "external"
    return f"maya-data/{relative}" if relative else "maya-data"


def _documents(args) -> int:
    try:
        config = _load_config(args.config)
        gateway = _build_cli_gateway(config)
        audit_sink = _build_cli_audit_sink(config)
        if args.documents_command == "inspect":
            result = inspect_document(
                config,
                args.source,
                gateway=gateway,
                audit_sink=audit_sink,
                data_classification=args.data_classification,
            )
            _print_payload(result.redacted_summary())
            return 0
        if args.documents_command == "extract-text":
            result, text = extract_pdf_text(
                config,
                args.source,
                output=args.output,
                gateway=gateway,
                audit_sink=audit_sink,
                data_classification=args.data_classification,
            )
            payload = result.redacted_summary()
            if args.include_text:
                payload["text"] = text
            _print_payload(payload)
            return 0
        if args.documents_command == "create-pdf":
            result = create_pdf(
                config,
                text=args.text,
                output=args.output,
                source_format=args.source_format,
                gateway=gateway,
                audit_sink=audit_sink,
                data_classification=args.data_classification,
            )
            _print_payload(result.redacted_summary())
            return 0
        if args.documents_command == "convert":
            result = convert_document(
                config,
                args.source,
                output=args.output,
                output_format=args.format,
                gateway=gateway,
                audit_sink=audit_sink,
                data_classification=args.data_classification,
            )
            _print_payload(result.redacted_summary())
            return 0
    except (
        DocumentCapabilityError,
        DocumentDependencyUnavailable,
        OSError,
        ValueError,
        PermissionError,
    ):
        print(
            json.dumps(
                {
                    "error": {
                        "code": "document_operation_failed",
                        "message": "document operation failed",
                    }
                },
                sort_keys=True,
            )
        )
        return 1
    return 2


def _skills(args) -> int:
    try:
        _load_config(args.config)
        statuses = packaged_document_skill_status()
        payload = {
            "status": (
                "ready"
                if all(status.discoverable for status in statuses)
                else "blocked"
            ),
            "skills": [status.redacted_summary() for status in statuses],
        }
        _print_payload(payload, output_format=args.format)
        return 0 if payload["status"] == "ready" else 1
    except (OSError, ValueError):
        print(
            json.dumps(
                {
                    "error": {
                        "code": "skills_status_failed",
                        "message": "skills status failed",
                    }
                },
                sort_keys=True,
            )
        )
        return 1


def _metabase(args) -> int:
    try:
        config = _load_config(args.config)
        if args.metabase_command == "health":
            result = validate_metabase_health(config, live=args.live)
            _print_payload(result.redacted_summary())
            return 0 if result.status in {"ready", "live_unavailable"} else 1
        if args.metabase_command == "lifecycle":
            result = inspect_metabase_lifecycle(config)
            _print_payload(result.redacted_summary())
            return (
                0
                if result.status
                in {"customer_managed", "managed_local_ready", "managed_local_artifact_missing"}
                else 1
            )
        if args.metabase_command == "plan-provision":
            result = plan_metabase_provisioning(config)
            payload = result.redacted_summary()
            if args.write:
                plan_path = write_metabase_provisioning_plan(config, result)
                payload["plan_ref"] = _redacted_data_ref(config, plan_path)
            _print_payload(payload)
            return 0 if result.status == "planned" else 1
        if args.metabase_command == "apply-provision":
            result = apply_metabase_provisioning(
                config,
                gateway=_build_cli_gateway(config),
                audit_sink=_build_cli_audit_sink(config),
                data_classification=args.data_classification,
            )
            _print_payload(result.redacted_summary())
            return 0
    except (MetabaseCapabilityError, OSError, ValueError, PermissionError):
        print(
            json.dumps(
                {
                    "error": {
                        "code": "metabase_operation_failed",
                        "message": "Metabase operation failed",
                    }
                },
                sort_keys=True,
            )
        )
        return 1
    return 2


def _broker(args) -> int:
    try:
        config = _load_config(args.config)
        secret_store = build_platform_secret_store(config.deployment.data_dir)
        if args.broker_command == "status":
            result = broker_status(config, secret_store)
            _print_payload(result.redacted_summary(), output_format=args.format)
            return 0 if result.status.value in {"ready", "pending", "disabled"} else 1
        if args.broker_command == "register":
            result = register_broker_instance(
                config,
                secret_store,
                apply=args.apply,
            )
            _print_payload(result.redacted_summary(), output_format=args.format)
            return 0 if result.successful else 1
        if args.broker_command == "oauth-start":
            result = start_oauth_session(
                config,
                args.provider,
                apply=args.apply,
            )
            payload = {
                "operation": "broker.oauth-start",
                "status": "pending" if not args.apply else "ready",
                **result.redacted_summary(),
            }
            _print_payload(payload, output_format=args.format)
            return 0
        if args.broker_command == "oauth-complete":
            result = complete_oauth_session(
                config,
                secret_store,
                provider=args.provider,
                session_id=args.session,
                callback_url=args.callback_url,
                apply=args.apply,
            )
            _print_payload(result.redacted_summary(), output_format=args.format)
            return 0 if result.successful else 1
        if args.broker_command == "token-status":
            result = token_status(config, args.provider)
            _print_payload(result.redacted_summary(), output_format=args.format)
            return 0 if result.state.value in {"active", "not_configured"} else 1
        if args.broker_command == "token-refresh":
            result = refresh_token(
                config,
                secret_store,
                args.provider,
                apply=args.apply,
            )
            _print_payload(result.redacted_summary(), output_format=args.format)
            return 0 if result.successful else 1
        if args.broker_command == "token-revoke":
            result = revoke_token(
                config,
                secret_store,
                args.provider,
                apply=args.apply,
            )
            _print_payload(result.redacted_summary(), output_format=args.format)
            return 0 if result.successful else 1
        if args.broker_command == "conformance":
            result = run_mock_broker_conformance()
            _print_payload(result.redacted_summary(), output_format=args.format)
            return 0 if result.passed else 1
        if args.broker_command == "model-proxy-status":
            result = model_proxy_readiness(config, secret_store)
            _print_payload(result.redacted_summary(), output_format=args.format)
            return 0 if result.status.value in {"ready", "pending", "not_configured"} else 1
    except (
        BrokerOperationError,
        SecretStoreError,
        OSError,
        ValueError,
        PermissionError,
    ):
        print(
            json.dumps(
                {
                    "error": {
                        "code": "broker_operation_failed",
                        "message": "broker operation failed",
                    }
                },
                sort_keys=True,
            )
        )
        return 1
    return 2


def _build_cli_gateway(config):
    if config.governance.policy_file.is_file():
        return load_policy_gateway(config.governance.policy_file)
    return DenyByDefaultGateway()


def _build_cli_audit_sink(config):
    return LocalJsonlAuditSink(
        config.deployment.data_dir / "governance" / "audit" / "runtime.jsonl"
    )


def _redacted_data_ref(config, path: Path) -> str:
    root = config.deployment.data_dir.resolve()
    try:
        relative = path.resolve().relative_to(root).as_posix()
    except ValueError:
        relative = "external"
    return f"maya-data/{relative}"


def _print_payload(payload: dict[str, object], *, output_format: str = "json") -> None:
    redacted_payload = _redact_payload_for_output(payload)
    if output_format == "text":
        redacted_output = _text_payload(redacted_payload)
        _emit_redacted_payload(redacted_output)
        return
    redacted_output = json.dumps(redacted_payload, sort_keys=True)
    _emit_redacted_payload(redacted_output)


def _emit_redacted_payload(redacted_output: str) -> None:
    getattr(builtins, "print")(redacted_output)


def _redact_payload_for_output(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _redact_sensitive_value(key, item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_payload_for_output(item) for item in value]
    return value


def _redact_sensitive_value(key: str, value: Any) -> Any:
    lowered = key.lower()
    sensitive_terms = (
        "access_token",
        "refresh_token",
        "password",
        "private",
        "credential",
        "secret",
        "api_key",
    )
    if any(term in lowered for term in sensitive_terms):
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        return "configured"
    return _redact_payload_for_output(value)


def _text_payload(payload: dict[str, object]) -> str:
    lines = []
    for key, value in sorted(payload.items()):
        if isinstance(value, list):
            lines.append(f"{key}: {len(value)} item(s)")
        elif isinstance(value, dict):
            lines.append(f"{key}: " + ", ".join(sorted(value.keys())))
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines)


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
