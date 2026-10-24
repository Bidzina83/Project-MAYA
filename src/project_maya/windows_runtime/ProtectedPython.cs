// Product-owned startup candidate. No Hermes execution or containment acceptance.
#if HERMES_MODEL && !HERMES_BRIDGE
#error HERMES_MODEL requires the private HERMES_BRIDGE topology.
#endif
#if HERMES_BRIDGE && (!HERMES_CONSTRUCTION || !HERMES_IMPORT || HERMES_STATE || HERMES_MEMORY)
#error HERMES_BRIDGE requires CONSTRUCTION/IMPORT and excludes STATE/MEMORY.
#endif
#if HERMES_MEMORY && (!HERMES_CONSTRUCTION || HERMES_STATE)
#error HERMES_MEMORY requires HERMES_CONSTRUCTION and excludes HERMES_STATE.
#endif
#if HERMES_STATE && !HERMES_CONSTRUCTION
#error HERMES_STATE requires the HERMES_CONSTRUCTION profile.
#endif
#if HERMES_CONSTRUCTION && !HERMES_IMPORT
#error HERMES_CONSTRUCTION requires the HERMES_IMPORT payload and no-fixture profile.
#endif
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
#if HERMES_MODEL
[assembly: AssemblyFileVersion("0.2.1.1")]
[assembly: AssemblyInformationalVersion("0.2.1-offline-model.1")]
#elif HERMES_BRIDGE
[assembly: AssemblyFileVersion("0.2.0.2")]
[assembly: AssemblyInformationalVersion("0.2.0-bridge-document.2")]
#elif HERMES_MEMORY
[assembly: AssemblyFileVersion("0.1.4.1")]
[assembly: AssemblyInformationalVersion("0.1.4-hermes-memory.1")]
#elif HERMES_STATE
[assembly: AssemblyFileVersion("0.1.3.1")]
[assembly: AssemblyInformationalVersion("0.1.3-hermes-state.1")]
#elif HERMES_CONSTRUCTION
[assembly: AssemblyFileVersion("0.1.2.2")]
[assembly: AssemblyInformationalVersion("0.1.2-hermes-construction.2")]
#elif HERMES_IMPORT
[assembly: AssemblyFileVersion("0.1.1.1")]
[assembly: AssemblyInformationalVersion("0.1.1-hermes-import.1")]
#else
[assembly: AssemblyFileVersion("0.1.0.11")]
[assembly: AssemblyInformationalVersion("0.1.0-screen.11")]
#endif

namespace ProjectMaya.WindowsRuntime
{
    internal static class ProtectedPython
    {
#if HERMES_MODEL
        internal const string Version = "0.2.1-offline-model.1";
        internal const string Scope = "offline-hermes-model-wire-v1";
        internal const string Consent =
            "Maya offline model bridge " + Version + "\r\n\r\n" +
            "Unsigned development candidate, not production or containment qualified. One real pinned Hermes " +
            "conversation uses its genuine SDK with a private-pipe transport and an explicitly synthetic response. " +
            "There is NO external inference, network provider, credential, customer content or charge.\r\n\r\n" +
            "Maya copies verified Python 3.13.14, pinned Hermes, unchanged dependencies and canonical Maya code " +
            "into a fresh private ProgramData attempt. It provisions ordinary AppContainer with zero capabilities, " +
            "reduced tokens, one-process jobs, child-process block and six child-scoped deny-all WFP filters. " +
            "Shared All Application Packages access remains an isolation limitation.\r\n\r\n" +
            "One additional trusted medium-integrity Python gateway worker remains OUTSIDE AppContainer. " +
            "Child filters do not contain the worker. This profile implements no worker networking or live model " +
            "operation. Private inherited pipes, not HTTP/listeners or loopback exemptions, carry bounded messages.\r\n\r\n" +
            "A protected host folder retains request.json, exact policy, worker setup and durable audit. " +
            "Only SYSTEM, Administrators and this operator have access. Expected request text comes from reviewed " +
            "native literals and trusted setup, not the child's first request. The synthetic request includes " +
            "the private attempt's state path and UTC day; UTC is a private Hermes config, not an OS change.\r\n\r\n" +
            "A version-bound Maya subclass selects Hermes' native non-streaming path and delegates client creation " +
            "with fresh private HTTP transports. No wheel patch, fake runtime, credentials, tools, memory/database " +
            "workload, fallback or retries. One synthetic dispatch is allowed. Runtime output and final operator " +
            "output require separate existing-gateway decisions and exact synthetic-content validation. " +
            "The approved synthetic final text is displayed in this Maya window; reports contain only evidence.\r\n\r\n" +
            "This first positive compatibility slice does not qualify the pending model bypass/negative matrix. " +
            "Required audit faults have local fixtures only. Audit failure blocks further effects; possible sends " +
            "or display are reported uncertain, never recalled or retried. The poisoned ledger is not reopened.\r\n\r\n" +
            "Bounds stay 8192-byte frames, 128 KiB per channel direction/audit, 4 KiB request/response/stderr, " +
            "1 KiB final output and 64 KiB report. Child 22-second cooperative/30-second host budget; worker " +
            "readiness 5 seconds, RPC/display up to 2 seconds, incomplete frames 1 second. Output cap 32 tokens. " +
            "Payload ceilings stay 8192 files/4 MiB index, 32 MiB per file/256 MiB expanded.\r\n\r\n" +
            "No new OS account/service, network permit, registry/loopback grant, system Python/PATH, antivirus, " +
            "boot/encryption or test supervisor. Both jobs must stop before cleanup; automatic bridge recovery " +
            "is disabled. Files/reports remain for review. Independent cleanup is required. Stop after one result; " +
            "no automatic retry. Gate A, full containment and production remain unqualified.";
#elif HERMES_BRIDGE
        internal const string Version = "0.2.0-bridge-document.2";
        internal const string Scope = "offline-authorized-document-bridge-v1";
        internal const string Consent =
            "Maya authorization bridge " + Version + "\r\n\r\n" +
            "Unsigned development component, not production-qualified. Copies verified bundled Python 3.13.14, " +
            "pinned Hermes, the same dependency set and canonical Maya code into a fresh private ProgramData attempt.\r\n\r\n" +
            "Maya creates its ordinary zero-capability AppContainer, read/execute runtime and low-integrity " +
            "private state, reduced token, one-process job, child-process block and six deny-all network filters. " +
            "All Application Packages access remains a limitation, not full customer-data isolation.\r\n\r\n" +
            "NEW: Maya starts one additional trusted medium-integrity Python gateway worker outside AppContainer, " +
            "with a separate one-process kill-on-close job. This worker is trusted product code; the child's " +
            "network filters do not sandbox it. It has no model/network operation. Private inherited pipes " +
            "carry framed requests, not HTTP or listening sockets. No child can choose actor, path or policy.\r\n\r\n" +
            "NEW: a protected host folder contains an unpredictable synthetic document, exact local policy, " +
            "worker configuration and required audit. Only SYSTEM, Administrators and this operator have access; " +
            "there is no child package grant. These files and private reports remain after cleanup. No customer " +
            "file, provider credential, model call, business write, connector or Metabase is used.\r\n\r\n" +
            "Ten fixed native cases test one authorized document release and denied policy, direct file access, " +
            "wrong identity/target/action, replay, expiry, cancellation and disclosure. Both audit-failure cases " +
            "remain mandatory local tests, not native-qualified. A failed audit is never reopened to continue. " +
            "The real Hermes tool registry is used; there is no conversation/model selection test.\r\n\r\n" +
            "Required audit is flushed and fsynced before read and disclosure. Cancellation cannot recall " +
            "already committed bytes; uncertain outcomes stop without retry. NEW framing bounds: 8192 bytes " +
            "per frame, 128 KiB each channel direction, 1 KiB document, 128 KiB audit, 4 KiB stderr and 64 KiB " +
            "report. Child budgets stay 22 seconds cooperative/30 seconds host. Worker readiness 5 seconds, " +
            "processing 2 seconds and incomplete frames 1 second. Payload caps remain 8192 files/4 MiB index, " +
            "32 MiB per file/256 MiB expanded. No new capability, network permit, loopback or registry grant.\r\n\r\n" +
            "No system Python/PATH, account/service, Windows policy, antivirus, boot/encryption change or test " +
            "supervisor. Maya must confirm both jobs stopped before revoking permissions/profile/filters. " +
            "Forced closure or uncertain cleanup requires review; bridge automatic recovery is not qualified. " +
            "Independent cleanup remains necessary. Stop after one result. No weakened protection or retry; " +
            "Gate A, containment and production remain unqualified.";
#elif HERMES_MEMORY
        internal const string Version = "0.1.4-hermes-memory.1";
        internal const string Scope = "offline-hermes-native-memory-v1";
        internal const string Consent =
            "Maya protected Hermes native memory " + Version + "\r\n\r\n" +
            "Unsigned development component, not production-qualified. Maya copies verified Python 3.13.14, " +
            "the same pinned Hermes and 63 dependencies into a fresh private ProgramData attempt. Limits " +
            "remain 8192 files, 4 MiB inventory, 32 MiB per file and 256 MiB expanded.\r\n\r\n" +
            "With consent Maya creates one ordinary AppContainer, runtime read/execute and low-integrity " +
            "private-state read/write grants, six package-scoped WFP network denies, a reduced same-user token, " +
            "one-process job, child-process block and three inherited pipes. Existing All Application Packages " +
            "access is not complete customer-data isolation.\r\n\r\n" +
            "One real agent enables its native MemoryStore with 2200/1375-character limits and no external " +
            "memory provider. For each of MEMORY.md and USER.md it adds two fixed synthetic entries, replaces " +
            "the first and removes the second: eight native mutations. A fresh store reloads both files in " +
            "the same process; snapshots, exact readbacks, hashes and residue are checked. This is not " +
            "authoritative memory, tool authorization, crash/restart durability or atomic-write qualification.\r\n\r\n" +
            "Private state/memories holds MEMORY.md, USER.md and their .lock files; native .mem_*.tmp files " +
            "are transient, and unexpected backups cause failure. One nonblocking acquire/release probe per " +
            "lock file follows native calls, not a concurrent-writer test. A 64 KiB aggregate acceptance " +
            "ceiling is checked at stages, not enforced as a disk quota. Config/cache/logs/sessions and bounded " +
            "reports remain. Native setup may create an empty memories directory before construction.\r\n\r\n" +
            "No conversation, model request, tool, connector, customer data or real credential is supplied. " +
            "The SDK uses the same public non-secret placeholder, synthetic model and .invalid URL. All network " +
            "including localhost stays denied. SQLite is not exercised. Context files, checkpoints, compression, " +
            "environment probing, tool search and lazy installs stay disabled. No new permissions, registry " +
            "grant, loopback exemption, Windows policy, antivirus, boot/encryption, system Python/PATH or supervisor.\r\n\r\n" +
            "The 22-second cooperative budget, 30-second host deadline and output/report bounds remain. Maya " +
            "stops the job before revoking grants and removing profile/filters; synthetic files/reports remain. " +
            "Administrator consent and child-token verification are required. Shutdown may suppress errors; " +
            "independent cleanup is still necessary. Forced closure may leave cleanup pending. Stop on failure; " +
            "no retry or weakened protections. Containment, Gate A and production remain unqualified.";
#elif HERMES_STATE
        internal const string Version = "0.1.3-hermes-state.1";
        internal const string Scope = "offline-hermes-session-state-v1";
        internal const string Consent =
            "Maya protected Hermes session storage " + Version + "\r\n\r\n" +
            "Unsigned development component, not production-qualified. Maya copies the same verified Python " +
            "3.13.14, pinned Hermes and 63 dependencies into a fresh private ProgramData attempt. Limits " +
            "remain 8192 files, 4 MiB inventory, 32 MiB per file and 256 MiB expanded.\r\n\r\n" +
            "With your consent Maya creates one ordinary AppContainer, runtime read/execute and low-integrity " +
            "private-state read/write grants, and six package-scoped WFP network denies. Reduced same-user " +
            "token, one-process job, child-process block and three inherited pipes remain. Existing All " +
            "Application Packages access is not complete customer-data isolation.\r\n\r\n" +
            "Python creates Hermes' real state.db with its native schema and possible SQLite WAL/SHM/journal " +
            "sidecars. It creates one synthetic session, attaches the DB to one real agent, and stores exactly " +
            "two small fixed fixture messages, not model output. It verifies records, ends the agent session, " +
            "closes the DB, reopens it read-only in the same process, verifies persistence and closes again. " +
            "This is not crash recovery, restart durability, full search or memory-file qualification.\r\n\r\n" +
            "No model request, conversation, tool, connector, MEMORY.md/USER.md or customer-data operation is " +
            "invoked. Memory providers remain disabled. The real SDK/TLS client uses the same public non-secret " +
            "placeholder, synthetic model and .invalid URL. All network access stays denied, including localhost. " +
            "No real credentials, existing home/.env or authoritative business store is supplied.\r\n\r\n" +
            "Private config/cache/logs/sessions and bounded reports remain. SQLite files must stay within a " +
            "32 MiB acceptance ceiling at checked stages; this is not a disk quota. WAL must be observed; " +
            "no forced journal setting or fallback is accepted as success. No new permissions, registry grants, " +
            "loopback exemption, Windows policy, antivirus, boot/encryption, global Python/PATH or supervisor.\r\n\r\n" +
            "The 22-second cooperative budget, 30-second host deadline and output/report bounds remain. " +
            "Maya stops the job before revoking grants and removing profile/filters; files and reports remain. " +
            "Administrator consent is required; child token checks must pass. Shutdown may suppress errors, " +
            "so independent cleanup remains necessary. Forced closure may leave cleanup pending. Stop after " +
            "failure: no retry or weakened protections. No containment, governance or production qualification.";
#elif HERMES_CONSTRUCTION
        internal const string Version = "0.1.2-hermes-construction.2";
        internal const string Scope = "offline-hermes-construction-v1";
        internal const string Consent =
            "Maya protected Hermes construction " + Version + "\r\n\r\n" +
            "Unsigned development component, not production-qualified. With your consent Maya copies " +
            "verified Python 3.13.14, pinned Hermes and the same 63 dependencies into a new private " +
            "ProgramData attempt. Limits remain 8192 files, 4 MiB inventory, 32 MiB per file and 256 MiB expanded.\r\n\r\n" +
            "Maya creates one ordinary AppContainer, runtime read/execute and low-integrity private-state " +
            "read/write grants, and six package-scoped WFP network denies. A reduced same-user token, " +
            "one-process job and child-process block remain. Existing All Application Packages access " +
            "means this is not complete customer-data isolation.\r\n\r\n" +
            "Python imports and constructs one real Hermes agent with tools, memory providers, context " +
            "files, checkpoints and conversations disabled, then calls context shutdown and close. " +
            "The real SDK/TLS client initializes using a fixed public non-secret placeholder key, " +
            "synthetic model and https://maya-construction.invalid/v1. No server or model request is invoked. " +
            "All network access remains denied. No customer data, real credentials or existing home is supplied.\r\n\r\n" +
            "A fixed private config.yaml disables compression and the environment probe and sets context " +
            "size 131072. Hermes may create private sessions/logs/cache state. Supported lazy installs remain " +
            "disabled. No registry, loopback, antivirus, boot, encryption, machine Python/PATH or Windows " +
            "policy changes; no test listeners or external supervisor.\r\n\r\n" +
            "The 22-second cooperative budget, 30-second host deadline and output/report bounds remain. " +
            "Maya stops the job before revoking grants and removing profile/filters. Files and reports remain. " +
            "Administrator consent is required; the child must pass all restricted-token checks. " +
            "Shutdown methods suppress some errors: a returned call is not complete cleanup proof. " +
            "Forced closure can leave cleanup pending. Stop on failure; do not retry or weaken protections. " +
            "Success qualifies neither governed execution nor containment or production; independent cleanup remains required.";
#elif HERMES_IMPORT
        internal const string Version = "0.1.1-hermes-import.1";
        internal const string Scope = "offline-hermes-import-v1";
        internal const string Consent =
            "Maya protected Hermes import " + Version + "\r\n\r\n" +
            "Unsigned development component, not production-qualified. With your consent, Maya " +
            "copies verified Python 3.13.14, pinned Hermes and 63 dependencies into a new private " +
            "ProgramData attempt. This profile permits at most 8192 files and a 4 MiB inventory; " +
            "32 MiB per-file and 256 MiB expanded limits remain. Extraction and cleanup may take longer.\r\n\r\n" +
            "Maya creates one ordinary AppContainer profile, grants read/execute on its runtime " +
            "and read/write on its low-integrity private state, and creates six profile-scoped " +
            "WFP network denies. Ordinary AppContainer has Windows' existing All Application " +
            "Packages access; that is not complete customer-data isolation. A reduced same-user " +
            "token, one-process job and child-process policy restrict one Python process.\r\n\r\n" +
            "Python imports the real run_agent:AIAgent class but never constructs an agent or calls " +
            "a model, tool, skill, connector or authoritative store. Imports can initialize tool " +
            "registries and native dependencies. Existing modules may skip optional imports. " +
            "Hermes lazy installs are disabled through its supported environment option. " +
            "No existing home, .env, credentials or customer files are provided. A fresh private " +
            "home/cache/temp configuration and explicit read-only import/DLL paths are used.\r\n\r\n" +
            "No synthetic listeners, path aliases, shared-memory fixture, public-file grant or " +
            "WFP event collection is needed. No Windows policy, registry grants, loopback exemption, " +
            "antivirus, boot, encryption or machine Python/PATH setting changes. " +
            "All network access remains denied. Python has a 22-second cooperative import budget " +
            "and unchanged 30-second host deadline; output/report bounds remain unchanged.\r\n\r\n" +
            "Maya stops the job before removing grants, profile and filters. Files and reports " +
            "remain for inspection. Process-local critical-error handling is unchanged. " +
            "Administrator consent is required for setup; Python must pass restricted-token checks. " +
            "Closing forcibly may leave cleanup pending. Do not retry or weaken protection after " +
            "failure. Import success does not qualify construction, Hermes execution, governance " +
            "or containment; independent cleanup is still required.";
#else
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
#endif

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

        internal static string Execute(bool recover, Action<string,int> publish = null)
        {
            if (!recover) Native.CheckBaseline();
            ProductFiles.EnsureRoot();
            string ownerLock = Path.Combine(ProductFiles.Root, "lifecycle.lock");
            ProductFiles.NoLinks(ownerLock);
            using (var lifecycle = new FileStream(ownerLock, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None))
                return ExecuteOwned(recover, publish);
        }

        static string ExecuteOwned(bool recover, Action<string,int> publish)
        {
            var user = WindowsIdentity.GetCurrent().User;
            var pending = Pending();
            if (recover && pending.Count != 1) throw new StartupFailure("recovery_requires_one_pending_attempt");
            if (!recover && pending.Count != 0) throw new StartupFailure("cleanup_pending_use_recovery");
            string run = recover ? Path.GetFileName(pending[0]) : Guid.NewGuid().ToString("N");
            string directory = Path.Combine(ProductFiles.Root, run);
#if HERMES_BRIDGE
            if (recover) throw new StartupFailure("bridge_recovery_requires_review");
#endif
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
#if HERMES_MODEL
            record["real_inference"] = false;
            record["model_case"] = "M01";
            record["model_pending_cases"] = new[] {"M02","M03","M04","M05","M06","M07","M08","M09"};
#endif
            SaveRecord(recordPath, record);
            var isolation = new WindowsIsolation(moniker);
            var screen = new ContainmentScreen(directory, run, isolation.Package, user);
            var observations = new Dictionary<string, string>(StringComparer.Ordinal);
            record["security_resource_inventory"] = isolation.ResourceInventory();
            bool cleanup = false;
#if HERMES_MODEL
            ModelBridgeRuntime bridge = null;
#elif HERMES_BRIDGE
            BridgeRuntime bridge = null;
#endif
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
#if HERMES_MODEL
                    HermesImport.Prepare(directory);
                    File.Copy(Path.Combine(directory,"runtime","model-config.json"),Path.Combine(directory,"state","config.yaml"),false);
#elif HERMES_MEMORY
                    HermesMemory.Prepare(directory);
#elif HERMES_CONSTRUCTION
                    HermesConstruction.Prepare(directory);
#elif HERMES_IMPORT
                    HermesImport.Prepare(directory);
#else
                    screen.Prepare();
#endif
                    screen.Stage = "network_provision";
                    isolation.ProvisionNetwork();
                    record["network_filters_verified"] = 6;
#if HERMES_BRIDGE
                    screen.Stage = "bridge_worker_setup";
#if HERMES_MODEL
                    record["real_inference"] = false;
                    bridge = new ModelBridgeRuntime(directory, run, user, record, publish);
#else
                    bridge = new BridgeRuntime(directory, run, user, record);
#endif
                    bridge.PrepareWorker();
#endif
#if !HERMES_IMPORT
                    screen.Stage = "udp_evidence_setup";
                    screen.ConfigureUdp(isolation, record);
#endif
                    screen.Stage = "child_create_suspended";
                    isolation.Start(directory, run, user);
                    screen.BindChild(checked((int)isolation.ChildPid));
#if !HERMES_IMPORT
                    screen.Stage = "plan_write";
                    screen.WritePlan(isolation.StandardHandles);
                    record["screen_fixture_inventory"] = screen.Plan;
                    screen.Stage = "acl_inventory";
                    record["screen_acl_metadata_inventory"] = screen.AclInventory();
#endif
                    record["restricted_token_verified"] = true;
                    record["child_pid"] = isolation.ChildPid;
                    record["status"] = "restricted_child_suspended";
                    screen.Stage = "suspended_record_write";
                    SaveRecord(recordPath, record);
                    screen.Stage = "child_resume_wait";
#if HERMES_BRIDGE
                    uint exit = bridge.Run(isolation);
                    record["child_resumed"] = true;
                    record["child_exit_hex"] = "0x" + exit.ToString("X8");
                    record["fresh_state_beacon"] = ReadFreshBeacon(directory, run);
#if HERMES_MODEL
                    record["python_started"] = exit == 0 && (bool)record["fresh_state_beacon"] &&
                        record.ContainsKey("model_python_entry_observed") && true.Equals(record["model_python_entry_observed"]);
                    record["status"] = "offline_model_child_completed";
#else
                    record["python_started"] = exit == 0 && (bool)record["fresh_state_beacon"] &&
                        record.ContainsKey("bridge_python_entry_observed") && true.Equals(record["bridge_python_entry_observed"]);
                    record["status"] = "bridge_child_completed";
#endif
#else
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
#endif
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
#if HERMES_BRIDGE
                    if (bridge != null) bridge.Stop();
#endif
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
                        try {
#if HERMES_MODEL
                            record["model_evidence_collected"] = true;
#elif HERMES_BRIDGE
                            record["bridge_evidence_collected"] = true;
#elif HERMES_MEMORY
                            screen.Stage = "hermes_memory_report";
                            HermesMemory.Collect(directory, run, record);
#elif HERMES_STATE
                            screen.Stage = "hermes_state_report";
                            HermesState.Collect(directory, run, record);
#elif HERMES_CONSTRUCTION
                            screen.Stage = "hermes_construction_report";
                            HermesConstruction.Collect(directory, run, record);
#elif HERMES_IMPORT
                            screen.Stage = "hermes_import_report";
                            HermesImport.Collect(directory, run, record);
#else
                            observations = screen.Collect(record);
#endif
                        }
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
#if HERMES_BRIDGE
                if (bridge != null) bridge.Dispose();
#endif
                record["cleanup_complete"] = cleanup;
                if (!recover)
                {
#if HERMES_MODEL
                    record["status"] = cleanup && true.Equals(record["python_started"]) &&
                        record.ContainsKey("model_evidence_matches") && true.Equals(record["model_evidence_matches"]) &&
                        record.ContainsKey("model_worker_stopped") && true.Equals(record["model_worker_stopped"])
                        ? "offline_model_wire_completed_pending_independent_cleanup" : "blocked";
                    record["independent_cleanup_verified"] = false;
#elif HERMES_BRIDGE
                    record["status"] = cleanup && true.Equals(record["python_started"]) &&
                        record.ContainsKey("bridge_evidence_matches") && true.Equals(record["bridge_evidence_matches"]) &&
                        record.ContainsKey("bridge_worker_stopped") && true.Equals(record["bridge_worker_stopped"])
                        ? "bridge_document_completed_pending_independent_cleanup" : "blocked";
                    record["independent_cleanup_verified"] = false;
#elif HERMES_MEMORY
                    record["hermes_memory_status"] = HermesMemory.Result(record, cleanup);
                    record["status"] = record["hermes_memory_status"];
                    record["independent_cleanup_verified"] = false;
#elif HERMES_STATE
                    record["hermes_state_status"] = HermesState.Result(record, cleanup);
                    record["status"] = record["hermes_state_status"];
                    record["independent_cleanup_verified"] = false;
#elif HERMES_CONSTRUCTION
                    record["hermes_construction_status"] = HermesConstruction.Result(record, cleanup);
                    record["status"] = record["hermes_construction_status"];
                    record["independent_cleanup_verified"] = false;
#elif HERMES_IMPORT
                    record["hermes_import_status"] = HermesImport.Result(record, cleanup);
                    record["status"] = record["hermes_import_status"];
                    record["independent_cleanup_verified"] = false;
#else
                    if (!isolation.ExitCode.HasValue || isolation.ExitCode.Value != 0 ||
                        !record.ContainsKey("python_started") || !(bool)record["python_started"])
                        observations["execution.incomplete"] = "inconclusive";
                    record["screen_status"] = ContainmentScreen.Finish(observations, cleanup);
                    if ((string)record["screen_status"] == "screen_completed_not_containment_qualified")
                        record["screen_status"] = "observations_completed_pending_independent_cleanup";
                    record["screen_observations"] = observations;
                    record["screen_independent_cleanup_verified"] = false;
                    record["status"] = record["screen_status"];
#endif
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
#if HERMES_MODEL
        readonly TextBox modelOutput = new TextBox { ReadOnly=true, Multiline=true, Dock=DockStyle.Fill, ScrollBars=ScrollBars.Vertical };
#endif
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
#if HERMES_MODEL
            Text = "Maya | Offline model bridge";ClientSize = new Size(700,720);
#endif
            MinimumSize = new Size(650, 620); StartPosition = FormStartPosition.CenterScreen;
            var layout = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 1, RowCount = 5, Padding = new Padding(18) };
#if HERMES_MODEL
            layout.RowCount=6;
#endif
            layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 42));
            layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
            layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 50));
            layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 45));
#if HERMES_MODEL
            layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 60));
#endif
            layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 85));
#if HERMES_MODEL
            layout.Controls.Add(new Label { Text = "Maya offline model bridge", Font = new Font(Font.FontFamily, 18), Dock = DockStyle.Fill }, 0, 0);
#else
            layout.Controls.Add(new Label { Text = "Maya protected Python", Font = new Font(Font.FontFamily, 18), Dock = DockStyle.Fill }, 0, 0);
#endif
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
#if HERMES_MODEL
            layout.Controls.Add(modelOutput,0,4);layout.Controls.Add(status,0,5);
#else
            layout.Controls.Add(status, 0, 4);
#endif
            Controls.Add(layout);
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
#if HERMES_MODEL
                modelOutput.Clear();
                reportPath = await Task.Run(() => ProtectedPython.Execute(cleanup, PublishModelOutput));
#else
                reportPath = await Task.Run(() => ProtectedPython.Execute(cleanup));
#endif
                var record = ProtectedPython.ReadRecord(reportPath);
                string outcome = (string)record["status"];
                string description = !(bool)record["cleanup_complete"] ? "Cleanup needs attention. Stop here; do not run Python again." :
                    cleanup ? "Security cleanup completed. Python was not launched again." :
#if HERMES_MODEL
                    outcome == "offline_model_wire_completed_pending_independent_cleanup" ? "Offline model-wire test completed with a synthetic response. No inference occurred." :
#endif
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
#if HERMES_MODEL
        void PublishModelOutput(string text, int milliseconds)
        {
            if(text==null || System.Text.Encoding.UTF8.GetByteCount(text)>1024)throw new StartupFailure("model_operator_output_size");
            ModelPublication.Run(action=>BeginInvoke(action),delegate {
                modelOutput.Text=text;modelOutput.Update();
                if(modelOutput.Text!=text)throw new StartupFailure("model_operator_readback");
            },milliseconds);
        }
#endif
    }
}
