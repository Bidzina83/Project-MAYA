"""Build a separate, explicitly unqualified Inno governance-test product."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

import build_phase6_release as release
from project_maya.hermes_plugins.candidate import CANDIDATE_SHA256, CANDIDATE_VERSION
from project_maya.hermes_plugins.candidate_qualification import SCENARIOS


APP_ID = "{{AD7D50D8-93F5-47B8-BA64-095429D67AA2}"


def candidate_template() -> dict:
    template = json.loads(release._standard_config_template())
    template["product"]["instance_id"] = "governance-candidate"
    template["runtime"].update(enabled_profiles=["maya-core"], hermes_runtime_version=CANDIDATE_VERSION)
    template["broker"] = {"mode": "disabled"}
    template["llm"].update(mode="local", provider="openai-compatible", model="synthetic-model",
                            endpoint="http://127.0.0.1:9/v1", credential_ref=None)
    for integration in template["integrations"].values():
        integration.update(enabled=False, credential_mode="disabled", credential_ref=None)
    template["metabase"]["enabled"] = False
    return template


def inno_source(version: str, icon: bool) -> str:
    icon_line = 'SetupIconFile="..\\payload\\assets\\maya.ico"' if icon else ""
    shortcut_icon = '; IconFilename: "{app}\\assets\\maya.ico"' if icon else ""
    return f'''#define MayaVersion "{version}"
[Setup]
AppId={APP_ID}
AppName=Maya Governance Test (Unqualified)
AppVersion={version}
AppPublisher=Maya the Info Manager
DefaultDirName={{localappdata}}\\Programs\\Maya Governance Test
DefaultGroupName=Maya Governance Test
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
AllowNoIcons=yes
Compression=lzma2/fast
SolidCompression=yes
OutputDir=.
OutputBaseFilename=Maya-the-Info-Manager-{version}-Standard-Setup
{icon_line}
[Tasks]
Name: "startmenu"; Description: "Create governance-test Start Menu shortcuts"; Flags: checkedonce
Name: "desktop"; Description: "Create a governance-test desktop shortcut"; Flags: unchecked
[Files]
Source: "..\\payload\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{{group}}\\Qualify Maya Governance Test"; Filename: "{{app}}\\bin\\qualify-governance.cmd"; Tasks: startmenu{shortcut_icon}
Name: "{{group}}\\Governance Test Reports"; Filename: "{{localappdata}}\\Maya Governance Test"; Tasks: startmenu
Name: "{{autodesktop}}\\Qualify Maya Governance Test"; Filename: "{{app}}\\bin\\qualify-governance.cmd"; Tasks: desktop{shortcut_icon}
[UninstallDelete]
; Only this product's managed runtime is removed. Test data and other Hermes homes survive.
Type: filesandordirs; Name: "{{app}}\\runtime"
'''


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--managed-python-runtime", type=Path, required=True)
    p.add_argument("--python-wheelhouse-dir", type=Path, required=True)
    p.add_argument("--hermes-wheel", type=Path, required=True)
    p.add_argument("--hermes-provenance", type=Path, required=True)
    p.add_argument("--app-icon", type=Path)
    p.add_argument("--version", default="0.1.0+govtest.20261002")
    p.add_argument("--inno-compiler", type=Path, required=True)
    p.add_argument("--allow-unsigned-installers", action="store_true")
    p.add_argument("--signtool", type=Path)
    p.add_argument("--sign-cert-sha1")
    p.add_argument("--sign-cert-subject")
    p.add_argument("--timestamp-url", default="http://timestamp.digicert.com")
    a = p.parse_args(argv)
    if not a.signtool and not a.allow_unsigned_installers:
        raise SystemExit("Signing is required; explicitly allow unsigned installers for local smoke only.")
    if not a.inno_compiler.is_file():
        raise SystemExit("Inno Setup compiler is required.")
    if release.sha256_file(a.hermes_wheel) != CANDIDATE_SHA256:
        raise SystemExit("Candidate wheel checksum mismatch.")
    provenance = json.loads(a.hermes_provenance.read_text(encoding="utf-8"))
    if provenance.get("wheel", {}).get("sha256") != CANDIDATE_SHA256 or provenance.get("version") != CANDIDATE_VERSION:
        raise SystemExit("Candidate provenance mismatch.")
    out = a.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise SystemExit("Output must be empty.")
    out.mkdir(parents=True, exist_ok=True)
    payload = out / "payload"
    for directory in ("app", "runtime", "wheels", "config-templates", "bin", "release", "assets"):
        (payload / directory).mkdir(parents=True)
    maya_wheel = release._build_wheel(out, version=a.version)
    shutil.copy2(maya_wheel, payload / "wheels" / maya_wheel.name)
    shutil.copy2(a.hermes_wheel, payload / "wheels" / a.hermes_wheel.name)
    for wheel in sorted(a.python_wheelhouse_dir.glob("*.whl")):
        if wheel.name.startswith(("project_maya-", "hermes_agent-")):
            continue
        shutil.copy2(wheel, payload / "wheels" / wheel.name)
    python_manifest = release._stage_managed_python_runtime(payload / "runtime", a.managed_python_runtime)
    if python_manifest["status"] != "included":
        raise SystemExit("Managed Python is required.")
    release._materialize_python_wheelhouse(payload / "wheels", payload / "runtime/site-packages")
    release._write_runtime_bootstrap(payload / "runtime")
    template = candidate_template()
    release.write_canonical_json(payload / "config-templates/candidate.json", template)
    shutil.copy2(a.hermes_provenance, payload / "release/hermes-candidate-provenance.json")
    wheelhouse = release._write_wheelhouse_manifest(payload / "wheels")
    release.write_canonical_json(payload / "runtime/runtime-manifest.json", {
        "qualification": "test_only_unqualified", "production_qualified": False,
        "python": python_manifest, "hermes_version": CANDIDATE_VERSION, "hermes_sha256": CANDIDATE_SHA256,
        "wheelhouse": wheelhouse, "enabled_profiles": ["maya-core"],
    })
    release.write_canonical_json(payload / "release/sbom.json", release._sbom(a.version, "windows-governance-test",
        [release.artifact_from_file(w, kind="python-wheel") for w in sorted((payload / "wheels").glob("*.whl"))]))
    release._stage_app_icon(payload / "assets", a.app_icon)
    (payload / "bin/qualify-governance.cmd").write_text(
        '@echo off\nsetlocal\nset "MAYA_DATA_DIR=%LOCALAPPDATA%\\Maya Governance Test"\n'
        'set "HERMES_HOME=%MAYA_DATA_DIR%\\hermes"\nset "MAYA_CONFIG="\n'
        'set "PYTHONDONTWRITEBYTECODE=1"\n'
        'for %%S in (' + ' '.join(SCENARIOS) + ') do (\n'
        '  "%~dp0..\\runtime\\python\\python.exe" "%~dp0..\\runtime\\maya_runtime.py" -m project_maya.hermes_plugins.candidate_qualification --install-dir "%~dp0.." --data-root "%MAYA_DATA_DIR%" --scenario %%S\n'
        '  if errorlevel 1 goto failed\n)\nset "RESULT=0"\ngoto done\n'
        ':failed\nset "RESULT=1"\n:done\necho.\necho Governance test finished with exit code %RESULT%. This is not production qualification.\npause\nexit /b %RESULT%\n',
        encoding="utf-8", newline="\r\n")
    # Candidate wheel and bootstrap code, never source-tree paths, supply execution.
    files = [{"path": f.relative_to(payload).as_posix(), "sha256": release.sha256_file(f)}
             for f in release._iter_payload_files(payload)]
    release.write_canonical_json(out / "payload-files.json", {"files": files})
    inno = out / "inno"
    inno.mkdir()
    script = inno / "maya-governance-standard.iss"
    script.write_text(inno_source(a.version, (payload / "assets/maya.ico").is_file()), encoding="utf-8")
    installer = release._compile_inno_script(script, a.inno_compiler)
    if installer is None:
        raise RuntimeError("Installer compilation did not produce an executable.")
    destination = inno / f"Maya-Governance-Test-{a.version}-Setup.exe"
    installer.rename(destination)
    release._sign_windows_installer(destination, signtool=a.signtool, sign_cert_sha1=a.sign_cert_sha1,
                                   sign_cert_subject=a.sign_cert_subject, timestamp_url=a.timestamp_url)
    release.write_canonical_json(out / "governance-test-installer.json", {
        "schema_version": 1, "qualification": "test_only_unqualified", "production_qualified": False,
        "signing": "authenticode" if a.signtool else "unsigned-local-smoke-only",
        "version": a.version, "hermes_version": CANDIDATE_VERSION, "hermes_sha256": CANDIDATE_SHA256,
        "maya_source_commit": release._git_commit(), "maya_source_tree_clean": release._git_tree_clean(),
        "installer": {"path": destination.relative_to(out).as_posix(), "sha256": release.sha256_file(destination)},
        "inno_source_sha256": release.sha256_file(script),
        "payload_manifest_sha256": release.sha256_file(out / "payload-files.json"),
        "install_root": "{localappdata}/Programs/Maya Governance Test",
        "data_root": "{localappdata}/Maya Governance Test",
        "included": "managed Python, patched Hermes, current Maya wheel, prepared Python dependencies",
        "disabled": ["Metabase", "documents", "browser", "connectors", "broker", "real provider authorization"],
    })
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
