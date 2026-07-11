"""Verify a Project MAYA Phase 6 release directory."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from project_maya.release import (  # noqa: E402
    load_json_object,
    sha256_file,
    verify_release_manifest,
    verify_rollback_manifest,
    verify_update_manifest,
)


FORBIDDEN_ARTIFACT_FRAGMENTS = (
    "__pycache__",
    ".pytest_cache",
    "/tests/",
    "\\tests\\",
    "secret://",
)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    release_dir = args.release_dir.resolve()
    if args.platform != "windows-desktop":
        raise SystemExit("Phase 6 only advertises windows-desktop")
    release_manifest = verify_release_manifest(
        load_json_object(release_dir / "release-manifest.json"),
        expected_platform=args.platform,
    )
    update_manifest = verify_update_manifest(
        load_json_object(release_dir / "update-manifest.json"),
        expected_platform=args.platform,
    )
    rollback_manifest = verify_rollback_manifest(
        load_json_object(release_dir / "rollback.json"),
        expected_platform=args.platform,
    )
    _require_file(release_dir / release_manifest.sbom_ref)
    _require_file(release_dir / release_manifest.provenance_ref)
    _verify_artifacts(release_dir, release_manifest)
    _verify_artifact_checksum(release_dir / update_manifest.artifact.path, update_manifest.artifact.sha256)
    _verify_artifact_checksum(release_dir / rollback_manifest.artifact.path, rollback_manifest.artifact.sha256)
    _verify_installer_bundle(release_dir / update_manifest.artifact.path)
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify signed Project MAYA Phase 6 release artifacts."
    )
    parser.add_argument("--release-dir", type=Path, required=True)
    parser.add_argument("--platform", required=True)
    return parser.parse_args(argv)


def _verify_artifacts(release_dir: Path, manifest) -> None:
    names = [artifact.path for artifact in manifest.artifacts]
    if not any(name.endswith(".whl") for name in names):
        raise RuntimeError("release does not include a wheel artifact")
    if not any(name.endswith(".zip") for name in names):
        raise RuntimeError("release does not include a Windows installer bundle")
    if not any(name.endswith("project-maya-standard.iss") for name in names):
        raise RuntimeError("release does not include Standard Inno Setup source")
    if not any(name.endswith("project-maya-enterprise.iss") for name in names):
        raise RuntimeError("release does not include Enterprise Inno Setup source")
    if not any(name.endswith("inno-installer-manifest.json") for name in names):
        raise RuntimeError("release does not include Inno installer manifest")
    for artifact in manifest.artifacts:
        path = release_dir / artifact.path
        _require_file(path)
        _verify_artifact_checksum(path, artifact.sha256)
        if any(fragment in artifact.path for fragment in FORBIDDEN_ARTIFACT_FRAGMENTS):
            raise RuntimeError("release artifact path contains forbidden content")
    _verify_inno_products(release_dir)


def _verify_artifact_checksum(path: Path, expected: str) -> None:
    if sha256_file(path) != expected:
        raise RuntimeError(f"artifact checksum mismatch: {path.name}")


def _verify_installer_bundle(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if "installer-manifest.json" not in names:
            raise RuntimeError("installer bundle lacks installer manifest")
        if not any(name.endswith(".whl") for name in names):
            raise RuntimeError("installer bundle lacks built wheel")
        _verify_payload_entries(names)
        forbidden = [
            name
            for name in names
            if any(fragment in name for fragment in FORBIDDEN_ARTIFACT_FRAGMENTS)
        ]
        if forbidden:
            raise RuntimeError("installer bundle contains forbidden entries")
        manifest = json.loads(archive.read("installer-manifest.json").decode("utf-8"))
    if not manifest.get("installs_from_built_artifact"):
        raise RuntimeError("installer bundle does not install from a built artifact")
    if manifest.get("payload_root") != "windows-app-payload":
        raise RuntimeError("installer bundle does not declare installed app payload")
    for required_layout in (
        "app",
        "runtime",
        "wheels",
        "skills",
        "services",
        "config-templates",
        "scripts",
        "release",
    ):
        if required_layout not in manifest.get("payload_layout", []):
            raise RuntimeError(f"installer bundle lacks managed payload layout: {required_layout}")
    for entry_point in (
        "bin/maya-cli.cmd",
        "bin/setup-maya.cmd",
        "bin/maya.cmd",
        "bin/maya-console.cmd",
        "bin/maya-doctor.cmd",
        "bin/maya-self-check.cmd",
    ):
        if entry_point not in manifest.get("installed_entry_points", []):
            raise RuntimeError(f"installer bundle does not declare {entry_point}")
    if manifest.get("silent_system_dependency_install"):
        raise RuntimeError("installer bundle silently installs system dependencies")
    if manifest.get("customer_tenant_resources_created"):
        raise RuntimeError("installer bundle creates customer tenant resources")
    if manifest.get("raw_secrets_stored"):
        raise RuntimeError("installer bundle stores raw secrets")
    payload_dir = path.parent / "windows-app-payload"
    if payload_dir.is_dir():
        _verify_product_launchers(payload_dir)
        _verify_installed_qualification(payload_dir)


def _verify_payload_entries(names: list[str]) -> None:
    required = (
        "windows-app-payload/app/project_maya/__init__.py",
        "windows-app-payload/app/sitecustomize.py",
        "windows-app-payload/app/plugins/__init__.py",
        "windows-app-payload/app/plugins/browser/__init__.py",
        "windows-app-payload/runtime/runtime-manifest.json",
        "windows-app-payload/runtime/component-readiness.json",
        "windows-app-payload/runtime/maya_runtime.py",
        "windows-app-payload/runtime/python/python.cmd",
        "windows-app-payload/wheels/requirements-pinned.txt",
        "windows-app-payload/wheels/wheelhouse-manifest.json",
        "windows-app-payload/skills/skills-manifest.json",
        "windows-app-payload/services/managed-services.json",
        "windows-app-payload/config-templates/standard.json.template",
        "windows-app-payload/config-templates/default-governance-policy.json",
        "windows-app-payload/scripts/maya_first_run.py",
        "windows-app-payload/scripts/maya_qualification.py",
        "windows-app-payload/bin/maya-cli.cmd",
        "windows-app-payload/bin/setup-maya.cmd",
        "windows-app-payload/bin/maya.cmd",
        "windows-app-payload/bin/maya-console.cmd",
        "windows-app-payload/bin/maya-doctor.cmd",
        "windows-app-payload/bin/maya-doctor-console.cmd",
        "windows-app-payload/bin/maya-self-check.cmd",
        "windows-app-payload/bin/maya-self-check-console.cmd",
    )
    for name in required:
        if name not in names:
            raise RuntimeError(f"installer bundle lacks payload entry: {name}")
    if not any(name.startswith("windows-app-payload/wheels/") and name.endswith(".whl") for name in names):
        raise RuntimeError("installer bundle lacks managed wheelhouse wheel")


def _verify_inno_products(release_dir: Path) -> None:
    inno_dir = release_dir / "inno"
    manifest = json.loads(
        (inno_dir / "inno-installer-manifest.json").read_text(encoding="utf-8")
    )
    if manifest.get("installer_family") != "inno-setup":
        raise RuntimeError("Inno installer manifest has unexpected family")
    if manifest.get("silent_system_dependency_install"):
        raise RuntimeError("Inno installer silently installs system dependencies")
    if manifest.get("customer_tenant_resources_created"):
        raise RuntimeError("Inno installer creates customer tenant resources")
    if not manifest.get("installs_from_built_artifact"):
        raise RuntimeError("Inno installer does not install from built artifacts")
    for edition in ("standard", "enterprise"):
        script = inno_dir / f"project-maya-{edition}.iss"
        _require_file(script)
        text = script.read_text(encoding="utf-8")
        for expected in (
            "#define MayaProductName \"Maya the Info Manager\"",
            "AppName={#MayaProductName} {#MayaEdition}",
            "DefaultDirName={localappdata}\\Programs\\Maya the Info Manager",
            "DefaultGroupName=Maya the Info Manager",
            "AllowNoIcons=yes",
            "UninstallDisplayName={#MayaProductName} {#MayaEdition}",
            "PrivilegesRequired=lowest",
            "[Tasks]",
            'Name: "startmenuicon"; Description: "Create Start Menu shortcuts"',
            'Name: "desktopicon"; Description: "Create a desktop shortcut"',
            'Source: "..\\windows-app-payload\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs',
            'Name: "{group}\\Maya the Info Manager"; Filename: "{app}\\bin\\maya-console.cmd"; Tasks: startmenuicon',
            'Name: "{group}\\Setup Maya"; Filename: "{app}\\bin\\setup-maya.cmd"; Tasks: startmenuicon',
            'Name: "{group}\\Start Maya"; Filename: "{app}\\bin\\maya-console.cmd"; Tasks: startmenuicon',
            'Name: "{group}\\Maya Doctor"; Filename: "{app}\\bin\\maya-doctor-console.cmd"; Tasks: startmenuicon',
            'Name: "{group}\\Maya Installed Qualification"; Filename: "{app}\\bin\\maya-self-check-console.cmd"; Tasks: startmenuicon',
            'Name: "{group}\\Maya Data Folder"; Filename: "{localappdata}\\Maya the Info Manager\\maya-data"; Tasks: startmenuicon',
            'Name: "{autodesktop}\\Maya the Info Manager"; Filename: "{app}\\bin\\maya-console.cmd"; Tasks: desktopicon',
            "Source: \"..\\",
            "release-manifest.json",
            "update-manifest.json",
            "rollback.json",
            "No system software, credentials, OAuth grants",
            "MAYA_HOME and MAYA_DATA_DIR are never deleted",
        ):
            if expected not in text:
                raise RuntimeError(f"Inno script missing required boundary: {expected}")
    _verify_compiled_installers_are_signed(inno_dir)
    _verify_managed_runtime_payload(release_dir / "windows-app-payload")
    _verify_packaged_payload_starts(release_dir / "windows-app-payload")
    _verify_product_launchers(release_dir / "windows-app-payload")
    _verify_installed_qualification(release_dir / "windows-app-payload")


def _verify_managed_runtime_payload(payload_dir: Path) -> None:
    runtime_manifest = json.loads(
        (payload_dir / "runtime" / "runtime-manifest.json").read_text(
            encoding="utf-8"
        )
    )
    mode = runtime_manifest.get("qualification_mode")
    if mode not in {"production", "local_smoke_blocked"}:
        raise RuntimeError("runtime manifest lacks explicit qualification mode")
    python = runtime_manifest.get("python", {})
    executable = python.get("executable")
    if not executable:
        raise RuntimeError("runtime manifest lacks managed Python executable")
    executable_path = payload_dir / executable
    _require_file(executable_path)
    if python.get("silent_system_install"):
        raise RuntimeError("managed Python runtime silently installs system software")
    hermes = runtime_manifest.get("hermes_agent", {})
    if hermes.get("artifact_status") == "pinned_requirement_recorded":
        raise RuntimeError("Hermes runtime is only recorded as a Git requirement")
    if mode == "production":
        if python.get("status") != "included":
            raise RuntimeError("production payload lacks included managed Python")
        if not hermes.get("included") or not hermes.get("artifact"):
            raise RuntimeError("production payload lacks bundled Hermes runtime")
        python_dependencies = runtime_manifest.get("python_dependencies", {})
        if python_dependencies.get("status") != "included":
            raise RuntimeError(
                "production payload lacks bundled Python dependency wheelhouse"
            )
    wheelhouse = json.loads(
        (payload_dir / "wheels" / "wheelhouse-manifest.json").read_text(
            encoding="utf-8"
        )
    )
    for wheel in wheelhouse.get("wheels", []):
        path = payload_dir / wheel["path"]
        _require_file(path)
        _verify_artifact_checksum(path, wheel["sha256"])
    services = json.loads(
        (payload_dir / "services" / "managed-services.json").read_text(
            encoding="utf-8"
        )
    )
    if services.get("silent_system_dependency_install"):
        raise RuntimeError("managed services silently install system dependencies")
    for name, artifact in services.get("artifacts", {}).items():
        if artifact.get("included"):
            path = payload_dir / "services" / artifact["path"]
            _require_file(path)
            _verify_artifact_checksum(path, artifact["sha256"])


def _verify_product_launchers(payload_dir: Path) -> None:
    launchers = {
        "setup-maya.cmd": ("maya_first_run.py", "MAYA_DATA_DIR", "MAYA_RUNTIME_PYTHON"),
        "maya.cmd": ("health summary", "Blocked items must be resolved"),
        "maya-doctor.cmd": ("doctor --config", "setup-maya.cmd"),
        "maya-self-check.cmd": ("maya_qualification.py", "installed qualification"),
    }
    for name, expected_parts in launchers.items():
        launcher = payload_dir / "bin" / name
        _require_file(launcher)
        text = launcher.read_text(encoding="utf-8")
        for expected in expected_parts:
            if expected not in text:
                raise RuntimeError(f"{name} does not run product action: {expected}")
        if name in {"setup-maya.cmd", "maya-self-check.cmd"} and "maya_runtime.py" not in text:
            raise RuntimeError(f"{name} does not use installed runtime bootstrap")
    menu_text = (payload_dir / "bin" / "maya.cmd").read_text(encoding="utf-8")
    if "Choose an option" in menu_text or re.search(r"\b--help\b", menu_text):
        raise RuntimeError("Start Maya is still a thin menu/help wrapper")
    for launcher_name in ("maya-cli.cmd", "setup-maya.cmd", "maya-self-check.cmd"):
        text = (payload_dir / "bin" / launcher_name).read_text(encoding="utf-8")
        if "MAYA_RUNTIME_PYTHON" not in text:
            raise RuntimeError(f"{launcher_name} does not use managed runtime")
        if "maya_runtime.py" not in text:
            raise RuntimeError(f"{launcher_name} does not use managed runtime bootstrap")
    first_run = (payload_dir / "scripts" / "maya_first_run.py").read_text(
        encoding="utf-8"
    )
    for expected in ("setup\", \"plan", "setup\", \"init", "--apply"):
        if expected not in first_run:
            raise RuntimeError(
                f"first-run setup does not run product setup action: {expected}"
            )


def _verify_compiled_installers_are_signed(inno_dir: Path) -> None:
    installers = sorted(inno_dir.glob("Maya-the-Info-Manager-*-Setup.exe"))
    for installer in installers:
        status = _windows_authenticode_status(installer)
        if status != "Valid":
            raise RuntimeError(
                f"compiled Windows installer is not trusted by Authenticode: "
                f"{installer.name} status={status}"
            )


def _windows_authenticode_status(installer: Path) -> str:
    if sys.platform != "win32":
        return "UnsupportedVerificationPlatform"
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            (
                "$sig = Get-AuthenticodeSignature -LiteralPath "
                + repr(str(installer))
                + "; $sig.Status"
            ),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return "VerificationFailed"
    return result.stdout.strip()


def _verify_packaged_payload_starts(payload_dir: Path) -> None:
    if not payload_dir.is_dir():
        raise RuntimeError("release does not include Windows app payload")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(payload_dir / "app")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            str(payload_dir / "runtime" / "maya_runtime.py"),
            "-m",
            "project_maya.cli",
            "--help",
        ],
        cwd=payload_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if result.returncode != 0 or "usage: maya" not in result.stdout:
        raise RuntimeError(
            "packaged Windows app payload cannot start:\n" + result.stdout
        )


def _verify_installed_qualification(payload_dir: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(payload_dir / "app")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            str(payload_dir / "runtime" / "maya_runtime.py"),
            str(payload_dir / "scripts" / "maya_qualification.py"),
            "--install-dir",
            str(payload_dir),
        ],
        cwd=payload_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if result.returncode not in {0, 1}:
        raise RuntimeError("installed qualification crashed:\n" + result.stdout)
    try:
        payload = json.loads(result.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as exc:
        raise RuntimeError("installed qualification did not emit JSON") from exc
    if payload.get("qualification_status") not in {"ready", "blocked"}:
        raise RuntimeError("installed qualification failed:\n" + result.stdout)
    if not payload.get("secret_safe"):
        raise RuntimeError("installed qualification output is not secret-safe")
    required_commands = {
        "setup_plan",
        "setup_init_dry_run",
        "hermes_runtime",
        "doctor",
        "health_summary",
        "local_api_contract",
        "connector_authorization_readiness",
        "metabase_readiness",
        "document_conversion_readiness",
        "update_check",
        "rollback_check",
        "migration_dry_run",
        "backup_create",
        "backup_inspect",
        "restore_dry_run",
        "broker_status",
        "broker_conformance",
    }
    commands = payload.get("commands", {})
    missing = required_commands.difference(commands)
    if missing:
        raise RuntimeError(
            "installed qualification skipped commands: " + ", ".join(sorted(missing))
        )


def _require_file(path: Path) -> None:
    if not path.is_file():
        raise RuntimeError(f"required release file is missing: {path.name}")


if __name__ == "__main__":
    raise SystemExit(main())
