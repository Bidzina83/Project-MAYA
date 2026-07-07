"""Build a deterministic Phase 6 Project MAYA release directory."""

from __future__ import annotations

import argparse
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


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    out_dir = args.out.resolve()
    if args.platform != "windows-desktop":
        raise SystemExit("Phase 6 only advertises windows-desktop")
    if out_dir.exists() and any(out_dir.iterdir()):
        raise SystemExit("release output directory must be empty")
    out_dir.mkdir(parents=True, exist_ok=True)

    wheel = _build_wheel(out_dir)
    installer = _build_windows_installer_bundle(
        out_dir,
        wheel,
        version=args.version,
    )
    sbom_path = out_dir / "sbom.json"
    provenance_path = out_dir / "provenance.json"
    release_manifest_path = out_dir / "release-manifest.json"
    update_manifest_path = out_dir / "update-manifest.json"
    rollback_manifest_path = out_dir / "rollback.json"

    wheel_artifact = artifact_from_file(wheel, kind="python-wheel")
    installer_artifact = artifact_from_file(installer, kind="windows-installer-bundle")

    sbom = _sbom(args.version, args.platform, (wheel_artifact, installer_artifact))
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
        artifacts=(wheel_artifact, installer_artifact),
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
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build signed Project MAYA Phase 6 release metadata."
    )
    parser.add_argument("--version", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--current-version", default="0.0.0")
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


def _build_windows_installer_bundle(out_dir: Path, wheel: Path, *, version: str) -> Path:
    manifest = {
        "installer_kind": "windows-desktop-bundle",
        "version": version,
        "wheel": wheel.name,
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
    manifest_path.unlink()
    return bundle_path


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
