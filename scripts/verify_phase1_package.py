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


REQUIRED_COMMANDS = (
    "doctor",
    "repair",
    "reset-integration",
    "run",
    "serve-local-api",
    "rotate-secret",
    "export-config",
    "import-config",
    "backup",
    "restore",
    "migrate",
    "update",
)


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
        missing_commands = [
            command
            for command in REQUIRED_COMMANDS
            if command not in help_result.stdout
        ]
        if missing_commands:
            raise RuntimeError(
                "installed CLI help is missing: " + ", ".join(missing_commands)
            )
        _verify_installed_repair_cli(python, work_dir)
        _verify_installed_reset_integration_cli(python, work_dir)
        _verify_installed_update_cli(python, work_dir)
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


def _verify_installed_repair_cli(python: Path, work_dir: Path) -> None:
    data_dir = work_dir / "maya-data"
    config_path = work_dir / "maya-config.json"
    _write_minimal_config(config_path, data_dir)
    result = _run(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "repair",
            "--config",
            str(config_path),
        ],
        cwd=work_dir,
        env=_clean_env(),
    )
    payload = json.loads(result.stdout)
    if payload.get("status") != "dry_run":
        raise RuntimeError("installed repair CLI did not default to dry-run")
    if data_dir.exists():
        raise RuntimeError("installed repair dry-run created data directory")


def _verify_installed_reset_integration_cli(python: Path, work_dir: Path) -> None:
    data_dir = work_dir / "reset-maya-data"
    state_dir = data_dir / "integrations" / "google"
    state_dir.mkdir(parents=True)
    (state_dir / "state.json").write_text("{}", encoding="utf-8")
    config_path = work_dir / "reset-maya-config.json"
    _write_minimal_config(config_path, data_dir, include_google=True)
    result = _run(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "reset-integration",
            "google",
            "--config",
            str(config_path),
            "--dry-run",
        ],
        cwd=work_dir,
        env=_clean_env(),
    )
    payload = json.loads(result.stdout)
    if payload.get("status") != "dry_run":
        raise RuntimeError("installed reset-integration CLI did not dry-run")
    if "secret://" in result.stdout:
        raise RuntimeError("installed reset-integration CLI printed a secret ref")
    if not state_dir.exists():
        raise RuntimeError("installed reset-integration dry-run removed local state")


def _verify_installed_update_cli(python: Path, work_dir: Path) -> None:
    data_dir = work_dir / "update-maya-data"
    config_path = work_dir / "update-maya-config.json"
    _write_minimal_config(config_path, data_dir)
    result = _run(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "update",
            "--config",
            str(config_path),
            "--check",
        ],
        cwd=work_dir,
        env=_clean_env(),
    )
    payload = json.loads(result.stdout)
    if payload.get("operation") != "check":
        raise RuntimeError("installed update CLI did not run check")
    if payload.get("network_used"):
        raise RuntimeError("installed update CLI used network")


def _write_minimal_config(
    config_path: Path,
    data_dir: Path,
    *,
    include_google: bool = False,
) -> None:
    integrations = {}
    if include_google:
        integrations["google"] = {
            "enabled": True,
            "credential_mode": "broker",
            "credential_ref": "secret://integrations/google",
        }
    config_path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "product": {"edition": "standard", "instance_id": "verify"},
                "deployment": {
                    "class": "desktop",
                    "network_policy": "standard",
                    "data_dir": str(data_dir),
                },
                "runtime": {
                    "hermes_compatibility": "phase1-test",
                    "enabled_profiles": ["maya-core"],
                },
                "broker": {"mode": "disabled", "endpoint": None},
                "llm": {
                    "mode": "customer_owned",
                    "provider": "openai",
                    "model": "gpt-test",
                    "fallback_model": None,
                    "credential_ref": "secret://llm/openai",
                    "endpoint": None,
                    "timeout_seconds": 60,
                },
                "integrations": integrations,
                "memory": {
                    "hermes_provider": "local",
                    "retriever": "local_json",
                    "registry": "sqlite",
                    "governance_enabled": True,
                },
                "governance": {
                    "policy_file": str(data_dir / "governance" / "policy.json"),
                    "audit_enabled": True,
                    "default_action": "deny",
                    "minimum_memory_trust": 0.7,
                },
                "metabase": {
                    "enabled": False,
                    "deployment": "disabled",
                    "endpoint": None,
                    "application_database": None,
                    "analytics_sources": [],
                },
                "local_api": {
                    "bind": "127.0.0.1",
                    "port": None,
                    "remote_access": False,
                },
            }
        ),
        encoding="utf-8",
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
            "--dry-run",
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
