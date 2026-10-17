"""Portable source guards plus Windows-only inert C# evidence-policy fixtures."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/native/governance_v2_observer.cs"
SUPERVISION = ROOT / "scripts/native/governance_v2_observer_supervision.cs"
NATIVE_LAUNCH = ROOT / "scripts/native/governance_v2_observer_launch.cs"
FIXTURES = ROOT / "tests/governance_v2_observer_fixtures.cs"
FROZEN = {
    "governance-v2-python-comparison.json": "1c8b6075b9cf55358e5af3d0f49490532af15bd940d3c070b0300b0108b07072",
    "governance_v2_python_comparison.md": "9ad2d4050183a62f9b4b343719058afc21023848f33e559191caeab4519db33b",
    "governance-v2-python-comparison-26h2.json": "07b04c4577277780a2352e970185f949e7f3cdf755bc3f1c5a6312cd29f29a27",
    "governance_v2_python_comparison_26h2.md": "4009eef072a7c1e2b160ac72aa07d9b488342ffa8138d2f01ae3c599f7f242f3",
}


class ObserverSourceTests(unittest.TestCase):
    def test_review_package_binds_current_sources(self):
        package = json.loads((ROOT / "docs/architecture/governance-v2-observer-review-package.json").read_text(encoding="utf-8"))
        expected_paths = {path.relative_to(ROOT).as_posix() for path in (SOURCE, SUPERVISION, NATIVE_LAUNCH, FIXTURES)}
        self.assertEqual({row["path"] for row in package["sources"]}, expected_paths)
        self.assertEqual(len(package["sources"]), len(expected_paths))
        for row in package["sources"]:
            self.assertEqual(hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest(), row["sha256"])
        contract = package["frozen_inputs"]
        self.assertEqual(hashlib.sha256((ROOT / contract["contract_path"]).read_bytes()).hexdigest(), contract["contract_sha256"])

    def test_review_package_cannot_authorize_or_invent_a_host(self):
        package = json.loads((ROOT / "docs/architecture/governance-v2-observer-review-package.json").read_text(encoding="utf-8"))
        for field in ("execution_authorized", "external_sharing_authorized", "native_qualified", "production_qualified"):
            self.assertIs(package[field], False)
        self.assertIsNone(package["artifacts"]["library"]["entry_point"])
        self.assertIs(package["artifacts"]["fixture"]["include_in_vm_payload"], False)
        self.assertIs(package["proposed_vm_layout"]["deployed"], False)
        invocation = package["invocation_review"]
        self.assertIsNone(invocation["host_entry_point"])
        self.assertIsNone(invocation["approved_run_command"])
        self.assertIs(invocation["trusted_host_review_complete"], False)
        self.assertIs(invocation["durable_single_attempt_record_required_in_future_host"], True)
        for artifact in ("library", "fixture"):
            self.assertRegex(package["artifacts"][artifact]["sha256"], r"^[0-9a-f]{64}$")

    def test_review_package_preserves_fixed_budget_and_matrix(self):
        package = json.loads((ROOT / "docs/architecture/governance-v2-observer-review-package.json").read_text(encoding="utf-8"))
        contract = json.loads((ROOT / "docs/architecture/governance-v2-python-comparison-26h2.json").read_text(encoding="utf-8"))
        for field in ("ordered_cases", "runs_per_case", "timeout_seconds", "automatic_retries", "automatic_corrections"):
            self.assertEqual(package["budget"][field], contract["budget"][field])
        self.assertEqual(package["budget"]["termination_requested_at_seconds"], 95)
        self.assertEqual([row["id"] for row in package["cases"]], contract["budget"]["ordered_cases"])
        for row, original in zip(package["cases"], contract["cases"], strict=True):
            self.assertEqual(row["capabilities"], contract["common"]["network_capabilities"] + original["extra_capabilities"])
            self.assertEqual(row["ordinary_control_required"], row["id"] == "A")
        self.assertEqual(package["proposed_vm_layout"]["root"], r"C:\MayaGateA")

    def test_original_comparison_inputs_unchanged(self):
        for filename, expected in FROZEN.items():
            with self.subTest(file=filename):
                data = (ROOT / "docs/architecture" / filename).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), expected)

    def test_library_has_no_armed_entrypoint_or_process_launcher(self):
        source = SOURCE.read_text(encoding="utf-8")
        for forbidden in (r"\bMain\s*\(", r"\bCreateProcess\w*\s*\(",
                          r"\bResumeThread\s*\(", r"\bProcess\.Start\s*\(",
                          r"\bShellExecute\w*\s*\("):
            self.assertNotRegex(source, forbidden)

    def test_no_provisioning_or_credential_apis(self):
        source = SOURCE.read_text(encoding="utf-8")
        for forbidden in ("fwpuclnt.dll", "CreateAppContainerProfile(", "SetTokenInformation(",
                          "AdjustTokenPrivileges(", "RegSet", "SetNamedSecurityInfo(",
                          "ReadProcessMemory(", "GetEnvironmentVariable("):
            self.assertNotIn(forbidden, source)

    def test_fixture_executable_has_no_native_or_process_calls(self):
        source = FIXTURES.read_text(encoding="utf-8")
        for forbidden in (r"new\s+NativeProcessReader\b", r"new\s+ObserverJob\b",
                          r"new\s+NativeSupervisionBackend\b", r"\bDllImport\b", r"\bProcess\.Start\b", r"\bNative\."):
            self.assertNotRegex(source, forbidden)

    def test_no_assumed_class_46_or_fixed_token_buffer(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertNotRegex(source, r"TokenBuffer\(token,\s*46\)")
        self.assertIn("Marshal.GetLastWin32Error() != 122", source)
        self.assertIn("needed > 65536", source)
        self.assertIn('Marshal.OffsetOf(typeof(Native.Groups), "first")', source)

    def test_no_breakaway_or_silent_cleanup_claim(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"flags\s*=\s*(0x[0-9a-fA-F]+)", source), ["0x2000"])
        self.assertIn("counts.activeProcesses == 0", source)
        self.assertIn("caseClock.ElapsedMilliseconds", source)
        self.assertNotIn("TerminateProcess(", source)

    def test_sources_are_lf_only(self):
        for path in (SOURCE, SUPERVISION, NATIVE_LAUNCH, FIXTURES):
            self.assertNotIn(b"\r", path.read_bytes())

    def test_supervisor_remains_unarmed_and_without_provisioning(self):
        for path in (SUPERVISION, NATIVE_LAUNCH):
            source = path.read_text(encoding="utf-8")
            self.assertNotRegex(source, r"\bMain\s*\(")
            for forbidden in ("CreateAppContainerProfile(", "Fwpm", "RegSet", "SetNamedSecurityInfo(",
                              "ReadProcessMemory(", "ShellExecute(", "Process.Start("):
                self.assertNotIn(forbidden, source)

    def test_native_dispatch_is_suspended_and_explicitly_permitted(self):
        source = NATIVE_LAUNCH.read_text(encoding="utf-8")
        self.assertIn("reviewedVmExecutionPermission == null || !reviewedVmExecutionPermission()", source)
        self.assertIn("0x80404,environment,plan.Cwd", source)
        self.assertIn("LaunchNative.ResumeThread(launcher.thread) == 1", source)
        self.assertIn("job.AttachOwnedSuspendedLauncher(launcher.process)", source)
        self.assertNotIn("ReadToEnd(", source)
        self.assertNotIn("WaitForExit(", source)
        self.assertIn("watchdog.IsBackground = true", source)
        self.assertIn("if (!stopWatchdog) job.RequestTermination()", source)
        self.assertIn("watchdog.IsAlive", source)
        self.assertIn('environmentValues["PATH"] = Path.GetDirectoryName(plan.Python) + ";" + Environment.SystemDirectory', source)
        self.assertNotIn("SearchOption.AllDirectories", source)
        self.assertIn("LaunchNative.FreeSid(sid)", source)
        self.assertIn('plan.User.StartsWith("S-1-5-21-"', source)
        self.assertIn('identity.Name.StartsWith(Environment.MachineName + "\\\\"', source)


@unittest.skipUnless(os.name == "nt", "C# fixture executable requires Windows .NET Framework")
class ObserverWindowsFixtureTests(unittest.TestCase):
    def test_inert_evidence_and_deadline_matrix(self):
        compiler = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
        self.assertTrue(compiler.is_file(), "Windows fixture compiler is required")
        with tempfile.TemporaryDirectory(prefix="maya-observer-fixtures-") as temporary:
            output = Path(temporary) / "ObserverFixtures.exe"
            compiled = subprocess.run(
                [str(compiler), "/nologo", "/warnaserror+", "/platform:x64",
                 "/target:exe", "/main:ObserverFixtures", f"/out:{output}",
                 "/r:System.Management.dll", "/r:System.Web.Extensions.dll",
                 str(SOURCE), str(SUPERVISION), str(NATIVE_LAUNCH), str(FIXTURES)],
                capture_output=True, text=True, timeout=60, check=False,
            )
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            result = subprocess.run([str(output)], capture_output=True, text=True,
                                    timeout=15, check=False)
            self.assertEqual(result.returncode, 0, "Inert observer fixture matrix failed")
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "fixture_passed")
            self.assertGreaterEqual(report["cases"], 150)
            self.assertIs(report["native_calls"], False)
            self.assertIs(report["production_qualified"], False)


if __name__ == "__main__":
    unittest.main()
