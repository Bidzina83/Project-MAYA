"""Verify the Project MAYA package installs from a built wheel.

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
from email.parser import Parser
from pathlib import Path


HERMES_RUNTIME_COMMIT = "b13e2fd6948a59eeb59fe618914147d97a2ee90a"
HERMES_RUNTIME_REQUIREMENT_PREFIX = (
    "hermes-agent@git+https://github.com/Bidzina83/hermes-agent.git@"
)
MAYA_PYTHON_REQUIRES = frozenset((">=3.11", "<3.14"))
DOCUMENTS_EXTRA_REQUIREMENTS = frozenset(
    ("markdown", "pillow", "pypdf", "reportlab")
)
BROKER_CRYPTO_REQUIREMENT = "cryptography"

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
    "documents",
    "metabase",
    "setup",
    "health",
    "skills",
    "broker",
)


def main(argv: list[str] | None = None) -> int:
    options = _parse_args(argv or [])
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
        _install_wheel(
            python,
            wheels[0],
            with_runtime_deps=options.with_hermes_runtime,
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
        _verify_installed_dependency_contract_surfaces(python, work_dir)
        _verify_installed_skill_allowlist_surfaces(python, work_dir)
        _verify_installed_phase3_metabase_document_surfaces(python, work_dir)
        _verify_installed_phase4_operator_surfaces(python, work_dir)
        _verify_installed_phase5_broker_surfaces(python, work_dir)
        _verify_installed_enterprise_byo_surfaces(python, work_dir)
        _verify_installed_phase2_profile_model_and_secret_surfaces(
            python,
            work_dir,
        )
        if options.with_hermes_runtime:
            _verify_installed_hermes_runtime_dependency(python, work_dir)
    return 0


def _parse_args(argv: list[str]):
    import argparse

    parser = argparse.ArgumentParser(
        description="Verify the Project MAYA package installs from a built wheel."
    )
    parser.add_argument(
        "--with-hermes-runtime",
        action="store_true",
        help=(
            "Install package dependencies and verify the pinned Hermes runtime "
            "is importable. This may use network access for the pinned Git "
            "dependency."
        ),
    )
    return parser.parse_args(argv)


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _verify_wheel_contents(wheel_path: Path) -> None:
    with zipfile.ZipFile(wheel_path) as wheel:
        names = wheel.namelist()
        metadata_name = next(
            (name for name in names if name.endswith(".dist-info/METADATA")),
            None,
        )
        if metadata_name is None:
            raise RuntimeError("wheel does not contain distribution metadata")
        metadata = Parser().parsestr(wheel.read(metadata_name).decode("utf-8"))
    if "project_maya/__init__.py" not in names:
        raise RuntimeError("wheel does not contain project_maya")
    requires_python = frozenset(
        item.strip()
        for item in (metadata.get("Requires-Python") or "").split(",")
        if item.strip()
    )
    if requires_python != MAYA_PYTHON_REQUIRES:
        raise RuntimeError(
            "wheel has unexpected Python requirement: "
            f"{metadata.get('Requires-Python')!r}"
        )
    requires_dist = metadata.get_all("Requires-Dist") or []
    hermes_requirement = next(
        (
            item
            for item in requires_dist
            if item.replace(" ", "").startswith(HERMES_RUNTIME_REQUIREMENT_PREFIX)
        ),
        "",
    )
    if HERMES_RUNTIME_COMMIT not in hermes_requirement:
        raise RuntimeError("wheel does not declare pinned Hermes runtime dependency")
    normalized_requires_dist = [
        item.replace(" ", "").lower() for item in requires_dist
    ]
    if not any(
        item.startswith(f"{BROKER_CRYPTO_REQUIREMENT}>=")
        for item in normalized_requires_dist
    ):
        raise RuntimeError("wheel does not declare broker cryptography dependency")
    extras = set(metadata.get_all("Provides-Extra") or [])
    if "documents" not in extras:
        raise RuntimeError("wheel does not declare documents extra")
    if "documents-preview" not in extras:
        raise RuntimeError("wheel does not declare documents-preview extra")
    for package in sorted(DOCUMENTS_EXTRA_REQUIREMENTS):
        if not any(
            item.startswith(package) and 'extra=="documents"' in item
            for item in normalized_requires_dist
        ):
            raise RuntimeError(f"documents extra missing requirement: {package}")
    if not any(
        item.startswith("pymupdf") and 'extra=="documents-preview"' in item
        for item in normalized_requires_dist
    ):
        raise RuntimeError("documents-preview extra missing PyMuPDF requirement")
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


def _install_wheel(
    python: Path,
    wheel_path: Path,
    *,
    with_runtime_deps: bool = False,
) -> None:
    command = [
        str(python),
        "-m",
        "pip",
        "install",
        "--force-reinstall",
    ]
    if not with_runtime_deps:
        command.append("--no-deps")
    else:
        # The pinned Hermes dependency is a Git URL with a reused package
        # version. Force a source rebuild so a stale local wheel cache cannot
        # mask packaging regressions in the installed runtime surface.
        command.append("--no-cache-dir")
    command.append(str(wheel_path))
    _run(command, env=_clean_env())


def _verify_installed_hermes_runtime_dependency(python: Path, work_dir: Path) -> None:
    _run(
        [
            str(python),
            "-c",
            (
                "import importlib.metadata as metadata; "
                "import hermes_cli.config as hermes_config; "
                "from project_maya.adapters import HermesRuntimeAdapter; "
                "from run_agent import AIAgent; "
                "assert callable(AIAgent); "
                "required_config_attrs = "
                "('load_config', 'load_env', 'get_hermes_home', "
                "'_expand_env_vars'); "
                "missing = [name for name in required_config_attrs "
                "if not hasattr(hermes_config, name)]; "
                "assert not missing, "
                "f'installed hermes_cli.config missing {missing}'; "
                "dist = metadata.distribution('hermes-agent'); "
                "direct_url = dist.read_text('direct_url.json') or ''; "
                f"assert '{HERMES_RUNTIME_COMMIT}' in direct_url; "
                "adapter = HermesRuntimeAdapter(); "
                "compatibility = adapter.compatibility(); "
                "assert compatibility.compatible, compatibility.reason; "
                "print('hermes-runtime', dist.version, compatibility.runtime_name)"
            ),
        ],
        cwd=work_dir,
        env=_clean_env(),
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


def _verify_installed_dependency_contract_surfaces(
    python: Path,
    work_dir: Path,
) -> None:
    data_dir = work_dir / "dependency-maya-data"
    config_path = work_dir / "dependency-config.json"
    _write_minimal_config(config_path, data_dir)
    result = _run(
        [
            str(python),
            "-c",
            (
                "import json; "
                "from pathlib import Path; "
                "from project_maya import ComponentProfile, dependency_contracts; "
                "from project_maya.dependencies import evaluate_profile_readiness; "
                "from project_maya.config import config_from_mapping; "
                f"config = config_from_mapping(json.loads(Path(r'{config_path}').read_text())); "
                "contracts = dependency_contracts(); "
                "profiles = {contract.profile for contract in contracts}; "
                "assert ComponentProfile.DOCUMENTS in profiles; "
                "assert ComponentProfile.METABASE in profiles; "
                "assert ComponentProfile.MESSAGING in profiles; "
                "readiness = evaluate_profile_readiness(config, ComponentProfile.CORE); "
                "assert readiness.profile is ComponentProfile.CORE; "
                "print('dependency-contracts', len(contracts))"
            ),
        ],
        cwd=work_dir,
        env=_clean_env(),
    )
    if "dependency-contracts" not in result.stdout:
        raise RuntimeError("installed dependency contract check did not run")
    metadata_result = _run(
        [
            str(python),
            "-c",
            (
                "import importlib.metadata as metadata; "
                "dist = metadata.distribution('project-maya'); "
                "meta = dist.metadata; "
                "extras = set(meta.get_all('Provides-Extra') or []); "
                "assert 'documents' in extras; "
                "assert 'documents-preview' in extras; "
                "requires = [item.replace(' ', '').lower() "
                "for item in (meta.get_all('Requires-Dist') or [])]; "
                "missing = [package for package in "
                "('markdown', 'pillow', 'pypdf', 'reportlab') "
                "if not any(item.startswith(package) and "
                "'extra==\"documents\"' in item for item in requires)]; "
                "assert not missing, missing; "
                "assert any(item.startswith('pymupdf') and "
                "'extra==\"documents-preview\"' in item for item in requires); "
                "print('documents-extra-ready')"
            ),
        ],
        cwd=work_dir,
        env=_clean_env(),
    )
    if "documents-extra-ready" not in metadata_result.stdout:
        raise RuntimeError("installed documents extra metadata check did not run")
    documents_config_path = work_dir / "documents-dependency-config.json"
    _write_minimal_config(
        documents_config_path,
        work_dir / "documents-dependency-maya-data",
        enabled_profiles=("maya-core", "maya-documents"),
    )
    doctor_result = _run_allow_exit(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "doctor",
            "--config",
            str(documents_config_path),
        ],
        cwd=work_dir,
        env=_clean_env(),
        expected_exit=1,
    )
    for expected in (
        "dependencies.profile.maya-documents",
        "dependencies.python.pypdf",
        "dependencies.python.markdown",
        "dependencies.python.pillow",
        "dependencies.command.pdftoppm",
        "dependencies.application.ms-office",
    ):
        if expected not in doctor_result.stdout:
            raise RuntimeError(f"installed doctor missing document check: {expected}")
    if "secret://" in doctor_result.stdout:
        raise RuntimeError("installed document dependency doctor printed a secret ref")
    metabase_config_path = work_dir / "metabase-dependency-config.json"
    _write_minimal_config(
        metabase_config_path,
        work_dir / "metabase-dependency-maya-data",
        enabled_profiles=("maya-core", "maya-metabase"),
        include_metabase=True,
    )
    metabase_doctor_result = _run_allow_exit(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "doctor",
            "--config",
            str(metabase_config_path),
        ],
        cwd=work_dir,
        env=_clean_env(),
        expected_exit=1,
    )
    for expected in (
        "dependencies.profile.maya-metabase",
        "dependencies.runtime.java",
        "dependencies.service.metabase",
        "dependencies.database.metabase-application",
        "dependencies.database.metabase-analytics-sources",
    ):
        if expected not in metabase_doctor_result.stdout:
            raise RuntimeError(f"installed doctor missing Metabase check: {expected}")
    if "secret://metabase" in metabase_doctor_result.stdout:
        raise RuntimeError("installed Metabase dependency doctor printed a secret ref")
    browser_config_path = work_dir / "browser-dependency-config.json"
    _write_minimal_config(
        browser_config_path,
        work_dir / "browser-dependency-maya-data",
        enabled_profiles=("maya-core", "maya-browser"),
    )
    browser_doctor_result = _run_allow_exit(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "doctor",
            "--config",
            str(browser_config_path),
        ],
        cwd=work_dir,
        env=_clean_env(),
        expected_exit=1,
    )
    for expected in (
        "dependencies.profile.maya-browser",
        "dependencies.browser.executable",
        "dependencies.browser.automation-driver",
        "dependencies.browser.governance-policy",
    ):
        if expected not in browser_doctor_result.stdout:
            raise RuntimeError(f"installed doctor missing browser check: {expected}")
    if "secret://" in browser_doctor_result.stdout:
        raise RuntimeError("installed browser dependency doctor printed a secret ref")
    local_model_config_path = work_dir / "local-model-dependency-config.json"
    _write_minimal_config(
        local_model_config_path,
        work_dir / "local-model-dependency-maya-data",
        enabled_profiles=("maya-core", "maya-local-models"),
        include_local_model=True,
    )
    local_model_doctor_result = _run_allow_exit(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "doctor",
            "--config",
            str(local_model_config_path),
        ],
        cwd=work_dir,
        env=_clean_env(),
        expected_exit=1,
    )
    for expected in (
        "dependencies.profile.maya-local-models",
        "dependencies.endpoint.local-model",
        "dependencies.runtime.local-model-family",
        "dependencies.model.local-model-artifact",
        "family=ollama",
        "model_presence=not_probed",
    ):
        if expected not in local_model_doctor_result.stdout:
            raise RuntimeError(
                f"installed doctor missing local model check: {expected}"
            )
    if "127.0.0.1:11434" in local_model_doctor_result.stdout:
        raise RuntimeError("installed local model doctor printed endpoint host")
    messaging_config_path = work_dir / "messaging-dependency-config.json"
    _write_minimal_config(
        messaging_config_path,
        work_dir / "messaging-dependency-maya-data",
        enabled_profiles=("maya-core", "maya-messaging"),
        include_messaging=True,
    )
    messaging_doctor_result = _run_allow_exit(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "doctor",
            "--config",
            str(messaging_config_path),
        ],
        cwd=work_dir,
        env=_clean_env(),
        expected_exit=1,
    )
    for expected in (
        "dependencies.profile.maya-messaging",
        "dependencies.service.google",
        "dependencies.connector.google-contract",
        "dependencies.connector.google-governance",
        "dependencies.service.slack",
        "dependencies.connector.slack-contract",
        "dependencies.connector.slack-governance",
        "dependencies.service.telegram",
        "dependencies.connector.telegram-contract",
        "dependencies.connector.telegram-governance",
    ):
        if expected not in messaging_doctor_result.stdout:
            raise RuntimeError(f"installed doctor missing messaging check: {expected}")
    if "secret://integrations" in messaging_doctor_result.stdout:
        raise RuntimeError("installed messaging dependency doctor printed a secret ref")


def _verify_installed_skill_allowlist_surfaces(
    python: Path,
    work_dir: Path,
) -> None:
    result = _run(
        [
            str(python),
            "-c",
            (
                "from project_maya import document_skill_allowlist; "
                "skills = document_skill_allowlist(); "
                "assert len(skills) == 1; "
                "skill = skills[0]; "
                "assert skill.skill_id == 'documents/pdf'; "
                "assert skill.source_path == 'packaged_skills/pdf/SKILL.md'; "
                "assert 'documents.extract-text' in skill.capabilities; "
                "assert 'documents.convert' in skill.capabilities; "
                "print('document-skill-allowlist-ready')"
            ),
        ],
        cwd=work_dir,
        env=_clean_env(),
    )
    if "document-skill-allowlist-ready" not in result.stdout:
        raise RuntimeError("installed document skill allowlist check did not run")


def _verify_installed_phase3_metabase_document_surfaces(
    python: Path,
    work_dir: Path,
) -> None:
    data_dir = work_dir / "phase3-metabase-documents-maya-data"
    config_path = work_dir / "phase3-metabase-documents-config.json"
    _write_minimal_config(
        config_path,
        data_dir,
        enabled_profiles=("maya-core", "maya-documents", "maya-metabase"),
        include_metabase=True,
    )
    policy_path = data_dir / "governance" / "policy.json"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text(
        json.dumps(
            {
                "allow": [
                    {
                        "capability": "documents.inspect",
                        "operation": "inspect",
                        "decision": "allow",
                    },
                    {
                        "capability": "documents.create-pdf",
                        "operation": "create-pdf",
                        "decision": "allow",
                    },
                    {
                        "capability": "documents.extract-text",
                        "operation": "extract-text",
                        "decision": "allow",
                    },
                    {
                        "capability": "documents.convert",
                        "operation": "convert",
                        "decision": "allow",
                    },
                    {
                        "capability": "metabase.apply-provision",
                        "operation": "apply-provision",
                        "decision": "allow",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    documents_dir = data_dir / "documents"
    documents_dir.mkdir(parents=True)
    sample = documents_dir / "sample.txt"
    sample.write_text("installed package smoke text", encoding="utf-8")
    import_result = _run(
        [
            str(python),
            "-c",
            (
                "from project_maya.documents import inspect_document, convert_document; "
                "from project_maya.metabase import ("
                "GovernedMetabaseViewSpec, MetabaseDashboardSpec, "
                "plan_metabase_provisioning); "
                "from project_maya.skills import packaged_document_skill_status; "
                "assert callable(inspect_document); "
                "assert callable(convert_document); "
                "assert GovernedMetabaseViewSpec; "
                "assert MetabaseDashboardSpec; "
                "assert callable(plan_metabase_provisioning); "
                "assert packaged_document_skill_status()[0].discoverable; "
                "print('phase3-metabase-documents-importable')"
            ),
        ],
        cwd=work_dir,
        env=_clean_env(),
    )
    if "phase3-metabase-documents-importable" not in import_result.stdout:
        raise RuntimeError("installed V2 Phase 3 capability import check did not run")
    documents_result = _run(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "documents",
            "inspect",
            "--config",
            str(config_path),
            "--source",
            str(sample),
        ],
        cwd=work_dir,
        env=_clean_env(),
    )
    documents_payload = json.loads(documents_result.stdout)
    if documents_payload.get("operation") != "inspect":
        raise RuntimeError("installed documents inspect did not run")
    if "installed package smoke text" in documents_result.stdout:
        raise RuntimeError("installed documents inspect leaked document contents")
    if str(sample) in documents_result.stdout:
        raise RuntimeError("installed documents inspect leaked full source path")
    create_result = _run_allow_exit(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "documents",
            "create-pdf",
            "--config",
            str(config_path),
            "--output",
            "created.pdf",
            "--text",
            "installed package create text",
        ],
        cwd=work_dir,
        env=_clean_env(),
        expected_exit=1,
    )
    if "document_operation_failed" not in create_result.stdout:
        raise RuntimeError("installed documents create-pdf did not fail safely")
    if "installed package create text" in create_result.stdout:
        raise RuntimeError("installed documents create-pdf leaked source text")
    fake_pdf = documents_dir / "sample.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4\n% package verifier placeholder\n")
    extract_result = _run_allow_exit(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "documents",
            "extract-text",
            "--config",
            str(config_path),
            "--source",
            str(fake_pdf),
            "--to",
            "sample.txt",
        ],
        cwd=work_dir,
        env=_clean_env(),
        expected_exit=1,
    )
    if "document_operation_failed" not in extract_result.stdout:
        raise RuntimeError("installed documents extract-text did not fail safely")
    if str(fake_pdf) in extract_result.stdout:
        raise RuntimeError("installed documents extract-text leaked full source path")
    if (documents_dir / "outputs" / "sample.txt").exists():
        raise RuntimeError("installed documents failed extraction wrote output")
    metabase_health_result = _run(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "metabase",
            "health",
            "--config",
            str(config_path),
        ],
        cwd=work_dir,
        env=_clean_env(),
    )
    health_payload = json.loads(metabase_health_result.stdout)
    if health_payload.get("status") != "ready":
        raise RuntimeError("installed Metabase health did not report ready")
    metabase_lifecycle_result = _run(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "metabase",
            "lifecycle",
            "--config",
            str(config_path),
        ],
        cwd=work_dir,
        env=_clean_env(),
    )
    lifecycle_payload = json.loads(metabase_lifecycle_result.stdout)
    if lifecycle_payload.get("status") not in {
        "customer_managed",
        "managed_local_ready",
        "managed_local_artifact_missing",
    }:
        raise RuntimeError("installed Metabase lifecycle reported unexpected state")
    metabase_plan_result = _run(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "metabase",
            "plan-provision",
            "--config",
            str(config_path),
            "--write",
        ],
        cwd=work_dir,
        env=_clean_env(),
    )
    plan_payload = json.loads(metabase_plan_result.stdout)
    if plan_payload.get("status") != "planned":
        raise RuntimeError("installed Metabase provisioning plan did not run")
    if plan_payload.get("plan_ref") != "maya-data/metabase/provisioning/latest-plan.json":
        raise RuntimeError("installed Metabase provisioning plan was not persisted")
    plan_path = data_dir / "metabase" / "provisioning" / "latest-plan.json"
    if not plan_path.is_file():
        raise RuntimeError("installed Metabase provisioning plan file missing")
    plan_text = plan_path.read_text(encoding="utf-8")
    if "secret://metabase" in metabase_plan_result.stdout:
        raise RuntimeError("installed Metabase plan printed a secret ref")
    if "secret://metabase" in plan_text:
        raise RuntimeError("installed Metabase persisted plan printed a secret ref")
    metabase_apply_result = _run(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "metabase",
            "apply-provision",
            "--config",
            str(config_path),
            "--apply",
        ],
        cwd=work_dir,
        env=_clean_env(),
    )
    apply_payload = json.loads(metabase_apply_result.stdout)
    if apply_payload.get("status") != "applied":
        raise RuntimeError("installed Metabase apply-provision did not run")
    applied_path = data_dir / "metabase" / "provisioning" / "last-applied-plan.json"
    if not applied_path.is_file():
        raise RuntimeError("installed Metabase applied plan file missing")
    dashboard_path = data_dir / "metabase" / "provisioning" / "dashboards.json"
    if not dashboard_path.is_file():
        raise RuntimeError("installed Metabase dashboards.json file missing")
    if "secret://metabase" in applied_path.read_text(encoding="utf-8"):
        raise RuntimeError("installed Metabase applied plan printed a secret ref")
    if "secret://metabase" in dashboard_path.read_text(encoding="utf-8"):
        raise RuntimeError("installed Metabase dashboard plan printed a secret ref")
    doctor_result = _run_allow_exit(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "doctor",
            "--config",
            str(config_path),
        ],
        cwd=work_dir,
        env=_clean_env(),
        expected_exit=1,
    )
    for expected in (
        "documents.documents-root",
        "documents.documents-cache",
        "documents.documents-outputs",
        "documents.pdf-extraction",
        "documents.pdf-creation",
        "documents.libreoffice-conversion",
        "metabase.health",
        "metabase.lifecycle",
        "metabase.provisioning",
        "skills.documents.pdf",
    ):
        if expected not in doctor_result.stdout:
            raise RuntimeError(f"installed doctor missing V2 Phase 3 check: {expected}")
    if "secret://metabase" in doctor_result.stdout:
        raise RuntimeError("installed V2 Phase 3 doctor printed a secret ref")
    skills_result = _run(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "skills",
            "status",
            "--config",
            str(config_path),
        ],
        cwd=work_dir,
        env=_clean_env(),
    )
    if "documents/pdf" not in skills_result.stdout:
        raise RuntimeError("installed skills status omitted packaged document skill")


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
    if payload.get("mutation"):
        raise RuntimeError("installed update CLI reported mutation")


def _verify_installed_phase5_broker_surfaces(
    python: Path,
    work_dir: Path,
) -> None:
    data_dir = work_dir / "phase5-broker-maya-data"
    config_path = work_dir / "phase5-broker-config.json"
    _write_minimal_config(config_path, data_dir)
    import_result = _run(
        [
            str(python),
            "-c",
            (
                "from project_maya import (BROKER_PROTOCOL_VERSION, "
                "BrokerInstanceIdentity, SignedBrokerRequest, "
                "TokenLifecycleStatus, broker_status); "
                "assert BROKER_PROTOCOL_VERSION == 'maya-broker-v1'; "
                "assert callable(broker_status); "
                "print('phase5-broker-surfaces-importable')"
            ),
        ],
        cwd=work_dir,
        env=_clean_env(),
    )
    if "phase5-broker-surfaces-importable" not in import_result.stdout:
        raise RuntimeError("installed V2 Phase 5 broker surfaces were not importable")
    status_result = _run(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "broker",
            "status",
            "--config",
            str(config_path),
        ],
        cwd=work_dir,
        env=_clean_env(),
    )
    payload = json.loads(status_result.stdout)
    if payload.get("operation") != "broker.status":
        raise RuntimeError("installed broker status did not run")
    if payload.get("network_used"):
        raise RuntimeError("installed broker status used network")
    if "access_token" in status_result.stdout or "refresh_token" in status_result.stdout:
        raise RuntimeError("installed broker status leaked token field names")


def _verify_installed_phase4_operator_surfaces(
    python: Path,
    work_dir: Path,
) -> None:
    data_dir = work_dir / "phase4-operator-maya-data"
    runtime_module = work_dir / "phase4_operator_runtime.py"
    runtime_module.write_text(
        "\n".join(
            [
                "class Runtime:",
                "    def __init__(self, **kwargs):",
                "        self.session_id = 'phase4-operator-runtime'",
                "        self._memory_manager = type('MemoryManager', (), {'provider': type('Provider', (), {'shutdown': lambda self: None})()})()",
                "    def chat(self, message):",
                "        return 'phase4-ok'",
                "    def shutdown_memory_provider(self):",
                "        self._memory_manager.provider.shutdown()",
            ]
        ),
        encoding="utf-8",
    )
    config_path = work_dir / "phase4-operator-config.json"
    _write_minimal_config(
        config_path,
        data_dir,
        hermes_factory="phase4_operator_runtime:Runtime",
    )
    import_result = _run(
        [
            str(python),
            "-c",
            (
                "from project_maya import plan_setup, summarize_health, "
                "inspect_backup_archive, plan_restore_backup; "
                "assert callable(plan_restore_backup); "
                "print('phase4-operator-surfaces-importable')"
            ),
        ],
        cwd=work_dir,
        env=_clean_env(),
    )
    if "phase4-operator-surfaces-importable" not in import_result.stdout:
        raise RuntimeError("installed V2 Phase 4 operator surfaces were not importable")
    setup_result = _run(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "setup",
            "plan",
            "--config",
            str(config_path),
        ],
        cwd=work_dir,
        env=_clean_env(),
    )
    setup_payload = json.loads(setup_result.stdout)
    if setup_payload.get("operation") != "plan":
        raise RuntimeError("installed setup plan did not run")
    if "secret://" in setup_result.stdout:
        raise RuntimeError("installed setup plan printed a secret ref")
    init_result = _run(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "setup",
            "init",
            "--config",
            str(config_path),
        ],
        cwd=work_dir,
        env=_clean_env(),
    )
    if not json.loads(init_result.stdout).get("dry_run"):
        raise RuntimeError("installed setup init was not dry-run by default")
    data_dir.mkdir(parents=True, exist_ok=True)
    health_result = _run_allow_exit(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "health",
            "summary",
            "--config",
            str(config_path),
        ],
        expected_exit=1,
        cwd=work_dir,
        env=_clean_env(),
    )
    health_payload = json.loads(health_result.stdout)
    if "categories" not in health_payload:
        raise RuntimeError("installed health summary omitted categories")
    if health_payload.get("network_used"):
        raise RuntimeError("installed health summary used network")
    backup_path = work_dir / "phase4-backup.zip"
    backup_result = _run(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "backup",
            "--config",
            str(config_path),
            "--to",
            str(backup_path),
        ],
        cwd=work_dir,
        env=_clean_env(),
    )
    if "maya-backup-manifest" in backup_result.stdout:
        raise RuntimeError("installed backup printed archive internals")
    inspect_result = _run(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "backup",
            "inspect",
            "--from",
            str(backup_path),
        ],
        cwd=work_dir,
        env=_clean_env(),
    )
    inspect_payload = json.loads(inspect_result.stdout)
    if inspect_payload["manifest"]["schema_version"] != 1:
        raise RuntimeError("installed backup inspect omitted manifest")
    restore_result = _run(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "restore",
            "--from",
            str(backup_path),
            "--to",
            str(work_dir / "phase4-restore"),
        ],
        cwd=work_dir,
        env=_clean_env(),
    )
    if json.loads(restore_result.stdout).get("status") != "dry_run":
        raise RuntimeError("installed restore was not dry-run")
    conflict_destination = work_dir / "phase4-restore-conflict"
    conflict_file = conflict_destination / "config" / "maya-config.json"
    conflict_file.parent.mkdir(parents=True, exist_ok=True)
    conflict_file.write_text("existing", encoding="utf-8")
    conflict_result = _run_allow_exit(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "restore",
            "--from",
            str(backup_path),
            "--to",
            str(conflict_destination),
        ],
        expected_exit=1,
        cwd=work_dir,
        env=_clean_env(),
    )
    if "restore_failed" not in conflict_result.stdout:
        raise RuntimeError("installed restore conflict did not fail safely")
    if str(conflict_destination) in conflict_result.stdout:
        raise RuntimeError("installed restore conflict leaked destination path")
    update_result = _run(
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
    update_payload = json.loads(update_result.stdout)
    if update_payload.get("network_used") or update_payload.get("mutation"):
        raise RuntimeError("installed update readiness used network or mutation")
    legacy_db = work_dir / "phase4-legacy-memory.sqlite"
    migrated_db = work_dir / "phase4-migrated-memory.sqlite"
    with closing(sqlite3.connect(legacy_db)) as conn:
        conn.execute("CREATE TABLE memory_kv (key TEXT PRIMARY KEY, value TEXT)")
        conn.execute("INSERT INTO memory_kv(key, value) VALUES (?, ?)", ("k", "v"))
        conn.commit()
    migrate_result = _run(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "migrate",
            "--from",
            str(legacy_db),
            "--to",
            str(migrated_db),
            "--dry-run",
        ],
        cwd=work_dir,
        env=_clean_env(),
    )
    migrate_payload = json.loads(migrate_result.stdout)
    if not migrate_payload.get("dry_run"):
        raise RuntimeError("installed Phase 4 migration was not dry-run")
    if migrated_db.exists():
        raise RuntimeError("installed Phase 4 migration dry-run wrote destination")


def _verify_installed_enterprise_byo_surfaces(
    python: Path,
    work_dir: Path,
) -> None:
    data_dir = work_dir / "enterprise-maya-data"
    runtime_module = work_dir / "package_verify_runtime.py"
    runtime_module.write_text(
        "\n".join(
            [
                "class Runtime:",
                "    def __init__(self, **kwargs):",
                "        self.kwargs = kwargs",
                "    def attach_memory(self, memory_provider):",
                "        self.memory_provider = memory_provider",
                "    def start(self, *, agent_name):",
                "        self.agent_name = agent_name",
                "    def run(self, request, **kwargs):",
                "        return {'request': request, 'kwargs': kwargs}",
                "    def stop(self):",
                "        self.stopped = True",
            ]
        ),
        encoding="utf-8",
    )
    config_path = work_dir / "enterprise-byo-config.json"
    _write_enterprise_byo_config(
        config_path,
        data_dir,
        hermes_factory="package_verify_runtime:Runtime",
    )

    _run(
        [
            str(python),
            "-c",
            (
                "import json; "
                "from pathlib import Path; "
                "from project_maya import "
                "ProviderRevocationStatus, config_from_mapping, "
                "validate_configured_connectors, validate_model_config; "
                f"config = config_from_mapping(json.loads(Path(r'{config_path}').read_text())); "
                "model = validate_model_config(config); "
                "connectors = validate_configured_connectors(config.integrations, broker_mode=config.broker.mode); "
                "assert model.valid and not model.network_used; "
                "assert all(item.valid and not item.network_used for item in connectors); "
                "assert ProviderRevocationStatus.UNAVAILABLE.value == 'unavailable'"
            ),
        ],
        cwd=work_dir,
        env=_clean_env(),
    )

    export_result = _run(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "export-config",
            "--config",
            str(config_path),
        ],
        cwd=work_dir,
        env=_clean_env(),
    )
    exported = json.loads(export_result.stdout)
    if exported["product"]["edition"] != "enterprise":
        raise RuntimeError("installed export-config did not preserve Enterprise edition")
    if exported["broker"]["mode"] != "disabled":
        raise RuntimeError("installed export-config did not preserve disabled broker")
    if exported["integrations"]["google"]["credential_mode"] != "customer_owned":
        raise RuntimeError("installed export-config did not preserve BYO Google mode")

    imported_path = work_dir / "enterprise-imported-config.json"
    import_result = _run(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "import-config",
            "--from",
            str(config_path),
            "--to",
            str(imported_path),
        ],
        cwd=work_dir,
        env=_clean_env(),
    )
    import_payload = json.loads(import_result.stdout)
    if import_payload.get("status") != "dry_run":
        raise RuntimeError("installed import-config did not default to dry-run")
    if imported_path.exists():
        raise RuntimeError("installed import-config dry-run wrote destination")

    state_dir = data_dir / "integrations" / "google"
    state_dir.mkdir(parents=True)
    (state_dir / "state.json").write_text("{}", encoding="utf-8")
    reset_result = _run(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "reset-integration",
            "google",
            "--config",
            str(config_path),
            "--revoke-provider",
        ],
        cwd=work_dir,
        env=_clean_env(),
    )
    reset_payload = json.loads(reset_result.stdout)
    if reset_payload.get("provider_revocation_status") != "unavailable":
        raise RuntimeError(
            "installed reset-integration did not report revocation unavailable"
        )
    if reset_payload.get("external_revocation_performed"):
        raise RuntimeError("installed reset-integration falsely claimed revocation")
    if "secret://" in reset_result.stdout:
        raise RuntimeError("installed reset-integration printed a secret ref")

    doctor_result = _run_allow_exit(
        [
            str(python),
            "-m",
            "project_maya.cli",
            "doctor",
            "--config",
            str(config_path),
        ],
        cwd=work_dir,
        env=_clean_env(),
        expected_exit=1,
    )
    if "model.config" not in doctor_result.stdout:
        raise RuntimeError("installed doctor did not report model config")
    if "connectors.config" not in doctor_result.stdout:
        raise RuntimeError("installed doctor did not report connector config")
    if "health=unavailable" not in doctor_result.stdout:
        raise RuntimeError("installed doctor did not report redacted connector health")
    if "secret://" in doctor_result.stdout:
        raise RuntimeError("installed doctor printed a secret ref")


def _verify_installed_phase2_profile_model_and_secret_surfaces(
    python: Path,
    work_dir: Path,
) -> None:
    data_dir = work_dir / "enterprise-local-model-data"
    profile_path = work_dir / "enterprise-local-model-profile.json"
    runtime_module = work_dir / "package_verify_local_runtime.py"
    runtime_module.write_text(
        "\n".join(
            [
                "EVENTS = []",
                "class Runtime:",
                "    def __init__(self, **kwargs):",
                "        EVENTS.append(('init', kwargs))",
                "    def attach_memory(self, memory_provider):",
                "        EVENTS.append(('memory', type(memory_provider).__name__))",
                "    def start(self, *, agent_name):",
                "        EVENTS.append(('start', agent_name))",
                "    def run(self, request, **kwargs):",
                "        EVENTS.append(('run', request, kwargs))",
                "        return 'local-model-ok'",
                "    def stop(self):",
                "        EVENTS.append(('stop',))",
            ]
        ),
        encoding="utf-8",
    )
    _write_enterprise_local_model_profile(profile_path)
    _run(
        [
            str(python),
            "-c",
            (
                "from pathlib import Path; "
                "from project_maya import "
                "AuthorizationResult, GovernanceDecision, "
                "InMemoryEnterpriseSecretBackend, SecretBackendDescriptor, "
                "SecretBackendKind, SecretRef, build_local_product, "
                "config_from_mapping, config_to_mapping, load_config_profile, "
                "validate_local_model_endpoint; "
                "Gateway = type('Gateway', (), {"
                "'__init__': lambda self: setattr(self, 'requests', []), "
                "'authorize': lambda self, request: "
                "(self.requests.append(request) or AuthorizationResult("
                "decision=GovernanceDecision.ALLOW, "
                "reason_code='verify.allow'))}); "
                f"profile = Path(r'{profile_path}'); "
                f"data_dir = Path(r'{data_dir}'); "
                "config = load_config_profile("
                "profile, data_dir=data_dir, instance_id='verify-local-model'); "
                "readiness = validate_local_model_endpoint(config); "
                "assert readiness.ready and readiness.endpoint_family == 'ollama'; "
                "assert readiness.openai_compatible and not readiness.network_used; "
                "assert '127.0.0.1:11434' not in readiness.redacted_summary(); "
                "mapping = config_to_mapping(config); "
                "mapping['runtime']['hermes_factory'] = "
                "'package_verify_local_runtime:Runtime'; "
                "gateway = Gateway(); "
                "product = build_local_product("
                "config_from_mapping(mapping), gateway=gateway); "
                "product.start(); "
                "assert product.run('hello') == 'local-model-ok'; "
                "product.stop(); "
                "assert [r.capability for r in gateway.requests] == "
                "['runtime.execute']; "
                "descriptor = SecretBackendDescriptor("
                "kind=SecretBackendKind.EXTERNAL_VAULT, "
                "name='verify-vault', "
                "location='https://vault.customer.example', "
                "key_ref=SecretRef.parse('secret://vault/key')); "
                "backend = InMemoryEnterpriseSecretBackend(descriptor); "
                "ref = SecretRef.parse('secret://llm/local'); "
                "backend.write(ref, 'secret-value'); "
                "assert backend.read(ref) == 'secret-value'; "
                "health = backend.health(); "
                "assert health.backend == 'verify-vault'; "
                "assert 'secret-value' not in health.message; "
                "assert 'https://vault.customer.example' not in health.message; "
                "assert 'secret://vault/key' not in health.message"
            ),
        ],
        cwd=work_dir,
        env=_clean_env(),
    )


def _write_minimal_config(
    config_path: Path,
    data_dir: Path,
    *,
    include_google: bool = False,
    enabled_profiles: tuple[str, ...] = ("maya-core",),
    include_metabase: bool = False,
    include_local_model: bool = False,
    include_messaging: bool = False,
    hermes_factory: str | None = None,
) -> None:
    integrations = {}
    if include_google:
        integrations["google"] = {
            "enabled": True,
            "credential_mode": "customer_owned",
            "credential_ref": "secret://integrations/google",
        }
    if include_messaging:
        integrations.update(
            {
                "google": {
                    "enabled": True,
                    "credential_mode": "customer_owned",
                    "credential_ref": "secret://integrations/google",
                },
                "slack": {
                    "enabled": True,
                    "credential_mode": "customer_owned",
                    "credential_ref": "secret://integrations/slack",
                },
                "telegram": {
                    "enabled": True,
                    "credential_mode": "customer_owned",
                    "credential_ref": "secret://integrations/telegram",
                },
            }
        )
    metabase = {
        "enabled": False,
        "deployment": "disabled",
        "endpoint": None,
        "application_database": None,
        "analytics_sources": [],
    }
    if include_metabase:
        metabase = {
            "enabled": True,
            "deployment": "managed_local",
            "endpoint": "http://127.0.0.1:3000",
            "application_database": {
                "engine": "sqlite",
                "credential_ref": "secret://metabase/application-db",
            },
            "analytics_sources": [
                {
                    "name": "maya_operational",
                    "engine": "sqlite",
                    "credential_ref": "secret://metabase/maya-operational",
                }
            ],
        }
    llm = {
        "mode": "customer_owned",
        "provider": "openai",
        "model": "gpt-test",
        "fallback_model": None,
        "credential_ref": "secret://llm/openai",
        "endpoint": None,
        "timeout_seconds": 60,
    }
    if include_local_model:
        llm = {
            "mode": "local",
            "provider": "openai-compatible",
            "model": "local-model",
            "fallback_model": None,
            "credential_ref": None,
            "endpoint": "http://127.0.0.1:11434/v1",
            "timeout_seconds": 120,
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
                    "enabled_profiles": list(enabled_profiles),
                    "hermes_factory": hermes_factory,
                },
                "broker": {"mode": "disabled", "endpoint": None},
                "llm": llm,
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
                "metabase": metabase,
                "local_api": {
                    "bind": "127.0.0.1",
                    "port": None,
                    "remote_access": False,
                },
            }
        ),
        encoding="utf-8",
    )


def _write_enterprise_local_model_profile(profile_path: Path) -> None:
    profile_path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "product": {
                    "edition": "enterprise",
                    "instance_id": "${MAYA_INSTANCE_ID}",
                },
                "deployment": {
                    "class": "desktop",
                    "network_policy": "enterprise-local-model",
                    "data_dir": "${MAYA_DATA_DIR}",
                },
                "runtime": {
                    "hermes_compatibility": "phase2-test",
                    "enabled_profiles": ["maya-core", "maya-local-models"],
                },
                "broker": {"mode": "disabled", "endpoint": None},
                "llm": {
                    "mode": "local",
                    "provider": "openai-compatible",
                    "model": "local-model",
                    "credential_ref": None,
                    "endpoint": "http://127.0.0.1:11434/v1",
                    "timeout_seconds": 120,
                },
                "integrations": {
                    "google": {
                        "enabled": False,
                        "credential_mode": "disabled",
                        "credential_ref": None,
                    },
                    "slack": {
                        "enabled": False,
                        "credential_mode": "disabled",
                        "credential_ref": None,
                    },
                    "telegram": {
                        "enabled": False,
                        "credential_mode": "disabled",
                        "credential_ref": None,
                    },
                },
                "memory": {
                    "hermes_provider": "local",
                    "retriever": "local_json",
                    "registry": "sqlite",
                    "governance_enabled": True,
                },
                "governance": {
                    "policy_file": (
                        "${MAYA_DATA_DIR}/governance/policies/local-model.json"
                    ),
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


def _write_enterprise_byo_config(
    config_path: Path,
    data_dir: Path,
    *,
    hermes_factory: str,
) -> None:
    config_path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "product": {
                    "edition": "enterprise",
                    "instance_id": "verify-enterprise",
                },
                "deployment": {
                    "class": "desktop",
                    "network_policy": "offline",
                    "data_dir": str(data_dir),
                },
                "runtime": {
                    "hermes_compatibility": "phase2-test",
                    "enabled_profiles": ["maya-core"],
                    "hermes_factory": hermes_factory,
                },
                "broker": {"mode": "disabled", "endpoint": None},
                "llm": {
                    "mode": "customer_owned",
                    "provider": "openai",
                    "model": "gpt-test",
                    "credential_ref": "secret://llm/openai",
                    "endpoint": None,
                    "timeout_seconds": 60,
                },
                "integrations": {
                    "google": {
                        "enabled": True,
                        "credential_mode": "customer_owned",
                        "credential_ref": "secret://integrations/google",
                    },
                    "slack": {
                        "enabled": True,
                        "credential_mode": "customer_owned",
                        "credential_ref": "secret://integrations/slack",
                    },
                    "telegram": {
                        "enabled": True,
                        "credential_mode": "customer_owned",
                        "credential_ref": "secret://integrations/telegram",
                    },
                },
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


def _run_allow_exit(
    command: list[str],
    *,
    expected_exit: int,
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
    if result.returncode != expected_exit:
        joined = " ".join(command)
        raise RuntimeError(
            f"command returned {result.returncode}, expected {expected_exit}: "
            f"{joined}\n{result.stdout}"
        )
    return result


if __name__ == "__main__":
    raise SystemExit(main())
