// Inert readers only. This executable never calls NativeProcessReader or ObserverJob.
using System;
using System.Collections.Generic;
using Maya.GateA.Observation;

public static class ObserverFixtures
{
    sealed class Reader : IProcessEvidenceReader
    {
        public ProcessIdentity Process = IdentityValue();
        public TokenEvidence Value = TokenValue();
        public bool IsExited, ExitAfterToken, ChangeIdentity;
        public uint Code;
        public Exception Failure;
        public int Reads;
        public ProcessIdentity Identity()
        {
            Reads++;
            if (ChangeIdentity && Reads > 1)
                return new ProcessIdentity { Pid = 17, Created = 1001, Image = "fixture-python" };
            return Process;
        }
        public TokenEvidence Token()
        {
            if (Failure != null) throw Failure;
            if (ExitAfterToken) IsExited = true;
            return Value;
        }
        public bool Exited() { return IsExited; }
        public uint ExitCode() { return Code; }
    }

    static int count;
    static ProcessIdentity IdentityValue()
    { return new ProcessIdentity { Pid = 17, Created = 1000, Image = "fixture-python" }; }
    static TokenEvidence TokenValue()
    {
        return new TokenEvidence { User = "fixture-user", Package = "fixture-package",
            Integrity = "S-1-16-4096", AppContainer = true, PackageAllowed = true,
            Capabilities = new [] { "fixture-network" }, CapabilityAttributes = new uint[] { 4 } };
    }
    static ExpectedProcess Expected()
    {
        return new ExpectedProcess { Identity = IdentityValue(), User = "fixture-user",
            Package = "fixture-package", Capabilities = new [] { "fixture-network" } };
    }
    static void Check(string name, bool value)
    {
        if (!value) throw new Exception("fixture.failed:" + name);
        count++;
    }
    static void Reject(string name, Action<Reader, ExpectedProcess> change)
    {
        var reader = new Reader(); var expected = Expected(); change(reader, expected);
        EvidenceResult result = ObservationPolicy.Capture(reader, expected);
        Check(name, !result.ProfileMatched && !result.ProductionQualified && !result.ContainmentQualified);
    }
    public static int Main()
    {
        try
        {
            Check("x64_layout", ObservationLayout.ValidX64());
            var good = ObservationPolicy.Capture(new Reader(), Expected());
            Check("live_token", good.TokenObserved && good.ProfileMatched && !good.ExitObserved);
            Check("not_qualification", !good.ProductionQualified && !good.ContainmentQualified);
            var exited = new Reader { IsExited = true, Code = 0 };
            var early = ObservationPolicy.Capture(exited, Expected());
            Check("early_zero_not_success", !early.ProfileMatched && !early.TokenObserved && early.ExitObserved && early.ChildExitCode == 0);
            Check("early_reason", early.Reason == "observer.exited_before_token");
            var race = ObservationPolicy.Capture(new Reader { ExitAfterToken = true, Code = 3221225506 }, Expected());
            Check("exit_during_read", race.ProfileMatched && race.ExitObserved && race.ChildExitCode == 3221225506);
            var code259 = ObservationPolicy.Capture(new Reader { ExitAfterToken = true, Code = 259 }, Expected());
            Check("real_exit_259", code259.ExitObserved && code259.ChildExitCode == 259);
            Reject("pid", (r,e) => r.Process.Pid++);
            Reject("pid_zero", (r,e) => { r.Process.Pid = 0; e.Identity.Pid = 0; });
            Reject("creation", (r,e) => r.Process.Created++);
            Reject("creation_zero", (r,e) => { r.Process.Created = 0; e.Identity.Created = 0; });
            Reject("image", (r,e) => r.Process.Image = "other-fixture");
            Reject("image_empty", (r,e) => r.Process.Image = "");
            Reject("identity_race", (r,e) => r.ChangeIdentity = true);
            Reject("user", (r,e) => r.Value.User = "other-user");
            Reject("package", (r,e) => r.Value.Package = "other-package");
            Reject("integrity", (r,e) => r.Value.Integrity = "S-1-16-8192");
            Reject("ordinary_process", (r,e) => r.Value.AppContainer = false);
            Reject("ordinary_appcontainer", (r,e) => r.Value.AapAllowed = true);
            Reject("package_grant_denied", (r,e) => r.Value.PackageAllowed = false);
            Reject("wrong_grant_allowed", (r,e) => r.Value.WrongPackageAllowed = true);
            Reject("no_grant_allowed", (r,e) => r.Value.NoGrantAllowed = true);
            Reject("capability_missing", (r,e) => { r.Value.Capabilities = new string[0]; r.Value.CapabilityAttributes = new uint[0]; });
            Reject("capability_extra", (r,e) => { r.Value.Capabilities = new [] { "fixture-network", "fixture-extra" }; r.Value.CapabilityAttributes = new uint[] { 4,4 }; });
            Reject("capability_disabled", (r,e) => r.Value.CapabilityAttributes[0] = 0);
            Reject("capability_deny_only", (r,e) => r.Value.CapabilityAttributes[0] = 16);
            Reject("capability_null", (r,e) => r.Value.Capabilities = null);
            Reject("attributes_null", (r,e) => r.Value.CapabilityAttributes = null);
            Reject("attributes_count", (r,e) => r.Value.CapabilityAttributes = new uint[0]);
            Reject("expected_capability_null", (r,e) => e.Capabilities = null);
            Reject("expected_user_empty", (r,e) => e.User = "");
            Reject("token_null", (r,e) => r.Value = null);
            Reject("api_failure", (r,e) => r.Failure = new ObservationFault("observer.native_read_failed"));
            Reject("cleanup_failure", (r,e) => r.Failure = new ObservationFault("observer.handle_cleanup_failed"));
            var rawError = new Reader { Failure = new Exception("sk-test-fixture-not-a-real-secret") };
            Check("exception_not_exposed", ObservationPolicy.Capture(rawError, Expected()).Reason == "observer.evidence_failed");
            rawError.Failure = new ObservationFault("sk-test-fixture-not-a-real-secret");
            Check("fault_code_allowlist", ObservationPolicy.Capture(rawError, Expected()).Reason == "observer.evidence_failed");
            Check("null_reader", !ObservationPolicy.Capture(null, Expected()).ProfileMatched);
            Check("null_expectation", !ObservationPolicy.Capture(new Reader(), null).ProfileMatched);
            var pair = TokenValue();
            pair.Capabilities = new [] { "fixture-b", "fixture-a" }; pair.CapabilityAttributes = new uint[] { 4,4 };
            Check("unordered_caps", ObservationPolicy.CapabilitiesMatch(pair, new [] { "fixture-a", "fixture-b" }));
            pair.Capabilities = new [] { "fixture-a", "fixture-a" };
            Check("duplicate_actual", !ObservationPolicy.CapabilitiesMatch(pair, new [] { "fixture-a", "fixture-b" }));
            Check("duplicate_expected", !ObservationPolicy.CapabilitiesMatch(pair, new [] { "fixture-a", "fixture-a" }));
            Check("empty_expected", !ObservationPolicy.CapabilitiesMatch(TokenValue(), new string[0]));
            var later = new Reader();
            var prior = ObservationPolicy.Capture(later, Expected()); later.IsExited = true; later.Code = 7;
            var finished = ObservationPolicy.FinishExit(later, Expected(), prior);
            Check("retained_exit", finished.ProfileMatched && finished.ExitObserved && finished.ChildExitCode == 7);
            Check("no_new_token_read", later.Reads == 3);
            Check("finish_still_live", !ObservationPolicy.FinishExit(new Reader(), Expected(), good).ExitObserved);
            Check("finish_no_prior", !ObservationPolicy.FinishExit(later, Expected(), null).ProfileMatched);
            later.Process.Created++;
            Check("finish_identity_changed", !ObservationPolicy.FinishExit(later, Expected(), prior).ProfileMatched);
            Check("budget_start", ObservationBudget.At(0) == DeadlineAction.Observe);
            Check("budget_before_cleanup", ObservationBudget.At(94999) == DeadlineAction.Observe);
            Check("budget_cleanup", ObservationBudget.At(95000) == DeadlineAction.TerminateTree);
            Check("budget_last", ObservationBudget.At(99999) == DeadlineAction.TerminateTree);
            Check("budget_deadline", ObservationBudget.At(100000) == DeadlineAction.DeadlineExceeded);
            Check("budget_exceeded", ObservationBudget.At(Int64.MaxValue) == DeadlineAction.DeadlineExceeded);
            Check("remaining_reserve", ObservationBudget.Remaining(95000) == 5000);
            Check("remaining_expired", ObservationBudget.Remaining(Int64.MaxValue) == 0);
            bool negative = false;
            try { ObservationBudget.At(-1); } catch (ObservationFault) { negative = true; }
            Check("negative_clock", negative);
            negative = false;
            try { ObservationBudget.Remaining(-1); } catch (ObservationFault) { negative = true; }
            Check("negative_remaining", negative);
            var ordinary = new Reader(); ordinary.Value.AapAllowed = true;
            Check("ordinary_control_allowed",ObservationPolicy.CaptureOrdinaryControl(ordinary,Expected()).ProfileMatched);
            Check("ordinary_not_selected",!ObservationPolicy.Capture(ordinary,Expected()).ProfileMatched);
            Check("selected_not_ordinary",!ObservationPolicy.CaptureOrdinaryControl(new Reader(),Expected()).ProfileMatched);
            count += SupervisionFixtures.Run();
            Console.WriteLine("{\"status\":\"fixture_passed\",\"cases\":" + count +
                ",\"native_calls\":false,\"production_qualified\":false}");
            return 0;
        }
        catch { Console.WriteLine("{\"status\":\"fixture_failed\",\"production_qualified\":false}"); return 1; }
    }
}

public static class SupervisionFixtures
{
    sealed class Backend : ISupervisionBackend
    {
        public readonly LaunchPlan Plan;
        public readonly List<string> Events = new List<string>();
        public readonly List<MemberSample[]> Frames = new List<MemberSample[]>();
        public long Time, CreateDelay, AttachDelay, PollDelay, CleanupDelay;
        public int Index;
        public bool CleanupOk = true, InputsOk = true, AuxiliaryOk = true, EmptyOk = true, ReturnOk = true;
        public bool PrematureBeacon, Beacon = true, ThrowCleanup, ThrowDispose;
        public string ThrowAt = "";
        public uint? TotalOverride, LauncherCodeOverride;
        public ProcessIdentity Launcher = new ProcessIdentity { Pid = 100,Created = 1000 };
        public Backend(string caseId)
        {
            Plan = new LaunchPlan(caseId,@"C:\MayaGateA","fixture-user","fixture-package",@"C:\Windows");
            Launcher.Image = Plan.Launcher;
            Frames.Add(caseId == "A" ? new [] { Member(false,false),Member(true,false) } : new [] { Member(false,false) });
            if (caseId == "A") Frames.Add(new [] { Member(false,false),Member(true,true) });
            Frames.Add(caseId == "A" ? new [] { Member(false,true),Member(true,true) } : new [] { Member(false,true) });
        }
        public MemberSample Member(bool control, bool exited)
        {
            return new MemberSample {
                Identity = new ProcessIdentity { Pid = control ? 102u : 101u,Created = control ? 1002 : 1001,Image = Plan.Python },
                ParentPid = 100,InJob = true,Exited = exited,CommandReadComplete = !control,CommandMatched = !control,
                Token = new TokenEvidence { User = Plan.User,Package = Plan.Package,Integrity = "S-1-16-4096",AppContainer = true,
                    PackageAllowed = true,AapAllowed = control,Capabilities = Plan.CapabilityNames,CapabilityAttributes = Attributes() },
                Evidence = new EvidenceResult { TokenObserved = true,ProfileMatched = true,ExitObserved = exited,ChildExitCode = exited ? (uint?)0 : null }
            };
        }
        uint[] Attributes() { var a = new uint[Plan.CapabilityNames.Length]; for (int i = 0; i < a.Length; i++) a[i] = 4; return a; }
        void Event(string name) { Events.Add(name); if (ThrowAt == name) throw new Exception("PRIVATE_FIXTURE_DIAGNOSTIC"); }
        public long Elapsed { get { return Time; } }
        public ProcessIdentity LauncherIdentity { get { return Launcher; } }
        public string[] ExpectedCapabilities { get { return Plan.CapabilityNames; } }
        public void CreateSuspended(LaunchPlan plan) { Event("create-suspended"); Time += CreateDelay; }
        public void AttachOuterJob() { Event("attach-job"); Time += AttachDelay; }
        public void ResumeLauncher() { Event("resume-launcher"); }
        public MemberSample[] Poll() { Event("poll"); Time += PollDelay; return Frames[Math.Min(Index++,Frames.Count-1)]; }
        public void AdmitMaya() { Event("admit"); }
        public bool LauncherExited { get { return Index >= Frames.Count; } }
        public uint LauncherExitCode { get { return LauncherCodeOverride ?? 0; } }
        public uint TotalProcesses { get { return TotalOverride ?? (Plan.Case == "A" ? 3u : 2u); } }
        public JobPopulation Population
        {
            get {
                uint active = LauncherExited ? 0u : 1u;
                if (Index > 0) foreach (var member in Frames[Math.Min(Index-1,Frames.Count-1)]) if (!member.Exited) active++;
                return new JobPopulation { Total = TotalProcesses,Active = active };
            }
        }
        public bool Empty { get { return LauncherExited && EmptyOk; } }
        public bool FreshBeacon { get { return PrematureBeacon || (Beacon && LauncherExited); } }
        public bool InputsUnchanged { get { Event("verify-inputs"); return InputsOk; } }
        public bool MayaReturnMatches(uint code) { Event("correlate-return"); return ReturnOk; }
        public bool AuxiliaryWorkComplete { get { return AuxiliaryOk; } }
        public bool TerminateAndConfirm() { Event("terminate-confirm"); Time += CleanupDelay; if (ThrowCleanup) throw new Exception(); return CleanupOk; }
        public void Pause() { Event("pause"); Time += 10000; }
        public void Dispose() { Event("dispose"); if (ThrowDispose) throw new Exception(); }
    }
    static int checks;
    static void Check(string name, bool value) { if (!value) throw new Exception("fixture.supervision_failed:"+name); checks++; }
    static void Invalid(string name, Action<Backend> change, string caseId)
    {
        var backend = new Backend(caseId); change(backend);
        var result = Supervision.Run(backend.Plan,backend);
        Check(name,!result.CaseEvidenceComplete && !result.ProductionQualified && !result.NetworkingMayResume);
        Check(name+"_cleanup",backend.Events.Contains("terminate-confirm") && backend.Events.Contains("dispose"));
    }
    public static int Run()
    {
        checks = 0;
        Check("native_launch_layout",NativeSupervisionBackend.ValidLayout());
        byte[] returned = System.Text.Encoding.ASCII.GetBytes("{\"status\":\"native_returned\",\"exit_code\":0,\"production_qualified\":false}\r\n");
        Check("exact_return_frame",ObserverProtocol.MayaReturnMatches(returned,0));
        Check("return_code_mismatch",!ObserverProtocol.MayaReturnMatches(returned,1));
        Check("missing_return",!ObserverProtocol.MayaReturnMatches(null,0));
        Check("partial_return",!ObserverProtocol.MayaReturnMatches(new byte[0],0));
        foreach (string invalidFrame in new [] {
            "{\"status\":\"native_returned\",\"exit_code\":false,\"production_qualified\":false}\r\n",
            "{\"status\":\"native_returned\",\"exit_code\":\"0\",\"production_qualified\":false}\r\n",
            "{\"status\":\"wrong\",\"status\":\"native_returned\",\"exit_code\":0,\"production_qualified\":false}\r\n",
            "PRIVATE_FIXTURE_DIAGNOSTIC\r\n{\"status\":\"native_returned\",\"exit_code\":0,\"production_qualified\":false}\r\n" })
            Check("invalid_return_frame",!ObserverProtocol.MayaReturnMatches(System.Text.Encoding.ASCII.GetBytes(invalidFrame),0));
        foreach (string id in new [] { "A","B","C","D" })
        {
            var backend = new Backend(id); var result = Supervision.Run(backend.Plan,backend);
            Check("case_"+id,result.CaseEvidenceComplete && result.TreeTerminated && result.ChildExitCode == 0 && result.BeaconMatched);
            Check("case_not_production_"+id,!result.ProductionQualified && !result.SecurityCleanupVerified && !result.NetworkingMayResume);
            Check("launch_order_"+id,String.Join(",",backend.Events.GetRange(0,3).ToArray()) == "create-suspended,attach-job,resume-launcher");
            Check("control_case_"+id,result.OrdinaryControlObserved == (id == "A"));
            Check("admission_case_"+id,result.AdmissionSent == (id == "A"));
            Check("cleanup_order_"+id,backend.Events[backend.Events.Count-2] == "terminate-confirm" && backend.Events[backend.Events.Count-1] == "dispose");
            var again = new Backend(id);
            Check("one_attempt_"+id,!Supervision.Run(backend.Plan,again).CaseEvidenceComplete && again.Events.Count == 0);
        }
        var a = new Backend("A"); var b = new Backend("B");
        Check("same_package",a.Plan.Moniker == b.Plan.Moniker);
        Check("maya_cwd",a.Plan.Cwd == a.Plan.Root);
        Check("reference_cwd",b.Plan.Cwd == b.Plan.State);
        Check("reference_flags",b.Plan.Command.EndsWith(" -l -w") && !b.Plan.Command.Contains(" -r") && !b.Plan.Command.Contains(" -k"));
        Check("maya_command",a.Plan.Command.Contains(" launch ") && a.Plan.Command.EndsWith(" 18765"));
        Check("child_flags",b.Plan.ChildCommand.Contains(" -I -S "));
        Check("environment_count",a.Plan.Environment.Count == 8);
        Check("environment_path",a.Plan.Environment["PATH"] == System.IO.Path.GetDirectoryName(a.Plan.Python)+@";C:\Windows\System32");
        var environment = a.Plan.Environment; environment["OPENAI_API_KEY"] = "fixture-not-a-key";
        Check("environment_detached",a.Plan.Environment.Count == 8);
        var caps = a.Plan.CapabilityNames; caps[0] = "other";
        Check("capabilities_detached",a.Plan.CapabilityNames[0] == "privateNetworkClientServer");
        Check("case_c_capabilities",String.Join(";",new Backend("C").Plan.CapabilityNames) == "privateNetworkClientServer;registryRead");
        Check("case_d_capabilities",String.Join(";",new Backend("D").Plan.CapabilityNames) == "privateNetworkClientServer;registryRead;lpacCom");
        Check("quote_empty",LaunchPlan.Quote("") == "\"\"");
        Check("quote_spaces",LaunchPlan.Quote("a b") == "\"a b\"");
        Check("quote_internal",LaunchPlan.Quote("a\"b") == "\"a\\\"b\"");
        Check("quote_trailing_slash",LaunchPlan.Quote("a\\") == "\"a\\\\\"");
        bool bad = false; try { LaunchPlan.Quote("a\nb"); } catch (ObservationFault) { bad = true; }
        Check("quote_control",bad);
        bad = false; try { new LaunchPlan("E",@"C:\MayaGateA","u","p",@"C:\Windows"); } catch (ObservationFault) { bad = true; }
        Check("unknown_case",bad);
        bad = false; try { new LaunchPlan("A",@"C:\other","u","p",@"C:\Windows"); } catch (ObservationFault) { bad = true; }
        Check("other_root",bad);
        foreach (string action in new [] { "create-suspended","attach-job","resume-launcher","poll","admit","verify-inputs","correlate-return" })
            Invalid("fault_"+action,x => x.ThrowAt = action,"A");
        var attach = new Backend("A") { ThrowAt = "attach-job" };
        Supervision.Run(attach.Plan,attach);
        Check("no_resume_on_attach_failure",!attach.Events.Contains("resume-launcher"));
        Invalid("wrong_parent",x => x.Frames[0][0].ParentPid = 999,"B");
        Invalid("not_job_member",x => x.Frames[0][0].InJob = false,"B");
        Invalid("wrong_image",x => x.Frames[0][0].Identity.Image = "fixture-other","B");
        Invalid("predates_launcher",x => x.Frames[0][0].Identity.Created = 999,"B");
        Invalid("missing_token",x => x.Frames[0][0].Token = null,"B");
        Invalid("denied_profile",x => x.Frames[0][0].Evidence.ProfileMatched = false,"B");
        Invalid("wrong_user",x => x.Frames[0][0].Token.User = "other","B");
        Invalid("wrong_package",x => x.Frames[0][0].Token.Package = "other","B");
        Invalid("wrong_capability",x => x.Frames[0][0].Token.Capabilities[0] = "other","B");
        Invalid("missing_command",x => x.Frames[x.Frames.Count-1][0].CommandReadComplete = false,"B");
        Invalid("bad_command",x => x.Frames[0][0].CommandMatched = false,"B");
        Invalid("missing_exit",x => x.Frames[1][0].Evidence.ExitObserved = false,"B");
        Invalid("missing_exit_code",x => x.Frames[1][0].Evidence.ChildExitCode = null,"B");
        Invalid("extra_transient_member",x => x.TotalOverride = 3,"B");
        Invalid("tree_still_active",x => x.EmptyOk = false,"B");
        Invalid("input_drift",x => x.InputsOk = false,"B");
        Invalid("pending_context_worker",x => x.AuxiliaryOk = false,"B");
        Invalid("unseen_control",x => { for (int i = 0; i < x.Frames.Count; i++) x.Frames[i] = new [] { x.Frames[i][0] }; },"A");
        var unseen = new Backend("A");
        for (int i = 0; i < unseen.Frames.Count; i++) unseen.Frames[i] = new [] { unseen.Frames[i][0] };
        var unseenResult = Supervision.Run(unseen.Plan,unseen);
        Check("unseen_control_stops_early",unseenResult.Reason == "observer.unobserved_exit" && !unseen.Events.Contains("admit") && unseen.Time < 95000);
        Invalid("control_bad_exit",x => x.Frames[1][1].Evidence.ChildExitCode = 1,"A");
        Invalid("control_in_reference",x => x.Frames[0][0].Token.AapAllowed = true,"B");
        Invalid("pre_admission_beacon",x => x.PrematureBeacon = true,"A");
        Invalid("bad_maya_return",x => x.ReturnOk = false,"A");
        Invalid("bad_launcher_exit",x => x.LauncherCodeOverride = 1,"B");
        Invalid("pid_reuse",x => x.Frames[1][0].Identity.Created++,"B");
        Invalid("second_selected",x => x.Frames[1][0].Identity.Pid = 103,"B");
        Invalid("late_create",x => x.CreateDelay = 95000,"A");
        Invalid("late_attach",x => x.AttachDelay = 95000,"A");
        Invalid("late_poll",x => x.PollDelay = 95000,"A");
        Invalid("late_cleanup",x => x.CleanupDelay = 100000,"B");
        Invalid("cleanup_denial",x => x.CleanupOk = false,"B");
        Invalid("cleanup_exception",x => x.ThrowCleanup = true,"B");
        Invalid("handle_close_exception",x => x.ThrowDispose = true,"B");
        var missing = new Backend("B"); missing.Frames[0][0].Token = null;
        missing.Frames[0][0].Evidence = new EvidenceResult { ExitObserved = true,ChildExitCode = 3221225506 };
        var missingResult = Supervision.Run(missing.Plan,missing);
        Check("unclassified_exit_retained",missingResult.UnclassifiedChildExitCodes.Count == 1 && missingResult.UnclassifiedChildExitCodes[0] == 3221225506 && !missingResult.ChildExitObserved);
        var failedStartup = new Backend("B") { Beacon = false,LauncherCodeOverride = 3221225506 };
        failedStartup.Frames[1][0].Evidence.ChildExitCode = 3221225506;
        var observedFailure = Supervision.Run(failedStartup.Plan,failedStartup);
        Check("native_failure_not_healthy",observedFailure.CaseEvidenceComplete && observedFailure.Reason == "observer.startup_not_established" && !observedFailure.BeaconMatched);
        Check("no_native_approval_from_fixture",!observedFailure.ProductionQualified && !observedFailure.NetworkingMayResume);
        var deadline = new Backend("A");
        foreach (var frame in deadline.Frames) frame[0].CommandReadComplete = false;
        // Keep the selected child waiting; no admission should be sent while context is missing.
        deadline.Frames.RemoveAt(deadline.Frames.Count-1);
        var waiting = deadline.Frames[deadline.Frames.Count-1];
        for (int i = 0; i < 20; i++) deadline.Frames.Add(waiting);
        var deadlineResult = Supervision.Run(deadline.Plan,deadline);
        Check("deadline_without_admission",!deadlineResult.CaseEvidenceComplete && !deadline.Events.Contains("admit") && deadlineResult.Reason == "observer.deadline");
        return checks;
    }
}
