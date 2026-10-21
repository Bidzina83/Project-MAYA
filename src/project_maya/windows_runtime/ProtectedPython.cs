// Product-owned startup candidate. No Hermes execution or containment acceptance.
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Security.Principal;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;

[assembly: AssemblyTitle("Maya protected Python startup candidate")]
[assembly: AssemblyVersion("0.1.0.0")]
[assembly: AssemblyFileVersion("0.1.0.11")]
[assembly: AssemblyInformationalVersion("0.1.0-screen.11")]

namespace ProjectMaya.WindowsRuntime
{
    internal static class ProtectedPython
    {
        internal const string Version = "0.1.0-screen.11";
        internal const string Scope = "synthetic-containment-screen-v1";
        internal const string Consent =
            "Maya protected Python containment screen " + Version + "\r\n\r\n" +
            "This is an unsigned development component, not the complete Maya product.\r\n\r\n" +
            "With your approval, Maya will:\r\n" +
            "- Copy its embedded Python 3.13.14 into a new, private Maya folder under ProgramData.\r\n" +
            "- Create one ordinary Windows AppContainer profile for this attempt, not LPAC.\r\n" +
            "  Ordinary AppContainer can access resources Windows already grants to All Application " +
            "Packages; this is broader implicit access than LPAC, not containment qualification.\r\n" +
            "- Give that profile read/execute access to its Python files and read/write access " +
            "to its private state; lower only that state folder's integrity label.\r\n" +
            "- Add six persistent network-block rules, scoped only to that profile: IPv4/IPv6 " +
            "outbound, listening and incoming connections. No network access is requested.\r\n" +
            "- Create a reduced, non-elevated launch token for your same user, without " +
            "changing your account, UAC settings or the setup host's token.\r\n" +
            "- Start one low-integrity Python process, with no extra capabilities or child " +
            "processes, for at most 30 seconds. It writes a fresh local startup record.\r\n" +
            "- Stop the process and remove its profile, rules and file grants afterward. " +
            "Keep the prepared files and result report for inspection.\r\n\r\n" +
             "Maya sets a process-local error mode inherited by Python to avoid critical-error " +
             "dialogs hiding exit failures. Windows Error Reporting is not disabled. " +
             "After a timeout, Maya stops Python before recording available output counts and " +
             "its startup marker; a timeout is never reported as startup success.\r\n\r\n" +
            "This screen also creates synthetic document, memory, business, policy, audit " +
            "and dummy-secret canaries inside this new Maya attempt folder. Python attempts " +
            "direct reads, writes, creation and deletion, plus fixed path/ADS/link routes. " +
            "One new public canary gets temporary All Application Packages read access. " +
            "Maya creates a private shared-memory object and four temporary loopback-only " +
            "TCP/UDP endpoints (IPv4 and IPv6), with host positive controls. Python attempts " +
            "network access, host process/token access and one fixed inert subprocess; no " +
            "shell or caller-selected code is used. No existing customer resource is a target. " +
            "For UDP, Maya attempts synthetic send/receive traffic and reads a bounded " +
            "snapshot of existing Windows filtering events to identify its own rule drops. " +
            "Event collection must already be enabled; Maya does not enable or change it. " +
            "Missing events remain inconclusive. No complete event-loss accounting is available. " +
            "The screen reads ACL metadata on the runtime and System32 roots, not private " +
            "contents. Temporary links, endpoints, shared memory and fixture grants are " +
            "removed after confirmed stop; inert canaries and reports remain for inspection. " +
            "Any observed unauthorized effect fails the screen. Missing evidence, a timeout " +
            "or unavailable target is never a pass. All protections and the 30-second child " +
            "limit remain unchanged. A completed screen still does not qualify containment.\r\n\r\n" +
            "No registry permissions, loopback exemptions, firewall defaults, antivirus, " +
            "encryption, boot settings or Azure resources will be changed. " +
            "No models, connectors, credentials or customer files are used.\r\n\r\n" +
            "The trusted setup host needs administrator rights for these changes; Python " +
            "must still pass restricted-token checks. This first candidate does not qualify " +
            "standard-user setup. If startup or cleanup fails, stop and send the report. " +
            "Do not disable Windows protections. Closing Maya forcibly may leave cleanup " +
            "pending; reopen it and use Recover cleanup. No unrestricted fallback or retry occurs.";

        [STAThread]
        public static int Main(string[] args)
        {
            try
            {
                Native.ConfigureErrorMode();
                Native.Require(Native.SetDefaultDllDirectories(0x800), "system_dll_search");
                if (IntPtr.Size != 8) throw new StartupFailure("requires_x64");
                string user = WindowsIdentity.GetCurrent().User.Value;
                if (args.Length != 0 && (args.Length != 2 || args[0] != "--elevated" || args[1] != user))
                    throw new StartupFailure("elevation_identity_changed");
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                using (var window = new StartupWindow()) Application.Run(window);
                return 0;
            }
            catch (Exception error)
            {
                MessageBox.Show("Maya did not start Python. Reason: " + FailureCode(error),
                    "Maya protected Python", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return 1;
            }
        }

        internal static string FailureCode(Exception error)
        {
            var failure = error as StartupFailure;
            return failure != null ? failure.Message : "operation_failed_" + error.GetType().Name;
        }

        internal static void RecordStartupFailure(Dictionary<string, object> record, Exception error)
        {
            record["status"] = "blocked";
            record["reason_code"] = FailureCode(error);
            var failure = error as StartupFailure;
            if (failure != null && failure.TokenCheck != null) record["token_check_failure"] = failure.TokenCheck;
        }

        internal static string ExpectedBeacon(string run)
        {
            Guid parsed;
            if (run == null || run.Length != 32 || !Guid.TryParseExact(run, "N", out parsed)) throw new StartupFailure("invalid_attempt_id");
            foreach (char value in run)
                if (!(value >= '0' && value <= '9' || value >= 'a' && value <= 'f')) throw new StartupFailure("invalid_attempt_id");
            return "MAYA_PROTECTED_PYTHON_STARTED_V1:" + run + "\n";
        }

        internal static bool StartupComplete(uint exit, string output, bool freshState, string run)
        {
            return exit == 0 && freshState && output == ExpectedBeacon(run);
        }

        internal static void RecordChildEvidence(Dictionary<string, object> record, uint? exit,
            string stdout, int stderrBytes, bool captureComplete, string run)
        {
            bool known = captureComplete && stdout != null;
            record["output_capture_complete"] = known;
            record["child_stdout_bytes"] = known ? (object)stdout.Length : null;
            record["child_stderr_bytes"] = known ? (object)stderrBytes : null;
            record["stdout_beacon_matches"] = known ? (object)(stdout == ExpectedBeacon(run)) : null;
            // Never substitute the job's forced-termination code for a natural exit.
            record["child_exit_observed_before_cleanup"] = exit.HasValue;
            if (exit.HasValue) record["child_exit_hex"] = "0x" + exit.Value.ToString("X8");
        }

        static bool ReadFreshBeacon(string directory, string run)
        {
            string path = Path.Combine(directory, "state", "python-startup.txt");
            try { File.GetAttributes(path); }
            catch (FileNotFoundException) { return false; }
            catch (DirectoryNotFoundException) { return false; }
            ProductFiles.NoLinks(path);
            return new FileInfo(path).Length <= 256 && File.ReadAllText(path) == ExpectedBeacon(run);
        }

        internal static Dictionary<string, object> ReadRecord(string path)
        {
            ProductFiles.NoLinks(path);
            if (new FileInfo(path).Length > 65536) throw new StartupFailure("record_too_large");
            return new JavaScriptSerializer().Deserialize<Dictionary<string, object>>(File.ReadAllText(path));
        }

        internal static void SaveRecord(string path, object value)
        {
            string text = SerializeRecord(value);
            ProductFiles.NoLinks(Path.GetDirectoryName(path));
            string temporary = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
            using (var file = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
            using (var writer = new StreamWriter(file, new System.Text.UTF8Encoding(false)))
            {
                writer.Write(text);
                writer.Flush(); file.Flush(true);
            }
            if (File.Exists(path)) { ProductFiles.NoLinks(path); File.Replace(temporary, path, null); }
            else File.Move(temporary, path);
        }
        internal static string SerializeRecord(object value)
        {
            string text = new JavaScriptSerializer().Serialize(value);
            if (System.Text.Encoding.UTF8.GetByteCount(text) > ContainmentEvidence.MaximumReportBytes)
                throw new StartupFailure("record_too_large");
            return text;
        }
        internal static void RecordStageFailure(Dictionary<string, object> record, string prefix, string stage, Exception error)
        {
            record[prefix + "_stage"] = stage;
            record[prefix + "_hresult"] = "0x" + error.HResult.ToString("X8");
        }

        internal static List<string> Pending()
        {
            var result = new List<string>();
            if (!Directory.Exists(ProductFiles.Root)) return result;
            ProductFiles.VerifyRoot();
            foreach (string directory in Directory.GetDirectories(ProductFiles.Root))
            {
                Guid id;
                if (!Guid.TryParseExact(Path.GetFileName(directory), "N", out id))
                    throw new StartupFailure("unexpected_product_directory");
                ProductFiles.NoLinks(directory);
                string journal = Path.Combine(directory, "attempt.json");
                if (!File.Exists(journal)) throw new StartupFailure("attempt_record_missing");
                var record = ReadRecord(journal);
                if ((string)record["operator_sid"] != WindowsIdentity.GetCurrent().User.Value)
                    throw new StartupFailure("other_operator_attempt_present");
                if (!record.ContainsKey("cleanup_complete") || !(bool)record["cleanup_complete"])
                    result.Add(directory);
            }
            return result;
        }

        internal static string Execute(bool recover)
        {
            if (!recover) Native.CheckBaseline();
            ProductFiles.EnsureRoot();
            string ownerLock = Path.Combine(ProductFiles.Root, "lifecycle.lock");
            ProductFiles.NoLinks(ownerLock);
            using (var lifecycle = new FileStream(ownerLock, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None))
                return ExecuteOwned(recover);
        }

        static string ExecuteOwned(bool recover)
        {
            var user = WindowsIdentity.GetCurrent().User;
            var pending = Pending();
            if (recover && pending.Count != 1) throw new StartupFailure("recovery_requires_one_pending_attempt");
            if (!recover && pending.Count != 0) throw new StartupFailure("cleanup_pending_use_recovery");
            string run = recover ? Path.GetFileName(pending[0]) : Guid.NewGuid().ToString("N");
            string directory = Path.Combine(ProductFiles.Root, run);
            string moniker = "Maya.ProtectedPython.Startup1." + run;
            Dictionary<string, object> record;
            if (recover)
            {
                record = ReadRecord(Path.Combine(directory, "attempt.json"));
                if ((string)record["version"] != Version || (string)record["scope"] != Scope ||
                    (string)record["profile"] != moniker) throw new StartupFailure("recovery_record_mismatch");
                if (record.ContainsKey("profile_collision") && (bool)record["profile_collision"])
                    throw new StartupFailure("profile_collision_requires_review_not_deletion");
                int pid = Convert.ToInt32(record["host_pid"]);
                long ticks = Convert.ToInt64(record["host_start_ticks"]);
                try
                {
                    using (var prior = Process.GetProcessById(pid))
                        if (!prior.HasExited && prior.StartTime.ToUniversalTime().Ticks == ticks)
                            throw new StartupFailure("close_previous_maya_window_before_recovery");
                }
                catch (ArgumentException) { }
            }
            else
            {
                ProductFiles.CreateAttempt(directory, user);
                using (var host = Process.GetCurrentProcess())
                    record = new Dictionary<string, object> {
                        {"schema", "maya.protected_python.startup.v1"}, {"version", Version}, {"scope", Scope},
                        {"isolation_mode", "appcontainer-wfp"},
                        {"operator_sid", user.Value}, {"profile", moniker}, {"attempt_id", run},
                        {"host_pid", host.Id}, {"host_start_ticks", host.StartTime.ToUniversalTime().Ticks},
                        {"os_build", "26300.9711"}, {"host_elevated", true}, {"informed_consent", true},
                        {"python_version", "3.13.14"}, {"python_started", false}, {"child_resumed", false},
                        {"cleanup_complete", false}, {"production_qualified", false}, {"containment_qualified", false},
                        {"status", "preparing"}, {"created_utc", DateTime.UtcNow.ToString("o")},
                        {"launcher_sha256", ProductFiles.HashFile(Assembly.GetExecutingAssembly().Location)}
                    };
            }
            string recordPath = Path.Combine(directory, "attempt.json");
            SaveRecord(recordPath, record);
            var isolation = new WindowsIsolation(moniker);
            var screen = new ContainmentScreen(directory, run, isolation.Package, user);
            var observations = new Dictionary<string, string>(StringComparer.Ordinal);
            record["security_resource_inventory"] = isolation.ResourceInventory();
            bool cleanup = false;
            try
            {
                if (!recover)
                {
                    screen.Stage = "payload_extract";
                    ProductFiles.ExtractPayload(directory);
                    record["payload_verified"] = true;
                    screen.Stage = "profile_create";
                    isolation.CreateProfile();
                    screen.Stage = "file_grants";
                    ProductFiles.Grant(directory, isolation.Package, user);
                    screen.Prepare();
                    screen.Stage = "network_provision";
                    isolation.ProvisionNetwork();
                    record["network_filters_verified"] = 6;
                    screen.Stage = "udp_evidence_setup";
                    screen.ConfigureUdp(isolation, record);
                    screen.Stage = "child_create_suspended";
                    isolation.Start(directory, run, user);
                    screen.BindChild(checked((int)isolation.ChildPid));
                    screen.Stage = "plan_write";
                    screen.WritePlan(isolation.StandardHandles);
                    record["screen_fixture_inventory"] = screen.Plan;
                    screen.Stage = "acl_inventory";
                    record["screen_acl_metadata_inventory"] = screen.AclInventory();
                    record["restricted_token_verified"] = true;
                    record["child_pid"] = isolation.ChildPid;
                    record["status"] = "restricted_child_suspended";
                    screen.Stage = "suspended_record_write";
                    SaveRecord(recordPath, record);
                    screen.Stage = "child_resume_wait";
                    uint exit = isolation.ResumeAndWait();
                    record["child_resumed"] = true;
                    screen.Stage = "child_startup_evidence";
                    RecordChildEvidence(record, exit, isolation.Stdout, isolation.StderrBytes,
                        isolation.OutputCaptureComplete, run);
                    bool beacon = ReadFreshBeacon(directory, run);
                    record["fresh_state_beacon"] = beacon;
                    record["python_entry_observed"] = beacon && isolation.OutputCaptureComplete && isolation.Stdout == ExpectedBeacon(run);
                    record["python_started"] = StartupComplete(exit, isolation.Stdout, beacon, run);
                    record["status"] = (bool)record["python_started"] ? "startup_completed_not_containment_qualified" : "startup_failed";
                }
            }
            catch (Exception error)
            {
                RecordStartupFailure(record, error);
                RecordStageFailure(record, "screen_failure", screen.Stage, error);
                record["profile_collision"] = isolation.ProfileCollision;
                record["child_resumed"] = isolation.Resumed;
                if (isolation.ExitCode.HasValue) record["child_exit_hex"] = "0x" + isolation.ExitCode.Value.ToString("X8");
            }
            finally
            {
                if (!recover) record["reduced_launch_token_verified"] = isolation.ReducedLaunchTokenVerified;
                if (!recover) record["startup_status"] = record["status"];
                // Keep durable network denies and grants if stopping the job is uncertain.
                try
                {
                    screen.Stage = "job_stop";
                    isolation.Stop();
                    if (!recover && isolation.Resumed && (string)record["startup_status"] == "blocked")
                    {
                        try
                        {
                            RecordChildEvidence(record, isolation.ExitCode, isolation.Stdout, isolation.StderrBytes,
                                isolation.OutputCaptureComplete, run);
                            record["evidence_phase"] = "after_job_stop";
                            record["fresh_state_beacon"] = null;
                            record["fresh_state_beacon"] = ReadFreshBeacon(directory, run);
                        }
                        catch (Exception error) { record["evidence_reason_code"] = FailureCode(error); }
                    }
                    if (!recover && isolation.Resumed)
                    {
                        try { observations = screen.Collect(record); }
                        catch (Exception error)
                        {
                            record["screen_evidence_reason_code"] = FailureCode(error);
                            RecordStageFailure(record, "screen_evidence_failure", screen.Stage, error);
                            screen.RecordNetworkEvidence(record);
                            if (record.ContainsKey("screen_host_unauthorized_network_effect") && (bool)record["screen_host_unauthorized_network_effect"] ||
                                record.ContainsKey("screen_host_postconditions") && !(bool)record["screen_host_postconditions"])
                                observations["host.effect"] = "failed";
                        }
                    }
                    screen.Cleanup();
                    screen.Stage = "file_grant_revocation";
                    ProductFiles.Revoke(directory, isolation.Package);
                    screen.Stage = "profile_delete";
                    isolation.DeleteProfile();
                    screen.Stage = "network_remove";
                    isolation.RemoveNetwork();
                    cleanup = true;
                    screen.Stage = "cleanup_complete";
                }
                catch (Exception error)
                {
                    record["cleanup_reason_code"] = FailureCode(error);
                    RecordStageFailure(record, "screen_cleanup_failure", screen.Stage, error);
                }
                record["screen_last_stage"] = screen.Stage;
                isolation.Dispose();
                record["cleanup_complete"] = cleanup;
                if (!recover)
                {
                    if (!isolation.ExitCode.HasValue || isolation.ExitCode.Value != 0 ||
                        !record.ContainsKey("python_started") || !(bool)record["python_started"])
                        observations["execution.incomplete"] = "inconclusive";
                    record["screen_status"] = ContainmentScreen.Finish(observations, cleanup);
                    if ((string)record["screen_status"] == "screen_completed_not_containment_qualified")
                        record["screen_status"] = "observations_completed_pending_independent_cleanup";
                    record["screen_observations"] = observations;
                    record["screen_independent_cleanup_verified"] = false;
                    record["status"] = record["screen_status"];
                }
                if (!recover) record["finished_utc"] = DateTime.UtcNow.ToString("o");
                if (recover && cleanup)
                {
                    record["recovery_completed"] = true;
                    record["recovery_utc"] = DateTime.UtcNow.ToString("o");
                    record["status"] = record.ContainsKey("startup_status") ? record["startup_status"] : "security_cleanup_recovered";
                }
                if (!cleanup) record["status"] = "cleanup_pending_stop";
                SaveRecord(recordPath, record);
            }
            return recordPath;
        }
    }

    internal sealed class TokenCheckFailure
    {
        public string check { get; private set; }
        public int information_class { get; private set; }
        public uint expected { get; private set; }
        public uint observed { get; private set; }

        internal TokenCheckFailure(string name, int type, uint required, uint actual)
        { check = name; information_class = type; expected = required; observed = actual; }
    }

    internal sealed class StartupFailure : Exception
    {
        internal TokenCheckFailure TokenCheck { get; private set; }
        internal StartupFailure(string code) : base(code) { }
        internal StartupFailure(string code, TokenCheckFailure detail) : base(code) { TokenCheck = detail; }
    }

    internal sealed class StartupWindow : Form
    {
        readonly CheckBox consent = new CheckBox();
        readonly Button start = new Button(), recover = new Button(), reports = new Button();
        readonly Label status = new Label();
        bool active;
        string reportPath;
        readonly bool administrator;

        internal StartupWindow()
        {
            administrator = new WindowsPrincipal(WindowsIdentity.GetCurrent()).IsInRole(WindowsBuiltInRole.Administrator);
            Text = "Maya | Protected Python startup"; Font = new Font("Segoe UI", 9);
            AutoScaleMode = AutoScaleMode.Dpi; ClientSize = new Size(700, 660);
            MinimumSize = new Size(650, 620); StartPosition = FormStartPosition.CenterScreen;
            var layout = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 1, RowCount = 5, Padding = new Padding(18) };
            layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 42));
            layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
            layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 50));
            layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 45));
            layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 85));
            layout.Controls.Add(new Label { Text = "Maya protected Python", Font = new Font(Font.FontFamily, 18), Dock = DockStyle.Fill }, 0, 0);
            layout.Controls.Add(new TextBox { Text = ProtectedPython.Consent, Multiline = true, ReadOnly = true,
                ScrollBars = ScrollBars.Vertical, Dock = DockStyle.Fill, BackColor = Color.White }, 0, 1);
            consent.Text = "I approve the changes described above for this VM attempt.";
            consent.Dock = DockStyle.Fill; layout.Controls.Add(consent, 0, 2);
            var buttons = new FlowLayoutPanel { Dock = DockStyle.Fill, WrapContents = false };
            start.Text = administrator ? "Start protected Python" : "Open setup";
            start.AutoSize = true; start.Enabled = false;
            recover.Text = "Recover cleanup"; recover.AutoSize = true; recover.Enabled = false;
            reports.Text = "Open results"; reports.AutoSize = true; reports.Enabled = false;
            buttons.Controls.Add(start); buttons.Controls.Add(recover); buttons.Controls.Add(reports);
            layout.Controls.Add(buttons, 0, 3);
            status.Dock = DockStyle.Fill; status.Text = "No security changes made. Prepared for Windows 11 Pro build 26300.9711 only.";
            layout.Controls.Add(status, 0, 4); Controls.Add(layout);
            consent.CheckedChanged += delegate { if (!active) { start.Enabled = consent.Checked; recover.Enabled = consent.Checked; } };
            start.Click += async delegate { await Run(false); };
            recover.Click += async delegate { await Run(true); };
            reports.Click += delegate { Process.Start(new ProcessStartInfo(Path.GetDirectoryName(reportPath)) { UseShellExecute = true }); };
            FormClosing += delegate(object sender, FormClosingEventArgs e) { if (active) { e.Cancel = true; status.Text = "Finishing startup and security cleanup. Please wait."; } };
        }

        async Task Run(bool cleanup)
        {
            if (!consent.Checked || active) return;
            start.Enabled = recover.Enabled = consent.Enabled = false;
            if (!administrator)
            {
                try
                {
                    if (cleanup) throw new StartupFailure("open_setup_then_select_recover_cleanup");
                    string user = WindowsIdentity.GetCurrent().User.Value;
                    using (Process.Start(new ProcessStartInfo(Assembly.GetExecutingAssembly().Location,
                        "--elevated " + user) { UseShellExecute = true, Verb = "runas" })) { }
                    Close();
                }
                catch (Win32Exception error)
                { status.Text = error.NativeErrorCode == 1223 ? "Administrator approval cancelled. Python was not started." : "Setup did not open. No security setup attempted."; }
                catch (Exception error) { status.Text = ProtectedPython.FailureCode(error); }
                return;
            }
            active = true; status.Text = cleanup ? "Removing this product's pending security setup..." : "Preparing and starting protected Python...";
            try
            {
                reportPath = await Task.Run(() => ProtectedPython.Execute(cleanup));
                var record = ProtectedPython.ReadRecord(reportPath);
                string outcome = (string)record["status"];
                string description = !(bool)record["cleanup_complete"] ? "Cleanup needs attention. Stop here; do not run Python again." :
                    cleanup ? "Security cleanup completed. Python was not launched again." :
                    outcome == "startup_completed_not_containment_qualified" ? "Python completed startup. Containment is not yet qualified." :
                    "Python did not complete startup.";
                status.Text = description + "\r\n" +
                    (record.ContainsKey("child_exit_hex") ? "Python exit: " + record["child_exit_hex"] + ". " : "") +
                    "Cleanup complete: " + record["cleanup_complete"] + ".\r\n" + reportPath;
                reports.Enabled = true;
            }
            catch (Exception error) { status.Text = "Python was not started again. Reason: " + ProtectedPython.FailureCode(error); }
            finally { active = false; }
        }
    }
}
