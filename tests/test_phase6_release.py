import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from project_maya import (
    NON_PRODUCTION_TEST_KEY_ID,
    ReleaseSignatureError,
    default_release_public_keys,
    platform_qualification_for,
    sign_mapping_for_release,
    verify_release_manifest,
    verify_update_manifest,
)
from project_maya.release import (
    PHASE6_METADATA_VERSION,
    ReleaseMetadataError,
    non_production_test_private_key,
)
import scripts.build_phase6_release as build_release_module
import scripts.verify_phase6_release as verify_release_module
from scripts.build_phase6_release import main as build_phase6_release
from scripts.verify_phase6_release import main as verify_phase6_release


class TestPhase6Release(unittest.TestCase):
    def test_signed_update_manifest_verifies_and_rejects_tampering(self):
        payload = self._update_payload()
        signed = self._sign(payload)

        verified = verify_update_manifest(
            signed,
            expected_platform="windows-desktop",
        )

        self.assertEqual(verified.available_version, "1.0.0")
        tampered = dict(signed)
        tampered["available_version"] = "9.9.9"
        with self.assertRaises(ReleaseSignatureError):
            verify_update_manifest(tampered, expected_platform="windows-desktop")

    def test_update_manifest_rejects_unsigned_wrong_key_and_wrong_platform(self):
        payload = self._update_payload()
        with self.assertRaises(ReleaseSignatureError):
            verify_update_manifest(payload, expected_platform="windows-desktop")

        signed = self._sign(payload)
        with self.assertRaises(ReleaseSignatureError):
            verify_update_manifest(
                signed,
                {"other-key": next(iter(default_release_public_keys().values()))},
                expected_platform="windows-desktop",
            )
        with self.assertRaises(ReleaseMetadataError):
            verify_update_manifest(signed, expected_platform="linux-desktop")

    def test_update_manifest_requires_sbom_and_provenance(self):
        payload = self._update_payload()
        payload["sbom_ref"] = ""
        signed = self._sign(payload)

        with self.assertRaises(ReleaseMetadataError):
            verify_update_manifest(signed, expected_platform="windows-desktop")

    def test_platform_qualification_advertises_windows_only(self):
        windows = platform_qualification_for("windows-desktop")
        linux = platform_qualification_for("linux-desktop")

        self.assertTrue(windows.advertised)
        self.assertEqual(windows.status, "qualified")
        self.assertFalse(linux.advertised)
        self.assertEqual(linux.status, "not_advertised")

    def test_release_builder_outputs_signed_verifiable_release_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            release_dir = Path(tmp) / "release"

            self.assertEqual(
                build_phase6_release(
                    [
                        "--version",
                        "1.0.0",
                        "--platform",
                        "windows-desktop",
                        "--out",
                        str(release_dir),
                    ]
                ),
                0,
            )
            self.assertEqual(
                verify_phase6_release(
                    [
                        "--release-dir",
                        str(release_dir),
                        "--platform",
                        "windows-desktop",
                    ]
                ),
                0,
            )
            manifest = json.loads(
                (release_dir / "release-manifest.json").read_text(encoding="utf-8")
            )
            verified = verify_release_manifest(
                manifest,
                expected_platform="windows-desktop",
            )
            self.assertEqual(verified.platform, "windows-desktop")
            self.assertTrue((release_dir / verified.sbom_ref).is_file())
            self.assertTrue((release_dir / verified.provenance_ref).is_file())
            contents = "\n".join(
                path.relative_to(release_dir).as_posix()
                for path in release_dir.rglob("*")
                if path.is_file()
            )
            self.assertIn("windows-app-payload/app/project_maya/__init__.py", contents)
            self.assertIn("windows-app-payload/bin/maya.cmd", contents)
            self.assertIn("windows-app-payload/bin/maya-console.cmd", contents)
            self.assertIn("windows-app-payload/bin/maya-doctor.cmd", contents)
            self.assertIn(
                "windows-app-payload/bin/maya-doctor-console.cmd",
                contents,
            )
            self.assertIn("windows-app-payload/bin/maya-self-check.cmd", contents)
            self.assertIn(
                "windows-app-payload/bin/maya-self-check-console.cmd",
                contents,
            )
            self.assertIn("inno/project-maya-standard.iss", contents)
            self.assertIn("inno/project-maya-enterprise.iss", contents)
            self.assertIn("inno/inno-installer-manifest.json", contents)
            self.assertNotIn("secret://", contents)
            self.assertNotIn("__pycache__", contents)
            with zipfile.ZipFile(
                release_dir / "project-maya-1.0.0-windows-desktop.zip"
            ) as archive:
                self.assertIn(
                    "windows-app-payload/app/project_maya/__init__.py",
                    archive.namelist(),
                )
                self.assertIn(
                    "windows-app-payload/bin/maya.cmd",
                    archive.namelist(),
                )
                self.assertIn(
                    "windows-app-payload/bin/maya-console.cmd",
                    archive.namelist(),
                )

    def test_release_builder_rejects_unadvertised_platform(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                build_phase6_release(
                    [
                        "--version",
                        "1.0.0",
                        "--platform",
                        "linux-desktop",
                        "--out",
                        str(Path(tmp) / "release"),
                    ]
                )

    def test_release_builder_blocks_compiled_unsigned_installers_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            release_dir = Path(tmp) / "release"
            compiled = release_dir / "inno" / "Maya-the-Info-Manager-1.0.0-Standard-Setup.exe"

            def fake_compile(script_path, compiler):
                compiled.parent.mkdir(parents=True, exist_ok=True)
                compiled.write_bytes(b"unsigned installer")
                return compiled

            with patch.object(
                build_release_module,
                "_compile_inno_script",
                side_effect=fake_compile,
            ):
                with self.assertRaisesRegex(RuntimeError, "Authenticode-signed"):
                    build_phase6_release(
                        [
                            "--version",
                            "1.0.0",
                            "--platform",
                            "windows-desktop",
                            "--out",
                            str(release_dir),
                            "--inno-compiler",
                            str(Path(tmp) / "ISCC.exe"),
                        ]
                    )

    def test_release_verifier_rejects_unsigned_compiled_installers(self):
        with tempfile.TemporaryDirectory() as tmp:
            release_dir = Path(tmp) / "release"
            self.assertEqual(
                build_phase6_release(
                    [
                        "--version",
                        "1.0.0",
                        "--platform",
                        "windows-desktop",
                        "--out",
                        str(release_dir),
                    ]
                ),
                0,
            )
            installer = (
                release_dir
                / "inno"
                / "Maya-the-Info-Manager-1.0.0-Standard-Setup.exe"
            )
            installer.write_bytes(b"unsigned installer")

            with patch.object(
                verify_release_module,
                "_windows_authenticode_status",
                return_value="NotSigned",
            ):
                with self.assertRaisesRegex(RuntimeError, "not trusted"):
                    verify_phase6_release(
                        [
                            "--release-dir",
                            str(release_dir),
                            "--platform",
                            "windows-desktop",
                        ]
                    )

    def test_wrong_public_key_rejects_signature(self):
        wrong_private_key = Ed25519PrivateKey.from_private_bytes(bytes(range(32, 64)))
        signed = sign_mapping_for_release(
            self._update_payload(),
            private_key=wrong_private_key,
            key_id=NON_PRODUCTION_TEST_KEY_ID,
        )

        with self.assertRaises(ReleaseSignatureError):
            verify_update_manifest(signed, expected_platform="windows-desktop")

    def _update_payload(self):
        return {
            "metadata_version": PHASE6_METADATA_VERSION,
            "current_version": "0.0.0",
            "available_version": "1.0.0",
            "platform": "windows-desktop",
            "artifact": {
                "name": "project-maya-1.0.0-windows-desktop.zip",
                "path": "project-maya-1.0.0-windows-desktop.zip",
                "sha256": "a" * 64,
                "size_bytes": 10,
                "kind": "windows-installer-bundle",
            },
            "sbom_ref": "sbom.json",
            "provenance_ref": "provenance.json",
            "migration_compatibility": "dry-run-required",
            "rollback_ref": "rollback.json",
            "release_manifest_ref": "release-manifest.json",
        }

    def _sign(self, payload):
        return sign_mapping_for_release(
            payload,
            private_key=non_production_test_private_key(),
            key_id=NON_PRODUCTION_TEST_KEY_ID,
        )


if __name__ == "__main__":
    unittest.main()
