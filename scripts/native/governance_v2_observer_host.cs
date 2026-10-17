// Diagnostic host policy and local attempt journal; no native dispatch in this file.
using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Web.Script.Serialization;
using Maya.GateA.Observation;

namespace Maya.GateA.Host
{
    public sealed class HostManifest
    {
        public const string LibraryHash = "1a07c156ddd55b5e18066d747344721b71100083c1e9a29ad0011d6344aafcdc";
        public const string ReviewHash = "eeb0e435457b6219db6582706530dd6f8c07e0d95a76c90f222a5e1fb0a0e75b";
        public const string ContractHash = "07b04c4577277780a2352e970185f949e7f3cdf755bc3f1c5a6312cd29f29a27";
        static readonly string[] recordNames = { "authorization", "baseline", "console", "external_attempt", "inventory", "parent_context", "security" };
        public static string[] RecordNames { get { return (string[])recordNames.Clone(); } }
        readonly Dictionary<string,object> values;
        public readonly string Hash;
        public string Case { get { return Text("case_id"); } }
        public string User { get { return Text("operator_sid"); } }
        public string Package { get { return Text("package_sid"); } }
        public string Vm { get { return Text("vm_uuid"); } }
        public string ExecutableHash { get { return Text("host_sha256"); } }
        public int Session { get { return (int)values["context_session_id"]; } }
        public string[] Adapters
        {
            get { var result = new List<string>(); foreach (object value in (IEnumerable)values["adapter_guids"]) result.Add((string)value); return result.ToArray(); }
        }
        string Text(string key) { return (string)values[key]; }
        public string RecordHash(string name)
        {
            if (Array.IndexOf(RecordNames,name) < 0) throw new InvalidOperationException();
            return Text(name + "_sha256");
        }
        HostManifest(Dictionary<string,object> input, string hash) { values = input; Hash = hash; }
        static void Require(bool value) { if (!value) throw new InvalidOperationException(); }
        public static bool IsHash(string value) { return value != null && Regex.IsMatch(value,"\\A[0-9a-f]{64}\\z"); }
        public static string CanonicalGuid(string value)
        { Guid parsed; Require(Guid.TryParseExact(value,"D",out parsed) && parsed != Guid.Empty && parsed.ToString("D") == value); return value; }
        public static HostManifest Parse(byte[] bytes, string expectedHash, string requestedCase)
        {
            Require(bytes != null && bytes.Length > 0 && bytes.Length <= 32768 && IsHash(expectedHash));
            Require(HostFiles.Hash(bytes) == expectedHash);
            foreach (byte value in bytes) Require(value >= 32 && value <= 126);
            var json = new JavaScriptSerializer { MaxJsonLength = 32768, RecursionLimit = 8 };
            var fields = json.Deserialize<Dictionary<string,object>>(Encoding.ASCII.GetString(bytes));
            var wanted = new HashSet<string>(new [] { "schema", "case_id", "execution_authorized", "root", "windows_directory",
                "operator_sid", "package_sid", "vm_uuid", "adapter_guids", "context_session_id", "host_sha256", "library_sha256",
                "review_package_sha256", "contract_sha256", "issued_utc", "expires_utc" },StringComparer.Ordinal);
            foreach (string name in RecordNames) wanted.Add(name + "_sha256");
            Require(fields != null && wanted.SetEquals(fields.Keys));
            // Exact canonical bytes reject duplicate keys, ambiguous types, BOMs and hidden suffixes.
            var sorted = new SortedDictionary<string,object>(fields,StringComparer.Ordinal);
            Require(json.Serialize(sorted) == Encoding.ASCII.GetString(bytes));
            foreach (var field in fields)
                if (field.Key != "execution_authorized" && field.Key != "adapter_guids" && field.Key != "context_session_id")
                    Require(field.Value is string && ((string)field.Value).Length <= 256);
            Require(fields["execution_authorized"] is bool && (bool)fields["execution_authorized"]);
            Require((string)fields["schema"] == "maya.observer_execution.v1");
            Require(requestedCase != null && Regex.IsMatch(requestedCase,"\\A[A-D]\\z") && (string)fields["case_id"] == requestedCase);
            Require((string)fields["root"] == @"C:\MayaGateA" && (string)fields["windows_directory"] == @"C:\Windows");
            Require(Regex.IsMatch((string)fields["operator_sid"],"\\AS-1-5-21-(?:[0-9]+-){2}[0-9]+-[0-9]+\\z"));
            Require(Regex.IsMatch((string)fields["package_sid"],"\\AS-1-15-2-(?:[0-9]+-){6}[0-9]+\\z"));
            CanonicalGuid((string)fields["vm_uuid"]);
            Require(fields["context_session_id"] is int && (int)fields["context_session_id"] >= 0 && (int)fields["context_session_id"] <= 65535);
            foreach (string key in wanted) if (key.EndsWith("_sha256",StringComparison.Ordinal)) Require(IsHash((string)fields[key]));
            Require((string)fields["library_sha256"] == LibraryHash && (string)fields["review_package_sha256"] == ReviewHash &&
                (string)fields["contract_sha256"] == ContractHash);
            Require(fields["adapter_guids"] is object[] || fields["adapter_guids"] is ArrayList);
            var adapters = new List<string>();
            foreach (object item in (IEnumerable)fields["adapter_guids"])
            { Require(item is string); adapters.Add(CanonicalGuid((string)item)); }
            Require(adapters.Count > 0 && adapters.Count <= 64 && new HashSet<string>(adapters).Count == adapters.Count);
            var ordered = new List<string>(adapters); ordered.Sort(StringComparer.Ordinal);
            Require(String.Join(",",adapters) == String.Join(",",ordered));
            var result = new HostManifest(fields,expectedHash);
            DateTime issued = result.Time("issued_utc"), expires = result.Time("expires_utc");
            Require(expires > issued && expires - issued <= TimeSpan.FromMinutes(30));
            return result;
        }
        DateTime Time(string name)
        { return DateTime.ParseExact(Text(name),"yyyy-MM-dd'T'HH:mm:ss'Z'",CultureInfo.InvariantCulture,DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal); }
        public void ValidateTime(DateTime now)
        { Require(now.Kind == DateTimeKind.Utc && now >= Time("issued_utc") && now < Time("expires_utc")); }
        public LaunchPlan Plan() { return new LaunchPlan(Case,@"C:\MayaGateA",User,Package,@"C:\Windows"); }
        public string Confirmation { get { return "AUTHORIZE CASE " + Case + " " + Hash; } }
    }

    public static class HostFiles
    {
        public static void Plain(string path)
        {
            for (string part = Path.GetFullPath(path); !String.IsNullOrEmpty(part); part = Path.GetDirectoryName(part))
                if ((File.GetAttributes(part) & FileAttributes.ReparsePoint) != 0) throw new IOException();
        }
        public static string Hash(byte[] bytes)
        { using (var sha = SHA256.Create()) return BitConverter.ToString(sha.ComputeHash(bytes)).Replace("-","").ToLowerInvariant(); }
        public static string HashFile(string path)
        { Plain(path); using (var file = File.OpenRead(path)) using (var sha = SHA256.Create()) return BitConverter.ToString(sha.ComputeHash(file)).Replace("-","").ToLowerInvariant(); }
        public static byte[] Read(string path)
        {
            Plain(path);
            using (var stream = File.OpenRead(path))
            {
                if (stream.Length <= 0 || stream.Length > 32768) throw new IOException();
                var bytes = new byte[(int)stream.Length]; int count = 0;
                while (count < bytes.Length) { int got = stream.Read(bytes,count,bytes.Length-count); if (got <= 0) throw new IOException(); count += got; }
                if (stream.ReadByte() != -1) throw new IOException(); return bytes;
            }
        }
        internal static void WriteAndVerify(FileStream stream, byte[] bytes)
        {
            stream.Write(bytes,0,bytes.Length); stream.Flush(true);
            if (stream.Length != bytes.Length) throw new IOException();
            stream.Position = 0;
            foreach (byte value in bytes) if (stream.ReadByte() != value) throw new IOException();
            if (stream.ReadByte() != -1) throw new IOException();
        }
    }

    public interface IHostEnvironment { DateTime UtcNow { get; } void Verify(HostManifest manifest); }
    public interface IAttemptRecord : IDisposable { void Complete(string sanitizedReport); }
    public interface IAttemptJournal { IAttemptRecord Reserve(HostManifest manifest); }

    public sealed class FileAttemptJournal : IAttemptJournal
    {
        readonly string directory;
        public FileAttemptJournal(string path) { directory = path; }
        public IAttemptRecord Reserve(HostManifest manifest)
        {
            HostFiles.Plain(directory);
            if (Directory.GetFileSystemEntries(directory).Length != 0) throw new IOException();
            // One reservation for this baseline disk, not a per-process or per-case reset switch.
            var stream = new FileStream(Path.Combine(directory,"attempt.claim"),FileMode.CreateNew,FileAccess.ReadWrite,FileShare.None,4096,FileOptions.WriteThrough);
            try
            {
                HostFiles.WriteAndVerify(stream,Encoding.ASCII.GetBytes("maya.observer_attempt.v1\n" + manifest.Case + "\n" + manifest.Hash + "\n"));
                return new Record(directory,stream);
            }
            catch { stream.Dispose(); throw; }
        }
        sealed class Record : IAttemptRecord
        {
            readonly string directory; readonly FileStream claim; bool finished;
            public Record(string path, FileStream stream) { directory = path; claim = stream; }
            public void Complete(string report)
            {
                if (finished) throw new IOException(); finished = true; HostFiles.Plain(directory);
                using (var output = new FileStream(Path.Combine(directory,"outcome.json"),FileMode.CreateNew,FileAccess.ReadWrite,FileShare.None,4096,FileOptions.WriteThrough))
                    HostFiles.WriteAndVerify(output,Encoding.ASCII.GetBytes(report));
            }
            public void Dispose() { claim.Dispose(); }
        }
    }

    public sealed class HostResult
    {
        public readonly string Json; public readonly int ExitCode;
        HostResult(Dictionary<string,object> fields, int code)
        { Json = new JavaScriptSerializer().Serialize(fields); ExitCode = code; }
        public static HostResult Blocked(string code)
        {
            if (code != "host.result_unrecorded" && code != "host.attempt_incomplete") code = "host.preflight_blocked";
            return new HostResult(new Dictionary<string,object> { {"schema","maya.observer_host_result.v1"}, {"status","blocked"},
                {"reason",code}, {"production_qualified",false}, {"security_cleanup_verified",false}, {"networking_may_resume",false} },3);
        }
        public static HostResult From(HostManifest manifest, SupervisionResult observed)
        {
            if (observed == null) return Blocked("host.attempt_incomplete");
            bool complete = observed.CaseEvidenceComplete && observed.TreeTerminated && observed.SelectedTokenObserved &&
                observed.CommandMatched && observed.ChildExitObserved && observed.ChildExitCode.HasValue &&
                (manifest.Case != "A" || (observed.OrdinaryControlObserved && observed.AdmissionSent));
            bool entry = complete && observed.ChildExitCode == 0 && observed.BeaconMatched && observed.Reason == "observer.python_entry_observed";
            complete &= entry || observed.Reason == "observer.startup_not_established";
            string reason = !observed.TreeTerminated ? "observer.cleanup_uncertain" : entry ? "observer.python_entry_observed" :
                complete ? "observer.startup_not_established" : "observer.case_invalid";
            return new HostResult(new Dictionary<string,object> { {"schema","maya.observer_host_result.v1"}, {"case_id",manifest.Case},
                {"status",entry ? "python_entry_observed" : complete ? "startup_not_established" : "blocked"}, {"reason",reason},
                {"case_evidence_complete",complete}, {"selected_token_observed",observed.SelectedTokenObserved},
                {"ordinary_control_observed",observed.OrdinaryControlObserved}, {"admission_sent",observed.AdmissionSent},
                {"command_matched",observed.CommandMatched}, {"beacon_matched",observed.BeaconMatched},
                {"child_exit_code",observed.ChildExitObserved ? observed.ChildExitCode : null}, {"tree_terminated",observed.TreeTerminated},
                {"production_qualified",false}, {"security_cleanup_verified",false}, {"networking_may_resume",false} },entry ? 0 : complete ? 2 : 3);
        }
    }

    public static class HostController
    {
        public static HostResult Run(HostManifest manifest, IHostEnvironment environment, IAttemptJournal journal,
            Func<string,bool> confirm, Func<LaunchPlan,Func<bool>,SupervisionResult> dispatch)
        {
            IAttemptRecord record = null; bool active = false, callbackUsed = false, permissionGranted = false;
            try
            {
                manifest.ValidateTime(environment.UtcNow); environment.Verify(manifest); manifest.ValidateTime(environment.UtcNow);
                if (!confirm(manifest.Confirmation)) return HostResult.Blocked("host.preflight_blocked");
                manifest.ValidateTime(environment.UtcNow); environment.Verify(manifest); manifest.ValidateTime(environment.UtcNow);
                record = journal.Reserve(manifest); active = true;
                Func<bool> permission = delegate {
                    if (!active || callbackUsed) return false; callbackUsed = true;
                    manifest.ValidateTime(environment.UtcNow); environment.Verify(manifest); manifest.ValidateTime(environment.UtcNow);
                    permissionGranted = true; return true;
                };
                SupervisionResult observed;
                try { observed = dispatch(manifest.Plan(),permission); }
                finally { active = false; }
                HostResult result = permissionGranted ? HostResult.From(manifest,observed) : HostResult.Blocked("host.attempt_incomplete");
                try { record.Complete(result.Json); } catch { return HostResult.Blocked("host.result_unrecorded"); }
                record.Dispose(); record = null; return result;
            }
            catch
            {
                var failed = HostResult.Blocked(record == null ? "host.preflight_blocked" : "host.attempt_incomplete");
                if (record != null) try { record.Complete(failed.Json); } catch { return HostResult.Blocked("host.result_unrecorded"); }
                return failed;
            }
            finally { active = false; if (record != null) record.Dispose(); }
        }
    }
}
