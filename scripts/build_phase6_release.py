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
    sign_mapping_for_release,
    write_canonical_json,
)


HERMES_RUNTIME_COMMIT = "b13e2fd6948a59eeb59fe618914147d97a2ee90a"
PRODUCT_DISPLAY_NAME = "Maya the Info Manager"
WINDOWS_APP_PAYLOAD_DIR = "windows-app-payload"


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


def _build_windows_app_payload(out_dir: Path, wheel: Path, *, version: str) -> Path:
    payload_dir = out_dir / WINDOWS_APP_PAYLOAD_DIR
    if payload_dir.exists():
        shutil.rmtree(payload_dir)
    app_dir = payload_dir / "app"
    bin_dir = payload_dir / "bin"
    app_dir.mkdir(parents=True)
    bin_dir.mkdir(parents=True)

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

    maya_launcher = "\r\n".join(
        [
            "@echo off",
            "setlocal",
            'set "MAYA_APP_DIR=%~dp0..\\app"',
            'set "PYTHONPATH=%MAYA_APP_DIR%;%PYTHONPATH%"',
            'if "%~1"=="" (',
            '  call "%~f0" --help',
            "  exit /b %ERRORLEVEL%",
            ")",
            "where py >nul 2>nul",
            "if %ERRORLEVEL%==0 (",
            '  py -3 -m project_maya.cli %*',
            "  exit /b %ERRORLEVEL%",
            ")",
            "where python >nul 2>nul",
            "if %ERRORLEVEL%==0 (",
            '  python -m project_maya.cli %*',
            "  exit /b %ERRORLEVEL%",
            ")",
            "echo Python 3 is required to run Maya the Info Manager.",
            "echo Install Python 3, then run this command again.",
            "exit /b 1",
            "",
        ]
    )
    console_launcher = "\r\n".join(
        [
            "@echo off",
            'call "%~dp0maya.cmd" %*',
            "set MAYA_EXIT=%ERRORLEVEL%",
            "echo.",
            "echo Press any key to close this window.",
            "pause >nul",
            "exit /b %MAYA_EXIT%",
            "",
        ]
    )
    doctor_launcher = "\r\n".join(
        [
            "@echo off",
            'if "%~1"=="" (',
            "  echo Maya Doctor needs a configuration file.",
            "  echo.",
            '  echo Example: "%~dp0maya.cmd" doctor --config "%USERPROFILE%\\maya-data\\config\\maya.json"',
            "  echo.",
            '  echo Run "%~dp0maya.cmd" --help to see available commands.',
            "  exit /b 2",
            ")",
            'call "%~dp0maya.cmd" doctor %*',
            "exit /b %ERRORLEVEL%",
            "",
        ]
    )
    doctor_console_launcher = "\r\n".join(
        [
            "@echo off",
            'call "%~dp0maya-doctor.cmd" %*',
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
            'call "%~dp0maya.cmd" --help',
            "exit /b %ERRORLEVEL%",
            "",
        ]
    )
    self_check_console_launcher = "\r\n".join(
        [
            "@echo off",
            'call "%~dp0maya-self-check.cmd"',
            "set MAYA_EXIT=%ERRORLEVEL%",
            "echo.",
            "echo Press any key to close this window.",
            "pause >nul",
            "exit /b %MAYA_EXIT%",
            "",
        ]
    )
    (bin_dir / "maya.cmd").write_text(maya_launcher, encoding="utf-8", newline="")
    (bin_dir / "maya-console.cmd").write_text(
        console_launcher, encoding="utf-8", newline=""
    )
    (bin_dir / "maya-doctor.cmd").write_text(
        doctor_launcher, encoding="utf-8", newline=""
    )
    (bin_dir / "maya-doctor-console.cmd").write_text(
        doctor_console_launcher, encoding="utf-8", newline=""
    )
    (bin_dir / "maya-self-check.cmd").write_text(
        self_check_launcher, encoding="utf-8", newline=""
    )
    (bin_dir / "maya-self-check-console.cmd").write_text(
        self_check_console_launcher, encoding="utf-8", newline=""
    )
    (payload_dir / "README.txt").write_text(
        "\r\n".join(
            [
                f"{PRODUCT_DISPLAY_NAME} {version}",
                "",
                "This folder contains the installed Maya application payload.",
                "Use the Start Menu shortcuts for a visible console window.",
                "Run bin\\maya.cmd from PowerShell or Command Prompt for normal CLI use.",
                "Run bin\\maya-self-check.cmd to confirm the installed payload can start.",
                "Python 3 must be installed separately; this installer does not silently install system software.",
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


def _remove_python_caches(payload_dir: Path) -> None:
    for cache_dir in sorted(payload_dir.rglob("__pycache__"), reverse=True):
        shutil.rmtree(cache_dir)


def _iter_payload_files(payload_dir: Path) -> tuple[Path, ...]:
    return tuple(sorted(path for path in payload_dir.rglob("*") if path.is_file()))


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
        "installed_entry_points": [
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
        "heavy_dependencies": "validated-or-installed-on-demand",
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
            'Name: "{group}\\Maya Doctor"; Filename: "{app}\\bin\\maya-doctor-console.cmd"',
            'Name: "{group}\\Maya Self Check"; Filename: "{app}\\bin\\maya-self-check-console.cmd"',
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
