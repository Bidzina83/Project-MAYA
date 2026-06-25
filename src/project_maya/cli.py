"""Command-line entry points for minimal Project MAYA operations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .bootstrap import build_local_product
from .config import config_from_mapping
from .doctor import DoctorStatus, run_doctor


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

    args = parser.parse_args(argv)
    if args.command == "doctor":
        return _doctor(args.config)
    parser.error(f"unknown command: {args.command}")
    return 2


def _doctor(config_path: Path) -> int:
    config = config_from_mapping(json.loads(config_path.read_text(encoding="utf-8")))
    try:
        product = build_local_product(config)
    except Exception as exc:
        print(f"{DoctorStatus.FAIL.value}\truntime.assembly\t{exc}")
        return 1
    report = run_doctor(config, product.runtime, secret_store=product.secret_store)
    for check in report.checks:
        print(f"{check.status.value}\t{check.name}\t{check.message}")
    return 0 if report.healthy else 1


if __name__ == "__main__":
    raise SystemExit(main())
