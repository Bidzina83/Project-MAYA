// Inert host decisions and isolated temporary-file I/O only; never construct WindowsHostEnvironment.
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using Maya.GateA.Host;
using Maya.GateA.Observation;

public static class ObserverHostFixtures
{
    static int checks;
    static readonly DateTime Now = new DateTime(2026,10,17,12,0,0,DateTimeKind.Utc);
    static void Check(string name, bool value) { if (!value) throw new Exception("fixture.failed:" + name); checks++; }
    static SortedDictionary<string,object> Fields(string caseId)
    {
        var fields = new SortedDictionary<string,object>(StringComparer.Ordinal) {
            {"schema","maya.observer_execution.v1"}, {"case_id",caseId}, {"execution_authorized",true},
            {"root",@"C:\MayaGateA"}, {"windows_directory",@"C:\Windows"}, {"operator_sid","S-1-5-21-1-2-3-1001"},
            {"package_sid","S-1-15-2-1-2-3-4-5-6-7"}, {"vm_uuid","11111111-2222-3333-4444-555555555555"},
            {"adapter_guids",new [] {"22222222-3333-4444-5555-666666666666"}}, {"context_session_id",0},
            {"host_sha256",new string('b',64)}, {"library_sha256",HostManifest.LibraryHash},
            {"review_package_sha256",HostManifest.ReviewHash}, {"contract_sha256",HostManifest.ContractHash},
            {"issued_utc","2026-10-17T12:00:00Z"}, {"expires_utc","2026-10-17T12:30:00Z"}
        };
        foreach (string name in HostManifest.RecordNames) fields.Add(name + "_sha256",new string('a',64));
        return fields;
    }
    static byte[] Bytes(SortedDictionary<string,object> fields)
    { return Encoding.ASCII.GetBytes(new JavaScriptSerializer().Serialize(fields)); }
    static HostManifest Manifest(string caseId)
    { byte[] bytes = Bytes(Fields(caseId)); return HostManifest.Parse(bytes,HostFiles.Hash(bytes),caseId); }
    static void Reject(string name, Action<SortedDictionary<string,object>> mutation)
    {
        var fields = Fields("A"); mutation(fields); byte[] bytes = Bytes(fields); bool rejected = false;
        try { HostManifest.Parse(bytes,HostFiles.Hash(bytes),"A"); } catch { rejected = true; }
        Check(name,rejected);
    }
    static void RejectBytes(string name, byte[] bytes, string hash)
    { bool rejected = false; try { HostManifest.Parse(bytes,hash,"A"); } catch { rejected = true; } Check(name,rejected); }
    sealed class EnvironmentFixture : IHostEnvironment
    {
        public DateTime Time = Now;
        public DateTime UtcNow { get { return Time; } }
        public int Verifications, FailAt, ExpireAt;
        public void Verify(HostManifest manifest)
        { Verifications++; if (Verifications == ExpireAt) Time = Now.AddMinutes(30); if (Verifications == FailAt) throw new Exception("fixture-sensitive-value"); }
    }
    sealed class Journal : IAttemptJournal, IAttemptRecord
    {
        public bool Claimed, Completed, Disposed, FailReserve, FailComplete;
        public string Report;
        public IAttemptRecord Reserve(HostManifest manifest)
        { if (Claimed || FailReserve) throw new IOException("fixture-sensitive-value"); Claimed = true; return this; }
        public void Complete(string report) { if (FailComplete || Completed) throw new IOException(); Completed = true; Report = report; }
        public void Dispose() { Disposed = true; }
    }
    static SupervisionResult Observed(string caseId)
    {
        return new SupervisionResult { Reason = "observer.python_entry_observed",SelectedTokenObserved = true,
            OrdinaryControlObserved = caseId == "A",AdmissionSent = caseId == "A",ChildExitObserved = true,
            ChildExitCode = 0,CommandMatched = true,BeaconMatched = true,TreeTerminated = true,CaseEvidenceComplete = true };
    }
    static void RunPolicy()
    {
        foreach (string id in new [] {"A","B","C","D"})
        {
            var manifest = Manifest(id); var env = new EnvironmentFixture(); var journal = new Journal();
            int effects = 0; Func<bool> held = null;
            HostResult result = HostController.Run(manifest,env,journal,challenge => challenge == manifest.Confirmation,
                delegate(LaunchPlan plan,Func<bool> permission) {
                    Check("reserve_before_dispatch_" + id,journal.Claimed && !journal.Completed && plan.Case == id);
                    held = permission; if (permission()) effects++; Check("single_permission_" + id,!permission()); return Observed(id);
                });
            Check("entry_" + id,result.ExitCode == 0 && effects == 1 && env.Verifications == 3);
            Check("persist_before_result_" + id,journal.Completed && journal.Disposed && journal.Report == result.Json);
            Check("callback_revoked_" + id,!held());
            Check("no_product_or_network_" + id,result.Json.Contains("\"production_qualified\":false") && result.Json.Contains("\"networking_may_resume\":false"));
            int repeatEffects = 0;
            HostResult repeat = HostController.Run(manifest,env,journal,x => true,(p,a) => { repeatEffects++; return Observed(id); });
            Check("restart_refused_" + id,repeat.ExitCode == 3 && repeatEffects == 0);
        }
        for (int stage = 1; stage <= 3; stage++)
        {
            var env = new EnvironmentFixture { FailAt = stage }; var journal = new Journal(); int effects = 0;
            var result = HostController.Run(Manifest("A"),env,journal,x => true,(p,a) => { if (a()) effects++; return Observed("A"); });
            Check("verify_denial_" + stage,result.ExitCode == 3 && effects == 0 && !result.Json.Contains("fixture-sensitive-value"));
            Check("consume_only_after_preflight_" + stage,journal.Claimed == (stage == 3));
        }
        for (int stage = 1; stage <= 3; stage++)
        {
            var env = new EnvironmentFixture { ExpireAt = stage }; var journal = new Journal(); int effects = 0;
            var result = HostController.Run(Manifest("A"),env,journal,x => true,(p,a) => { if (a()) effects++; return Observed("A"); });
            Check("expiry_during_verification_" + stage,result.ExitCode == 3 && effects == 0);
        }
        var swallowed = HostController.Run(Manifest("A"),new EnvironmentFixture { FailAt = 3 },new Journal(),x => true,
            (p,a) => { try { a(); } catch { } return Observed("A"); });
        Check("failed_callback_cannot_be_swallowed_as_permission",swallowed.ExitCode == 3);
        foreach (string fault in new [] {"decline","expired","reserve","dispatch","unrecorded","no_callback","cleanup","missing_control","unknown_reason"})
        {
            var env = new EnvironmentFixture(); var journal = new Journal { FailReserve = fault == "reserve",FailComplete = fault == "unrecorded" };
            int effects = 0; Func<bool> held = null;
            HostResult result = HostController.Run(Manifest("A"),env,journal,delegate(string challenge) {
                if (fault == "expired") env.Time = Now.AddMinutes(30); return fault != "decline";
            },delegate(LaunchPlan plan,Func<bool> permission) {
                held = permission;
                if (fault == "dispatch") throw new Exception("fixture-sensitive-value");
                if (fault != "no_callback" && permission()) effects++;
                var observed = Observed("A");
                if (fault == "cleanup") observed.TreeTerminated = false;
                if (fault == "missing_control") observed.OrdinaryControlObserved = false;
                if (fault == "unknown_reason") observed.Reason = "fixture-sensitive-value";
                return observed;
            });
            Check("fault_blocks_" + fault,result.ExitCode == 3 && !result.Json.Contains("fixture-sensitive-value"));
            if (fault == "decline" || fault == "expired" || fault == "reserve") Check("zero_dispatch_" + fault,effects == 0 && held == null);
            if (held != null) Check("revoked_on_failure_" + fault,!held());
        }
        var failure = Observed("B"); failure.Reason = "observer.startup_not_established"; failure.ChildExitCode = 3221225506; failure.BeaconMatched = false;
        var failed = HostController.Run(Manifest("B"),new EnvironmentFixture(),new Journal(),x => true,(p,a) => { a(); return failure; });
        Check("observed_startup_failure_not_success",failed.ExitCode == 2 && failed.Json.Contains("startup_not_established"));
    }
    static void RunFiles(string temporary)
    {
        string directory = Path.Combine(temporary,"attempts"); Directory.CreateDirectory(directory);
        var journal = new FileAttemptJournal(directory); var manifest = Manifest("A");
        using (IAttemptRecord reservation = journal.Reserve(manifest))
        {
            Check("claim_exists",File.Exists(Path.Combine(directory,"attempt.claim")));
            bool blocked = false; try { new FileAttemptJournal(directory).Reserve(manifest); } catch { blocked = true; }
            Check("second_host_blocked",blocked);
            reservation.Complete("{\"status\":\"fixture_only\"}");
        }
        Check("record_bytes",Encoding.ASCII.GetString(HostFiles.Read(Path.Combine(directory,"attempt.claim"))).Contains(manifest.Hash));
        Check("outcome_bytes",Encoding.ASCII.GetString(HostFiles.Read(Path.Combine(directory,"outcome.json"))) == "{\"status\":\"fixture_only\"}");
        bool restarted = false; try { new FileAttemptJournal(directory).Reserve(Manifest("B")); } catch { restarted = true; }
        Check("other_case_cannot_reuse_baseline",restarted);
        foreach (string stale in new [] { "attempt.claim","outcome.json","unknown-file" })
        {
            string path = Path.Combine(temporary,stale.Replace('.','-')); Directory.CreateDirectory(path);
            File.WriteAllBytes(Path.Combine(path,stale),new byte[0]);
            bool blocked = false; try { new FileAttemptJournal(path).Reserve(manifest); } catch { blocked = true; }
            Check("stale_or_partial_denies_" + stale,blocked);
        }
        string interrupted = Path.Combine(temporary,"interrupted"); Directory.CreateDirectory(interrupted);
        new FileAttemptJournal(interrupted).Reserve(manifest).Dispose();
        bool denied = false; try { new FileAttemptJournal(interrupted).Reserve(manifest); } catch { denied = true; }
        Check("no_terminal_record_no_resume",denied && !File.Exists(Path.Combine(interrupted,"outcome.json")));
        string contention = Path.Combine(temporary,"contention"); Directory.CreateDirectory(contention);
        int winners = 0; int losers = 0;
        using (var start = new ManualResetEventSlim(false))
        {
            Action compete = delegate {
                start.Wait();
                try { using (new FileAttemptJournal(contention).Reserve(manifest)) Interlocked.Increment(ref winners); }
                catch { Interlocked.Increment(ref losers); }
            };
            Task first = Task.Factory.StartNew(compete), second = Task.Factory.StartNew(compete);
            start.Set(); Task.WaitAll(first,second);
        }
        Check("one_file_reservation_wins_contention",winners == 1 && losers == 1);
    }
    public static int Main(string[] args)
    {
        try
        {
            if (args.Length != 1 || !Directory.Exists(args[0])) throw new Exception();
            foreach (string id in new [] {"A","B","C","D"}) Check("case_" + id,Manifest(id).Case == id);
            Reject("disabled",x => x["execution_authorized"] = false);
            Reject("string_consent",x => x["execution_authorized"] = "true");
            Reject("unknown_key",x => x.Add("fallback",true));
            Reject("case_mismatch",x => x["case_id"] = "B");
            Reject("wrong_root",x => x["root"] = @"C:\Other");
            Reject("system_actor",x => x["operator_sid"] = "S-1-5-18");
            Reject("bad_package",x => x["package_sid"] = "S-1-1-0");
            Reject("zero_vm",x => x["vm_uuid"] = Guid.Empty.ToString("D"));
            Reject("no_adapters",x => x["adapter_guids"] = new string[0]);
            Reject("duplicate_adapters",x => x["adapter_guids"] = new [] {"22222222-3333-4444-5555-666666666666","22222222-3333-4444-5555-666666666666"});
            Reject("string_session",x => x["context_session_id"] = "0");
            Reject("unpinned_library",x => x["library_sha256"] = new string('c',64));
            Reject("unpinned_review",x => x["review_package_sha256"] = new string('c',64));
            Reject("unpinned_contract",x => x["contract_sha256"] = new string('c',64));
            Reject("missing_security",x => x.Remove("security_sha256"));
            Reject("bad_record_hash",x => x["security_sha256"] = "fixture-sensitive-value");
            Reject("overlong_permission",x => x["expires_utc"] = "2026-10-17T12:30:01Z");
            byte[] bytes = Bytes(Fields("A"));
            RejectBytes("hash_drift",bytes,new string('d',64));
            byte[] duplicate = Encoding.ASCII.GetBytes(Encoding.ASCII.GetString(bytes).Replace("{","{\"execution_authorized\":true,"));
            RejectBytes("duplicate_key",duplicate,HostFiles.Hash(duplicate));
            byte[] whitespace = Encoding.ASCII.GetBytes(" " + Encoding.ASCII.GetString(bytes));
            RejectBytes("noncanonical",whitespace,HostFiles.Hash(whitespace));
            byte[] suffix = Encoding.ASCII.GetBytes(Encoding.ASCII.GetString(bytes) + "\n");
            RejectBytes("suffix",suffix,HostFiles.Hash(suffix));
            foreach (DateTime time in new [] {Now.AddSeconds(-1),Now.AddMinutes(30),Now.ToLocalTime()})
            { bool denied = false; try { Manifest("A").ValidateTime(time); } catch { denied = true; } Check("time_guard",denied); }
            var manifest = Manifest("A"); var adapters = manifest.Adapters; adapters[0] = "changed";
            Check("immutable_adapters",manifest.Adapters[0] != "changed");
            var recordNames = HostManifest.RecordNames; recordNames[0] = "changed";
            Check("immutable_record_names",HostManifest.RecordNames[0] != "changed");
            RunPolicy(); RunFiles(args[0]);
            Console.WriteLine("{\"status\":\"fixture_passed\",\"cases\":" + checks + ",\"native_dispatch\":false,\"vm_checks_executed\":false,\"production_qualified\":false}"); return 0;
        }
        catch { Console.WriteLine("{\"status\":\"fixture_failed\",\"native_dispatch\":false,\"production_qualified\":false}"); return 1; }
    }
}
