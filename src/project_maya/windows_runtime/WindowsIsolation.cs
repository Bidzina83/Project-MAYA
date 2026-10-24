// Native layouts and token controls follow the reviewed Gate A prototype.
// This product component owns consent/setup/launch/cleanup, not test supervision.
using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;
using System.Threading;
using Microsoft.Win32;

[assembly: DefaultDllImportSearchPaths(DllImportSearchPath.System32)]

namespace ProjectMaya.WindowsRuntime
{
    internal static class Native
    {
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)] internal struct OsVersion
        {
            internal uint size, major, minor, build, platform;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)] internal string service;
        }
        [DllImport("ntdll.dll")] static extern int RtlGetVersion(ref OsVersion version);
        [DllImport("kernel32.dll", SetLastError = true)] internal static extern bool SetDefaultDllDirectories(uint flags);
        [DllImport("kernel32.dll")] static extern uint GetErrorMode();
        [DllImport("kernel32.dll")] static extern uint SetErrorMode(uint mode);
        [DllImport("kernel32.dll", SetLastError = true)] internal static extern bool CloseHandle(IntPtr handle);
        [DllImport("kernel32.dll")] internal static extern IntPtr LocalFree(IntPtr memory);
        [DllImport("advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)] internal static extern bool ConvertStringSecurityDescriptorToSecurityDescriptor(
            string text, uint revision, out IntPtr descriptor, out uint size);
        [DllImport("advapi32.dll", SetLastError = true)] static extern bool GetSecurityDescriptorSacl(IntPtr descriptor, out bool present, out IntPtr acl, out bool defaulted);
        [DllImport("advapi32.dll", CharSet = CharSet.Unicode)] static extern uint SetNamedSecurityInfoW(string path, uint type, uint info,
            IntPtr owner, IntPtr group, IntPtr dacl, IntPtr sacl);
        [DllImport("advapi32.dll", CharSet = CharSet.Unicode)] static extern uint GetNamedSecurityInfoW(string path, uint type, uint info,
            out IntPtr owner, out IntPtr group, out IntPtr dacl, out IntPtr sacl, out IntPtr descriptor);
        [DllImport("advapi32.dll")] static extern uint GetSecurityDescriptorLength(IntPtr descriptor);

        internal static void Require(bool value, string operation)
        {
            if (!value) throw new StartupFailure(operation + ":win32_" + Marshal.GetLastWin32Error());
        }
        internal static void Check(uint code, string operation)
        {
            if (code != 0) throw new StartupFailure(operation + ":0x" + code.ToString("X8"));
        }
        internal static void ConfigureErrorMode()
        {
            ConfigureErrorMode(GetErrorMode, SetErrorMode);
        }
        internal static void ConfigureErrorMode(Func<uint> read, Func<uint, uint> write)
        {
            // The child inherits this process-local mode; preserve all other flags.
            uint expected = read() | 1u; // SEM_FAILCRITICALERRORS, not WER suppression.
            write(expected);
            if (read() != expected) throw new StartupFailure("critical_error_mode_not_verified");
        }
        internal static void CheckBaseline()
        {
            var version = new OsVersion { size = (uint)Marshal.SizeOf(typeof(OsVersion)) };
            if (RtlGetVersion(ref version) != 0 || version.major != 10 || version.build != 26300)
                throw new StartupFailure("windows_build_outside_first_package_scope");
            using (var machine = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64))
            using (var key = machine.OpenSubKey(@"SOFTWARE\Microsoft\Windows NT\CurrentVersion", false))
                if (key == null || Convert.ToInt32(key.GetValue("UBR", -1)) != 9711 ||
                    (string)key.GetValue("EditionID", "") != "Professional")
                    throw new StartupFailure("windows_edition_or_revision_changed");
        }
        internal static void SetLabel(string path, bool low)
        {
            ProductFiles.NoLinks(path);
            SetAndVerifyLabel(path, low);
        }
        static void SetAndVerifyLabel(string path, bool low)
        {
            bool folder = Directory.Exists(path);
            IntPtr descriptor = IntPtr.Zero;
            try
            {
                uint size; bool present, defaulted; IntPtr acl;
                Require(ConvertStringSecurityDescriptorToSecurityDescriptor("S:(ML;" + (folder ? "OICI" : "") + ";NW;;;" + (low ? "LW" : "ME") + ")",
                    1, out descriptor, out size), "state_label_descriptor");
                Require(GetSecurityDescriptorSacl(descriptor, out present, out acl, out defaulted) && present, "state_label_acl");
                Check(SetNamedSecurityInfoW(path, 1, 0x10, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero, acl), "state_label_set");
            }
            finally { if (descriptor != IntPtr.Zero) LocalFree(descriptor); }
            IntPtr owner, group, dacl, sacl, found;
            Check(GetNamedSecurityInfoW(path, 1, 0x10, out owner, out group, out dacl, out sacl, out found), "state_label_read");
            try
            {
                int length = checked((int)GetSecurityDescriptorLength(found));
                if (length < 20 || length > 65536) throw new StartupFailure("state_label_descriptor_size");
                byte[] bytes = new byte[length]; Marshal.Copy(found, bytes, 0, length);
                var raw = new RawSecurityDescriptor(bytes, 0);
                VerifyLabel(raw, low, folder);
            }
            finally { LocalFree(found); }
        }
        internal static void VerifyLabel(RawSecurityDescriptor raw, bool low, bool folder)
        {
                if (raw.SystemAcl == null || raw.SystemAcl.Count != 1) throw new StartupFailure("state_label_mismatch");
                // Mandatory-label ACEs are represented as custom ACEs by some CLR versions.
                byte[] ace = new byte[raw.SystemAcl[0].BinaryLength]; raw.SystemAcl[0].GetBinaryForm(ace, 0);
                if (ace[0] != 0x11 || ace[1] != (folder ? 3 : 0) || BitConverter.ToInt32(ace, 4) != 1 ||
                    new SecurityIdentifier(ace, 8).Value != (low ? "S-1-16-4096" : "S-1-16-8192"))
                    throw new StartupFailure("state_label_mismatch");
        }
    }

    internal sealed partial class WindowsIsolation : IDisposable
    {
        // DETACHED_PROCESS | EXTENDED_STARTUPINFO_PRESENT | CREATE_UNICODE_ENVIRONMENT | CREATE_SUSPENDED.
        internal const uint LaunchCreationFlags = 0x0008040c;
        [StructLayout(LayoutKind.Sequential)] struct Display { internal IntPtr name, description; }
        [StructLayout(LayoutKind.Sequential)] struct Blob { internal uint size; internal IntPtr data; }
        [StructLayout(LayoutKind.Explicit)] struct Scalar { [FieldOffset(0)] internal uint number; [FieldOffset(0)] internal IntPtr pointer; }
        [StructLayout(LayoutKind.Sequential)] struct Value { internal uint type; internal Scalar data; }
        [StructLayout(LayoutKind.Sequential)] struct Condition { internal Guid key; internal uint match; internal Value value; }
        [StructLayout(LayoutKind.Sequential)] struct FilterAction { internal uint type; internal Guid key; }
        [StructLayout(LayoutKind.Explicit, Size = 16)] struct Context { [FieldOffset(0)] internal ulong raw; }
        [StructLayout(LayoutKind.Sequential)] struct Filter
        {
            internal Guid key; internal Display display; internal uint flags; internal IntPtr provider;
            internal Blob data; internal Guid layer, sublayer; internal Value weight; internal uint count;
            internal IntPtr conditions; internal FilterAction action; internal Context context; internal IntPtr reserved;
            internal ulong id; internal Value effectiveWeight;
        }
        [StructLayout(LayoutKind.Sequential)] struct Sublayer
        {
            internal Guid key; internal Display display; internal uint flags; internal IntPtr provider;
            internal Blob data; internal ushort weight;
        }
        [StructLayout(LayoutKind.Sequential)] struct Capabilities { internal IntPtr sid, capabilities; internal uint count, reserved; }
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)] struct Startup
        {
            internal uint size; internal IntPtr reserved, desktop, title;
            internal uint x, y, xSize, ySize, xChars, yChars, fill, flags; internal ushort show, reservedSize;
            internal IntPtr reservedBytes, input, output, error;
        }
        [StructLayout(LayoutKind.Sequential)] struct StartupEx { internal Startup startup; internal IntPtr attributes; }
        [StructLayout(LayoutKind.Sequential)] struct ProcessInfo { internal IntPtr process, thread; internal uint pid, tid; }
        [StructLayout(LayoutKind.Sequential)] struct SecurityAttributes { internal uint size; internal IntPtr descriptor; internal int inherit; }
        [StructLayout(LayoutKind.Sequential)] struct BasicLimits
        {
            internal long processTime, jobTime; internal uint flags; internal UIntPtr minWorkingSet, maxWorkingSet;
            internal uint activeProcessLimit; internal UIntPtr affinity; internal uint priority, scheduling;
        }
        [StructLayout(LayoutKind.Sequential)] struct IoCounters { internal ulong readOps, writeOps, otherOps, readBytes, writeBytes, otherBytes; }
        [StructLayout(LayoutKind.Sequential)] struct JobLimits
        { internal BasicLimits basic; internal IoCounters io; internal UIntPtr processMemory, jobMemory, peakProcess, peakJob; }
        [StructLayout(LayoutKind.Sequential)] struct JobAccounting
        {
            internal long userTime, kernelTime, periodUser, periodKernel;
            internal uint pageFaults, totalProcesses, activeProcesses, terminated;
        }
        [StructLayout(LayoutKind.Sequential)] struct GenericMapping { internal uint read, write, execute, all; }
        [StructLayout(LayoutKind.Sequential)] struct SidAttributes { internal IntPtr sid; internal uint attributes; }

        [DllImport("userenv.dll", CharSet = CharSet.Unicode)] static extern int CreateAppContainerProfile(string name, string display, string description, IntPtr caps, uint count, out IntPtr sid);
        [DllImport("userenv.dll", CharSet = CharSet.Unicode)] static extern int DeriveAppContainerSidFromAppContainerName(string name, out IntPtr sid);
        [DllImport("userenv.dll", CharSet = CharSet.Unicode)] static extern int DeleteAppContainerProfile(string name);
        [DllImport("advapi32.dll")] static extern IntPtr FreeSid(IntPtr sid);
        [DllImport("fwpuclnt.dll")] static extern uint FwpmEngineOpen0(IntPtr server, uint auth, IntPtr identity, IntPtr session, out IntPtr engine);
        [DllImport("fwpuclnt.dll")] static extern uint FwpmEngineClose0(IntPtr engine);
        [DllImport("fwpuclnt.dll")] static extern uint FwpmTransactionBegin0(IntPtr engine, uint flags);
        [DllImport("fwpuclnt.dll")] static extern uint FwpmTransactionCommit0(IntPtr engine);
        [DllImport("fwpuclnt.dll")] static extern uint FwpmTransactionAbort0(IntPtr engine);
        [DllImport("fwpuclnt.dll")] static extern uint FwpmSubLayerAdd0(IntPtr engine, ref Sublayer layer, IntPtr security);
        [DllImport("fwpuclnt.dll")] static extern uint FwpmSubLayerDeleteByKey0(IntPtr engine, ref Guid key);
        [DllImport("fwpuclnt.dll")] static extern uint FwpmFilterAdd0(IntPtr engine, ref Filter filter, IntPtr security, out ulong id);
        [DllImport("fwpuclnt.dll")] static extern uint FwpmFilterGetByKey0(IntPtr engine, ref Guid key, out IntPtr filter);
        [DllImport("fwpuclnt.dll")] static extern uint FwpmFilterDeleteByKey0(IntPtr engine, ref Guid key);
        [DllImport("fwpuclnt.dll")] static extern void FwpmFreeMemory0(ref IntPtr pointer);
        [DllImport("kernel32.dll", SetLastError = true)] static extern bool InitializeProcThreadAttributeList(IntPtr list, int count, uint flags, ref UIntPtr size);
        [DllImport("kernel32.dll", SetLastError = true)] static extern bool UpdateProcThreadAttribute(IntPtr list, uint flags, IntPtr attribute, IntPtr value, UIntPtr size, IntPtr previous, IntPtr returned);
        [DllImport("kernel32.dll")] static extern void DeleteProcThreadAttributeList(IntPtr list);
        [DllImport("advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)] static extern bool CreateProcessAsUserW(IntPtr token, string app, StringBuilder command,
            IntPtr ps, IntPtr ts, bool inherit, uint flags, IntPtr environment, string cwd, ref StartupEx startup, out ProcessInfo info);
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)] static extern IntPtr CreateJobObject(IntPtr security, string name);
        [DllImport("kernel32.dll", SetLastError = true)] static extern bool SetInformationJobObject(IntPtr job, int type, ref JobLimits data, uint length);
        [DllImport("kernel32.dll", SetLastError = true)] static extern bool QueryInformationJobObject(IntPtr job, int type, out JobAccounting data, uint length, IntPtr returned);
        [DllImport("kernel32.dll", SetLastError = true)] static extern uint ResumeThread(IntPtr thread);
        [DllImport("kernel32.dll")] static extern uint WaitForSingleObject(IntPtr handle, uint milliseconds);
        [DllImport("kernel32.dll", SetLastError = true)] static extern bool GetExitCodeProcess(IntPtr process, out uint code);
        [DllImport("kernel32.dll", SetLastError = true)] static extern bool TerminateJobObject(IntPtr job, uint code);
        [DllImport("kernel32.dll", SetLastError = true)] static extern bool CreatePipe(out IntPtr read, out IntPtr write, ref SecurityAttributes attributes, uint size);
        [DllImport("kernel32.dll", SetLastError = true)] static extern bool SetHandleInformation(IntPtr handle, uint mask, uint flags);
        [DllImport("advapi32.dll", SetLastError = true)] static extern bool OpenProcessToken(IntPtr process, uint access, out IntPtr token);
        [DllImport("advapi32.dll", SetLastError = true)] static extern bool GetTokenInformation(IntPtr token, int type, IntPtr data, uint length, out uint required);
        [DllImport("advapi32.dll", SetLastError = true)] static extern bool CreateRestrictedToken(IntPtr existing, uint flags,
            uint disableCount, ref SidAttributes disabled, uint deleteCount, IntPtr deleted, uint restrictCount, IntPtr restricted, out IntPtr token);
        [DllImport("advapi32.dll", SetLastError = true)] static extern bool SetTokenInformation(IntPtr token, int type, IntPtr data, uint length);
        [DllImport("advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)] static extern bool LookupPrivilegeValueW(string system, string name, out long luid);
        [DllImport("advapi32.dll", SetLastError = true)] static extern bool DuplicateToken(IntPtr token, int level, out IntPtr duplicate);
        [DllImport("advapi32.dll", SetLastError = true)] static extern bool AccessCheck(IntPtr descriptor, IntPtr token, uint desired,
            ref GenericMapping mapping, IntPtr privileges, ref uint privilegeLength, out uint granted, out bool status);

        static readonly Guid PackageCondition = new Guid("71bc78fa-f17c-4997-a602-6abb261f351c");
        static readonly Guid[] Layers = {
            new Guid("c38d57d1-05a7-4c33-904f-7fbceee60e82"), new Guid("4a72393b-319f-44bc-84c3-ba54dcb3b6b4"),
            new Guid("88bb5dad-76d7-4227-9c71-df0a3ed7be7e"), new Guid("7ac9de24-17dd-4814-b4bd-a9fbc95a321b"),
            new Guid("e1cd9fe7-f4b5-4273-96c0-592e487b8650"), new Guid("a3b42c97-9f04-4672-b87e-cee9c483257f") };
        readonly string profile;
        IntPtr sid, engine, job, readOutput, readError;
        ProcessInfo child;
        Thread outputThread, errorThread;
        bool captureFailed;
        internal bool ProfileCollision { get; private set; }
        internal bool Resumed { get; private set; }
        internal bool ReducedLaunchTokenVerified { get; private set; }
        internal uint? ExitCode { get; private set; }
        internal string Stdout { get; private set; }
        internal int StderrBytes { get; private set; }
        internal bool OutputCaptureComplete
        {
            get { return outputThread != null && errorThread != null &&
                !outputThread.IsAlive && !errorThread.IsAlive && !captureFailed; }
        }
        internal uint ChildPid { get { return child.pid; } }
        internal long[] StandardHandles { get; private set; }
        internal SecurityIdentifier Package { get { return new SecurityIdentifier(sid); } }

        internal WindowsIsolation(string name)
        {
            profile = name;
            Native.Check(unchecked((uint)DeriveAppContainerSidFromAppContainerName(profile, out sid)), "derive_package_sid");
        }
        Guid Key(string label)
        {
            using (var hash = SHA256.Create())
            {
                byte[] bytes = new byte[16]; Array.Copy(hash.ComputeHash(Encoding.UTF8.GetBytes(profile + ":" + label)), bytes, 16);
                return new Guid(bytes);
            }
        }
        internal Dictionary<string, object> ResourceInventory()
        {
            var filters = new List<string>();
            for (int i = 0; i < Layers.Length; i++) filters.Add(Key("filter-" + i).ToString());
            return new Dictionary<string, object> { {"profile", profile}, {"package_sid", Package.Value},
                {"sublayer_key", Key("sublayer").ToString()}, {"filter_keys", filters} };
        }
        internal void CreateProfile()
        {
            IntPtr created;
            uint result = unchecked((uint)CreateAppContainerProfile(profile, "Maya protected Python startup",
                "Offline startup candidate, no extra capabilities", IntPtr.Zero, 0, out created));
            ProfileCollision = result == 0x800700B7;
            Native.Check(result, "create_container_profile");
            try { if (!new SecurityIdentifier(created).Equals(Package)) throw new StartupFailure("created_package_sid_mismatch"); }
            finally { FreeSid(created); }
        }
        void Engine()
        {
            if (engine == IntPtr.Zero) Native.Check(FwpmEngineOpen0(IntPtr.Zero, 10, IntPtr.Zero, IntPtr.Zero, out engine), "wfp_open");
        }
        Filter Expected(int index, IntPtr condition)
        {
            return new Filter { key = Key("filter-" + index), layer = Layers[index], sublayer = Key("sublayer"), flags = 1,
                count = 1, conditions = condition, action = new FilterAction { type = 0x1001 } };
        }
        internal void ProvisionNetwork()
        {
            Engine(); IntPtr descriptor = IntPtr.Zero, condition = IntPtr.Zero, name = IntPtr.Zero;
            try
            {
                uint size;
                Native.Require(Native.ConvertStringSecurityDescriptorToSecurityDescriptor("O:BAG:BAD:P(A;;GA;;;SY)(A;;GA;;;BA)",
                    1, out descriptor, out size), "wfp_security_descriptor");
                condition = Marshal.AllocHGlobal(Marshal.SizeOf(typeof(Condition)));
                Marshal.StructureToPtr(new Condition { key = PackageCondition, match = 0,
                    value = new Value { type = 13, data = new Scalar { pointer = sid } } }, condition, false);
                name = Marshal.StringToHGlobalUni("Maya protected Python - deny all network");
                Native.Check(FwpmTransactionBegin0(engine, 0), "wfp_begin");
                try
                {
                    var layer = new Sublayer { key = Key("sublayer"), flags = 1, weight = 65535, display = new Display { name = name } };
                    Native.Check(FwpmSubLayerAdd0(engine, ref layer, descriptor), "wfp_add_sublayer");
                    for (int i = 0; i < Layers.Length; i++)
                    {
                        var filter = Expected(i, condition); filter.display.name = name; ulong id;
                        Native.Check(FwpmFilterAdd0(engine, ref filter, descriptor, out id), "wfp_add_filter");
                    }
                    Native.Check(FwpmTransactionCommit0(engine), "wfp_commit");
                }
                catch { FwpmTransactionAbort0(engine); throw; }
                for (int i = 0; i < Layers.Length; i++) if (!VerifyFilter(i)) throw new StartupFailure("network_filter_missing");
            }
            finally
            {
                if (descriptor != IntPtr.Zero) Native.LocalFree(descriptor);
                if (condition != IntPtr.Zero) Marshal.FreeHGlobal(condition);
                if (name != IntPtr.Zero) Marshal.FreeHGlobal(name);
            }
        }
        internal Dictionary<ulong, int> VerifiedNetworkIds()
        {
            var ids = new Dictionary<ulong, int>();
            for (int i = 0; i < Layers.Length; i++)
            {
                if (!VerifyFilter(i)) throw new StartupFailure("network_filter_missing");
                Guid key = Key("filter-" + i); IntPtr memory;
                Native.Check(FwpmFilterGetByKey0(engine, ref key, out memory), "network_id_read");
                try
                {
                    var got = (Filter)Marshal.PtrToStructure(memory, typeof(Filter));
                    if (got.id == 0 || got.key != key) throw new StartupFailure("network_id_mismatch");
                    ids.Add(got.id, i);
                }
                finally { FwpmFreeMemory0(ref memory); }
            }
            return ids;
        }
        internal static Guid NetworkLayer(int index) { return Layers[index]; }
        internal Guid NetworkFilterKey(int index) { return Key("filter-" + index); }
        bool VerifyFilter(int index)
        {
            Guid key = Key("filter-" + index); IntPtr memory;
            uint code = FwpmFilterGetByKey0(engine, ref key, out memory);
            if (code == 0x80320003) return false;
            Native.Check(code, "network_filter_read");
            try
            {
                var got = (Filter)Marshal.PtrToStructure(memory, typeof(Filter));
                if (got.key != key || got.layer != Layers[index] || got.sublayer != Key("sublayer") ||
                    (got.flags & ~0x40u) != 1 || got.action.type != 0x1001 || got.provider != IntPtr.Zero ||
                    got.count != 1 || got.conditions == IntPtr.Zero || got.weight.type != 0)
                    throw new StartupFailure("network_filter_definition_mismatch");
                var condition = (Condition)Marshal.PtrToStructure(got.conditions, typeof(Condition));
                if (condition.key != PackageCondition || condition.match != 0 || condition.value.type != 13 ||
                    !new SecurityIdentifier(condition.value.data.pointer).Equals(Package))
                    throw new StartupFailure("network_filter_package_mismatch");
                return true;
            }
            finally { FwpmFreeMemory0(ref memory); }
        }
        internal void RemoveNetwork()
        {
            Engine();
            for (int i = 0; i < Layers.Length; i++) VerifyFilter(i);
            Native.Check(FwpmTransactionBegin0(engine, 0), "wfp_cleanup_begin");
            try
            {
                for (int i = 0; i < Layers.Length; i++)
                {
                    Guid key = Key("filter-" + i); uint code = FwpmFilterDeleteByKey0(engine, ref key);
                    if (code != 0x80320003) Native.Check(code, "wfp_delete_filter");
                }
                Guid sublayer = Key("sublayer"); uint sub = FwpmSubLayerDeleteByKey0(engine, ref sublayer);
                if (sub != 0x80320007) Native.Check(sub, "wfp_delete_sublayer");
                Native.Check(FwpmTransactionCommit0(engine), "wfp_cleanup_commit");
            }
            catch { FwpmTransactionAbort0(engine); throw; }
            for (int i = 0; i < Layers.Length; i++) if (VerifyFilter(i)) throw new StartupFailure("network_filter_remains");
        }
        internal void DeleteProfile()
        {
            if (ProfileCollision) throw new StartupFailure("profile_collision_requires_review_not_deletion");
            Native.Check(unchecked((uint)DeleteAppContainerProfile(profile)), "delete_container_profile");
        }
        static string Quote(string text)
        {
            if (text.IndexOfAny(new[] { '"', '\r', '\n', '\0' }) >= 0 || text.EndsWith("\\"))
                throw new StartupFailure("invalid_process_argument");
            return "\"" + text + "\"";
        }
        static void Attribute(IntPtr list, int type, IntPtr value, int length)
        {
            Native.Require(UpdateProcThreadAttribute(list, 0, new IntPtr(type), value, new UIntPtr((uint)length),
                IntPtr.Zero, IntPtr.Zero), "process_attribute");
        }
        internal void Start(string directory, string run, SecurityIdentifier user)
        {
            for (int i = 0; i < Layers.Length; i++) if (!VerifyFilter(i)) throw new StartupFailure("network_filter_missing_before_start");
            job = CreateJobObject(IntPtr.Zero, null); Native.Require(job != IntPtr.Zero, "create_job");
            var limits = new JobLimits { basic = new BasicLimits { flags = 0x2000 | 8, activeProcessLimit = 1 } };
            Native.Require(SetInformationJobObject(job, 9, ref limits, (uint)Marshal.SizeOf(typeof(JobLimits))), "set_job_limits");
            IntPtr attributes = IntPtr.Zero, environment = IntPtr.Zero, launchToken = IntPtr.Zero;
            bool ready = false; var allocations = new List<IntPtr>(); var handles = new List<IntPtr>();
            try
            {
                UIntPtr size = UIntPtr.Zero; InitializeProcThreadAttributeList(IntPtr.Zero, 4, 0, ref size);
                attributes = Marshal.AllocHGlobal(checked((int)size.ToUInt64()));
                Native.Require(InitializeProcThreadAttributeList(attributes, 4, 0, ref size), "initialize_process_attributes"); ready = true;
                IntPtr caps = Allocate(allocations, Marshal.SizeOf(typeof(Capabilities)));
                Marshal.StructureToPtr(new Capabilities { sid = sid, capabilities = IntPtr.Zero, count = 0 }, caps, false);
                Attribute(attributes, 0x20009, caps, Marshal.SizeOf(typeof(Capabilities)));
                IntPtr childPolicy = Allocate(allocations, 4); Marshal.WriteInt32(childPolicy, 1); Attribute(attributes, 0x2000E, childPolicy, 4);
                // Atomic job assignment closes the create-before-assign crash window.
                IntPtr jobList = Allocate(allocations, IntPtr.Size); Marshal.WriteIntPtr(jobList, job); Attribute(attributes, 0x2000D, jobList, IntPtr.Size);
                var sa = new SecurityAttributes { size = (uint)Marshal.SizeOf(typeof(SecurityAttributes)), inherit = 1 };
                IntPtr inputRead, inputWrite, outputWrite, errorWrite;
                Native.Require(CreatePipe(out inputRead, out inputWrite, ref sa, 0), "stdin_pipe"); handles.Add(inputRead); handles.Add(inputWrite);
                Native.Require(CreatePipe(out readOutput, out outputWrite, ref sa, 0), "stdout_pipe"); handles.Add(outputWrite);
                Native.Require(CreatePipe(out readError, out errorWrite, ref sa, 0), "stderr_pipe"); handles.Add(errorWrite);
                foreach (IntPtr pipe in new[] { inputWrite, readOutput, readError }) Native.Require(SetHandleInformation(pipe, 1, 0), "private_pipe_handle");
                IntPtr inherited = Allocate(allocations, 3 * IntPtr.Size);
                Marshal.WriteIntPtr(inherited, inputRead); Marshal.WriteIntPtr(inherited, IntPtr.Size, outputWrite); Marshal.WriteIntPtr(inherited, 2 * IntPtr.Size, errorWrite);
                Attribute(attributes, 0x20002, inherited, 3 * IntPtr.Size);
                string runtime = Path.Combine(directory, "runtime"), state = Path.Combine(directory, "state");
                string python = Path.Combine(runtime, "python", "python.exe"), check = Path.Combine(runtime, "containment_check.py");
#if HERMES_MODEL
                check = Path.Combine(runtime, "model_child_entry.py");
#elif HERMES_BRIDGE
                check = Path.Combine(runtime, "bridge_child_entry.py");
#elif HERMES_MEMORY
                check = Path.Combine(runtime, "hermes_memory_check.py");
#elif HERMES_STATE
                check = Path.Combine(runtime, "hermes_state_check.py");
#elif HERMES_CONSTRUCTION
                check = Path.Combine(runtime, "hermes_construction_check.py");
#elif HERMES_IMPORT
                check = Path.Combine(runtime, "hermes_import_check.py");
#endif
                StandardHandles = new[] { inputRead.ToInt64(), outputWrite.ToInt64(), errorWrite.ToInt64() };
                string system = Environment.GetFolderPath(Environment.SpecialFolder.Windows);
                string env = "HERMES_HOME=" + state + "\0LOCALAPPDATA=" + state + "\0PATH=" + Path.Combine(runtime, "python") + ";" + Environment.SystemDirectory +
                    "\0SYSTEMROOT=" + system + "\0TEMP=" + state + "\0TMP=" + state + "\0USERPROFILE=" + state + "\0WINDIR=" + system + "\0\0";
#if HERMES_IMPORT
                env = "HERMES_DISABLE_LAZY_INSTALLS=1\0" + env;
#endif
                environment = Marshal.StringToHGlobalUni(env);
                var startup = new StartupEx { startup = new Startup { size = (uint)Marshal.SizeOf(typeof(StartupEx)), flags = 0x100,
                    input = inputRead, output = outputWrite, error = errorWrite }, attributes = attributes };
                launchToken = CreateReducedLaunchToken(user);
                ReducedLaunchTokenVerified = true;
                Native.Require(CreateProcessAsUserW(launchToken, python, new StringBuilder(Quote(python) + " -I -S -B " + Quote(check) + " " + run),
                    IntPtr.Zero, IntPtr.Zero, true, LaunchCreationFlags, environment, state, ref startup, out child), "create_suspended_python");
                TokenCheck(child.process, user);
#if HERMES_BRIDGE
                BridgeInput = inputWrite; handles.Remove(inputWrite);
#endif
            }
            finally
            {
                if (launchToken != IntPtr.Zero) Native.CloseHandle(launchToken);
                foreach (IntPtr handle in handles) Native.CloseHandle(handle);
                if (ready) DeleteProcThreadAttributeList(attributes);
                if (attributes != IntPtr.Zero) Marshal.FreeHGlobal(attributes);
                foreach (IntPtr memory in allocations) Marshal.FreeHGlobal(memory);
                if (environment != IntPtr.Zero) Marshal.FreeHGlobal(environment);
            }
        }
        static IntPtr Allocate(List<IntPtr> owned, int size)
        { IntPtr value = Marshal.AllocHGlobal(size); owned.Add(value); return value; }

        static IntPtr CreateReducedLaunchToken(SecurityIdentifier user)
        {
            IntPtr original = IntPtr.Zero, reduced = IntPtr.Zero, admin = IntPtr.Zero, label = IntPtr.Zero;
            try
            {
                // Modify only a new token, never the elevated setup host or account.
                Native.Require(OpenProcessToken(new IntPtr(-1), 0x8B, out original), "open_launch_host_token");
                uint session = ReadLaunchScalar(original, 12, GetTokenInformation);
                var administrators = new SecurityIdentifier("S-1-5-32-544");
                byte[] bytes = new byte[administrators.BinaryLength]; administrators.GetBinaryForm(bytes, 0);
                admin = Marshal.AllocHGlobal(bytes.Length); Marshal.Copy(bytes, 0, admin, bytes.Length);
                var disabled = new SidAttributes { sid = admin };
                // DISABLE_MAX_PRIVILEGE | LUA_TOKEN. Never SANDBOX_INERT or WRITE_RESTRICTED.
                Native.Require(CreateRestrictedToken(original, 0x1 | 0x4, 1, ref disabled, 0, IntPtr.Zero,
                    0, IntPtr.Zero, out reduced), "create_reduced_launch_token");
                Native.Require(reduced != IntPtr.Zero, "reduced_launch_token_missing");
                Native.Require(SetHandleInformation(reduced, 1, 0), "private_launch_token_handle");
                var medium = new SecurityIdentifier("S-1-16-8192");
                int header = Marshal.SizeOf(typeof(SidAttributes));
                label = Marshal.AllocHGlobal(header + medium.BinaryLength);
                byte[] mediumBytes = new byte[medium.BinaryLength]; medium.GetBinaryForm(mediumBytes, 0);
                Marshal.Copy(mediumBytes, 0, IntPtr.Add(label, header), mediumBytes.Length);
                Marshal.StructureToPtr(new SidAttributes { sid = IntPtr.Add(label, header), attributes = 0x20 }, label, false);
                Native.Require(SetTokenInformation(reduced, 25, label, (uint)(header + mediumBytes.Length)), "lower_launch_token_integrity");
                long notify;
                Native.Require(LookupPrivilegeValueW(null, "SeChangeNotifyPrivilege", out notify), "lookup_launch_traverse_privilege");
                VerifyReducedLaunchToken(reduced, user, session, notify, GetTokenInformation);
                IntPtr result = reduced; reduced = IntPtr.Zero; return result;
            }
            finally
            {
                if (label != IntPtr.Zero) Marshal.FreeHGlobal(label);
                if (admin != IntPtr.Zero) Marshal.FreeHGlobal(admin);
                if (reduced != IntPtr.Zero) Native.CloseHandle(reduced);
                if (original != IntPtr.Zero) Native.CloseHandle(original);
            }
        }

        internal static uint ReadLaunchScalar(IntPtr token, int type, TokenInformationQuery query)
        {
            IntPtr memory = Marshal.AllocHGlobal(4);
            try
            {
                uint needed;
                Native.Require(query(token, type, memory, 4, out needed), "read_launch_token_" + type);
                if (needed != 4) throw new StartupFailure("launch_token_scalar_size_mismatch");
                return unchecked((uint)Marshal.ReadInt32(memory));
            }
            finally { Marshal.FreeHGlobal(memory); }
        }
        static void LaunchScalar(IntPtr token, int type, uint expected, string name, TokenInformationQuery query)
        {
            uint value = ReadLaunchScalar(token, type, query);
            if (value != expected) throw new StartupFailure("launch_token_" + name + "_mismatch",
                new TokenCheckFailure("launch_" + name, type, expected, value));
        }
        static uint ReadLaunchData(IntPtr token, int type, IntPtr memory, uint minimum, TokenInformationQuery query)
        {
            uint needed;
            Native.Require(query(token, type, memory, 65536, out needed), "read_launch_token_" + type);
            if (needed < minimum || needed > 65536) throw new StartupFailure("launch_token_buffer_size");
            return needed;
        }
        static SecurityIdentifier LaunchSid(IntPtr memory, uint length, int offset, int minimumOffset)
        {
            long relative = Marshal.ReadIntPtr(memory, offset).ToInt64() - memory.ToInt64();
            if (relative < minimumOffset || relative > length - 8) throw new StartupFailure("launch_token_sid_bounds");
            IntPtr pointer = IntPtr.Add(memory, (int)relative);
            int size = 8 + 4 * Marshal.ReadByte(pointer, 1);
            if (Marshal.ReadByte(pointer) != 1 || size > 68 || relative + size > length)
                throw new StartupFailure("launch_token_sid_size");
            byte[] bytes = new byte[size]; Marshal.Copy(pointer, bytes, 0, size);
            return new SecurityIdentifier(bytes, 0);
        }
        internal static void VerifyReducedLaunchToken(IntPtr token, SecurityIdentifier user, uint session, long notify, TokenInformationQuery query)
        {
            if (token == IntPtr.Zero) throw new StartupFailure("reduced_launch_token_missing");
            LaunchScalar(token, 8, 1, "primary_type", query);
            LaunchScalar(token, 12, session, "session", query);
            LaunchScalar(token, 20, 0, "is_elevated", query);
            LaunchScalar(token, 15, 0, "sandbox_inert", query);
            LaunchScalar(token, 26, 0, "ui_access", query);
            LaunchScalar(token, 29, 0, "is_appcontainer", query);
            IntPtr memory = Marshal.AllocHGlobal(65536);
            try
            {
                uint length = ReadLaunchData(token, 1, memory, 16, query);
                if (!LaunchSid(memory, length, 0, 16).Equals(user)) throw new StartupFailure("launch_token_user_mismatch");
                length = ReadLaunchData(token, 25, memory, 16, query);
                if (LaunchSid(memory, length, 0, 16).Value != "S-1-16-8192" || (Marshal.ReadInt32(memory, 8) & 0x20) == 0)
                    throw new StartupFailure("launch_token_integrity_mismatch");
                length = ReadLaunchData(token, 2, memory, 8, query);
                uint groups = unchecked((uint)Marshal.ReadInt32(memory));
                if (groups > (length - 8) / 16) throw new StartupFailure("launch_token_group_bounds");
                bool adminDenied = false;
                for (int i = 0; i < groups; i++)
                {
                    int offset = 8 + i * 16;
                    if (LaunchSid(memory, length, offset, checked(8 + (int)groups * 16)).Value != "S-1-5-32-544") continue;
                    uint flags = unchecked((uint)Marshal.ReadInt32(memory, offset + 8));
                    if ((flags & (4 | 2 | 0x10)) != 0x10) throw new StartupFailure("launch_token_admin_not_deny_only");
                    adminDenied = true;
                }
                if (!adminDenied) throw new StartupFailure("launch_token_admin_deny_only_missing");
                length = ReadLaunchData(token, 3, memory, 4, query);
                uint privileges = unchecked((uint)Marshal.ReadInt32(memory));
                if (privileges > 1 || privileges > (length - 4) / 12) throw new StartupFailure("launch_token_privilege_count");
                if (privileges == 1 && (Marshal.ReadInt64(memory, 4) != notify || (unchecked((uint)Marshal.ReadInt32(memory, 12)) & ~3u) != 0))
                    throw new StartupFailure("launch_token_privilege_mismatch");
            }
            finally { Marshal.FreeHGlobal(memory); }
        }
        bool AccessProbe(IntPtr token, string grant)
        {
            IntPtr descriptor = IntPtr.Zero, privileges = Marshal.AllocHGlobal(256);
            try
            {
                uint size;
                string text = "O:BAG:BAD:P(A;;0x1;;;" + WindowsIdentity.GetCurrent().User.Value + ")";
                if (grant != null) text += "(A;;0x1;;;" + grant + ")";
                Native.Require(Native.ConvertStringSecurityDescriptorToSecurityDescriptor(text, 1, out descriptor, out size), "token_probe_descriptor");
                var mapping = new GenericMapping { read = 1, write = 2, execute = 4, all = 7 };
                uint length = 256, granted; bool allowed;
                Native.Require(AccessCheck(descriptor, token, 1, ref mapping, privileges, ref length, out granted, out allowed), "token_access_probe");
                if (length > 256 || granted != (allowed ? 1u : 0u)) throw new StartupFailure("token_access_probe_result");
                return allowed;
            }
            finally { if (descriptor != IntPtr.Zero) Native.LocalFree(descriptor); Marshal.FreeHGlobal(privileges); }
        }
        internal delegate bool TokenInformationQuery(IntPtr token, int type, IntPtr data, uint length, out uint required);

        internal static void RequireTokenScalar(int type, uint observed)
        {
            string name, code; uint expected;
            switch (type)
            {
                case 29: name = "is_appcontainer"; expected = 1; code = "child_token_is_appcontainer_mismatch"; break;
                case 30: name = "capability_count"; expected = 0; code = "child_token_capability_count_mismatch"; break;
                case 20: name = "is_elevated"; expected = 0; code = "child_token_elevation_mismatch"; break;
                default: throw new StartupFailure("unsupported_scalar_token_check");
            }
            if (observed != expected)
                throw new StartupFailure(code, new TokenCheckFailure(name, type, expected, observed));
        }

        internal static void RequireNotElevated(IntPtr token, TokenInformationQuery query)
        {
            // TOKEN_ELEVATION contains one DWORD; this query needs its exact size.
            const uint length = sizeof(uint);
            IntPtr memory = Marshal.AllocHGlobal((int)length);
            try
            {
                uint required;
                Native.Require(query(token, 20, memory, length, out required), "read_child_token_20");
                if (required != length) throw new StartupFailure("child_token_elevation_size_mismatch");
                RequireTokenScalar(20, unchecked((uint)Marshal.ReadInt32(memory)));
            }
            finally { Marshal.FreeHGlobal(memory); }
        }

        internal static void RequireAppContainerAccessControls(bool packageAllowed, bool noGrantAllowed,
            bool allApplicationPackagesAllowed, bool wrongPackageAllowed)
        {
            if (!packageAllowed || noGrantAllowed || !allApplicationPackagesAllowed || wrongPackageAllowed)
                throw new StartupFailure("appcontainer_access_controls_failed");
        }

        void TokenCheck(IntPtr process, SecurityIdentifier user)
        {
            IntPtr token; Native.Require(OpenProcessToken(process, 10, out token), "open_child_token");
            IntPtr memory = Marshal.AllocHGlobal(4096), duplicate = IntPtr.Zero;
            try
            {
                uint needed;
                foreach (int type in new[] { 29, 31, 25, 1, 30 })
                {
                    Native.Require(GetTokenInformation(token, type, memory, 4096, out needed), "read_child_token_" + type);
                    if (needed > 4096) throw new StartupFailure("child_token_buffer_size");
                    if (type == 29 || type == 30) RequireTokenScalar(type, unchecked((uint)Marshal.ReadInt32(memory)));
                    if (type == 31 && !new SecurityIdentifier(Marshal.ReadIntPtr(memory)).Equals(Package) ||
                        type == 25 && new SecurityIdentifier(Marshal.ReadIntPtr(memory)).Value != "S-1-16-4096" ||
                        type == 1 && !new SecurityIdentifier(Marshal.ReadIntPtr(memory)).Equals(user))
                        throw new StartupFailure("child_token_identity_mismatch");
                }
                RequireNotElevated(token, GetTokenInformation);
                Native.Require(DuplicateToken(token, 2, out duplicate), "duplicate_child_token");
                Native.Require(GetTokenInformation(token, 2, memory, 4096, out needed), "read_child_groups");
                int count = Marshal.ReadInt32(memory);
                if (count < 0 || count > (4096 - 8) / 16) throw new StartupFailure("child_group_buffer_size");
                for (int i = 0; i < count; i++)
                {
                    IntPtr group = IntPtr.Add(memory, 8 + i * 16);
                    if (new SecurityIdentifier(Marshal.ReadIntPtr(group)).Value == "S-1-5-32-544" &&
                        (Marshal.ReadInt32(group, IntPtr.Size) & 4) != 0)
                        throw new StartupFailure("child_admin_group_enabled");
                }
                RequireAppContainerAccessControls(AccessProbe(duplicate, Package.Value), AccessProbe(duplicate, null),
                    AccessProbe(duplicate, "S-1-15-2-1"),
                    AccessProbe(duplicate, "S-1-15-2-987654321-987654321-987654321-987654321-987654321-987654321-987654321"));
            }
            finally
            {
                Marshal.FreeHGlobal(memory);
                if (duplicate != IntPtr.Zero) Native.CloseHandle(duplicate);
                Native.CloseHandle(token);
            }
        }
        internal uint ResumeAndWait()
        {
            outputThread = new Thread(delegate() { try { Stdout = Encoding.ASCII.GetString(ReadBounded(readOutput)); } catch { captureFailed = true; } });
            errorThread = new Thread(delegate() { try { StderrBytes = ReadBounded(readError).Length; } catch { captureFailed = true; } });
            outputThread.IsBackground = errorThread.IsBackground = true; outputThread.Start(); errorThread.Start();
            if (ResumeThread(child.thread) != 1) throw new StartupFailure("resume_suspended_python_failed");
            Resumed = true;
            uint wait = WaitForSingleObject(child.process, 30000);
            if (wait == 258) throw new StartupFailure("python_startup_timeout");
            if (wait != 0) throw new StartupFailure("python_wait_failed");
            uint exit; Native.Require(GetExitCodeProcess(child.process, out exit), "python_exit_code"); ExitCode = exit;
            if (!outputThread.Join(5000) || !errorThread.Join(5000) || captureFailed) throw new StartupFailure("python_output_capture_failed");
            return exit;
        }
        static byte[] ReadBounded(IntPtr handle)
        {
            using (var stream = new FileStream(new Microsoft.Win32.SafeHandles.SafeFileHandle(handle, false), FileAccess.Read))
            using (var result = new MemoryStream())
            {
                byte[] buffer = new byte[1024]; bool overflow = false; int count;
                while ((count = stream.Read(buffer, 0, buffer.Length)) > 0)
                    if (result.Length + count <= 4096) result.Write(buffer, 0, count); else overflow = true;
                if (overflow) throw new StartupFailure("child_output_limit_exceeded");
                return result.ToArray();
            }
        }
        internal void Stop()
        {
            if (job != IntPtr.Zero)
            {
                Native.Require(TerminateJobObject(job, 1), "terminate_runtime_job");
                bool empty = false;
                for (int i = 0; i < 100; i++)
                {
                    JobAccounting data;
                    Native.Require(QueryInformationJobObject(job, 1, out data, (uint)Marshal.SizeOf(typeof(JobAccounting)), IntPtr.Zero), "read_runtime_job");
                    if (data.activeProcesses == 0) { empty = true; break; }
                    Thread.Sleep(50);
                }
                if (!empty) throw new StartupFailure("runtime_job_stop_uncertain");
            }
            if (outputThread != null && outputThread.IsAlive && !outputThread.Join(5000) ||
                errorThread != null && errorThread.IsAlive && !errorThread.Join(5000))
                throw new StartupFailure("runtime_pipe_cleanup_uncertain");
        }
        public void Dispose()
        {
            // KILL_ON_JOB_CLOSE remains the last-resort lifecycle boundary.
            if (job != IntPtr.Zero) { Native.CloseHandle(job); job = IntPtr.Zero; }
            foreach (IntPtr handle in new[] { child.thread, child.process, readOutput, readError, BridgeInput }) if (handle != IntPtr.Zero) Native.CloseHandle(handle);
            if (engine != IntPtr.Zero) { FwpmEngineClose0(engine); engine = IntPtr.Zero; }
            if (sid != IntPtr.Zero) { FreeSid(sid); sid = IntPtr.Zero; }
        }
    }
}
