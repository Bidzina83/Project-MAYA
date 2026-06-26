"""Verify the Phase 1 package installs from a built wheel.

The check intentionally avoids editable installs and repository PYTHONPATH
imports. It builds a wheel, installs that wheel into a temporary virtual
environment, imports the canonical package, verifies the CLI entry point
metadata, and runs the installed CLI module.
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import venv
import zipfile
from contextlib import closing
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    repo_root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="maya-package-verify-") as tmp:
        work_dir = Path(tmp)
        dist_dir = work_dir / "dist"
        build_dir = work_dir / "build"
        build_base = work_dir / "build-base"
        venv_dir = work_dir / "venv"

        _run(
            [
                sys.executable,
                "setup.py",
                "build",
                "--build-base",
                str(build_base),
                "bdist_wheel",
                "--dist-dir",
                str(dist_dir),
                "--bdist-dir",
                str(build_dir),
            ],
            cwd=repo_root,
        )
        wheels = sorted(dist_dir.glob("*.whl"))
        if len(wheels) != 1:
            raise RuntimeError(f"expected one wheel, found {len(wheels)}")
        _verify_wheel_contents(wheels[0])

        venv.EnvBuilder(with_pip=True, clear=True).create(venv_dir)
        python = _venv_python(venv_dir)
        _run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--no-deps",
                "--force-reinstall",
                str(wheels[0]),
            ],
            env=_clean_env(),
        )
        _run(
            [
                str(python),
                "-c",
                (
                    "import project_maya; "
                    "from project_maya import build_local_product; "
                    "print(project_maya.__name__, callable(build_local_product))"
                ),
            ],
            cwd=work_dir,
            env=_clean_env(),
        )
        _run(
            [
                str(python),
                "-c",
                (
                    "from importlib.metadata import entry_points; "
                    "eps = entry_points(group='console_scripts'); "
                    "maya = [ep for ep in eps if ep.name == 'maya']; "
                    "assert maya and maya[0].value == 'project_maya.cli:main'"
                ),
            ],
            cwd=work_dir,
            env=_clean_env(),
        )
        help_result = _run(
            [str(python), "-m", "project_maya.cli", "--help"],
            cwd=work_dir,
            env=_clean_env(),
        )
        required_commands = (
            "doctor",
            "run",
            "serve-local-api",
            "rotate-secret",
            "export-config",
            "import-config",
            "backup",
            "restore",
            "migrate",
        )
        missing_commands = [
            command
            for command in required_commands
            if command not in help_result.stdout
        ]
        if missing_commands:
            raise RuntimeError(
                "installed CLI help is missing: " + ", ".join(missing_commands)
            )
        _verify_installed_migration_cli(python, work_dir)
    return 0


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _verify_wheel_contents(wheel_path: Path) -> None:
    with zipfile.ZipFile(wheel_path) as wheel:
        names = wheel.namelist()
    if "project_maya/__init__.py" not in names:
        raise RuntimeError("wheel does not contain project_maya")
    disallowed_fragments = (
        "__pycache__/",
        "/tests/",
        ".pytest_cache/",
    )
    disallowed_prefixes = (
        "tests/",
        "hermes/",
        "hermes_cli/",
        "maya/",
        "maya_dev/",
        "plugins/",
    )
    leaked = [
        name
        for name in names
        if name.startswith(disallowed_prefixes)
        or any(fragment in name for fragment in disallowed_fragments)
    ]
    if leaked:
        raise RuntimeError(
            "wheel contains non-product files: " + ", ".join(sorted(leaked)[:10])
        )


def _verify_installed_migration_cli(python: Path, work_dir: Path) -> None:
    legacy_db = work_dir / "legacy-memory.sqlite"
    destination_db = work_dir / "migrated-memory.sqlite"
    with closing(sqlite3.connect(legacy_db)) as conn:
        conn.execute("CREATE TABLE memory_kv (key TEXT PRIMARY KEY, value TEXT)")
        conn.execute(
            "INSERT INTO memory_kv(key, value) VALUES (?, ?)",
            ("sample", "value"),
        )
        conn.commit()

    result = _run(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "migrate",
            "--from",
            str(legacy_db),
            "--to",
            str(destination_db),
        ],
        cwd=work_dir,
        env=_clean_env(),
    )
    payload = json.loads(result.stdout)
    if not payload.get("dry_run"):
        raise RuntimeError("installed migration CLI did not default to dry-run")
    if payload.get("source_rows") != 1:
        raise RuntimeError("installed migration CLI reported wrong source count")
    if destination_db.exists():
        raise RuntimeError("installed migration dry-run created destination database")


def _clean_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    return env


def _run(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode != 0:
        joined = " ".join(command)
        raise RuntimeError(
            f"command failed with exit code {result.returncode}: {joined}\n"
            f"{result.stdout}"
        )
    return result


if __name__ == "__main__":
    raise SystemExit(main())
