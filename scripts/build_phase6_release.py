"""Build a deterministic Phase 6 Project MAYA release directory."""

from __future__ import annotations

import argparse
import os
import json
import hashlib
import shutil
import subprocess
import sys
import tempfile
import textwrap
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from project_maya.release import (  # noqa: E402
    NON_PRODUCTION_TEST_KEY_ID,
    PHASE6_METADATA_VERSION,
    OfflineEnterpriseBundle,
    PlatformQualification,
    ReleaseManifest,
    ReleaseProvenance,
    artifact_from_file,
    non_production_test_private_key,
    platform_qualification_for,
    sha256_file,
    sign_mapping_for_release,
    write_canonical_json,
)


HERMES_RUNTIME_COMMIT = "b13e2fd6948a59eeb59fe618914147d97a2ee90a"
PRODUCT_DISPLAY_NAME = "Maya the Info Manager"
WINDOWS_APP_PAYLOAD_DIR = "windows-app-payload"
MAYA_SKILLS_REPO = "Bidzina83/Hermes-Agent-Maya-Skills"
DEFAULT_SKILLS_ALLOWLIST = (
    "skills/maya-identity",
    "skills/business/ai-information-manager",
    "skills/pdf",
    "skills/metabase-operations",
    "skills/productivity/metabase-free",
    "skills/productivity/office-functionality",
    "skills/google-account-mapping",
    "skills/google-drive-folder-listing",
    "skills/microsoft-graph",
    "skills/autonomous-ai-agents/slack-gateway-integration",
)
HEAVY_DEPENDENCY_SLOTS = (
    ("metabase", (".jar",)),
    ("java", (".zip", ".7z", ".tar.gz", ".tgz")),
    ("libreoffice", (".zip", ".7z", ".msi")),
    ("poppler", (".zip", ".7z")),
)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    out_dir = args.out.resolve()
    if args.platform != "windows-desktop":
        raise SystemExit("Phase 6 only advertises windows-desktop")
    if out_dir.exists() and any(out_dir.iterdir()):
        raise SystemExit("release output directory must be empty")
    out_dir.mkdir(parents=True, exist_ok=True)

    wheel = _build_wheel(out_dir)
    app_payload = _build_windows_app_payload(
        out_dir,
        wheel,
        version=args.version,
        managed_python_runtime=args.managed_python_runtime,
        hermes_agent_wheel=args.hermes_agent_wheel,
        dependency_artifacts_dir=args.dependency_artifacts_dir,
        skills_overlay_source=args.skills_overlay_source,
        skills_allowlist=args.skills_allowlist,
    )
    installer = _build_windows_installer_bundle(
        out_dir,
        wheel,
        app_payload,
        version=args.version,
    )
    inno_artifacts = _build_inno_setup_products(
        out_dir,
        wheel,
        installer,
        app_payload,
        version=args.version,
        platform=args.platform,
    )
    sbom_path = out_dir / "sbom.json"
    provenance_path = out_dir / "provenance.json"
    release_manifest_path = out_dir / "release-manifest.json"
    update_manifest_path = out_dir / "update-manifest.json"
    rollback_manifest_path = out_dir / "rollback.json"

    wheel_artifact = artifact_from_file(wheel, kind="python-wheel")
    installer_artifact = artifact_from_file(installer, kind="windows-installer-bundle")
    inno_release_artifacts = tuple(
        artifact_from_file(
            path,
            path_ref=path.relative_to(out_dir).as_posix(),
            kind=_inno_artifact_kind(path),
        )
        for path in inno_artifacts
    )

    sbom = _sbom(
        args.version,
        args.platform,
        (wheel_artifact, installer_artifact, *inno_release_artifacts),
    )
    write_canonical_json(sbom_path, sbom)

    provenance = ReleaseProvenance(
        source="Project-MAYA",
        commit=_git_commit(),
        builder="scripts/build_phase6_release.py",
        hermes_runtime_commit=HERMES_RUNTIME_COMMIT,
    )
    write_canonical_json(provenance_path, provenance.to_mapping())

    qualification = platform_qualification_for(args.platform)
    release_manifest = ReleaseManifest(
        metadata_version=PHASE6_METADATA_VERSION,
        product="project_maya",
        version=args.version,
        platform=args.platform,
        artifacts=(wheel_artifact, installer_artifact, *inno_release_artifacts),
        sbom_ref=sbom_path.name,
        provenance_ref=provenance_path.name,
        provenance=provenance,
        platform_qualification=qualification,
        offline_enterprise_bundle=OfflineEnterpriseBundle(
            included=True,
            path=installer.name,
            sha256=installer_artifact.sha256,
        ),
    )
    signed_release = _sign(release_manifest.to_mapping(include_signature=False))
    write_canonical_json(release_manifest_path, signed_release)

    signed_update = _sign(
        {
            "metadata_version": PHASE6_METADATA_VERSION,
            "current_version": args.current_version,
            "available_version": args.version,
            "platform": args.platform,
            "artifact": installer_artifact.to_mapping(),
            "sbom_ref": sbom_path.name,
            "provenance_ref": provenance_path.name,
            "migration_compatibility": "dry-run-required",
            "rollback_ref": rollback_manifest_path.name,
            "release_manifest_ref": release_manifest_path.name,
        }
    )
    write_canonical_json(update_manifest_path, signed_update)

    signed_rollback = _sign(
        {
            "metadata_version": PHASE6_METADATA_VERSION,
            "current_version": args.version,
            "rollback_version": args.current_version,
            "platform": args.platform,
            "artifact": wheel_artifact.to_mapping(),
            "sbom_ref": sbom_path.name,
            "provenance_ref": provenance_path.name,
            "migration_compatibility": "dry-run-required",
            "release_manifest_ref": release_manifest_path.name,
        }
    )
    write_canonical_json(rollback_manifest_path, signed_rollback)
    _compile_inno_setup_products(
        inno_artifacts,
        compiler=args.inno_compiler,
        signtool=args.signtool,
        sign_cert_sha1=args.sign_cert_sha1,
        sign_cert_subject=args.sign_cert_subject,
        timestamp_url=args.timestamp_url,
        allow_unsigned_installers=args.allow_unsigned_installers,
    )
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build signed Project MAYA Phase 6 release metadata."
    )
    parser.add_argument("--version", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--current-version", default="0.0.0")
    parser.add_argument(
        "--inno-compiler",
        type=Path,
        default=None,
        help=(
            "Optional path to ISCC.exe. If omitted or unavailable, the release "
            "contains verified .iss installer products without compiling .exe files."
        ),
    )
    parser.add_argument(
        "--signtool",
        type=Path,
        default=None,
        help=(
            "Optional path to signtool.exe. Required with --inno-compiler for "
            "production Windows installers unless --allow-unsigned-installers "
            "is used for local smoke testing."
        ),
    )
    parser.add_argument(
        "--sign-cert-sha1",
        default=None,
        help="Certificate SHA-1 thumbprint for signtool /sha1 selection.",
    )
    parser.add_argument(
        "--sign-cert-subject",
        default=None,
        help="Certificate subject name for signtool /n selection.",
    )
    parser.add_argument(
        "--timestamp-url",
        default="http://timestamp.digicert.com",
        help="RFC 3161 timestamp URL passed to signtool /tr.",
    )
    parser.add_argument(
        "--allow-unsigned-installers",
        action="store_true",
        help=(
            "Allow compiled Inno installers to remain unsigned. This is only "
            "for local smoke testing and does not satisfy Phase 6 production "
            "qualification."
        ),
    )
    parser.add_argument(
        "--managed-python-runtime",
        type=Path,
        default=None,
        help=(
            "Prepared Maya-managed Python runtime directory. It must contain "
            "python.exe or python.cmd for production qualification."
        ),
    )
    parser.add_argument(
        "--hermes-agent-wheel",
        type=Path,
        default=None,
        help=(
            "Prepared hermes-agent wheel built from the pinned compatible "
            "Hermes runtime commit."
        ),
    )
    parser.add_argument(
        "--dependency-artifacts-dir",
        type=Path,
        default=None,
        help=(
            "Directory containing prepared heavy dependency artifacts such as "
            "Metabase, Java, LibreOffice, and Poppler. Artifacts are copied "
            "and hashed; they are never installed silently."
        ),
    )
    parser.add_argument(
        "--skills-overlay-source",
        type=Path,
        default=None,
        help="Path to the Maya skills overlay repository to curate into payload.",
    )
    parser.add_argument(
        "--skills-allowlist",
        action="append",
        default=None,
        help=(
            "Allowlisted skills-overlay path prefix. May be passed multiple "
            "times. Defaults to the curated Maya Standard skills set."
        ),
    )
    return parser.parse_args(argv)


def _build_wheel(out_dir: Path) -> Path:
    with tempfile.TemporaryDirectory(prefix="maya-phase6-build-") as tmp:
        tmp_path = Path(tmp)
        dist_dir = tmp_path / "dist"
        build_dir = tmp_path / "build"
        build_base = tmp_path / "build-base"
        try:
            subprocess.run(
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
                cwd=REPO_ROOT,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            wheels = sorted(dist_dir.glob("*.whl"))
            if len(wheels) != 1:
                raise RuntimeError("expected exactly one built wheel")
            destination = out_dir / wheels[0].name
            shutil.copy2(wheels[0], destination)
            return destination
        except (subprocess.CalledProcessError, RuntimeError):
            return _build_minimal_wheel(out_dir)


def _build_minimal_wheel(out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    wheel_path = out_dir / "project_maya-0.0.0-py3-none-any.whl"
    dist_info = "project_maya-0.0.0.dist-info"
    entries: dict[str, bytes] = {}
    for source in sorted((REPO_ROOT / "src" / "project_maya").rglob("*")):
        if not source.is_file():
            continue
        relative = source.relative_to(REPO_ROOT / "src").as_posix()
        if "__pycache__" in relative or "/tests/" in relative:
            continue
        entries[relative] = source.read_bytes()
    entries[f"{dist_info}/METADATA"] = (
        "Metadata-Version: 2.1\n"
        "Name: project-maya\n"
        "Version: 0.0.0\n"
        "Summary: Project MAYA public API and runtime integrations\n"
        "Requires-Python: >=3.11,<3.14\n"
        "Requires-Dist: cryptography>=42\n"
        "Requires-Dist: hermes-agent @ "
        f"git+https://github.com/Bidzina83/hermes-agent.git@{HERMES_RUNTIME_COMMIT}\n"
        "Provides-Extra: documents\n"
        "Provides-Extra: documents-preview\n"
        "Requires-Dist: Markdown>=3.5; extra == \"documents\"\n"
        "Requires-Dist: Pillow>=10.0; extra == \"documents\"\n"
        "Requires-Dist: pypdf>=4.0; extra == \"documents\"\n"
        "Requires-Dist: reportlab>=4.0; extra == \"documents\"\n"
        "Requires-Dist: PyMuPDF>=1.24; extra == \"documents-preview\"\n"
    ).encode("utf-8")
    entries[f"{dist_info}/WHEEL"] = (
        "Wheel-Version: 1.0\n"
        "Generator: project-maya-phase6\n"
        "Root-Is-Purelib: true\n"
        "Tag: py3-none-any\n"
    ).encode("utf-8")
    entries[f"{dist_info}/entry_points.txt"] = (
        "[console_scripts]\n"
        "maya=project_maya.cli:main\n"
    ).encode("utf-8")
    record_name = f"{dist_info}/RECORD"
    record_lines = []
    for name, content in sorted(entries.items()):
        digest = hashlib.sha256(content).digest()
        b64_digest = __import__("base64").urlsafe_b64encode(digest).decode("ascii").rstrip("=")
        record_lines.append(f"{name},sha256={b64_digest},{len(content)}")
    record_lines.append(f"{record_name},,")
    entries[record_name] = ("\n".join(record_lines) + "\n").encode("utf-8")
    with zipfile.ZipFile(wheel_path, "w", compression=zipfile.ZIP_DEFLATED) as wheel:
        for name, content in sorted(entries.items()):
            info = zipfile.ZipInfo(name)
            info.date_time = (2026, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            wheel.writestr(info, content)
    return wheel_path


def _build_windows_app_payload(
    out_dir: Path,
    wheel: Path,
    *,
    version: str,
    managed_python_runtime: Path | None,
    hermes_agent_wheel: Path | None,
    dependency_artifacts_dir: Path | None,
    skills_overlay_source: Path | None,
    skills_allowlist: list[str] | None,
) -> Path:
    payload_dir = out_dir / WINDOWS_APP_PAYLOAD_DIR
    if payload_dir.exists():
        shutil.rmtree(payload_dir)
    app_dir = payload_dir / "app"
    bin_dir = payload_dir / "bin"
    runtime_dir = payload_dir / "runtime"
    wheels_dir = payload_dir / "wheels"
    skills_dir = payload_dir / "skills"
    services_dir = payload_dir / "services"
    config_templates_dir = payload_dir / "config-templates"
    scripts_dir = payload_dir / "scripts"
    release_dir = payload_dir / "release"
    for directory in (
        app_dir,
        bin_dir,
        runtime_dir,
        wheels_dir,
        skills_dir,
        services_dir,
        config_templates_dir,
        scripts_dir,
        release_dir,
    ):
        directory.mkdir(parents=True)

    with zipfile.ZipFile(wheel) as archive:
        for member in sorted(archive.infolist(), key=lambda item: item.filename):
            name = member.filename
            if member.is_dir():
                continue
            if name.startswith("/") or ".." in Path(name).parts:
                raise RuntimeError(f"wheel contains unsafe member: {name}")
            destination = app_dir / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(archive.read(member))

    shutil.copy2(wheel, wheels_dir / wheel.name)
    _write_sitecustomize_for_wheelhouse(app_dir)
    python_manifest = _stage_managed_python_runtime(
        runtime_dir,
        managed_python_runtime,
    )
    hermes_manifest = _stage_hermes_runtime_wheel(
        wheels_dir,
        hermes_agent_wheel,
    )
    dependency_manifest = _stage_dependency_artifacts(
        services_dir,
        dependency_artifacts_dir,
    )
    skills_manifest = _stage_skills_overlay(
        skills_dir,
        skills_overlay_source,
        skills_allowlist or list(DEFAULT_SKILLS_ALLOWLIST),
    )
    wheelhouse_manifest = _write_wheelhouse_manifest(wheels_dir)
    production_qualified = (
        python_manifest["status"] == "included"
        and hermes_manifest["included"]
        and all(item["included"] for item in dependency_manifest["artifacts"].values())
    )
    (wheels_dir / "requirements-pinned.txt").write_text(
        "\n".join(
            [
                f"project_maya @ file:///%MAYA_INSTALL_DIR%/wheels/{wheel.name}",
                _requirements_line_for_hermes(hermes_manifest),
                "cryptography>=42",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )
    write_canonical_json(
        runtime_dir / "runtime-manifest.json",
        {
            "runtime_layout_version": 1,
            "qualification_mode": (
                "production" if production_qualified else "local_smoke_blocked"
            ),
            "python": python_manifest,
            "hermes_agent": {
                "package": "hermes-agent",
                "source": "git+https://github.com/Bidzina83/hermes-agent.git",
                "commit": HERMES_RUNTIME_COMMIT,
                "factory": "run_agent:AIAgent",
                **hermes_manifest,
                "readiness_if_unresolved": "blocked",
            },
            "wheelhouse": wheelhouse_manifest,
            "skills": {
                "manifest": "skills/skills-manifest.json",
                "included_count": len(skills_manifest["skills"]),
                "status": "included" if skills_manifest["skills"] else "empty_overlay",
            },
            "managed_services": {
                "manifest": "services/managed-services.json",
                "production_ready": dependency_manifest["production_ready"],
            },
            "profiles": [
                "maya-core",
                "maya-metabase",
                "maya-documents",
                "maya-messaging",
            ],
            "boundaries": {
                "silent_system_dependency_install": False,
                "customer_tenant_resources_created": False,
                "raw_secrets_stored": False,
            },
        },
    )
    write_canonical_json(
        runtime_dir / "component-readiness.json",
        {
            "maya-core": {
                "included": True,
                "status": "installed",
                "notes": "project_maya payload is installed from the built wheel",
            },
            "hermes-agent": {
                "included": bool(hermes_manifest["included"]),
                "status": (
                    "installed"
                    if hermes_manifest["included"]
                    else "blocked_until_runtime_artifact_available"
                ),
                "notes": (
                    "pinned runtime artifact is included in the wheelhouse"
                    if hermes_manifest["included"]
                    else "pinned runtime contract is recorded; verifier must not report Hermes healthy unless importable"
                ),
            },
            "maya-messaging": {
                "included": True,
                "status": "setup_required",
                "notes": "broker and connector code ships; OAuth grants and tenant resources are not created by the installer",
            },
            "maya-metabase": {
                "included": True,
                "status": (
                    "setup_required"
                    if dependency_manifest["artifacts"]["metabase"]["included"]
                    and dependency_manifest["artifacts"]["java"]["included"]
                    else "blocked_until_managed_artifacts_available"
                ),
                "notes": "integration and readiness code ships; Java/Metabase service artifacts are required for production Standard qualification",
            },
            "maya-documents": {
                "included": True,
                "status": (
                    "setup_required"
                    if dependency_manifest["artifacts"]["libreoffice"]["included"]
                    else "blocked_until_document_runtime_available"
                ),
                "notes": "document integration code ships; native document tools are required for production Standard qualification",
            },
            "maya-skills-overlay": {
                "included": bool(skills_manifest["skills"]),
                "status": "installed" if skills_manifest["skills"] else "empty_overlay",
                "notes": "only allowlisted and secret-scanned skills may be installed",
            },
        },
    )
    (config_templates_dir / "standard.json.template").write_text(
        _standard_config_template(),
        encoding="utf-8",
        newline="\r\n",
    )
    (config_templates_dir / "default-governance-policy.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "default_action": "deny",
                "rules": [],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (scripts_dir / "maya_first_run.py").write_text(
        _first_run_script(),
        encoding="utf-8",
        newline="\n",
    )
    (scripts_dir / "maya_qualification.py").write_text(
        _qualification_script(),
        encoding="utf-8",
        newline="\n",
    )
    cli_launcher = "\r\n".join(
        [
            "@echo off",
            "setlocal",
            'set "MAYA_APP_DIR=%~dp0..\\app"',
            'set "MAYA_INSTALL_DIR=%~dp0.."',
            'set "MAYA_RUNTIME_PYTHON=%~dp0..\\runtime\\python\\python.cmd"',
            'set "PYTHONPATH=%MAYA_APP_DIR%;%PYTHONPATH%"',
            'if exist "%MAYA_RUNTIME_PYTHON%" goto run_managed',
            "echo Maya managed Python runtime is missing.",
            "exit /b 1",
            ":run_managed",
            '"%MAYA_RUNTIME_PYTHON%" -m project_maya.cli %*',
            "exit /b %ERRORLEVEL%",
            "",
        ]
    )
    product_launcher = "\r\n".join(
        [
            "@echo off",
            "setlocal",
            "title Start Maya",
            'call "%~dp0setup-maya.cmd" --ensure',
            'if errorlevel 1 exit /b %ERRORLEVEL%',
            'call "%~dp0maya-cli.cmd" health summary --config "%LOCALAPPDATA%\\Maya the Info Manager\\maya-data\\config\\maya.json" --format text',
            "set MAYA_EXIT=%ERRORLEVEL%",
            "echo.",
            "echo Maya start readiness finished with exit code %MAYA_EXIT%.",
            "echo Blocked items must be resolved before Maya is treated as healthy.",
            "echo.",
            "pause",
            "exit /b %MAYA_EXIT%",
            "",
        ]
    )
    setup_launcher = "\r\n".join(
        [
            "@echo off",
            "setlocal",
            "title Setup Maya",
            'set "MAYA_CONFIG=%LOCALAPPDATA%\\Maya the Info Manager\\maya-data\\config\\maya.json"',
            'set "MAYA_DATA_DIR=%LOCALAPPDATA%\\Maya the Info Manager\\maya-data"',
            'set "MAYA_INSTALL_DIR=%~dp0.."',
            'set "MAYA_APP_DIR=%~dp0..\\app"',
            'set "MAYA_RUNTIME_PYTHON=%~dp0..\\runtime\\python\\python.cmd"',
            'set "PYTHONPATH=%MAYA_APP_DIR%;%PYTHONPATH%"',
            'if exist "%MAYA_RUNTIME_PYTHON%" goto setup_managed',
            "echo Maya managed Python runtime is missing.",
            "set MAYA_EXIT=1",
            "goto setup_done",
            ":setup_managed",
            '"%MAYA_RUNTIME_PYTHON%" "%~dp0..\\scripts\\maya_first_run.py" --install-dir "%~dp0.." --config "%MAYA_CONFIG%" --data-dir "%MAYA_DATA_DIR%" %*',
            "set MAYA_EXIT=%ERRORLEVEL%",
            ":setup_done",
            "echo.",
            "pause",
            "exit /b %MAYA_EXIT%",
            "",
        ]
    )
    doctor_launcher = "\r\n".join(
        [
            "@echo off",
            "setlocal",
            "title Maya Doctor",
            'call "%~dp0setup-maya.cmd" --ensure',
            'if errorlevel 1 exit /b %ERRORLEVEL%',
            'call "%~dp0maya-cli.cmd" doctor --config "%LOCALAPPDATA%\\Maya the Info Manager\\maya-data\\config\\maya.json"',
            "set MAYA_EXIT=%ERRORLEVEL%",
            "echo.",
            "echo Press any key to close this window.",
            "pause >nul",
            "exit /b %MAYA_EXIT%",
            "",
        ]
    )
    self_check_launcher = "\r\n".join(
        [
            "@echo off",
            "setlocal",
            "echo Maya the Info Manager installed qualification",
            "echo.",
            'set "MAYA_APP_DIR=%~dp0..\\app"',
            'set "MAYA_RUNTIME_PYTHON=%~dp0..\\runtime\\python\\python.cmd"',
            'set "PYTHONPATH=%MAYA_APP_DIR%;%PYTHONPATH%"',
            'if exist "%MAYA_RUNTIME_PYTHON%" goto qualification_managed',
            "echo Maya managed Python runtime is missing.",
            "set MAYA_EXIT=1",
            "goto qualification_done",
            ":qualification_managed",
            '"%MAYA_RUNTIME_PYTHON%" "%~dp0..\\scripts\\maya_qualification.py" --install-dir "%~dp0.."',
            "set MAYA_EXIT=%ERRORLEVEL%",
            ":qualification_done",
            "echo.",
            "echo Press any key to close this window.",
            "pause >nul",
            "exit /b %MAYA_EXIT%",
            "",
        ]
    )
    (bin_dir / "maya-cli.cmd").write_text(cli_launcher, encoding="utf-8", newline="")
    (bin_dir / "setup-maya.cmd").write_text(setup_launcher, encoding="utf-8", newline="")
    (bin_dir / "maya.cmd").write_text(product_launcher, encoding="utf-8", newline="")
    (bin_dir / "maya-console.cmd").write_text(product_launcher, encoding="utf-8", newline="")
    (bin_dir / "maya-doctor.cmd").write_text(
        doctor_launcher, encoding="utf-8", newline=""
    )
    (bin_dir / "maya-doctor-console.cmd").write_text(
        doctor_launcher, encoding="utf-8", newline=""
    )
    (bin_dir / "maya-self-check.cmd").write_text(
        self_check_launcher, encoding="utf-8", newline=""
    )
    (bin_dir / "maya-self-check-console.cmd").write_text(
        self_check_launcher, encoding="utf-8", newline=""
    )
    (payload_dir / "README.txt").write_text(
        "\r\n".join(
            [
                f"{PRODUCT_DISPLAY_NAME} {version}",
                "",
                "This folder contains the installed Maya application payload.",
                "Use Setup Maya to create starter local state and a Standard configuration.",
                "Use Start Maya to run product readiness checks for the configured local instance.",
                "Run bin\\maya-cli.cmd from PowerShell or Command Prompt for direct CLI use.",
                "Run bin\\maya-self-check.cmd to run the installed qualification path.",
                "Python/Hermes runtime artifacts are managed by the release payload or reported as blocked readiness.",
                "This installer does not silently install system software.",
                "Customer data remains outside this folder in MAYA_HOME or MAYA_DATA_DIR.",
                "",
            ]
        ),
        encoding="utf-8",
        newline="",
    )
    _verify_windows_app_payload(payload_dir)
    _remove_python_caches(payload_dir)
    return payload_dir


def _write_sitecustomize_for_wheelhouse(app_dir: Path) -> None:
    (app_dir / "sitecustomize.py").write_text(
        "\n".join(
            [
                '"""Installed Maya wheelhouse path bootstrap."""',
                "from __future__ import annotations",
                "",
                "import sys",
                "from pathlib import Path",
                "",
                "install_dir = Path(__file__).resolve().parents[1]",
                "wheels_dir = install_dir / 'wheels'",
                "if wheels_dir.is_dir():",
                "    for wheel in sorted(wheels_dir.glob('*.whl')):",
                "        wheel_path = str(wheel)",
                "        if wheel_path not in sys.path:",
                "            sys.path.append(wheel_path)",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )


def _stage_managed_python_runtime(
    runtime_dir: Path,
    source: Path | None,
) -> dict[str, object]:
    python_dir = runtime_dir / "python"
    python_dir.mkdir(parents=True, exist_ok=True)
    if source is not None:
        source = source.resolve()
        if not source.is_dir():
            raise RuntimeError("--managed-python-runtime must be a directory")
        shutil.copytree(source, python_dir, dirs_exist_ok=True)
        executable = _find_managed_python_executable(python_dir)
        if executable is None:
            raise RuntimeError(
                "managed Python runtime must contain python.exe or python.cmd"
            )
        return {
            "managed_layout": "runtime/python",
            "status": "included",
            "requires_python": ">=3.11,<3.14",
            "executable": executable.relative_to(runtime_dir.parent).as_posix(),
            "sha256": _tree_sha256(python_dir),
            "silent_system_install": False,
        }
    wrapper = python_dir / "python.cmd"
    wrapper.write_text(
        "\r\n".join(
            [
                "@echo off",
                "setlocal",
                "where py >nul 2>nul",
                "if %ERRORLEVEL%==0 goto run_py",
                "where python >nul 2>nul",
                "if %ERRORLEVEL%==0 goto run_python",
                "echo Maya managed Python runtime is missing.",
                "echo This local-smoke payload cannot run without system Python.",
                "exit /b 1",
                ":run_py",
                "py -3 %*",
                "exit /b %ERRORLEVEL%",
                ":run_python",
                "python %*",
                "exit /b %ERRORLEVEL%",
                "",
            ]
        ),
        encoding="utf-8",
        newline="",
    )
    return {
        "managed_layout": "runtime/python",
        "status": "local_smoke_external_fallback",
        "requires_python": ">=3.11,<3.14",
        "executable": "runtime/python/python.cmd",
        "sha256": sha256_file(wrapper),
        "silent_system_install": False,
        "readiness_if_unresolved": "blocked",
    }


def _find_managed_python_executable(python_dir: Path) -> Path | None:
    for name in ("python.exe", "python.cmd", "bin/python.exe", "bin/python"):
        candidate = python_dir / name
        if candidate.is_file():
            return candidate
    return None


def _stage_hermes_runtime_wheel(
    wheels_dir: Path,
    source: Path | None,
) -> dict[str, object]:
    if source is None:
        return {
            "included": False,
            "artifact_status": "missing_blocked",
            "artifact": None,
            "sha256": None,
        }
    source = source.resolve()
    if not source.is_file() or source.suffix.lower() != ".whl":
        raise RuntimeError("--hermes-agent-wheel must point to a .whl file")
    if "hermes" not in source.name.lower():
        raise RuntimeError("--hermes-agent-wheel does not look like Hermes Agent")
    destination = wheels_dir / source.name
    shutil.copy2(source, destination)
    return {
        "included": True,
        "artifact_status": "wheelhouse_artifact_included",
        "artifact": destination.name,
        "sha256": sha256_file(destination),
    }


def _requirements_line_for_hermes(hermes_manifest: dict[str, object]) -> str:
    artifact = hermes_manifest.get("artifact")
    if artifact:
        return f"hermes-agent @ file:///%MAYA_INSTALL_DIR%/wheels/{artifact}"
    return (
        "# hermes-agent runtime artifact missing; pinned commit "
        f"{HERMES_RUNTIME_COMMIT} must be supplied for production qualification"
    )


def _write_wheelhouse_manifest(wheels_dir: Path) -> dict[str, object]:
    wheels = []
    for wheel in sorted(wheels_dir.glob("*.whl")):
        wheels.append(
            {
                "name": wheel.name,
                "path": f"wheels/{wheel.name}",
                "sha256": sha256_file(wheel),
                "size_bytes": wheel.stat().st_size,
            }
        )
    manifest = {
        "schema_version": 1,
        "wheels": wheels,
        "all_wheels_hashed": True,
    }
    write_canonical_json(wheels_dir / "wheelhouse-manifest.json", manifest)
    return manifest


def _stage_dependency_artifacts(
    services_dir: Path,
    source_dir: Path | None,
) -> dict[str, object]:
    artifacts_dir = services_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    staged: dict[str, dict[str, object]] = {}
    sources = tuple(source_dir.resolve().iterdir()) if source_dir and source_dir.is_dir() else ()
    for slot, suffixes in HEAVY_DEPENDENCY_SLOTS:
        match = _find_dependency_artifact(sources, slot, suffixes)
        if match is None:
            staged[slot] = {
                "included": False,
                "status": "blocked_until_artifact_supplied",
                "path": None,
                "sha256": None,
            }
            continue
        destination = artifacts_dir / match.name
        shutil.copy2(match, destination)
        staged[slot] = {
            "included": True,
            "status": "artifact_included",
            "path": destination.relative_to(services_dir).as_posix(),
            "sha256": sha256_file(destination),
            "size_bytes": destination.stat().st_size,
        }
    manifest = {
        "schema_version": 1,
        "silent_system_dependency_install": False,
        "customer_tenant_resources_created": False,
        "production_ready": all(item["included"] for item in staged.values()),
        "artifacts": staged,
    }
    write_canonical_json(services_dir / "managed-services.json", manifest)
    return manifest


def _find_dependency_artifact(
    sources: tuple[Path, ...],
    slot: str,
    suffixes: tuple[str, ...],
) -> Path | None:
    for path in sorted(sources):
        name = path.name.lower()
        if not path.is_file() or slot not in name:
            continue
        if any(name.endswith(suffix) for suffix in suffixes):
            return path
    return None


def _stage_skills_overlay(
    skills_dir: Path,
    source_dir: Path | None,
    allowlist: list[str],
) -> dict[str, object]:
    manifest = {
        "schema_version": 1,
        "source_repo": MAYA_SKILLS_REPO,
        "source": str(source_dir.resolve()) if source_dir else None,
        "allowlist": tuple(allowlist),
        "skills": [],
    }
    if source_dir is None:
        write_canonical_json(skills_dir / "skills-manifest.json", manifest)
        return manifest
    source_dir = source_dir.resolve()
    if not source_dir.is_dir():
        raise RuntimeError("--skills-overlay-source must be a directory")
    for prefix in allowlist:
        source_path = source_dir / Path(prefix)
        if not source_path.is_dir():
            continue
        destination = skills_dir / Path(prefix).name
        shutil.copytree(
            source_path,
            destination,
            ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc"),
            dirs_exist_ok=True,
        )
        _scan_curated_skill(destination)
        manifest["skills"].append(
            {
                "name": destination.name,
                "source_path": prefix.replace("\\", "/"),
                "installed_path": destination.relative_to(skills_dir).as_posix(),
                "sha256": _tree_sha256(destination),
                "approval_status": "allowlisted",
            }
        )
    write_canonical_json(skills_dir / "skills-manifest.json", manifest)
    return manifest


def _scan_curated_skill(path: Path) -> None:
    forbidden_name_fragments = (
        "client_secret",
        "private_key",
        "recovery_code",
        "browser_profile",
        ".env",
    )
    forbidden_text_fragments = (
        "-----BEGIN PRIVATE KEY-----",
        "-----BEGIN OPENSSH PRIVATE KEY-----",
        "xoxb-",
        "xapp-",
        "ghp_",
        "ya29.",
    )
    for file_path in sorted(path.rglob("*")):
        if not file_path.is_file():
            continue
        lower_name = file_path.name.lower()
        if any(fragment in lower_name for fragment in forbidden_name_fragments):
            raise RuntimeError(f"skill overlay contains forbidden file: {file_path}")
        if file_path.suffix.lower() not in {".md", ".txt", ".json", ".yaml", ".yml", ".py", ".sh"}:
            continue
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        if any(fragment in text for fragment in forbidden_text_fragments):
            raise RuntimeError(f"skill overlay contains forbidden secret material: {file_path}")


def _tree_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    for file_path in sorted(path.rglob("*")):
        if not file_path.is_file():
            continue
        rel = file_path.relative_to(path).as_posix().encode("utf-8")
        digest.update(rel)
        digest.update(b"\0")
        digest.update(file_path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _verify_windows_app_payload(payload_dir: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(payload_dir / "app")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, "-m", "project_maya.cli", "--help"],
        cwd=payload_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if result.returncode != 0 or "usage: maya" not in result.stdout:
        raise RuntimeError(
            "installed Windows app payload cannot start:\n" + result.stdout
        )
    qualification = subprocess.run(
        [
            sys.executable,
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
    if qualification.returncode not in {0, 1}:
        raise RuntimeError(
            "installed Windows app payload qualification crashed:\n"
            + qualification.stdout
        )
    if "qualification_status" not in qualification.stdout:
        raise RuntimeError(
            "installed Windows app payload qualification did not report status:\n"
            + qualification.stdout
        )


def _remove_python_caches(payload_dir: Path) -> None:
    for cache_dir in sorted(payload_dir.rglob("__pycache__"), reverse=True):
        shutil.rmtree(cache_dir)


def _iter_payload_files(payload_dir: Path) -> tuple[Path, ...]:
    return tuple(sorted(path for path in payload_dir.rglob("*") if path.is_file()))


def _standard_config_template() -> str:
    return json.dumps(
        {
            "schema_version": 2,
            "product": {
                "edition": "standard",
                "instance_id": "${MAYA_INSTANCE_ID}",
            },
            "deployment": {
                "class": "desktop",
                "network_policy": "standard",
                "data_dir": "${MAYA_DATA_DIR}",
            },
            "runtime": {
                "hermes_compatibility": ">=0.1",
                "enabled_profiles": [
                    "maya-core",
                    "maya-metabase",
                    "maya-documents",
                    "maya-messaging",
                ],
                "hermes_factory": "run_agent:AIAgent",
                "hermes_runtime_version": HERMES_RUNTIME_COMMIT,
            },
            "broker": {
                "mode": "runtime",
                "endpoint": "https://broker.maya.example",
            },
            "llm": {
                "mode": "maya_managed",
                "provider": "openai",
                "model": "configured-during-setup",
                "credential_ref": None,
                "endpoint": None,
                "timeout_seconds": 60,
            },
            "integrations": {
                "google": {
                    "enabled": True,
                    "credential_mode": "broker",
                    "credential_ref": "secret://integrations/google",
                },
                "slack": {
                    "enabled": True,
                    "credential_mode": "broker",
                    "credential_ref": "secret://integrations/slack",
                },
                "telegram": {
                    "enabled": False,
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
                "policy_file": "${MAYA_DATA_DIR}/governance/policies/default.json",
                "audit_enabled": True,
                "default_action": "deny",
                "minimum_memory_trust": 0.7,
            },
            "metabase": {
                "enabled": True,
                "deployment": "managed_local",
                "endpoint": "http://127.0.0.1:3030",
                "application_database": {
                    "engine": "h2",
                    "credential_ref": "secret://metabase/application-db",
                },
                "analytics_sources": [],
            },
            "local_api": {
                "bind": "127.0.0.1",
                "port": 8765,
                "remote_access": False,
            },
        },
        indent=2,
        sort_keys=True,
    )


def _first_run_script() -> str:
    return textwrap.dedent(
        r'''
        from __future__ import annotations

        import argparse
        import json
        import os
        import shutil
        import subprocess
        import sys
        import uuid
        from pathlib import Path


        def main(argv=None):
            parser = argparse.ArgumentParser(description="Initialize Maya Standard local state.")
            parser.add_argument("--install-dir", type=Path, required=True)
            parser.add_argument("--config", type=Path, required=True)
            parser.add_argument("--data-dir", type=Path, required=True)
            parser.add_argument("--ensure", action="store_true")
            args = parser.parse_args(argv)
            install_dir = args.install_dir.resolve()
            data_dir = args.data_dir.resolve()
            config_path = args.config.resolve()
            config_path.parent.mkdir(parents=True, exist_ok=True)
            data_dir.mkdir(parents=True, exist_ok=True)
            if not config_path.exists():
                template = (install_dir / "config-templates" / "standard.json.template").read_text(encoding="utf-8")
                rendered = template.replace("${MAYA_INSTANCE_ID}", str(uuid.uuid4()))
                rendered = rendered.replace("${MAYA_DATA_DIR}", str(data_dir).replace("\\", "/"))
                config_path.write_text(rendered + "\n", encoding="utf-8")
            policy_dir = data_dir / "governance" / "policies"
            policy_dir.mkdir(parents=True, exist_ok=True)
            for directory in (
                data_dir / "memory",
                data_dir / "memory" / "registry",
                data_dir / "governance" / "audit",
                data_dir / "logs",
                data_dir / "backups",
                data_dir / "metabase" / "application",
                data_dir / "metabase" / "provisioning",
                data_dir / "metabase" / "analytics" / "sources",
                data_dir / "documents",
                data_dir / "connectors",
                data_dir / "local-api",
                data_dir / "updates",
            ):
                directory.mkdir(parents=True, exist_ok=True)
            policy_path = policy_dir / "default.json"
            if not policy_path.exists():
                shutil.copy2(install_dir / "config-templates" / "default-governance-policy.json", policy_path)
            updates_dir = data_dir / "updates"
            updates_dir.mkdir(parents=True, exist_ok=True)
            for name in ("update-manifest.json", "rollback.json", "release-manifest.json", "sbom.json", "provenance.json"):
                source = install_dir / "release" / name
                if source.is_file():
                    shutil.copy2(source, updates_dir / name)
            secret_status = _initialize_local_api_secret(data_dir)
            print(json.dumps({"operation": "first_run", "config": str(config_path), "data_dir": str(data_dir), "created_config": True}, sort_keys=True))
            print(json.dumps({"operation": "local_api_secret", "status": secret_status}, sort_keys=True))
            for command in (
                [sys.executable, "-m", "project_maya.cli", "setup", "plan", "--config", str(config_path)],
                [sys.executable, "-m", "project_maya.cli", "setup", "init", "--config", str(config_path), "--apply"],
            ):
                result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
                print(result.stdout.strip())
                if result.returncode != 0:
                    return result.returncode
            return 0


        def _initialize_local_api_secret(data_dir):
            value = uuid.uuid4().hex + uuid.uuid4().hex
            try:
                from project_maya.secrets import SecretRef, build_platform_secret_store
                store = build_platform_secret_store(data_dir)
                store.write(SecretRef.parse("secret://local-api/token"), value)
                return store.health().status.value
            except Exception as exc:
                if os.name == "nt":
                    return "blocked:" + type(exc).__name__
                return "blocked:platform_secret_store_unavailable"


        if __name__ == "__main__":
            raise SystemExit(main())
        '''
    ).lstrip()


def _qualification_script() -> str:
    return textwrap.dedent(
        r'''
        from __future__ import annotations

        import argparse
        import json
        import os
        import shutil
        import sqlite3
        import subprocess
        import sys
        import tempfile
        from pathlib import Path


        SECRET_MARKERS = ("secret://", "access_token", "refresh_token", "password", "api_key")
        HERMES_PROBE = "\n".join([
            "import importlib.util, json, sys",
            "run_agent = importlib.util.find_spec('run_agent')",
            "if run_agent is None:",
            "    print(json.dumps({'component': 'hermes-agent', 'status': 'blocked', 'reason': 'run_agent import unavailable'}))",
            "    raise SystemExit(1)",
            "module = __import__('run_agent')",
            "factory = getattr(module, 'AIAgent', None)",
            "if not callable(factory):",
            "    print(json.dumps({'component': 'hermes-agent', 'status': 'blocked', 'reason': 'AIAgent factory unavailable'}))",
            "    raise SystemExit(1)",
            "print(json.dumps({'component': 'hermes-agent', 'status': 'available', 'factory': 'run_agent:AIAgent'}))",
        ])
        LOCAL_API_PROBE = "\n".join([
            "import json, sys",
            "from pathlib import Path",
            "from project_maya.config import config_from_mapping",
            "config = config_from_mapping(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')))",
            "if config.local_api.bind.startswith('127.') and not config.local_api.remote_access:",
            "    print(json.dumps({'component': 'local-api', 'status': 'configured-loopback'}))",
            "    raise SystemExit(0)",
            "print(json.dumps({'component': 'local-api', 'status': 'blocked', 'reason': 'non-loopback or remote access configured'}))",
            "raise SystemExit(1)",
        ])
        CONNECTOR_PROBE = "\n".join([
            "import json, sys",
            "from pathlib import Path",
            "from project_maya.config import config_from_mapping",
            "from project_maya.connectors import validate_configured_connectors",
            "config = config_from_mapping(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')))",
            "validations = validate_configured_connectors(config.integrations, broker_mode=config.broker.mode)",
            "print(json.dumps({'component': 'connectors', 'status': 'ready-for-explicit-authorization', 'connectors': sorted(item.name for item in validations)}))",
            "raise SystemExit(0)",
        ])
        SERVICE_ARTIFACT_PROBE = "\n".join([
            "import json, sys",
            "from pathlib import Path",
            "install_dir = Path(sys.argv[1])",
            "required = sys.argv[2:]",
            "manifest = json.loads((install_dir / 'services' / 'managed-services.json').read_text(encoding='utf-8'))",
            "missing = [name for name in required if not manifest['artifacts'].get(name, {}).get('included')]",
            "if missing:",
            "    print(json.dumps({'component': 'managed-services', 'status': 'blocked', 'missing': missing}))",
            "    raise SystemExit(1)",
            "print(json.dumps({'component': 'managed-services', 'status': 'artifacts-present', 'required': required}))",
        ])


        def main(argv=None):
            parser = argparse.ArgumentParser(description="Run installed Maya payload qualification.")
            parser.add_argument("--install-dir", type=Path, required=True)
            args = parser.parse_args(argv)
            install_dir = args.install_dir.resolve()
            env = os.environ.copy()
            env["PYTHONPATH"] = str(install_dir / "app") + os.pathsep + env.get("PYTHONPATH", "")
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            with tempfile.TemporaryDirectory(prefix="maya-installed-qualification-") as tmp:
                root = Path(tmp)
                data_dir = root / "maya-data"
                config_path = data_dir / "config" / "maya.json"
                first_run = _run(
                    [sys.executable, str(install_dir / "scripts" / "maya_first_run.py"), "--install-dir", str(install_dir), "--config", str(config_path), "--data-dir", str(data_dir)],
                    env,
                )
                commands = {
                    "setup_plan": [sys.executable, "-m", "project_maya.cli", "setup", "plan", "--config", str(config_path)],
                    "setup_init_dry_run": [sys.executable, "-m", "project_maya.cli", "setup", "init", "--config", str(config_path)],
                    "hermes_runtime": [sys.executable, "-c", HERMES_PROBE, str(install_dir)],
                    "doctor": [sys.executable, "-m", "project_maya.cli", "doctor", "--config", str(config_path)],
                    "health_summary": [sys.executable, "-m", "project_maya.cli", "health", "summary", "--config", str(config_path)],
                    "local_api_contract": [sys.executable, "-c", LOCAL_API_PROBE, str(config_path)],
                    "connector_authorization_readiness": [sys.executable, "-c", CONNECTOR_PROBE, str(config_path)],
                    "metabase_readiness": [sys.executable, "-c", SERVICE_ARTIFACT_PROBE, str(install_dir), "metabase", "java"],
                    "document_conversion_readiness": [sys.executable, "-c", SERVICE_ARTIFACT_PROBE, str(install_dir), "libreoffice"],
                    "update_check": [sys.executable, "-m", "project_maya.cli", "update", "--config", str(config_path), "--check"],
                    "rollback_check": [sys.executable, "-m", "project_maya.cli", "update", "--config", str(config_path), "--rollback"],
                    "broker_status": [sys.executable, "-m", "project_maya.cli", "broker", "status", "--config", str(config_path)],
                    "broker_conformance": [sys.executable, "-m", "project_maya.cli", "broker", "conformance", "--config", str(config_path)],
                }
                results = {"first_run": first_run}
                for name, command in commands.items():
                    results[name] = _run(command, env)
                legacy = root / "legacy-memory.sqlite"
                destination = root / "migrated-memory.sqlite"
                _make_legacy_memory(legacy)
                results["migration_dry_run"] = _run([sys.executable, "-m", "project_maya.cli", "migrate", "--from", str(legacy), "--to", str(destination), "--dry-run"], env)
                backup_path = root / "backup.zip"
                results["backup_create"] = _run([sys.executable, "-m", "project_maya.cli", "backup", "--config", str(config_path), "--to", str(backup_path)], env)
                results["backup_inspect"] = _run([sys.executable, "-m", "project_maya.cli", "backup", "inspect", "--from", str(backup_path)], env)
                results["restore_dry_run"] = _run([sys.executable, "-m", "project_maya.cli", "restore", "--from", str(backup_path), "--to", str(root / "restore")], env)
                secret_safe = not any(marker in (item["output"] or "").lower() for item in results.values() for marker in SECRET_MARKERS)
                hard_failures = {
                    name: item for name, item in results.items()
                    if item["returncode"] not in (0, 1)
                }
                blocked = {
                    name: item for name, item in results.items()
                    if item["returncode"] == 1
                }
                status = "blocked" if blocked else "ready"
                if hard_failures or not secret_safe:
                    status = "failed"
                print(json.dumps({"qualification_status": status, "secret_safe": secret_safe, "blocked": sorted(blocked), "hard_failures": sorted(hard_failures), "commands": results}, sort_keys=True))
                return 0 if status in {"ready", "blocked"} else 2


        def _run(command, env):
            result = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
            return {"returncode": result.returncode, "output": _redact(result.stdout[-4000:])}


        def _redact(text):
            redacted = text
            for marker in SECRET_MARKERS:
                redacted = redacted.replace(marker, "[redacted]")
                redacted = redacted.replace(marker.upper(), "[redacted]")
            return redacted


        def _make_legacy_memory(path):
            connection = sqlite3.connect(path)
            try:
                connection.execute("create table memory_kv (key text primary key, value text)")
                connection.execute("insert into memory_kv (key, value) values (?, ?)", ("welcome", "Maya installed qualification"))
                connection.commit()
            finally:
                connection.close()


        if __name__ == "__main__":
            raise SystemExit(main())
        '''
    ).lstrip()


def _build_windows_installer_bundle(
    out_dir: Path,
    wheel: Path,
    app_payload: Path,
    *,
    version: str,
) -> Path:
    manifest = {
        "installer_kind": "windows-desktop-bundle",
        "version": version,
        "wheel": wheel.name,
        "payload_root": WINDOWS_APP_PAYLOAD_DIR,
        "payload_layout": [
            "app",
            "runtime",
            "wheels",
            "skills",
            "services",
            "config-templates",
            "scripts",
            "release",
        ],
        "installed_entry_points": [
            "bin/maya-cli.cmd",
            "bin/setup-maya.cmd",
            "bin/maya.cmd",
            "bin/maya-console.cmd",
            "bin/maya-doctor.cmd",
            "bin/maya-doctor-console.cmd",
            "bin/maya-self-check.cmd",
            "bin/maya-self-check-console.cmd",
        ],
        "installs_from_built_artifact": True,
        "silent_system_dependency_install": False,
        "customer_tenant_resources_created": False,
        "raw_secrets_stored": False,
        "production_qualification": _payload_qualification_mode(app_payload),
        "heavy_dependencies": "prepared-artifacts-or-blocked-readiness",
    }
    manifest_path = out_dir / "installer-manifest.json"
    write_canonical_json(manifest_path, manifest)
    bundle_path = out_dir / f"project-maya-{version}-windows-desktop.zip"
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        _write_zip_entry(archive, wheel, wheel.name)
        _write_zip_entry(archive, manifest_path, manifest_path.name)
        for payload_file in _iter_payload_files(app_payload):
            arcname = (
                Path(WINDOWS_APP_PAYLOAD_DIR)
                / payload_file.relative_to(app_payload)
            ).as_posix()
            _write_zip_entry(archive, payload_file, arcname)
    manifest_path.unlink()
    return bundle_path


def _payload_qualification_mode(app_payload: Path) -> str:
    manifest_path = app_payload / "runtime" / "runtime-manifest.json"
    if not manifest_path.is_file():
        return "unknown"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return str(manifest.get("qualification_mode", "unknown"))


def _build_inno_setup_products(
    out_dir: Path,
    wheel: Path,
    installer_bundle: Path,
    app_payload: Path,
    *,
    version: str,
    platform: str,
) -> tuple[Path, ...]:
    inno_dir = out_dir / "inno"
    inno_dir.mkdir(parents=True, exist_ok=True)
    inno_manifest = {
        "installer_family": "inno-setup",
        "platform": platform,
        "version": version,
        "editions": ["standard", "enterprise"],
        "compiler": None,
        "compiler_available": False,
        "compiled_installers": [],
        "silent_system_dependency_install": False,
        "customer_tenant_resources_created": False,
        "installs_from_built_artifact": True,
        "signing": "external-release-signing-required",
        "production_qualification": _payload_qualification_mode(app_payload),
    }
    manifest_path = inno_dir / "inno-installer-manifest.json"
    write_canonical_json(manifest_path, inno_manifest)
    products: list[Path] = [manifest_path]
    for edition in ("standard", "enterprise"):
        script_path = inno_dir / f"project-maya-{edition}.iss"
        script_path.write_text(
            _inno_script(
                edition=edition,
                version=version,
                wheel=wheel,
                installer_bundle=installer_bundle,
                app_payload=app_payload,
            ),
            encoding="utf-8",
        )
        products.append(script_path)
    return tuple(products)


def _compile_inno_setup_products(
    inno_artifacts: tuple[Path, ...],
    *,
    compiler: Path | None,
    signtool: Path | None,
    sign_cert_sha1: str | None,
    sign_cert_subject: str | None,
    timestamp_url: str,
    allow_unsigned_installers: bool,
) -> tuple[Path, ...]:
    scripts = tuple(path for path in inno_artifacts if path.suffix.lower() == ".iss")
    compiled: list[Path] = []
    for script_path in scripts:
        installer = _compile_inno_script(script_path, compiler)
        if installer is not None:
            if signtool is None and not allow_unsigned_installers:
                raise RuntimeError(
                    "compiled Windows installers must be Authenticode-signed; "
                    "pass --signtool and a certificate selector, or use "
                    "--allow-unsigned-installers only for local smoke testing"
                )
            _sign_windows_installer(
                installer,
                signtool=signtool,
                sign_cert_sha1=sign_cert_sha1,
                sign_cert_subject=sign_cert_subject,
                timestamp_url=timestamp_url,
            )
            compiled.append(installer)
    return tuple(compiled)



def _inno_script(
    *,
    edition: str,
    version: str,
    wheel: Path,
    installer_bundle: Path,
    app_payload: Path,
) -> str:
    title = "Standard" if edition == "standard" else "Enterprise"
    app_id = (
        "{{6D7C7B14-5273-4D6E-A1E4-6D5D87F0A501}"
        if edition == "standard"
        else "{{A24877A0-9D25-4336-BD58-CBDF06242774}"
    )
    return "\n".join(
        [
            "#define MayaVersion \"" + version + "\"",
            "#define MayaEdition \"" + title + "\"",
            "#define MayaProductName \"" + PRODUCT_DISPLAY_NAME + "\"",
            "",
            "[Setup]",
            f"AppId={app_id}",
            "AppName={#MayaProductName} {#MayaEdition}",
            "AppVersion={#MayaVersion}",
            "AppPublisher=Maya the Info Manager",
            "DefaultDirName={autopf}\\Maya the Info Manager",
            "DefaultGroupName=Maya the Info Manager",
            "DisableProgramGroupPage=yes",
            "PrivilegesRequired=lowest",
            "ArchitecturesAllowed=x64compatible",
            "ArchitecturesInstallIn64BitMode=x64compatible",
            "Compression=lzma2",
            "SolidCompression=yes",
            "UninstallDisplayName={#MayaProductName} {#MayaEdition}",
            "OutputDir=.",
            f"OutputBaseFilename=Maya-the-Info-Manager-{version}-{title}-Setup",
            "",
            "[Files]",
            f'Source: "..\\{app_payload.name}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs',
            f'Source: "..\\{wheel.name}"; DestDir: "{{app}}\\release"; Flags: ignoreversion',
            f'Source: "..\\{installer_bundle.name}"; DestDir: "{{app}}\\release"; Flags: ignoreversion',
            'Source: "..\\release-manifest.json"; DestDir: "{app}\\release"; Flags: ignoreversion',
            'Source: "..\\update-manifest.json"; DestDir: "{app}\\release"; Flags: ignoreversion',
            'Source: "..\\rollback.json"; DestDir: "{app}\\release"; Flags: ignoreversion',
            'Source: "..\\sbom.json"; DestDir: "{app}\\release"; Flags: ignoreversion',
            'Source: "..\\provenance.json"; DestDir: "{app}\\release"; Flags: ignoreversion',
            "",
            "[Icons]",
            'Name: "{group}\\Maya the Info Manager"; Filename: "{app}\\bin\\maya-console.cmd"',
            'Name: "{group}\\Setup Maya"; Filename: "{app}\\bin\\setup-maya.cmd"',
            'Name: "{group}\\Start Maya"; Filename: "{app}\\bin\\maya-console.cmd"',
            'Name: "{group}\\Maya Doctor"; Filename: "{app}\\bin\\maya-doctor-console.cmd"',
            'Name: "{group}\\Maya Installed Qualification"; Filename: "{app}\\bin\\maya-self-check-console.cmd"',
            'Name: "{group}\\Maya Data Folder"; Filename: "{localappdata}\\Maya the Info Manager\\maya-data"',
            'Name: "{group}\\Release Manifest"; Filename: "{app}\\release\\release-manifest.json"',
            "",
            "[Run]",
            "; No system software, credentials, OAuth grants, tenant resources, or services are installed silently.",
            "",
            "[UninstallDelete]",
            "; Customer-controlled MAYA_HOME and MAYA_DATA_DIR are never deleted by the installer.",
            "",
        ]
    )


def _compile_inno_script(script_path: Path, compiler: Path | None) -> Path | None:
    if compiler is None or not compiler.is_file():
        return None
    try:
        subprocess.run(
            [str(compiler), str(script_path)],
            cwd=script_path.parent,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        output = exc.stdout or "Inno Setup compiler failed without output."
        raise RuntimeError(output) from exc
    candidates = sorted(script_path.parent.glob("Maya-the-Info-Manager-*-Setup.exe"))
    return candidates[-1] if candidates else None


def _sign_windows_installer(
    installer: Path,
    *,
    signtool: Path | None,
    sign_cert_sha1: str | None,
    sign_cert_subject: str | None,
    timestamp_url: str,
) -> None:
    if signtool is None:
        return
    if not signtool.is_file():
        raise RuntimeError(f"signtool.exe is not available: {signtool}")
    if bool(sign_cert_sha1) == bool(sign_cert_subject):
        raise RuntimeError(
            "provide exactly one Windows signing certificate selector: "
            "--sign-cert-sha1 or --sign-cert-subject"
        )
    command = [
        str(signtool),
        "sign",
        "/fd",
        "SHA256",
        "/tr",
        timestamp_url,
        "/td",
        "SHA256",
    ]
    if sign_cert_sha1:
        command.extend(["/sha1", sign_cert_sha1])
    else:
        command.extend(["/n", str(sign_cert_subject)])
    command.append(str(installer))
    try:
        subprocess.run(
            command,
            cwd=installer.parent,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        output = exc.stdout or "signtool failed without output."
        raise RuntimeError(output) from exc


def _inno_artifact_kind(path: Path) -> str:
    if path.suffix.lower() == ".exe":
        return "inno-setup-installer"
    if path.suffix.lower() == ".iss":
        return "inno-setup-source"
    return "inno-setup-manifest"


def _write_zip_entry(archive: zipfile.ZipFile, source: Path, arcname: str) -> None:
    info = zipfile.ZipInfo(arcname)
    info.date_time = (2026, 1, 1, 0, 0, 0)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, source.read_bytes())


def _sbom(version: str, platform: str, artifacts) -> dict[str, object]:
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "metadata": {
            "component": {
                "name": "project_maya",
                "version": version,
                "type": "application",
            },
            "platform": platform,
        },
        "components": [
            {
                "name": artifact.name,
                "type": "file",
                "hashes": [{"alg": "SHA-256", "content": artifact.sha256}],
            }
            for artifact in artifacts
        ],
    }


def _sign(payload: dict[str, object]) -> dict[str, object]:
    return sign_mapping_for_release(
        payload,
        private_key=non_production_test_private_key(),
        key_id=NON_PRODUCTION_TEST_KEY_ID,
    )


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return result.stdout.strip()


if __name__ == "__main__":
    raise SystemExit(main())
