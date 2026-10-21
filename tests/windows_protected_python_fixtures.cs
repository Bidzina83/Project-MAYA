// Inert unit checks: no profile, ACL, WFP, UAC, process launch or GUI invocation.
using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Text;
using System.Web.Script.Serialization;
using ProjectMaya.WindowsRuntime;

public static class ProtectedPythonFixtures
{
    static int count;
    static void Assert(bool condition, string name)
    {
        if (!condition) throw new Exception(name); count++;
    }
    static void Reject(System.Action action, string name)
    {
        bool rejected = false; try { action(); } catch (StartupFailure) { rejected = true; }
        Assert(rejected, name);
    }
    static PayloadIndex Index(List<PayloadFile> entries)
    {
        string json = new JavaScriptSerializer().Serialize(new PayloadIndex {
            python_version = "3.13.14", zip_sha256 = new string('a', 64), files = entries });
        using (var stream = new MemoryStream(Encoding.UTF8.GetBytes(json))) return ProductFiles.ReadIndex(stream);
    }
    static List<PayloadFile> Files()
    {
        var entries = new List<PayloadFile>();
        foreach (string path in new[] { "python/python.exe", "python/python313.dll", "startup_check.py" })
            entries.Add(new PayloadFile { path = path, size = 1, sha256 = new string('b', 64) });
        return entries;
    }
    static void Layout(string name, int expected)
    {
        Type type = typeof(WindowsIsolation).GetNestedType(name, BindingFlags.NonPublic);
        Assert(type != null && Marshal.SizeOf(type) == expected, "native_layout_" + name);
    }
    static void ElevationQueryRegression()
    {
        IntPtr expectedToken = new IntPtr(123);
        int calls = 0;
        WindowsIsolation.TokenInformationQuery exactSize = delegate(IntPtr token, int type, IntPtr data, uint length, out uint required)
        {
            calls++;
            if (token != expectedToken || type != 20) throw new Exception("elevation_query_identity");
            required = 4;
            if (length != 4) return false;
            if (data == IntPtr.Zero) throw new Exception("elevation_query_buffer_missing");
            Marshal.WriteInt32(data, 0);
            return true;
        };
        uint legacyRequired;
        Assert(!exactSize(expectedToken, 20, IntPtr.Zero, 4096, out legacyRequired), "regression_rejects_original_4096_byte_query");
        calls = 0;
        WindowsIsolation.RequireNotElevated(expectedToken, exactSize);
        Assert(calls == 1, "elevation_uses_one_exact_four_byte_query");
        foreach (int elevated in new[] { 1, 2, -1 })
        {
            WindowsIsolation.TokenInformationQuery denied = delegate(IntPtr token, int type, IntPtr data, uint length, out uint required)
            { required = 4; Marshal.WriteInt32(data, elevated); return true; };
            Reject(() => WindowsIsolation.RequireNotElevated(expectedToken, denied), "elevated_child_stays_blocked");
        }
        foreach (uint returned in new uint[] { 0, 3, 8, 4096 })
        {
            WindowsIsolation.TokenInformationQuery malformed = delegate(IntPtr token, int type, IntPtr data, uint length, out uint required)
            { required = returned; Marshal.WriteInt32(data, 0); return true; };
            Reject(() => WindowsIsolation.RequireNotElevated(expectedToken, malformed), "wrong_returned_size_stays_blocked");
        }
        WindowsIsolation.TokenInformationQuery failed = delegate(IntPtr token, int type, IntPtr data, uint length, out uint required)
        { required = 4; Marshal.WriteInt32(data, 0); return false; };
        Reject(() => WindowsIsolation.RequireNotElevated(expectedToken, failed), "failed_query_is_not_a_non_elevated_token");
    }
    static void TokenFailureReportingRegression()
    {
        int[] types = { 29, 30, 20 };
        string[] names = { "is_appcontainer", "capability_count", "is_elevated" };
        string[] codes = { "child_token_is_appcontainer_mismatch", "child_token_capability_count_mismatch", "child_token_elevation_mismatch" };
        var serializer = new JavaScriptSerializer();
        for (int i = 0; i < types.Length; i++)
        {
            uint expected = types[i] == 29 ? 1u : 0u;
            foreach (uint value in new uint[] { 0, 1, 2, 1024, UInt32.MaxValue })
            {
                StartupFailure failure = null;
                try { WindowsIsolation.RequireTokenScalar(types[i], value); } catch (StartupFailure error) { failure = error; }
                Assert((failure == null) == (value == expected), "token_predicate_unchanged");
                if (failure == null) continue;
                var record = new Dictionary<string, object>(); ProtectedPython.RecordStartupFailure(record, failure);
                string json = serializer.Serialize(record);
                var decoded = serializer.Deserialize<Dictionary<string, object>>(json);
                var detail = (Dictionary<string, object>)decoded["token_check_failure"];
                Assert((string)decoded["status"] == "blocked" && (string)decoded["reason_code"] == codes[i] &&
                    detail.Count == 4 && (string)detail["check"] == names[i] && Convert.ToInt32(detail["information_class"]) == types[i] &&
                    Convert.ToUInt32(detail["expected"]) == expected && Convert.ToUInt32(detail["observed"]) == value,
                    "exact_token_failure_survives_report_json");
            }
        }
        WindowsIsolation.TokenInformationQuery elevated = delegate(IntPtr token, int type, IntPtr data, uint length, out uint required)
        { required = 4; Marshal.WriteInt32(data, 1); return true; };
        StartupFailure elevatedFailure = null;
        try { WindowsIsolation.RequireNotElevated(new IntPtr(123), elevated); } catch (StartupFailure error) { elevatedFailure = error; }
        Assert(elevatedFailure != null && elevatedFailure.TokenCheck != null && elevatedFailure.TokenCheck.check == "is_elevated" &&
            elevatedFailure.TokenCheck.observed == 1, "elevation_query_uses_distinct_failure_reporting");
        var ordinary = new Dictionary<string, object>(); ProtectedPython.RecordStartupFailure(ordinary, new Exception("SECRET"));
        Assert(!ordinary.ContainsKey("token_check_failure") && !serializer.Serialize(ordinary).Contains("SECRET"), "ordinary_error_has_no_fabricated_token_data");
        WindowsIsolation.TokenInformationQuery failedQuery = delegate(IntPtr token, int type, IntPtr data, uint length, out uint required)
        { required = 4; Marshal.WriteInt32(data, 0); return false; };
        StartupFailure queryFailure = null;
        try { WindowsIsolation.RequireNotElevated(new IntPtr(123), failedQuery); } catch (StartupFailure error) { queryFailure = error; }
        Assert(queryFailure != null && queryFailure.TokenCheck == null && queryFailure.Message.StartsWith("read_child_token_20:"),
            "failed_query_has_no_fabricated_observed_token_value");
    }
    static void PutSid(IntPtr memory, int field, int position, string value)
    {
        var sid = new SecurityIdentifier(value); byte[] bytes = new byte[sid.BinaryLength]; sid.GetBinaryForm(bytes, 0);
        Marshal.WriteIntPtr(memory, field, IntPtr.Add(memory, position)); Marshal.Copy(bytes, 0, IntPtr.Add(memory, position), bytes.Length);
    }
    static bool ReducedQuery(IntPtr token, int type, IntPtr data, uint length, out uint required)
    {
        if (token != new IntPtr(456)) throw new Exception("launch_query_token_identity");
        bool scalar = type == 8 || type == 12 || type == 20 || type == 15 || type == 26 || type == 29;
        if (length != (scalar ? 4u : 65536u)) throw new Exception("launch_query_exact_buffer_size");
        required = 4;
        if (scalar) { Marshal.WriteInt32(data, type == 8 ? 1 : type == 12 ? 7 : 0); return true; }
        if (type == 1)
        {
            PutSid(data, 0, 16, "S-1-5-21-111-222-333-1001"); Marshal.WriteInt32(data, 8, 0); required = 44;
        }
        else if (type == 25)
        {
            PutSid(data, 0, 16, "S-1-16-8192"); Marshal.WriteInt32(data, 8, 0x20); required = 28;
        }
        else if (type == 2)
        {
            Marshal.WriteInt32(data, 1); PutSid(data, 8, 24, "S-1-5-32-544"); Marshal.WriteInt32(data, 16, 0x10); required = 40;
        }
        else if (type == 3)
        {
            Marshal.WriteInt32(data, 1); Marshal.WriteInt64(data, 4, 12345); Marshal.WriteInt32(data, 12, 3); required = 16;
        }
        else throw new Exception("unexpected_launch_query_class");
        return true;
    }
    static void VerifyReduced(WindowsIsolation.TokenInformationQuery query)
    {
        WindowsIsolation.VerifyReducedLaunchToken(new IntPtr(456), new SecurityIdentifier("S-1-5-21-111-222-333-1001"), 7, 12345, query);
    }
    static void RejectReducedMutation(int changedType, Action<IntPtr> change, string name)
    {
        WindowsIsolation.TokenInformationQuery changed = delegate(IntPtr token, int type, IntPtr data, uint length, out uint required)
        {
            bool result = ReducedQuery(token, type, data, length, out required);
            if (type == changedType) change(data);
            return result;
        };
        Reject(() => VerifyReduced(changed), name);
    }
    static void ReducedLaunchTokenRegression()
    {
        VerifyReduced(ReducedQuery); Assert(true, "same_user_reduced_primary_token_admitted");
        Reject(() => WindowsIsolation.VerifyReducedLaunchToken(IntPtr.Zero, null, 7, 12345, ReducedQuery), "missing_launch_token_rejected");
        foreach (int type in new[] { 8, 12, 20, 15, 26, 29, 1, 25, 2, 3 })
        {
            int selected = type;
            WindowsIsolation.TokenInformationQuery failed = delegate(IntPtr token, int kind, IntPtr data, uint length, out uint required)
            { bool ok = ReducedQuery(token, kind, data, length, out required); return ok && kind != selected; };
            Reject(() => VerifyReduced(failed), "each_launch_query_failure_blocks");
            foreach (uint returned in new uint[] { 0, 3, 65537 })
            {
                uint size = returned;
                WindowsIsolation.TokenInformationQuery malformed = delegate(IntPtr token, int kind, IntPtr data, uint length, out uint required)
                { bool ok = ReducedQuery(token, kind, data, length, out required); if (kind == selected) required = size; return ok; };
                Reject(() => VerifyReduced(malformed), "each_launch_query_bad_size_blocks");
            }
        }
        foreach (int type in new[] { 8, 12, 20, 15, 26, 29 })
        {
            int value = type == 8 ? 2 : type == 12 ? 8 : 1;
            RejectReducedMutation(type, p => Marshal.WriteInt32(p, value), "launch_scalar_restrictions_enforced");
        }
        StartupFailure scalarFailure = null;
        try { VerifyReduced(delegate(IntPtr token, int kind, IntPtr data, uint length, out uint required)
            { bool ok = ReducedQuery(token, kind, data, length, out required); if (kind == 20) Marshal.WriteInt32(data, 1); return ok; }); }
        catch (StartupFailure error) { scalarFailure = error; }
        var record = new Dictionary<string, object>(); ProtectedPython.RecordStartupFailure(record, scalarFailure);
        Assert((string)record["reason_code"] == "launch_token_is_elevated_mismatch" &&
            new JavaScriptSerializer().Serialize(record).Contains("launch_is_elevated"), "base_failure_is_not_misreported_as_child_failure");
        RejectReducedMutation(1, p => PutSid(p, 0, 16, "S-1-5-21-111-222-333-1002"), "different_user_rejected");
        RejectReducedMutation(25, p => PutSid(p, 0, 16, "S-1-16-12288"), "high_integrity_base_rejected");
        RejectReducedMutation(25, p => Marshal.WriteInt32(p, 8, 0), "missing_integrity_attribute_rejected");
        foreach (int type in new[] { 1, 25, 2 })
        {
            int offset = type == 2 ? 8 : 0;
            RejectReducedMutation(type, p => Marshal.WriteIntPtr(p, offset, IntPtr.Zero), "null_sid_pointer_rejected");
            RejectReducedMutation(type, p => Marshal.WriteIntPtr(p, offset, IntPtr.Add(p, 65536)), "out_of_buffer_sid_rejected");
            RejectReducedMutation(type, p => Marshal.WriteIntPtr(p, offset, p), "sid_overlapping_header_rejected");
            RejectReducedMutation(type, p => Marshal.WriteByte(Marshal.ReadIntPtr(p, offset), 1, 255), "oversize_sid_rejected");
        }
        foreach (int flags in new[] { 0, 4, 0x14, 0x12, 6 })
        {
            int value = flags;
            RejectReducedMutation(2, p => Marshal.WriteInt32(p, 16, value), "admin_must_be_deny_only_not_enabled_or_default");
        }
        RejectReducedMutation(2, p => Marshal.WriteInt32(p, 0), "missing_admin_deny_only_rejected");
        RejectReducedMutation(2, p => Marshal.WriteInt32(p, -1), "group_count_overflow_rejected");
        RejectReducedMutation(2, p => PutSid(p, 8, 24, "S-1-5-32-545"), "wrong_group_is_not_admin_deny_only");
        RejectReducedMutation(3, p => Marshal.WriteInt32(p, 2), "extra_privileges_rejected");
        RejectReducedMutation(3, p => Marshal.WriteInt32(p, -1), "privilege_count_overflow_rejected");
        RejectReducedMutation(3, p => Marshal.WriteInt64(p, 4, 54321), "even_disabled_non_traverse_privilege_rejected");
        RejectReducedMutation(3, p => Marshal.WriteInt32(p, 12, 4), "unexpected_privilege_attributes_rejected");
        VerifyReduced(delegate(IntPtr token, int kind, IntPtr data, uint length, out uint required)
            { bool ok = ReducedQuery(token, kind, data, length, out required); if (kind == 3) { Marshal.WriteInt32(data, 0); required = 4; } return ok; });
        Assert(true, "no_privileges_is_allowed");
    }
    static void ErrorModeRegression()
    {
        foreach (uint previous in new uint[] { 0, 1, 2, 4, 0x8000, 0x8007, 0x10000 })
        {
            uint current = previous; int reads = 0, writes = 0;
            Native.ConfigureErrorMode(() => { reads++; return current; }, value =>
            { writes++; uint old = current; current = value; return old; });
            Assert(current == (previous | 1u) && (current & ~1u) == (previous & ~1u), "only_critical_error_bit_added");
            Assert(reads == 2 && writes == 1, "error_mode_has_initial_and_final_readback");
        }
        Reject(() => Native.ConfigureErrorMode(() => 0u, value => 0u), "error_mode_ignored_write_blocks");
        int calls = 0;
        Reject(() => Native.ConfigureErrorMode(() => ++calls == 1 ? 0u : 3u, value => 0u), "extra_error_mode_bit_blocks");
    }
    static void TimeoutEvidenceRegression()
    {
        string run = "0123456789abcdef0123456789abcdef";
        string beacon = ProtectedPython.ExpectedBeacon(run);
        foreach (string output in new[] { "", beacon, "partial", beacon + "extra" })
        {
            var record = new Dictionary<string, object> { { "status", "blocked" },
                { "reason_code", "python_startup_timeout" }, { "python_started", false }, { "fresh_state_beacon", true } };
            ProtectedPython.RecordChildEvidence(record, null, output, 7, true, run);
            Assert((string)record["status"] == "blocked" && (string)record["reason_code"] == "python_startup_timeout" &&
                !(bool)record["python_started"], "timeout_and_success_decision_unchanged_by_evidence");
            Assert((bool)record["output_capture_complete"] && (int)record["child_stdout_bytes"] == output.Length &&
                (int)record["child_stderr_bytes"] == 7, "stopped_child_output_counts_recorded");
            Assert((bool)record["stdout_beacon_matches"] == (output == beacon), "stdout_match_is_exact_not_startup_success");
            Assert(!(bool)record["child_exit_observed_before_cleanup"] && !record.ContainsKey("child_exit_hex"),
                "forced_job_exit_never_fabricated_as_natural_exit");
            var decoded = new JavaScriptSerializer().Deserialize<Dictionary<string, object>>(
                new JavaScriptSerializer().Serialize(record));
            Assert((string)decoded["reason_code"] == "python_startup_timeout" && !(bool)decoded["python_started"],
                "timeout_classification_survives_json");
        }
        foreach (bool complete in new[] { false, true })
        {
            var unknown = new Dictionary<string, object>();
            ProtectedPython.RecordChildEvidence(unknown, null, null, 0, complete, run);
            Assert(!(bool)unknown["output_capture_complete"] && unknown["child_stdout_bytes"] == null &&
                unknown["child_stderr_bytes"] == null && unknown["stdout_beacon_matches"] == null,
                "missing_capture_is_unknown_not_zero_or_false");
        }
        var failed = new Dictionary<string, object>();
        ProtectedPython.RecordChildEvidence(failed, null, beacon, 5, false, run);
        Assert(failed["child_stdout_bytes"] == null && failed["child_stderr_bytes"] == null &&
            failed["stdout_beacon_matches"] == null, "incomplete_capture_does_not_claim_partial_counts");
        var exited = new Dictionary<string, object> { { "status", "blocked" }, { "reason_code", "python_output_capture_failed" } };
        ProtectedPython.RecordChildEvidence(exited, 0xC0000142, "", 0, true, run);
        Assert((bool)exited["child_exit_observed_before_cleanup"] && (string)exited["child_exit_hex"] == "0xC0000142" &&
            (string)exited["reason_code"] == "python_output_capture_failed", "observed_exit_preserved_without_reclassifying_failure");
    }
    static void DetachedLaunchRegression()
    {
        uint flags = WindowsIsolation.LaunchCreationFlags;
        Assert(flags == 0x0008040c, "exact_detached_launch_flags");
        foreach (uint bit in new uint[] { 0x8, 0x80000, 0x400, 0x4 })
            Assert((flags & bit) != 0, "required_detached_launch_bit_" + bit);
        Assert((flags & (0x08000000u | 0x10u | 0x01000000u | 0x1u | 0x2u)) == 0,
            "no_no_window_new_console_breakaway_or_debug_launch_flags");
        Assert((flags ^ 0x08080404u) == (0x08000000u | 0x8u), "only_console_mode_changed_from_package_5");
    }
    static void AppContainerAccessRegression()
    {
        for (int mask = 0; mask < 16; mask++)
        {
            bool package = (mask & 1) != 0, noGrant = (mask & 2) != 0;
            bool aap = (mask & 4) != 0, wrong = (mask & 8) != 0;
            if (mask == 5)
            {
                WindowsIsolation.RequireAppContainerAccessControls(package, noGrant, aap, wrong);
                Assert(true, "ordinary_appcontainer_expected_access_controls");
            }
            else Reject(() => WindowsIsolation.RequireAppContainerAccessControls(package, noGrant, aap, wrong),
                "reject_wrong_appcontainer_access_controls_" + mask);
        }
    }
    public static int Main(string[] args)
    {
        try
        {
            ElevationQueryRegression();
            TokenFailureReportingRegression();
            ReducedLaunchTokenRegression();
            ErrorModeRegression();
            TimeoutEvidenceRegression();
            DetachedLaunchRegression();
            AppContainerAccessRegression();
            string run = "0123456789abcdef0123456789abcdef";
            Assert(ProtectedPython.ExpectedBeacon(run) == "MAYA_PROTECTED_PYTHON_STARTED_V1:" + run + "\n", "beacon");
            string beacon = ProtectedPython.ExpectedBeacon(run);
            Assert(ProtectedPython.StartupComplete(0, beacon, true, run), "startup_success_requires_both_beacons");
            Assert(!ProtectedPython.StartupComplete(1, beacon, true, run), "nonzero_exit_is_not_success");
            Assert(!ProtectedPython.StartupComplete(0, beacon, false, run), "missing_fresh_state_is_not_success");
            Assert(!ProtectedPython.StartupComplete(0, null, true, run), "missing_stdout_is_not_success");
            Assert(!ProtectedPython.StartupComplete(0, beacon + "extra", true, run), "extra_stdout_is_not_success");
            Assert(!ProtectedPython.StartupComplete(0, beacon.Replace(run, new string('a', 32)), true, run), "stale_stdout_is_not_success");
            foreach (string bad in new[] { "", "../escape", new string('z', 32), run + "\n" })
                Reject(() => ProtectedPython.ExpectedBeacon(bad), "invalid_beacon_id");
            foreach (string bad in new[] { "../escape", "python/../outside", "python//file", "python/a.", "python/a ",
                "python/COn.txt", "python/LPT1", "python/COM9.py", "/python/file", "python\\file", "python/a:b", "elsewhere/file" })
                Reject(() => ProductFiles.PayloadPath(bad), "unsafe_payload_path");
            Assert(ProductFiles.PayloadPath("python/Lib/encodings/__init__.py").EndsWith("__init__.py"), "normal_payload_path");
            Assert(Index(Files()).files.Count == 3, "valid_inventory");
            var duplicate = Files(); duplicate.Add(new PayloadFile { path = "PYTHON/python.exe", size = 1, sha256 = new string('b', 64) });
            Reject(() => Index(duplicate), "case_insensitive_duplicate");
            var missing = Files(); missing[2].path = "notices/license.txt";
            Reject(() => Index(missing), "required_file_missing");
            var large = Files(); large[0].size = 32 * 1024 * 1024 + 1;
            Reject(() => Index(large), "oversized_file");
            var negative = Files(); negative[0].size = -1;
            Reject(() => Index(negative), "negative_size");
            var digest = Files(); digest[0].sha256 = new string('x', 64);
            Reject(() => Index(digest), "invalid_digest");
            Layout("Filter", 200); Layout("Condition", 40); Layout("Sublayer", 72);
            Layout("Startup", 104); Layout("StartupEx", 112); Layout("Capabilities", 24);
            Layout("JobLimits", 144); Layout("JobAccounting", 48);
            Layout("SidAttributes", 16);
            var user = new SecurityIdentifier("S-1-5-21-111-222-333-1001");
            var package = new SecurityIdentifier("S-1-15-2-111-222-333-444-555-666-777");
            ProductFiles.VerifyRootDescriptor(ProductFiles.RootSecurity());
            Assert(true, "expected_root_descriptor");
            var foreignRoot = ProductFiles.RootSecurity();
            foreignRoot.AddAccessRule(new FileSystemAccessRule(user, FileSystemRights.Write, AccessControlType.Allow));
            Reject(() => ProductFiles.VerifyRootDescriptor(foreignRoot), "foreign_root_grant");
            var inheritedRoot = ProductFiles.RootSecurity(); inheritedRoot.SetAccessRuleProtection(false, false);
            Reject(() => ProductFiles.VerifyRootDescriptor(inheritedRoot), "unprotected_root");
            var wrongOwner = ProductFiles.RootSecurity(); wrongOwner.SetOwner(user);
            Reject(() => ProductFiles.VerifyRootDescriptor(wrongOwner), "foreign_root_owner");
            var state = ProductFiles.StateSecurity(package, user);
            Assert(state.AreAccessRulesProtected, "private_state_dacl_protected");
            bool userWrite = false, fileGrant = false, folderGrant = false;
            foreach (FileSystemAccessRule rule in state.GetAccessRules(true, true, typeof(SecurityIdentifier)))
            {
                if (rule.IdentityReference.Equals(user) && (rule.FileSystemRights & FileSystemRights.WriteData) != 0) userWrite = true;
                if (!rule.IdentityReference.Equals(package)) continue;
                Assert((rule.FileSystemRights & (FileSystemRights.ChangePermissions | FileSystemRights.TakeOwnership)) == 0, "package_cannot_change_permissions");
                if (rule.InheritanceFlags == InheritanceFlags.ObjectInherit)
                {
                    fileGrant = true;
                    Assert(rule.PropagationFlags == PropagationFlags.InheritOnly && (rule.FileSystemRights & FileSystemRights.ExecuteFile) == 0,
                        "private_files_not_executable");
                }
                if (rule.InheritanceFlags == InheritanceFlags.ContainerInherit) folderGrant = true;
            }
            Assert(userWrite && fileGrant && folderGrant, "both_token_principals_can_write_state");
            foreach (FileSystemAccessRule rule in ProductFiles.RuntimeSecurity(package, user).GetAccessRules(true, true, typeof(SecurityIdentifier)))
                if (rule.IdentityReference.Equals(package))
                    Assert(rule.FileSystemRights == (FileSystemRights.ReadAndExecute | FileSystemRights.Synchronize), "runtime_package_read_only");
            Assert(ProtectedPython.FailureCode(new Exception("SECRET")) == "operation_failed_Exception", "safe_error");
            Assert(ProtectedPython.FailureCode(new StartupFailure("fixed_code")) == "fixed_code", "fixed_error");
            if (args.Length >= 1 && args.Length <= 2 && args[0] == "--unpack")
            {
                string build = "maya-protected-python-startup-20261018";
                if (args.Length == 2)
                {
                    if (args[1] == "--package-2") build += "-2";
                    else if (args[1] == "--package-3") build += "-3";
                    else if (args[1] == "--package-4") build += "-4";
                    else if (args[1] == "--package-5") build = "maya-protected-python-startup-20261020-5";
                    else if (args[1] == "--package-6") build = "maya-protected-python-startup-20261021-6";
                    else if (args[1] == "--package-7") build = "maya-protected-python-startup-20261021-7";
                    else if (args[1] == "--package-8") build = "maya-protected-python-containment-20261021-8";
                    else if (args[1] == "--package-9") build = "maya-protected-python-containment-20261021-9";
                    else if (args[1] == "--package-10") build = "maya-protected-python-containment-20261021-10";
                    else if (args[1] == "--package-11") build = "maya-protected-python-containment-20261021-11";
                    else throw new Exception("fixture_argument");
                }
                string target = Path.Combine(Directory.GetCurrentDirectory(), ".codex-build",
                    build, "unpack-check");
                Directory.CreateDirectory(target);
                ProductFiles.ExtractPayload(target);
                Console.WriteLine("Embedded payload unpack/hash checks passed; no security provisioning or Python execution.");
            }
            else if (args.Length != 0) throw new Exception("fixture_argument");
            Console.WriteLine("Inert checks passed: " + count); return 0;
        }
        catch (Exception error) { Console.Error.WriteLine(error.GetType().Name + ":" + error.Message); return 1; }
    }
}
