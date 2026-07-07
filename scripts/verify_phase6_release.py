"""Verify a Project MAYA Phase 6 release directory."""

from __future__ import annotations

import argparse
import json
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
    if manifest.get("silent_system_dependency_install"):
        raise RuntimeError("installer bundle silently installs system dependencies")
    if manifest.get("customer_tenant_resources_created"):
        raise RuntimeError("installer bundle creates customer tenant resources")


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
            "AppName=Project MAYA {#MayaEdition}",
            "PrivilegesRequired=lowest",
            "Source: \"..\\",
            "release-manifest.json",
            "update-manifest.json",
            "rollback.json",
            "No system software, credentials, OAuth grants",
            "MAYA_HOME and MAYA_DATA_DIR are never deleted",
        ):
            if expected not in text:
                raise RuntimeError(f"Inno script missing required boundary: {expected}")


def _require_file(path: Path) -> None:
    if not path.is_file():
        raise RuntimeError(f"required release file is missing: {path.name}")


if __name__ == "__main__":
    raise SystemExit(main())
