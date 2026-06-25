"""Validate Project MAYA's canonical product-context files.

This guard prevents product work from silently drifting away from the approved
Specification V2 architecture. It intentionally checks stable anchor text
rather than exact file hashes so normal editorial improvements remain possible.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RequiredFile:
    path: str
    anchors: tuple[str, ...]


REQUIRED_FILES = (
    RequiredFile(
        path="AGENTS.md",
        anchors=(
            "docs/product/project-maya-product-specification-v2.md",
            "If implementation instructions conflict with the product specification",
            "Hermes executes Maya. Local governance authorizes Maya.",
            "Do not create fake runtimes, duplicate plugin registries",
            "Telegram always uses a customer-owned bot and token.",
            "Broker mode is one enum: `runtime`, `setup_only`, or `disabled`.",
            "Do not use an ambiguous `metabase.db_path`.",
            "Runtime, governance, connector, model, secrets, and threat-model contracts",
        ),
    ),
    RequiredFile(
        path="PROJECT_MAYA.md",
        anchors=(
            "docs/product/project-maya-product-specification-v2.md",
            "Maya Standard",
            "Maya Enterprise",
            "The public `Agent` is a lifecycle facade over a concrete `AgentRuntime`.",
            "workflow may bypass local authorization.",
            "Key-value `read` and `write` methods are not the canonical memory contract.",
            "Metabase application database",
            "Valid editions are `standard` and `enterprise`.",
        ),
    ),
    RequiredFile(
        path="docs/product/project-maya-product-specification-v2.md",
        anchors=(
            "## Version 2",
            "**Status:** Approved product architecture specification",
            "Core execution runtime:** Hermes Agent",
            "No connector, plugin, skill, workflow, model adapter, or broker callback may",
            "Key-value `read` and `write` methods are not the persistent-memory contract.",
            "Broker mode is one enum:",
            "Maya does not provide a shared Maya-managed Telegram bot.",
            "Metabase is Maya's included, open-source business-intelligence",
            "## 22. Implementation Roadmap",
            "## 23. Acceptance Criteria",
        ),
    ),
)


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    for required in REQUIRED_FILES:
        path = root / required.path
        if not path.is_file():
            errors.append(f"missing required product-context file: {required.path}")
            continue

        text = path.read_text(encoding="utf-8")
        for anchor in required.anchors:
            if anchor not in text:
                errors.append(
                    f"{required.path} is missing required V2 anchor: {anchor!r}"
                )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate Project MAYA product-context files."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root. Defaults to the current directory.",
    )
    args = parser.parse_args(argv)

    errors = validate(args.root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("Project MAYA product context is present and aligned with V2 anchors.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
