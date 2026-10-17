// Gate A diagnostic library only. No entry point, provisioning or launcher fallback.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Text;
using System.Threading;

namespace Maya.GateA.Observation
{
    public sealed class ObservationFault : Exception
    {
        public readonly string Code;
        public ObservationFault(string code) : base("observer.operation_failed") { Code = code; }
    }

    public sealed class ProcessIdentity
    {
        public uint Pid;
        public long Created;
        public string Image;
    }

    public sealed class TokenEvidence
    {
        public string User, Package, Integrity;
        public bool AppContainer, PackageAllowed, AapAllowed, WrongPackageAllowed, NoGrantAllowed;
        public string[] Capabilities;
        public uint[] CapabilityAttributes;
    }

    public sealed class ExpectedProcess
    {
        public ProcessIdentity Identity;
        public string User, Package;
        public string[] Capabilities;
    }

    public sealed class EvidenceResult
    {
        public string Reason = "observer.missing_evidence";
        public bool TokenObserved, ProfileMatched, ExitObserved;
        public uint? ChildExitCode;
        public readonly bool ProductionQualified = false;
        public readonly bool ContainmentQualified = false;
    }

    public interface IProcessEvidenceReader
    {
        ProcessIdentity Identity();
        TokenEvidence Token();
        bool Exited();
        uint ExitCode();
    }

    public static class ObservationPolicy
    {
        static bool SameIdentity(ProcessIdentity a, ProcessIdentity b)
        {
            return a != null && b != null && a.Pid != 0 && a.Created > 0 &&
                a.Pid == b.Pid && a.Created == b.Created &&
                !String.IsNullOrEmpty(a.Image) &&
                String.Equals(a.Image, b.Image, StringComparison.OrdinalIgnoreCase);
        }

        public static bool CapabilitiesMatch(TokenEvidence token, string[] expected)
        {
            if (token == null || token.Capabilities == null || token.CapabilityAttributes == null ||
                expected == null || token.Capabilities.Length != expected.Length ||
                token.CapabilityAttributes.Length != expected.Length || expected.Length == 0)
                return false;
            var actual = new HashSet<string>(StringComparer.Ordinal);
            var wanted = new HashSet<string>(StringComparer.Ordinal);
            for (int i = 0; i < expected.Length; i++)
            {
                if (String.IsNullOrEmpty(expected[i]) || !wanted.Add(expected[i]) ||
                    String.IsNullOrEmpty(token.Capabilities[i]) || !actual.Add(token.Capabilities[i]) ||
                    token.CapabilityAttributes[i] != 4) return false;
            }
            return actual.SetEquals(wanted);
        }

        public static EvidenceResult Capture(IProcessEvidenceReader reader, ExpectedProcess expected)
        { return CaptureProfile(reader, expected, true); }

        public static EvidenceResult CaptureOrdinaryControl(IProcessEvidenceReader reader, ExpectedProcess expected)
        { return CaptureProfile(reader, expected, false); }

        static EvidenceResult CaptureProfile(IProcessEvidenceReader reader, ExpectedProcess expected, bool lpac)
        {
            var result = new EvidenceResult();
            try
            {
                if (reader == null || expected == null || expected.Identity == null ||
                    String.IsNullOrEmpty(expected.User) || String.IsNullOrEmpty(expected.Package))
                    throw new ObservationFault("observer.bad_expectation");
                if (!SameIdentity(reader.Identity(), expected.Identity))
                    throw new ObservationFault("observer.identity_mismatch");
                // A process which disappeared before token observation is not a passing denial.
                if (reader.Exited())
                {
                    result.ChildExitCode = reader.ExitCode();
                    result.ExitObserved = true;
                    result.Reason = "observer.exited_before_token";
                    return result;
                }
                TokenEvidence token = reader.Token();
                result.TokenObserved = token != null;
                if (!SameIdentity(reader.Identity(), expected.Identity))
                    throw new ObservationFault("observer.identity_changed");
                if (token == null || !token.AppContainer || token.User != expected.User ||
                    token.Package != expected.Package || token.Integrity != "S-1-16-4096" ||
                    !CapabilitiesMatch(token, expected.Capabilities) || !token.PackageAllowed ||
                    token.AapAllowed == lpac || token.WrongPackageAllowed || token.NoGrantAllowed)
                    throw new ObservationFault("observer.profile_mismatch");
                result.ProfileMatched = true;
                result.Reason = "observer.token_observed";
                if (reader.Exited())
                {
                    result.ChildExitCode = reader.ExitCode();
                    result.ExitObserved = true;
                    result.Reason = "observer.token_and_exit_observed";
                }
            }
            catch (ObservationFault error)
            {
                result.ProfileMatched = false;
                result.Reason = SafeCode(error.Code);
            }
            catch (Exception)
            {
                result.ProfileMatched = false;
                result.Reason = "observer.evidence_failed";
            }
            return result;
        }

        public static EvidenceResult FinishExit(IProcessEvidenceReader reader,
            ExpectedProcess expected, EvidenceResult prior)
        {
            var result = new EvidenceResult();
            if (prior == null || !prior.ProfileMatched || !prior.TokenObserved) return result;
            result.TokenObserved = true;
            try
            {
                if (reader == null || expected == null ||
                    !SameIdentity(reader.Identity(), expected.Identity))
                    throw new ObservationFault("observer.identity_changed");
                result.ProfileMatched = true;
                result.Reason = "observer.token_observed";
                if (reader.Exited())
                {
                    result.ChildExitCode = reader.ExitCode();
                    result.ExitObserved = true;
                    result.Reason = "observer.token_and_exit_observed";
                }
            }
            catch (ObservationFault error) { result.ProfileMatched = false; result.Reason = SafeCode(error.Code); }
            catch (Exception) { result.ProfileMatched = false; result.Reason = "observer.evidence_failed"; }
            return result;
        }

        static string SafeCode(string code)
        {
            switch (code)
            {
                case "observer.bad_expectation": case "observer.identity_mismatch":
                case "observer.identity_changed": case "observer.profile_mismatch":
                case "observer.native_read_failed": case "observer.buffer_invalid":
                case "observer.handle_cleanup_failed": return code;
                default: return "observer.evidence_failed";
            }
        }
    }

    public enum DeadlineAction { Observe, TerminateTree, DeadlineExceeded }

    public static class ObservationBudget
    {
        public const int TotalMilliseconds = 100000;
        public const int CleanupReserveMilliseconds = 5000;
        public static DeadlineAction At(long elapsedMilliseconds)
        {
            if (elapsedMilliseconds < 0) throw new ObservationFault("observer.bad_clock");
            if (elapsedMilliseconds >= TotalMilliseconds) return DeadlineAction.DeadlineExceeded;
            return elapsedMilliseconds >= TotalMilliseconds - CleanupReserveMilliseconds ?
                DeadlineAction.TerminateTree : DeadlineAction.Observe;
        }
        public static int Remaining(long elapsedMilliseconds)
        {
            if (elapsedMilliseconds < 0) throw new ObservationFault("observer.bad_clock");
            return elapsedMilliseconds >= TotalMilliseconds ? 0 :
                (int)(TotalMilliseconds - elapsedMilliseconds);
        }
    }

    public static class ObservationLayout
    {
        public static bool ValidX64()
        {
            return IntPtr.Size == 8 && Marshal.SizeOf(typeof(Native.SidAttributes)) == 16 &&
                (int)Marshal.OffsetOf(typeof(Native.Groups), "first") == 8 &&
                Marshal.SizeOf(typeof(Native.BasicLimits)) == 64 &&
                Marshal.SizeOf(typeof(Native.JobLimits)) == 144 &&
                Marshal.SizeOf(typeof(Native.Accounting)) == 48;
        }
    }

    // Owns a query/synchronize handle, not a process-creation or termination capability.
    public sealed class NativeProcessReader : IProcessEvidenceReader, IDisposable
    {
        IntPtr process;
        readonly uint pid;
        readonly string expectedPackage;

        internal IntPtr Handle { get { LiveHandle(); return process; } }

        internal NativeProcessReader(uint processId, string package)
        {
            if (!ObservationLayout.ValidX64() || processId == 0 || String.IsNullOrEmpty(package))
                throw new ObservationFault("observer.bad_expectation");
            pid = processId; expectedPackage = package;
            process = Native.OpenProcess(0x101000, false, pid);
            Native.Require(process != IntPtr.Zero);
        }

        public NativeProcessReader(uint processId, long creationTime, string image, string package)
        {
            if (!ObservationLayout.ValidX64()) throw new ObservationFault("observer.buffer_invalid");
            if (processId == 0 || creationTime <= 0 || String.IsNullOrEmpty(image) ||
                String.IsNullOrEmpty(package)) throw new ObservationFault("observer.bad_expectation");
            pid = processId;
            expectedPackage = package;
            process = Native.OpenProcess(0x101000, false, pid);
            Native.Require(process != IntPtr.Zero);
            try
            {
                ProcessIdentity actual = Identity();
                if (actual.Created != creationTime ||
                    !String.Equals(actual.Image, image, StringComparison.OrdinalIgnoreCase))
                    throw new ObservationFault("observer.identity_mismatch");
            }
            catch { Dispose(); throw; }
        }

        void LiveHandle() { if (process == IntPtr.Zero) throw new ObservationFault("observer.native_read_failed"); }

        public ProcessIdentity Identity()
        {
            LiveHandle();
            long created, exited, kernel, user;
            Native.Require(Native.GetProcessTimes(process, out created, out exited, out kernel, out user));
            var image = new StringBuilder(32768);
            uint length = (uint)image.Capacity;
            Native.Require(Native.QueryFullProcessImageName(process, 0, image, ref length));
            return new ProcessIdentity { Pid = pid, Created = created, Image = image.ToString() };
        }

        public bool Exited()
        {
            LiveHandle();
            uint status = Native.WaitForSingleObject(process, 0);
            if (status != 0 && status != 258) throw new ObservationFault("observer.native_read_failed");
            return status == 0;
        }

        public uint ExitCode()
        {
            // 259 can also be a real exit code; use the signaled process handle first.
            if (!Exited()) throw new ObservationFault("observer.native_read_failed");
            uint code;
            Native.Require(Native.GetExitCodeProcess(process, out code));
            return code;
        }

        public TokenEvidence Token()
        {
            LiveHandle();
            IntPtr token = IntPtr.Zero, duplicate = IntPtr.Zero;
            try
            {
                Native.Require(Native.OpenProcessToken(process, 10, out token));
                var data = new TokenEvidence();
                using (var buffer = new TokenBuffer(token, 29)) data.AppContainer = Marshal.ReadInt32(buffer.Pointer) == 1;
                using (var buffer = new TokenBuffer(token, 1)) data.User = buffer.SidAt(0);
                using (var buffer = new TokenBuffer(token, 31)) data.Package = buffer.SidAt(0);
                using (var buffer = new TokenBuffer(token, 25)) data.Integrity = buffer.SidAt(0);
                using (var buffer = new TokenBuffer(token, 30))
                {
                    int count = Marshal.ReadInt32(buffer.Pointer);
                    int start = (int)Marshal.OffsetOf(typeof(Native.Groups), "first");
                    int step = Marshal.SizeOf(typeof(Native.SidAttributes));
                    if (count < 0 || count > 256 || (long)start + (long)count * step > buffer.Size)
                        throw new ObservationFault("observer.buffer_invalid");
                    data.Capabilities = new string[count];
                    data.CapabilityAttributes = new uint[count];
                    for (int i = 0; i < count; i++)
                    {
                        int offset = start + i * step;
                        data.Capabilities[i] = buffer.SidAt(offset);
                        data.CapabilityAttributes[i] = unchecked((uint)Marshal.ReadInt32(buffer.Pointer, offset + IntPtr.Size));
                    }
                }
                Native.Require(Native.DuplicateToken(token, 2, out duplicate));
                data.PackageAllowed = Probe(duplicate, data.User, expectedPackage);
                data.AapAllowed = Probe(duplicate, data.User, "S-1-15-2-1");
                data.WrongPackageAllowed = Probe(duplicate, data.User,
                    "S-1-15-2-987654321-987654321-987654321-987654321-987654321-987654321-987654321");
                data.NoGrantAllowed = Probe(duplicate, data.User, null);
                return data;
            }
            finally
            {
                bool a = duplicate == IntPtr.Zero || Native.CloseHandle(duplicate);
                bool b = token == IntPtr.Zero || Native.CloseHandle(token);
                if (!a || !b) throw new ObservationFault("observer.handle_cleanup_failed");
            }
        }

        static bool Probe(IntPtr token, string user, string grant)
        {
            // SecurityIdentifier rejects SDDL injection; descriptors exist only in memory.
            user = new SecurityIdentifier(user).Value;
            if (grant != null) grant = new SecurityIdentifier(grant).Value;
            string sddl = "O:BAG:BAD:P(A;;0x1;;;" + user + ")";
            if (grant != null) sddl += "(A;;0x1;;;" + grant + ")";
            IntPtr descriptor = IntPtr.Zero, privileges = IntPtr.Zero;
            try
            {
                uint size;
                Native.Require(Native.ConvertStringSecurityDescriptorToSecurityDescriptor(sddl, 1, out descriptor, out size));
                privileges = Marshal.AllocHGlobal(1024);
                uint bytes = 1024, granted;
                bool status;
                var mapping = new Native.GenericMapping { read = 1, write = 2, execute = 4, all = 7 };
                Native.Require(Native.AccessCheck(descriptor, token, 1, ref mapping, privileges, ref bytes, out granted, out status));
                if (bytes > 1024 || granted != (status ? 1u : 0u))
                    throw new ObservationFault("observer.native_read_failed");
                return status;
            }
            finally
            {
                if (privileges != IntPtr.Zero) Marshal.FreeHGlobal(privileges);
                if (descriptor != IntPtr.Zero && Native.LocalFree(descriptor) != IntPtr.Zero)
                    throw new ObservationFault("observer.handle_cleanup_failed");
            }
        }

        public void Dispose()
        {
            IntPtr handle = process;
            process = IntPtr.Zero;
            if (handle != IntPtr.Zero && !Native.CloseHandle(handle))
                throw new ObservationFault("observer.handle_cleanup_failed");
        }
    }

    sealed class TokenBuffer : IDisposable
    {
        public readonly IntPtr Pointer;
        public readonly int Size;
        public TokenBuffer(IntPtr token, int informationClass)
        {
            uint needed;
            if (Native.GetTokenInformation(token, informationClass, IntPtr.Zero, 0, out needed) ||
                Marshal.GetLastWin32Error() != 122 || needed < 4 || needed > 65536)
                throw new ObservationFault("observer.buffer_invalid");
            Size = (int)needed;
            Pointer = Marshal.AllocHGlobal(Size);
            try
            {
                Native.Require(Native.GetTokenInformation(token, informationClass, Pointer, needed, out needed));
                if (needed > Size) throw new ObservationFault("observer.buffer_invalid");
            }
            catch { Marshal.FreeHGlobal(Pointer); throw; }
        }
        public string SidAt(int offset)
        {
            if (offset < 0 || offset > Size - IntPtr.Size)
                throw new ObservationFault("observer.buffer_invalid");
            IntPtr sid = Marshal.ReadIntPtr(Pointer, offset);
            long index = sid.ToInt64() - Pointer.ToInt64();
            if (sid == IntPtr.Zero || index < 0 || index > Size - 8)
                throw new ObservationFault("observer.buffer_invalid");
            int subAuthorities = Marshal.ReadByte(sid, 1);
            if (subAuthorities > 15 || 8 + subAuthorities * 4 > Size - index || !Native.IsValidSid(sid))
                throw new ObservationFault("observer.buffer_invalid");
            uint length = Native.GetLengthSid(sid);
            if (length < 8 || length > Size - index) throw new ObservationFault("observer.buffer_invalid");
            return new SecurityIdentifier(sid).Value;
        }
        public void Dispose() { Marshal.FreeHGlobal(Pointer); }
    }

    // No resource/UI/security limits: only kill-on-close, with neither breakaway flag.
    // The future launcher adapter must attach its OWN suspended launcher before resume.
    public sealed class ObserverJob : IDisposable
    {
        IntPtr job;
        public ObserverJob()
        {
            if (!ObservationLayout.ValidX64()) throw new ObservationFault("observer.buffer_invalid");
            job = Native.CreateJobObject(IntPtr.Zero, null);
            Native.Require(job != IntPtr.Zero);
            try
            {
                var limits = new Native.JobLimits { basic = new Native.BasicLimits { flags = 0x2000 } };
                Native.Require(Native.SetInformationJobObject(job, 9, ref limits,
                    (uint)Marshal.SizeOf(typeof(Native.JobLimits))));
            }
            catch { Dispose(); throw; }
        }
        public void AttachOwnedSuspendedLauncher(IntPtr processHandle)
        {
            if (job == IntPtr.Zero || processHandle == IntPtr.Zero)
                throw new ObservationFault("observer.native_read_failed");
            Native.Require(Native.AssignProcessToJobObject(job, processHandle));
            bool member;
            Native.Require(Native.IsProcessInJob(processHandle, job, out member) && member);
        }
        public bool Empty()
        {
            if (job == IntPtr.Zero) throw new ObservationFault("observer.native_read_failed");
            Native.Accounting counts;
            Native.Require(Native.QueryInformationJobObject(job, 1, out counts,
                (uint)Marshal.SizeOf(typeof(Native.Accounting)), IntPtr.Zero));
            return counts.activeProcesses == 0;
        }
        internal bool Contains(IntPtr processHandle)
        {
            bool member = false;
            Native.Require(job != IntPtr.Zero && Native.IsProcessInJob(processHandle, job, out member));
            return member;
        }
        internal uint TotalProcesses()
        { return Population().totalProcesses; }
        internal Native.Accounting Population()
        {
            Native.Accounting counts;
            Native.Require(job != IntPtr.Zero);
            Native.Require(Native.QueryInformationJobObject(job, 1, out counts,
                (uint)Marshal.SizeOf(typeof(Native.Accounting)), IntPtr.Zero));
            return counts;
        }
        internal uint[] Members()
        {
            Native.Require(job != IntPtr.Zero);
            const int capacity = 64, size = 8 + capacity * 8;
            IntPtr buffer = Marshal.AllocHGlobal(size);
            try
            {
                Native.Require(Native.QueryInformationJobObject(job, 3, buffer, size, IntPtr.Zero));
                int assigned = Marshal.ReadInt32(buffer), count = Marshal.ReadInt32(buffer, 4);
                if (assigned != count || count < 0 || count > capacity)
                    throw new ObservationFault("observer.buffer_invalid");
                var result = new uint[count];
                for (int i = 0; i < count; i++)
                {
                    long pid = Marshal.ReadInt64(buffer, 8 + i * 8);
                    if (pid <= 0 || pid > UInt32.MaxValue) throw new ObservationFault("observer.buffer_invalid");
                    result[i] = (uint)pid;
                }
                return result;
            }
            finally { Marshal.FreeHGlobal(buffer); }
        }
        public bool TerminateAndConfirm(Stopwatch caseClock)
        {
            if (job == IntPtr.Zero || caseClock == null || !caseClock.IsRunning)
                throw new ObservationFault("observer.native_read_failed");
            Native.Require(Native.TerminateJobObject(job, 1));
            while (ObservationBudget.Remaining(caseClock.ElapsedMilliseconds) > 0)
            {
                if (Empty()) return true;
                Thread.Sleep(Math.Min(10, ObservationBudget.Remaining(caseClock.ElapsedMilliseconds)));
            }
            return false;
        }
        internal void RequestTermination()
        {
            Native.Require(job != IntPtr.Zero);
            Native.Require(Native.TerminateJobObject(job,1));
        }
        public void Dispose()
        {
            IntPtr handle = job;
            job = IntPtr.Zero;
            // Closing is a safety net, not proof that every member finished terminating.
            if (handle != IntPtr.Zero && !Native.CloseHandle(handle))
                throw new ObservationFault("observer.handle_cleanup_failed");
        }
    }

    static class Native
    {
        public static void Require(bool value) { if (!value) throw new ObservationFault("observer.native_read_failed"); }
        [StructLayout(LayoutKind.Sequential)] public struct SidAttributes { public IntPtr sid; public uint attributes; }
        [StructLayout(LayoutKind.Sequential)] public struct Groups { public uint count; public SidAttributes first; }
        [StructLayout(LayoutKind.Sequential)] public struct GenericMapping { public uint read, write, execute, all; }
        [StructLayout(LayoutKind.Sequential)] public struct BasicLimits
        {
            public long processTime, jobTime; public uint flags; public UIntPtr minimum, maximum;
            public uint activeProcessLimit; public UIntPtr affinity; public uint priority, scheduling;
        }
        [StructLayout(LayoutKind.Sequential)] public struct IoCounters { public ulong a, b, c, d, e, f; }
        [StructLayout(LayoutKind.Sequential)] public struct JobLimits
        {
            public BasicLimits basic; public IoCounters io; public UIntPtr processMemory, jobMemory, peakProcess, peakJob;
        }
        [StructLayout(LayoutKind.Sequential)] public struct Accounting
        {
            public long userTime, kernelTime, periodUserTime, periodKernelTime;
            public uint faults, totalProcesses, activeProcesses, terminatedProcesses;
        }
        [DllImport("kernel32.dll", SetLastError=true)] public static extern IntPtr OpenProcess(uint access, bool inherit, uint pid);
        [DllImport("kernel32.dll", SetLastError=true)] public static extern bool CloseHandle(IntPtr handle);
        [DllImport("kernel32.dll", SetLastError=true)] public static extern bool GetProcessTimes(IntPtr process, out long created, out long exited, out long kernel, out long user);
        [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] public static extern bool QueryFullProcessImageName(IntPtr process, uint flags, StringBuilder image, ref uint length);
        [DllImport("kernel32.dll", SetLastError=true)] public static extern uint WaitForSingleObject(IntPtr handle, uint milliseconds);
        [DllImport("kernel32.dll", SetLastError=true)] public static extern bool GetExitCodeProcess(IntPtr process, out uint code);
        [DllImport("advapi32.dll", SetLastError=true)] public static extern bool OpenProcessToken(IntPtr process, uint access, out IntPtr token);
        [DllImport("advapi32.dll", SetLastError=true)] public static extern bool GetTokenInformation(IntPtr token, int kind, IntPtr data, uint size, out uint needed);
        [DllImport("advapi32.dll", SetLastError=true)] public static extern bool DuplicateToken(IntPtr token, int level, out IntPtr duplicate);
        [DllImport("advapi32.dll", SetLastError=true)] public static extern bool AccessCheck(IntPtr descriptor, IntPtr token, uint desired, ref GenericMapping mapping, IntPtr privileges, ref uint bytes, out uint granted, out bool status);
        [DllImport("advapi32.dll", CharSet=CharSet.Unicode, SetLastError=true)] public static extern bool ConvertStringSecurityDescriptorToSecurityDescriptor(string text, uint revision, out IntPtr descriptor, out uint bytes);
        [DllImport("advapi32.dll")] public static extern bool IsValidSid(IntPtr sid);
        [DllImport("advapi32.dll")] public static extern uint GetLengthSid(IntPtr sid);
        [DllImport("kernel32.dll")] public static extern IntPtr LocalFree(IntPtr memory);
        [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] public static extern IntPtr CreateJobObject(IntPtr security, string name);
        [DllImport("kernel32.dll", SetLastError=true)] public static extern bool SetInformationJobObject(IntPtr job, int kind, ref JobLimits limits, uint bytes);
        [DllImport("kernel32.dll", SetLastError=true)] public static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);
        [DllImport("kernel32.dll", SetLastError=true)] public static extern bool IsProcessInJob(IntPtr process, IntPtr job, out bool result);
        [DllImport("kernel32.dll", SetLastError=true)] public static extern bool QueryInformationJobObject(IntPtr job, int kind, out Accounting counts, uint bytes, IntPtr returned);
        [DllImport("kernel32.dll", SetLastError=true)] public static extern bool QueryInformationJobObject(IntPtr job, int kind, IntPtr buffer, int bytes, IntPtr returned);
        [DllImport("kernel32.dll", SetLastError=true)] public static extern bool TerminateJobObject(IntPtr job, uint code);
    }
}
