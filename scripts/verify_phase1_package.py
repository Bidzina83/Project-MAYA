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
) -> None:
    integrations = {}
    if include_google:
        integrations["google"] = {
            "enabled": True,
            "credential_mode": "customer_owned",
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
