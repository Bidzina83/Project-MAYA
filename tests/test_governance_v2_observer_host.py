"""Host policy fixtures, without executing the VM entry point or native backend."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "scripts/native/governance_v2_observer_host.cs"
WINDOWS = ROOT / "scripts/native/governance_v2_observer_host_windows.cs"
FIXTURE = ROOT / "tests/governance_v2_observer_host_fixtures.cs"


class HostSourceTests(unittest.TestCase):
    def test_host_review_binds_sources_and_library(self):
        record = json.loads((ROOT / "docs/architecture/governance-v2-observer-host-review.json").read_text(encoding="utf-8"))
        self.assertEqual({row["path"] for row in record["sources"]},
                         {path.relative_to(ROOT).as_posix() for path in (CORE, WINDOWS, FIXTURE)})
        for row in record["sources"]:
            self.assertEqual(hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest(), row["sha256"])
        template = json.loads((ROOT / "docs/architecture/governance-v2-observer-host-template.json").read_text(encoding="utf-8"))
        self.assertEqual(template["host_sha256"], record["artifacts"]["host"]["sha256"])
        self.assertEqual(template["library_sha256"], record["artifacts"]["library"]["sha256"])
        self.assertEqual(template["review_package_sha256"], record["predecessor"]["sha256"])

    def test_host_review_and_template_cannot_authorize_execution(self):
        record = json.loads((ROOT / "docs/architecture/governance-v2-observer-host-review.json").read_text(encoding="utf-8"))
        for field in ("execution_authorized", "external_sharing_authorized", "native_qualified", "production_qualified",
                      "vm_modified", "launchers_executed", "managed_python_executed"):
            self.assertIs(record[field], False)
        self.assertIs(record["artifacts"]["host"]["executed"], False)
        self.assertIs(record["proposed_invocation"]["ready_to_run"], False)
        self.assertIs(record["attempt_record"]["survives_baseline_disk_restore"], False)
        self.assertIs(record["attempt_record"]["external_attempt_journal_required"], True)
        template = json.loads((ROOT / "docs/architecture/governance-v2-observer-host-template.json").read_text(encoding="utf-8"))
        self.assertIs(template["execution_authorized"], False)
        self.assertEqual(template["adapter_guids"], [])
        for field in ("operator_sid", "package_sid", "case_id", "vm_uuid", "issued_utc", "expires_utc",
                      "authorization_sha256", "security_sha256", "external_attempt_sha256"):
            self.assertIsNone(template[field])

    def test_prior_review_package_is_preserved(self):
        package = ROOT / "docs/architecture/governance-v2-observer-review-package.json"
        self.assertEqual(hashlib.sha256(package.read_bytes()).hexdigest(),
                         "eeb0e435457b6219db6582706530dd6f8c07e0d95a76c90f222a5e1fb0a0e75b")
        for row in json.loads(package.read_text(encoding="utf-8"))["sources"]:
            self.assertEqual(hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest(), row["sha256"])

    def test_entry_point_has_no_provisioning_or_fallback(self):
        for path in (CORE, WINDOWS):
            source = path.read_text(encoding="utf-8")
            for forbidden in ("DllImport", "Process.Start(", "CreateProcess", "SetNamedSecurityInfo", "RegSet",
                              "CreateAppContainerProfile", "Fwpm", "Enable-NetAdapter", "Disable-NetAdapter",
                              "File.Delete(", "Directory.Delete(", "FileMode.Create,", "FileMode.OpenOrCreate"):
                self.assertNotIn(forbidden, source)
        windows = WINDOWS.read_text(encoding="utf-8")
        self.assertIn("Console.IsInputRedirected", windows)
        self.assertIn("new NativeSupervisionBackend(permission)", windows)
        self.assertIn("InterfaceAdminStatus", windows)
        self.assertNotIn("OperationalStatus", windows)
        self.assertIn("manifest.ExecutableHash", windows)

    def test_reservation_is_before_dispatch_and_durable(self):
        source = CORE.read_text(encoding="utf-8")
        self.assertLess(source.index("record = journal.Reserve(manifest)"), source.index("observed = dispatch("))
        self.assertIn("FileMode.CreateNew", source)
        self.assertIn("FileShare.None", source)
        self.assertIn("stream.Flush(true)", source)
        self.assertIn("HostFiles.WriteAndVerify(stream", source)
        self.assertIn("record.Complete(result.Json)", source)
        self.assertIn("if (!active || callbackUsed) return false", source)

    def test_fixtures_cannot_dispatch_or_read_vm_state(self):
        source = FIXTURE.read_text(encoding="utf-8")
        for forbidden in ("new WindowsHostEnvironment", "new NativeSupervisionBackend", "new ObserverJob",
                          "new NativeProcessReader", "ObserverHostProgram.Main", "DllImport", "Process.Start("):
            self.assertNotIn(forbidden, source)

    def test_new_sources_are_lf(self):
        for path in (CORE, WINDOWS, FIXTURE):
            self.assertNotIn(b"\r", path.read_bytes())


@unittest.skipUnless(os.name == "nt", "inert C# host fixtures require Windows .NET Framework")
class HostWindowsFixtureTests(unittest.TestCase):
    def test_host_policy_and_isolated_attempt_journal(self):
        compiler = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
        with tempfile.TemporaryDirectory(prefix="maya-observer-host-fixtures-") as temporary:
            directory = Path(temporary)
            executable = directory / "ObserverHostFixtures.exe"
            fixture_state = directory / "fixture-state"
            fixture_state.mkdir()
            source_paths = [ROOT / "scripts/native" / filename for filename in (
                "governance_v2_observer.cs", "governance_v2_observer_supervision.cs", "governance_v2_observer_launch.cs")]
            compiled = subprocess.run(
                [str(compiler), "/nologo", "/warnaserror+", "/platform:x64", "/target:exe",
                 "/main:ObserverHostFixtures", f"/out:{executable}",
                 "/r:System.Management.dll", "/r:System.Web.Extensions.dll",
                 *map(str, source_paths), str(CORE), str(WINDOWS), str(FIXTURE)],
                capture_output=True, text=True, timeout=60, check=False,
            )
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            result = subprocess.run([str(executable), str(fixture_state)],
                                    capture_output=True, text=True, timeout=20, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "fixture_passed")
            expected = json.loads((ROOT / "docs/architecture/governance-v2-observer-host-review.json").read_text(encoding="utf-8"))
            self.assertEqual(report["cases"], expected["artifacts"]["inert_fixture"]["checks_passed"])
            for field in ("native_dispatch", "vm_checks_executed", "production_qualified"):
                self.assertIs(report[field], False)


if __name__ == "__main__":
    unittest.main()
