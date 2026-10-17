// Unarmed diagnostic supervisor. Native execution requires a separately reviewed VM host.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Threading;

namespace Maya.GateA.Observation
{
    public static class ObserverProtocol
    {
        public static bool MayaReturnMatches(byte[] frame, uint childCode)
        {
            byte[] expected = Encoding.ASCII.GetBytes("{\"status\":\"native_returned\",\"exit_code\":" +
                childCode.ToString(CultureInfo.InvariantCulture) + ",\"production_qualified\":false}\r\n");
            if (frame == null || frame.Length != expected.Length) return false;
            for (int i = 0; i < frame.Length; i++) if (frame[i] != expected[i]) return false;
            return true;
        }
    }

    public sealed class LaunchPlan
    {
        public readonly string Case, Root, Stage, State, Python, Worker, Launcher, Command, Cwd;
        public readonly string User, Package, Moniker, ChildCommand;
        readonly string[] capabilityNames;
        readonly Dictionary<string,string> environment;
        public string[] CapabilityNames { get { return (string[])capabilityNames.Clone(); } }
        public Dictionary<string,string> Environment { get { return new Dictionary<string,string>(environment); } }
        internal int consumed;

        public static string Quote(string value)
        {
            if (value == null) throw new ObservationFault("observer.bad_plan");
            foreach (char c in value) if (c < 32 || c == 127) throw new ObservationFault("observer.bad_plan");
            var output = new StringBuilder("\""); int slashes = 0;
            foreach (char c in value)
            {
                if (c == '\\') { slashes++; continue; }
                output.Append('\\', c == '"' ? slashes * 2 + 1 : slashes);
                output.Append(c); slashes = 0;
            }
            return output.Append('\\', slashes * 2).Append('"').ToString();
        }

        public LaunchPlan(string caseId, string root, string user, string package, string windir)
        {
            if (caseId != "A" && caseId != "B" && caseId != "C" && caseId != "D")
                throw new ObservationFault("observer.bad_plan");
            // This fixed proposed guest workspace must be confirmed during VM preparation.
            if (root != @"C:\MayaGateA" || windir != @"C:\Windows" ||
                String.IsNullOrEmpty(user) || String.IsNullOrEmpty(package))
                throw new ObservationFault("observer.bad_plan");
            Quote(user); Quote(package);
            Case = caseId; Root = root; User = user; Package = package;
            Stage = Path.Combine(root, @".codex-build\governance-v2-lpac-stage");
            State = Path.Combine(Stage, "state");
            Python = Path.Combine(Stage, @"runtime\python\python.exe");
            Worker = Path.Combine(Stage, @"runtime\worker.py");
            using (var sha = SHA256.Create())
                Moniker = "Maya.GateA." + BitConverter.ToString(sha.ComputeHash(Encoding.UTF8.GetBytes(Stage + user)))
                    .Replace("-", "").Substring(0, 16);
            ChildCommand = Quote(Python) + " -I -S " + Quote(Worker);
            capabilityNames = caseId == "D" ? new [] { "privateNetworkClientServer", "registryRead", "lpacCom" } :
                caseId == "C" ? new [] { "privateNetworkClientServer", "registryRead" } : new [] { "privateNetworkClientServer" };
            Launcher = Path.Combine(root, caseId == "A" ? @".codex-build\governance-v2-native-tools\GateANative.exe" :
                @".codex-build\governance-v2-reference-tools\LaunchAppContainer.exe");
            Cwd = caseId == "A" ? root : State;
            Command = caseId == "A" ? Quote(Launcher) + " launch " + Quote(Stage) + " 18765" :
                Quote(Launcher) + " -m " + Quote(Moniker) + " -i " + Quote(ChildCommand) +
                " -c " + Quote(String.Join(";", CapabilityNames)) + " -l -w";
            environment = new Dictionary<string,string>(StringComparer.Ordinal) {
                {"HERMES_HOME", State}, {"LOCALAPPDATA", State},
                {"PATH", Path.GetDirectoryName(Python) + ";" + Path.Combine(windir,"System32")},
                {"SYSTEMROOT",windir}, {"TEMP",State}, {"TMP",State}, {"USERPROFILE",State}, {"WINDIR",windir}
            };
        }
        internal void Claim()
        {
            if (Interlocked.Exchange(ref consumed, 1) != 0) throw new ObservationFault("observer.already_consumed");
        }
    }

    public sealed class MemberSample
    {
        public ProcessIdentity Identity;
        public uint ParentPid;
        public bool InJob, Exited;
        public TokenEvidence Token;
        public EvidenceResult Evidence;
        public bool CommandReadComplete, CommandMatched;
    }

    public interface ISupervisionBackend : IDisposable
    {
        long Elapsed { get; }
        ProcessIdentity LauncherIdentity { get; }
        string[] ExpectedCapabilities { get; }
        void CreateSuspended(LaunchPlan plan);
        void AttachOuterJob();
        void ResumeLauncher();
        MemberSample[] Poll();
        void AdmitMaya();
        bool LauncherExited { get; }
        uint LauncherExitCode { get; }
        uint TotalProcesses { get; }
        JobPopulation Population { get; }
        bool Empty { get; }
        bool FreshBeacon { get; }
        bool InputsUnchanged { get; }
        bool MayaReturnMatches(uint childCode);
        bool AuxiliaryWorkComplete { get; }
        bool TerminateAndConfirm();
        void Pause();
    }

    public struct JobPopulation
    {
        public uint Total, Active;
    }

    public sealed class SupervisionResult
    {
        public string Reason = "observer.case_invalid";
        public bool SelectedTokenObserved, OrdinaryControlObserved, AdmissionSent;
        public bool ChildExitObserved, CommandMatched, BeaconMatched, TreeTerminated;
        public bool CaseEvidenceComplete;
        public uint? ChildExitCode;
        public readonly List<uint> UnclassifiedChildExitCodes = new List<uint>();
        public readonly bool SecurityCleanupVerified = false;
        public readonly bool NetworkingMayResume = false;
        public readonly bool ProductionQualified = false;
    }

    public static class Supervision
    {
        static string SafeReason(string code)
        {
            switch (code)
            {
                case "observer.ancestry": case "observer.member_evidence": case "observer.control_identity":
                case "observer.control_exit": case "observer.selected_identity": case "observer.command_mismatch":
                case "observer.missing_exit": case "observer.pre_admission_state": case "observer.incomplete_lifecycle":
                case "observer.launcher_exit": case "observer.input_or_worker_uncertain": case "observer.deadline":
                case "observer.already_consumed": case "observer.bad_plan": case "observer.launcher_identity":
                case "observer.input_invalid": case "observer.execution_not_authorized": case "observer.vm_mismatch":
                case "observer.stale_output": case "observer.launch_order": case "observer.admission_order":
                case "observer.pipe_failed": case "observer.output_limit": case "observer.beacon_invalid":
                case "observer.native_read_failed": case "observer.buffer_invalid": case "observer.handle_cleanup_failed":
                case "observer.unobserved_exit":
                    return code;
                default: return "observer.case_invalid";
            }
        }
        static void TimeCheck(ISupervisionBackend backend)
        {
            if (ObservationBudget.At(backend.Elapsed) != DeadlineAction.Observe)
                throw new ObservationFault("observer.deadline");
        }
        static bool IdentityEqual(ProcessIdentity a, ProcessIdentity b)
        {
            return a != null && b != null && a.Pid == b.Pid && a.Created == b.Created &&
                a.Created > 0 && String.Equals(a.Image,b.Image,StringComparison.OrdinalIgnoreCase);
        }
        public static SupervisionResult Run(LaunchPlan plan, ISupervisionBackend backend)
        {
            var result = new SupervisionResult();
            bool owned = false;
            try
            {
                if (plan == null || backend == null) throw new ObservationFault("observer.bad_plan");
                plan.Claim(); owned = true;
                backend.CreateSuspended(plan);
                TimeCheck(backend);
                backend.AttachOuterJob();
                TimeCheck(backend);
                backend.ResumeLauncher();
                TimeCheck(backend);
                ProcessIdentity launcher = backend.LauncherIdentity;
                if (launcher == null || launcher.Pid == 0 || launcher.Created <= 0 ||
                    !String.Equals(launcher.Image,plan.Launcher,StringComparison.OrdinalIgnoreCase))
                    throw new ObservationFault("observer.launcher_identity");
                ProcessIdentity selected = null, control = null;
                bool controlExited = false;
                var seen = new HashSet<uint>(); seen.Add(launcher.Pid);
                while (ObservationBudget.At(backend.Elapsed) == DeadlineAction.Observe)
                {
                    int observedExited = 0;
                    foreach (MemberSample member in backend.Poll())
                    {
                        if (member == null || member.Identity == null || !member.InJob ||
                            member.Identity.Pid == launcher.Pid || member.ParentPid != launcher.Pid ||
                            member.Identity.Created < launcher.Created ||
                            !String.Equals(member.Identity.Image,plan.Python,StringComparison.OrdinalIgnoreCase))
                            throw new ObservationFault("observer.ancestry");
                        seen.Add(member.Identity.Pid);
                        if (member.Exited) observedExited++;
                        if (member.Token == null && member.Evidence != null && member.Evidence.ExitObserved &&
                            member.Evidence.ChildExitCode.HasValue)
                            result.UnclassifiedChildExitCodes.Add(member.Evidence.ChildExitCode.Value);
                        if (member.Token == null || member.Evidence == null || !member.Evidence.ProfileMatched ||
                            !member.Evidence.TokenObserved || member.Token.User != plan.User ||
                            member.Token.Package != plan.Package || !member.Token.AppContainer ||
                            member.Token.Integrity != "S-1-16-4096" ||
                            !ObservationPolicy.CapabilitiesMatch(member.Token,backend.ExpectedCapabilities) ||
                            !member.Token.PackageAllowed || member.Token.WrongPackageAllowed || member.Token.NoGrantAllowed)
                            throw new ObservationFault("observer.member_evidence");
                        if (member.Token.AapAllowed)
                        {
                            if (plan.Case != "A" || (control != null && !IdentityEqual(control,member.Identity)) ||
                                (selected != null && selected.Pid == member.Identity.Pid))
                                throw new ObservationFault("observer.control_identity");
                            control = member.Identity; result.OrdinaryControlObserved = true;
                            if (member.Exited)
                            {
                                if (!member.Evidence.ExitObserved || member.Evidence.ChildExitCode != 0)
                                    throw new ObservationFault("observer.control_exit");
                                controlExited = true;
                            }
                        }
                        else
                        {
                            if ((selected != null && !IdentityEqual(selected,member.Identity)) ||
                                (control != null && control.Pid == member.Identity.Pid))
                                throw new ObservationFault("observer.selected_identity");
                            selected = member.Identity; result.SelectedTokenObserved = true;
                            if (member.CommandReadComplete && !member.CommandMatched)
                                throw new ObservationFault("observer.command_mismatch");
                            result.CommandMatched = member.CommandReadComplete && member.CommandMatched;
                            if (member.Exited)
                            {
                                if (!member.Evidence.ExitObserved || !member.Evidence.ChildExitCode.HasValue)
                                    throw new ObservationFault("observer.missing_exit");
                                result.ChildExitObserved = true; result.ChildExitCode = member.Evidence.ChildExitCode;
                            }
                        }
                    }
                    TimeCheck(backend);
                    if (backend.LauncherExited) observedExited++;
                    JobPopulation population = backend.Population;
                    if (population.Active > population.Total || population.Total > 64 ||
                        population.Total - population.Active > observedExited)
                        throw new ObservationFault("observer.unobserved_exit");
                    if (plan.Case == "A" && !result.AdmissionSent && selected != null && controlExited)
                    {
                        if (backend.FreshBeacon || result.ChildExitObserved || backend.LauncherExited)
                            throw new ObservationFault("observer.pre_admission_state");
                        // Query command evidence before releasing the suspended selected child.
                        if (result.CommandMatched) { backend.AdmitMaya(); result.AdmissionSent = true; }
                    }
                    if (backend.LauncherExited)
                    {
                        uint expectedCount = plan.Case == "A" ? 3u : 2u;
                        if (seen.Count != expectedCount || backend.TotalProcesses != expectedCount || !backend.Empty ||
                            selected == null || !result.ChildExitObserved || !result.CommandMatched ||
                            (plan.Case == "A" && (!result.AdmissionSent || !controlExited)))
                            throw new ObservationFault("observer.incomplete_lifecycle");
                        if ((plan.Case != "A" && backend.LauncherExitCode != result.ChildExitCode) ||
                            (plan.Case == "A" && (backend.LauncherExitCode != 0 ||
                                !backend.MayaReturnMatches(result.ChildExitCode.Value))))
                            throw new ObservationFault("observer.launcher_exit");
                        result.BeaconMatched = backend.FreshBeacon;
                        if (!backend.InputsUnchanged || !backend.AuxiliaryWorkComplete)
                            throw new ObservationFault("observer.input_or_worker_uncertain");
                        result.CaseEvidenceComplete = true;
                        result.Reason = result.ChildExitCode == 0 && result.BeaconMatched ?
                            "observer.python_entry_observed" : "observer.startup_not_established";
                        break;
                    }
                    backend.Pause();
                }
                if (!result.CaseEvidenceComplete) result.Reason = "observer.deadline";
            }
            catch (ObservationFault fault)
            {
                result.CaseEvidenceComplete = false;
                result.Reason = SafeReason(fault.Code);
            }
            catch (Exception)
            {
                result.CaseEvidenceComplete = false;
                result.Reason = "observer.case_invalid";
            }
            finally
            {
                if (owned)
                {
                    try { result.TreeTerminated = backend.TerminateAndConfirm(); }
                    catch (Exception) { result.TreeTerminated = false; }
                    try { backend.Dispose(); }
                    catch (Exception) { result.TreeTerminated = false; }
                    if (backend.Elapsed >= ObservationBudget.TotalMilliseconds)
                    { result.CaseEvidenceComplete = false; result.Reason = "observer.deadline"; }
                    if (!result.TreeTerminated)
                    { result.CaseEvidenceComplete = false; result.Reason = "observer.cleanup_uncertain"; }
                }
            }
            return result;
        }
    }
}
