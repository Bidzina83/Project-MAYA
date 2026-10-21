"""Startup health-check unit tests, not native Windows security qualification."""

import contextlib
import importlib.util
import io
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import mock_open, patch


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/project_maya/windows_runtime"
spec = importlib.util.spec_from_file_location("maya_startup_check_unit", SOURCE / "startup_check.py")
startup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(startup)


class StartupCheckTests(unittest.TestCase):
    def setUp(self):
        self.nonce = "0123456789abcdef0123456789abcdef"
        self.stdout = io.TextIOWrapper(io.BytesIO(), encoding="ascii", newline="\r\n")
        self.flags = SimpleNamespace(isolated=1, no_site=1, dont_write_bytecode=1)
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        for name, value in (("version_info", (3, 13, 14)), ("flags", self.flags),
                            ("argv", ["startup_check.py", self.nonce]), ("stdout", self.stdout)):
            self.stack.enter_context(patch.object(startup.sys, name, value))

    def test_success_uses_exclusive_creation_and_binary_stdout(self):
        beacon = "MAYA_PROTECTED_PYTHON_STARTED_V1:" + self.nonce + "\n"
        writer = mock_open()
        writer.return_value.write.return_value = len(beacon)
        with patch("builtins.open", writer):
            self.assertEqual(startup.main(), 0)
        writer.assert_called_once_with("python-startup.txt", "x", encoding="ascii", newline="\n")
        self.assertEqual(self.stdout.buffer.getvalue(), beacon.encode("ascii"))
        writer.return_value.write.assert_called_once_with(beacon)

    def test_existing_beacon_or_denied_write_is_not_success(self):
        for error in (FileExistsError(), PermissionError()):
            with self.subTest(error=type(error).__name__), patch("builtins.open", side_effect=error):
                self.assertEqual(startup.main(), 3)
        self.assertEqual(self.stdout.buffer.getvalue(), b"")

    def test_short_write_is_not_success(self):
        writer = mock_open()
        writer.return_value.write.return_value = 1
        with patch("builtins.open", writer):
            self.assertEqual(startup.main(), 3)
        self.assertEqual(self.stdout.buffer.getvalue(), b"")

    def test_wrong_version_flags_or_nonce_prevent_file_access(self):
        with patch("builtins.open") as writer:
            with patch.object(startup.sys, "version_info", (3, 13, 13)):
                self.assertEqual(startup.main(), 2)
            for flag in ("isolated", "no_site", "dont_write_bytecode"):
                with patch.object(self.flags, flag, 0):
                    self.assertEqual(startup.main(), 2)
            for argv in (["check"], ["check", "x" * 32], ["check", "A" * 32], ["check", self.nonce, "extra"]):
                with patch.object(startup.sys, "argv", argv):
                    self.assertEqual(startup.main(), 2)
            writer.assert_not_called()

    def test_native_candidate_has_no_reference_launcher_or_lab_stage_dependency(self):
        native = "\n".join(path.read_text() for path in SOURCE.glob("*.cs"))
        for forbidden in ("GateANative.exe", "LaunchAppContainer.exe", "CheckNetIsolation", "registryRead",
                          "lpacCom", "governance-v2-lpac-stage", "Console.ReadLine", "internetClient"):
            self.assertNotIn(forbidden, native)
        self.assertNotIn("0x2000F", native)
        self.assertIn("0x2000D", native)
        self.assertIn("0x2000E", native)
        self.assertIn("capabilities = IntPtr.Zero, count = 0", native)
        self.assertIn("UseShellExecute = true, Verb = \"runas\"", native)
        self.assertIn('record["cleanup_complete"] = cleanup', native)

    def test_elevation_query_is_wired_into_native_token_check(self):
        native = (SOURCE / "WindowsIsolation.cs").read_text()
        self.assertIn("RequireNotElevated(token, GetTokenInformation);", native)
        self.assertIn("foreach (int type in new[] { 29, 31, 25, 1, 30 })", native)
        self.assertNotIn("new[] { 29, 31, 25, 1, 30, 20 }", native)

    def test_ordinary_appcontainer_controls_are_checked_before_resume(self):
        native = (SOURCE / "WindowsIsolation.cs").read_text()
        host = (SOURCE / "ProtectedPython.cs").read_text()
        self.assertIn("InitializeProcThreadAttributeList(attributes, 4,", native)
        self.assertIn("RequireAppContainerAccessControls(AccessProbe(duplicate, Package.Value), AccessProbe(duplicate, null),", native)
        self.assertIn('AccessProbe(duplicate, "S-1-15-2-1")', native)
        self.assertIn("if (!packageAllowed || noGrantAllowed || !allApplicationPackagesAllowed || wrongPackageAllowed)", native)
        self.assertIn('throw new StartupFailure("appcontainer_access_controls_failed")', native)
        self.assertNotIn('throw new StartupFailure("lpac_access_controls_failed")', native)
        self.assertIn('{"isolation_mode", "appcontainer-wfp"}', host)
        self.assertIn("broader implicit access than LPAC", host)

    def test_specific_scalar_failures_are_wired_into_native_checks_and_report(self):
        native = (SOURCE / "WindowsIsolation.cs").read_text()
        host = (SOURCE / "ProtectedPython.cs").read_text()
        self.assertIn("RequireTokenScalar(20, unchecked((uint)Marshal.ReadInt32(memory)));", native)
        self.assertIn("if (type == 29 || type == 30) RequireTokenScalar(type, unchecked((uint)Marshal.ReadInt32(memory)));", native)
        self.assertNotIn('throw new StartupFailure("child_token_restriction_mismatch")', native)
        self.assertIn("RecordStartupFailure(record, error);", host)
        self.assertIn('record["token_check_failure"] = failure.TokenCheck;', host)

    def test_same_user_reduced_token_is_explicitly_used_without_a_launch_fallback(self):
        native = (SOURCE / "WindowsIsolation.cs").read_text()
        host = (SOURCE / "ProtectedPython.cs").read_text()
        start = native[native.index("internal void Start("):native.index("static IntPtr Allocate(")]
        self.assertLess(start.index("launchToken = CreateReducedLaunchToken(user);"),
                        start.index("CreateProcessAsUserW(launchToken,"))
        self.assertLess(start.index("CreateProcessAsUserW(launchToken,"), start.index("TokenCheck(child.process, user);"))
        self.assertIn("CreateRestrictedToken(original, 0x1 | 0x4, 1, ref disabled, 0, IntPtr.Zero,", native)
        self.assertIn("VerifyReducedLaunchToken(reduced, user, session, notify, GetTokenInformation);", native)
        self.assertIn("SetTokenInformation(reduced, 25,", native)
        self.assertNotIn("SetTokenInformation(original,", native)
        self.assertIn('record["reduced_launch_token_verified"] = isolation.ReducedLaunchTokenVerified;', host)
        for forbidden in ("CreateProcessW(", "CreateProcessWithTokenW(", "CreateProcessWithLogonW(",
                          "TokenLinkedToken", "LogonUser", "AdjustTokenPrivileges", "ImpersonateLoggedOnUser"):
            self.assertNotIn(forbidden, native)

    def test_process_local_error_mode_is_configured_before_ui_without_wer_suppression(self):
        native = (SOURCE / "WindowsIsolation.cs").read_text()
        host = (SOURCE / "ProtectedPython.cs").read_text()
        self.assertLess(host.index("Native.ConfigureErrorMode();"), host.index("Application.EnableVisualStyles();"))
        self.assertIn("ConfigureErrorMode(GetErrorMode, SetErrorMode);", native)
        self.assertIn("uint expected = read() | 1u;", native)
        self.assertIn("if (read() != expected)", native)
        self.assertNotIn("WerSetFlags", native)
        self.assertNotIn("SetThreadErrorMode", native)
        self.assertIn("true, LaunchCreationFlags, environment, state, ref startup, out child)", native)

    def test_detached_launch_mode_preserves_explicit_pipe_and_attribute_wiring(self):
        native = (SOURCE / "WindowsIsolation.cs").read_text()
        self.assertIn("internal const uint LaunchCreationFlags = 0x0008040c;", native)
        start = native[native.index("internal void Start("):native.index("static IntPtr Allocate(")]
        self.assertEqual(start.count("CreateProcessAsUserW("), 1)
        self.assertIn("true, LaunchCreationFlags, environment, state, ref startup, out child)", start)
        self.assertNotIn("0x08080404", start)
        self.assertIn("flags = 0x100,", start)
        self.assertIn("input = inputRead, output = outputWrite, error = errorWrite", start)
        self.assertIn("Attribute(attributes, 0x20002, inherited, 3 * IntPtr.Size);", start)
        self.assertLess(start.index("Attribute(attributes, 0x2000D, jobList, IntPtr.Size);"),
                        start.index("CreateProcessAsUserW("))
        self.assertLess(start.index("CreateProcessAsUserW("), start.index("TokenCheck(child.process, user);"))

    def test_failure_evidence_is_collected_only_after_stop_before_revocation(self):
        host = (SOURCE / "ProtectedPython.cs").read_text()
        final = host[host.index('// Keep durable network denies'):host.index('isolation.Dispose();')]
        self.assertLess(final.index('isolation.Stop();'), final.index('RecordChildEvidence('))
        self.assertLess(final.index('RecordChildEvidence('), final.index('ProductFiles.Revoke('))
        self.assertIn('!recover && isolation.Resumed && (string)record["startup_status"] == "blocked"', final)
        self.assertIn('catch (Exception error) { record["evidence_reason_code"] = FailureCode(error); }', final)
        self.assertIn('record["fresh_state_beacon"] = null;', final)
        self.assertIn('record["fresh_state_beacon"] = ReadFreshBeacon(directory, run);', final)
        self.assertNotIn('record["python_started"] =', final)
        self.assertNotIn('record["reason_code"] =', final)

    def test_stop_does_not_replace_natural_exit_with_forced_exit(self):
        native = (SOURCE / "WindowsIsolation.cs").read_text()
        wait = native[native.index('internal uint ResumeAndWait()'):native.index('static byte[] ReadBounded(')]
        self.assertIn('WaitForSingleObject(child.process, 30000)', wait)
        self.assertLess(wait.index('if (wait == 258)'), wait.index('GetExitCodeProcess('))
        stop = native[native.index('internal void Stop()'):native.index('public void Dispose()')]
        self.assertIn('TerminateJobObject(job, 1)', stop)
        self.assertNotIn('ExitCode =', stop)
        self.assertNotIn('GetExitCodeProcess(', stop)


if __name__ == "__main__":
    unittest.main()
