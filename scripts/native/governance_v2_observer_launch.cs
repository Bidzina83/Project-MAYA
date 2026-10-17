// Native lab backend only. No Main, provisioning, retry, fallback or automatic reconnect.
using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Management;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using Microsoft.Win32;

namespace Maya.GateA.Observation
{
    public sealed class NativeSupervisionBackend : ISupervisionBackend
    {
        const string ManifestHash = "17ad01535d3a70da86cc264b011cbb22528fdee5bf4b29203d9e7ed4daaeda60";
        const string HelperHash = "e72f101bea8222d14e908c2f39e7fecdca122b2f13b2abe9d5293490b7856f63";
        const string ReferenceHash = "812ab69ebcc45a241131b79b3c6c26319aaec802377d10ea733c5f70fcb36606";
        readonly Func<bool> reviewedVmExecutionPermission;
        readonly Stopwatch clock = new Stopwatch();
        readonly Dictionary<uint,KnownMember> known = new Dictionary<uint,KnownMember>();
        readonly List<IntPtr> pipes = new List<IntPtr>();
        readonly MemoryStream stdout = new MemoryStream();
        readonly Dictionary<string,string> inventory = new Dictionary<string,string>(StringComparer.OrdinalIgnoreCase);
        ObserverJob job;
        LaunchNative.ProcessInfo launcher;
        NativeProcessReader launcherReader;
        LaunchPlan plan;
        IntPtr input, output, error;
        bool attached, resumed, admitted, disposed;
        Thread watchdog;
        volatile bool stopWatchdog, watchdogFailed;
        int errorBytes;
        string[] expectedCapabilities;

        sealed class CommandProbe
        {
            public volatile bool Done;
            public bool Matched;
            public CommandProbe(uint pid, string expected)
            {
                Task.Factory.StartNew(delegate {
                    try
                    {
                        var options = new EnumerationOptions { ReturnImmediately = false, Timeout = TimeSpan.FromSeconds(1) };
                        using (var search = new ManagementObjectSearcher("root\\cimv2",
                            "SELECT CommandLine FROM Win32_Process WHERE ProcessId=" + pid,
                            options))
                        using (var rows = search.Get())
                        {
                            int count = 0;
                            foreach (ManagementObject row in rows)
                                using (row) { count++; Matched = String.Equals(row["CommandLine"] as string, expected, StringComparison.Ordinal); }
                            if (count != 1) Matched = false;
                        }
                    }
                    catch (Exception) { Matched = false; }
                    finally { Done = true; }
                });
            }
        }
        sealed class KnownMember
        {
            public NativeProcessReader Reader;
            public ProcessIdentity Identity;
            public uint Parent;
            public TokenEvidence Token;
            public EvidenceResult Evidence;
            public CommandProbe Command;
        }

        // The callback belongs to the future trusted VM host, not a child/request field.
        // This is an operational approval gate, not a security boundary against an administrator.
        public NativeSupervisionBackend(Func<bool> executionPermission)
        { reviewedVmExecutionPermission = executionPermission; }

        public long Elapsed { get { return clock.ElapsedMilliseconds; } }
        public ProcessIdentity LauncherIdentity { get { return launcherReader.Identity(); } }
        public string[] ExpectedCapabilities { get { return (string[])expectedCapabilities.Clone(); } }
        public bool LauncherExited { get { return launcherReader.Exited(); } }
        public uint LauncherExitCode { get { return launcherReader.ExitCode(); } }
        public uint TotalProcesses { get { return job.TotalProcesses(); } }
        public JobPopulation Population
        {
            get { var counts = job.Population(); return new JobPopulation { Total = counts.totalProcesses,Active = counts.activeProcesses }; }
        }
        public bool Empty { get { return job.Empty(); } }
        public bool AuxiliaryWorkComplete
        {
            get { foreach (var item in known.Values) if (item.Command != null && !item.Command.Done) return false; return true; }
        }
        static string Hash(string path)
        {
            Plain(path);
            using (var sha = SHA256.Create()) using (var file = File.OpenRead(path))
                return BitConverter.ToString(sha.ComputeHash(file)).Replace("-", "").ToLowerInvariant();
        }
        static void Plain(string path)
        {
            for (string cursor = Path.GetFullPath(path); !String.IsNullOrEmpty(cursor); cursor = Path.GetDirectoryName(cursor))
                if ((File.GetAttributes(cursor) & FileAttributes.ReparsePoint) != 0)
                    throw new ObservationFault("observer.input_invalid");
        }
        void VerifyInputs(bool first)
        {
            string manifest = Path.Combine(plan.Root,"reproduction-manifest.json");
            if (Hash(manifest) != ManifestHash || Hash(Path.Combine(plan.Root,@".codex-build\governance-v2-native-tools\GateANative.exe")) != HelperHash ||
                Hash(Path.Combine(plan.Root,@".codex-build\governance-v2-reference-tools\LaunchAppContainer.exe")) != ReferenceHash)
                throw new ObservationFault("observer.input_invalid");
            if (first)
            {
                var json = new JavaScriptSerializer { MaxJsonLength = 1024 * 1024 };
                var data = json.Deserialize<Dictionary<string,object>>(File.ReadAllText(manifest));
                if ((string)data["profile"] != "26h2") throw new ObservationFault("observer.input_invalid");
                foreach (Dictionary<string,object> row in (IEnumerable)data["files"])
                {
                    string relative = (string)row["path"];
                    if (Path.IsPathRooted(relative) || relative.Contains("..") || relative.Contains(":"))
                        throw new ObservationFault("observer.input_invalid");
                    string path = Path.GetFullPath(Path.Combine(plan.Root,relative.Replace('/',Path.DirectorySeparatorChar)));
                    if (!path.StartsWith(plan.Root + "\\",StringComparison.OrdinalIgnoreCase) || inventory.ContainsKey(path))
                        throw new ObservationFault("observer.input_invalid");
                    inventory.Add(path,(string)row["sha256"]);
                }
                if (!inventory.ContainsKey(plan.Python) || !inventory.ContainsKey(plan.Worker))
                    throw new ObservationFault("observer.input_invalid");
            }
            foreach (var pair in inventory) if (Hash(pair.Key) != pair.Value) throw new ObservationFault("observer.input_invalid");
            var directories = new Stack<string>(); directories.Push(Path.Combine(plan.Stage,"runtime"));
            int entries = 0;
            while (directories.Count != 0)
            {
                string directory = directories.Pop(); Plain(directory);
                foreach (string entry in Directory.EnumerateFileSystemEntries(directory))
                {
                    if (++entries > 65536) throw new ObservationFault("observer.input_invalid");
                    Plain(entry);
                    if (Directory.Exists(entry)) directories.Push(entry);
                    else if (!inventory.ContainsKey(Path.GetFullPath(entry))) throw new ObservationFault("observer.input_invalid");
                }
            }
        }
        void VerifyVm()
        {
            if (reviewedVmExecutionPermission == null || !reviewedVmExecutionPermission() ||
                Environment.OSVersion.Platform != PlatformID.Win32NT || !Environment.Is64BitProcess)
                throw new ObservationFault("observer.execution_not_authorized");
            using (var version = Registry.LocalMachine.OpenSubKey(@"SOFTWARE\Microsoft\Windows NT\CurrentVersion"))
            using (var bios = Registry.LocalMachine.OpenSubKey(@"HARDWARE\DESCRIPTION\System\BIOS"))
            using (var identity = WindowsIdentity.GetCurrent())
            {
                if (version == null || bios == null || (string)version.GetValue("CurrentBuildNumber") != "26300" ||
                    Convert.ToInt32(version.GetValue("UBR")) != 9711 || (string)version.GetValue("EditionID") != "Professional" ||
                    (string)bios.GetValue("SystemProductName") != "Virtual Machine" ||
                    !plan.User.StartsWith("S-1-5-21-",StringComparison.Ordinal) || identity.User.Value != plan.User ||
                    !identity.Name.StartsWith(Environment.MachineName + "\\",StringComparison.OrdinalIgnoreCase) ||
                    !new WindowsPrincipal(identity).IsInRole(WindowsBuiltInRole.Administrator))
                    throw new ObservationFault("observer.vm_mismatch");
            }
            if (new SecurityIdentifier(plan.Package).Value != plan.Package ||
                new SecurityIdentifier(plan.User).Value != plan.User)
                throw new ObservationFault("observer.input_invalid");
            IntPtr sid;
            int result = LaunchNative.DeriveAppContainerSidFromAppContainerName(plan.Moniker,out sid);
            if (result != 0) throw new ObservationFault("observer.input_invalid");
            try { if (new SecurityIdentifier(sid).Value != plan.Package) throw new ObservationFault("observer.input_invalid"); }
            finally { if (LaunchNative.FreeSid(sid) != IntPtr.Zero) throw new ObservationFault("observer.handle_cleanup_failed"); }
        }
        static string[] DeriveCapabilities(string[] names)
        {
            var result = new List<string>();
            foreach (string name in names)
            {
                IntPtr groups = IntPtr.Zero, caps = IntPtr.Zero; uint groupCount = 0, capCount = 0;
                try
                {
                    Native.Require(LaunchNative.DeriveCapabilitySidsFromName(name,out groups,out groupCount,out caps,out capCount));
                    if (groupCount > 256 || capCount == 0 || capCount > 256) throw new ObservationFault("observer.buffer_invalid");
                    for (int i = 0; i < capCount; i++) result.Add(new SecurityIdentifier(Marshal.ReadIntPtr(caps,i*IntPtr.Size)).Value);
                }
                finally
                {
                    // Bound unexpected counts before walking returned arrays; retain a failure, not a successful read-back.
                    if (groupCount <= 256) FreeSidArray(groups,groupCount);
                    if (capCount <= 256) FreeSidArray(caps,capCount);
                }
            }
            return result.ToArray();
        }
        static void FreeSidArray(IntPtr array, uint count)
        {
            if (array == IntPtr.Zero) { if (count != 0) throw new ObservationFault("observer.buffer_invalid"); return; }
            bool freed = true;
            for (int i = 0; i < count; i++) freed &= Native.LocalFree(Marshal.ReadIntPtr(array,i*IntPtr.Size)) == IntPtr.Zero;
            freed &= Native.LocalFree(array) == IntPtr.Zero;
            if (!freed) throw new ObservationFault("observer.handle_cleanup_failed");
        }
        public void CreateSuspended(LaunchPlan prepared)
        {
            if (plan != null || disposed) throw new ObservationFault("observer.already_consumed");
            if (!ValidLayout()) throw new ObservationFault("observer.buffer_invalid");
            plan = prepared; VerifyVm(); VerifyInputs(true);
            Plain(plan.State);
            if (Directory.GetFileSystemEntries(plan.State).Length != 0 || File.Exists(Path.Combine(plan.Stage,"child-result.json")))
                throw new ObservationFault("observer.stale_output");
            expectedCapabilities = DeriveCapabilities(plan.CapabilityNames);
            clock.Start();
            job = new ObserverJob();
            IntPtr childInput, childOutput, childError;
            Pipe(out childInput,out input); Pipe(out output,out childOutput); Pipe(out error,out childError);
            foreach (IntPtr handle in new [] { input,output,error }) Native.Require(LaunchNative.SetHandleInformation(handle,1,0));
            IntPtr attributes = IntPtr.Zero, handles = IntPtr.Zero, environment = IntPtr.Zero;
            bool initialized = false;
            try
            {
                UIntPtr bytes = UIntPtr.Zero;
                LaunchNative.InitializeProcThreadAttributeList(IntPtr.Zero,1,0,ref bytes);
                attributes = Marshal.AllocHGlobal(checked((int)bytes.ToUInt64()));
                Native.Require(LaunchNative.InitializeProcThreadAttributeList(attributes,1,0,ref bytes)); initialized = true;
                handles = Marshal.AllocHGlobal(3*IntPtr.Size);
                Marshal.WriteIntPtr(handles,0,childInput); Marshal.WriteIntPtr(handles,IntPtr.Size,childOutput); Marshal.WriteIntPtr(handles,2*IntPtr.Size,childError);
                Native.Require(LaunchNative.UpdateProcThreadAttribute(attributes,0,new IntPtr(0x20002),handles,new UIntPtr((uint)(3*IntPtr.Size)),IntPtr.Zero,IntPtr.Zero));
                var environmentValues = plan.Environment;
                if (!String.Equals(Environment.SystemDirectory,@"C:\Windows\System32",StringComparison.OrdinalIgnoreCase))
                    throw new ObservationFault("observer.vm_mismatch");
                // Use the same native SystemDirectory spelling as the frozen x64 Maya helper.
                environmentValues["PATH"] = Path.GetDirectoryName(plan.Python) + ";" + Environment.SystemDirectory;
                var block = new StringBuilder(); var keys = new List<string>(environmentValues.Keys); keys.Sort(StringComparer.Ordinal);
                foreach (string key in keys) block.Append(key).Append('=').Append(environmentValues[key]).Append('\0');
                block.Append('\0'); environment = Marshal.StringToHGlobalUni(block.ToString());
                var startup = new LaunchNative.StartupEx { startup = new LaunchNative.Startup {
                    size = (uint)Marshal.SizeOf(typeof(LaunchNative.StartupEx)), flags = 0x100,
                    input = childInput, output = childOutput, error = childError }, attributes = attributes };
                Native.Require(LaunchNative.CreateProcessW(plan.Launcher,new StringBuilder(plan.Command),IntPtr.Zero,IntPtr.Zero,true,
                    0x80404,environment,plan.Cwd,ref startup,out launcher));
                ClosePipe(childInput); ClosePipe(childOutput); ClosePipe(childError);
                launcherReader = new NativeProcessReader(launcher.pid,plan.Package);
            }
            finally
            {
                if (initialized) LaunchNative.DeleteProcThreadAttributeList(attributes);
                if (attributes != IntPtr.Zero) Marshal.FreeHGlobal(attributes);
                if (handles != IntPtr.Zero) Marshal.FreeHGlobal(handles);
                if (environment != IntPtr.Zero) Marshal.FreeHGlobal(environment);
            }
        }
        void Pipe(out IntPtr read, out IntPtr write)
        {
            var security = new LaunchNative.SecurityAttributes { size = (uint)Marshal.SizeOf(typeof(LaunchNative.SecurityAttributes)), inherit = 1 };
            bool created = LaunchNative.CreatePipe(out read,out write,ref security,0);
            if (read != IntPtr.Zero) pipes.Add(read);
            if (write != IntPtr.Zero) pipes.Add(write);
            Native.Require(created);
        }
        void ClosePipe(IntPtr handle)
        {
            if (!pipes.Contains(handle)) return;
            if (!Native.CloseHandle(handle)) throw new ObservationFault("observer.handle_cleanup_failed");
            pipes.Remove(handle);
        }
        public void AttachOuterJob()
        {
            if (attached || resumed || launcher.process == IntPtr.Zero) throw new ObservationFault("observer.launch_order");
            job.AttachOwnedSuspendedLauncher(launcher.process); attached = true;
            watchdog = new Thread(delegate() {
                try
                {
                    while (!stopWatchdog && ObservationBudget.At(Elapsed) == DeadlineAction.Observe) Thread.Sleep(10);
                    if (!stopWatchdog) job.RequestTermination();
                }
                catch (Exception) { watchdogFailed = true; }
            });
            watchdog.IsBackground = true;
            watchdog.Start();
        }
        public void ResumeLauncher()
        {
            if (!attached || resumed || ObservationBudget.At(Elapsed) != DeadlineAction.Observe)
                throw new ObservationFault("observer.launch_order");
            Native.Require(LaunchNative.ResumeThread(launcher.thread) == 1); resumed = true;
            if (plan.Case != "A") ClosePipe(input);
        }
        public void AdmitMaya()
        {
            if (plan.Case != "A" || admitted || !resumed || ObservationBudget.At(Elapsed) != DeadlineAction.Observe)
                throw new ObservationFault("observer.admission_order");
            uint written;
            Native.Require(LaunchNative.WriteFile(input,new byte[] { 10 },1,out written,IntPtr.Zero) && written == 1);
            admitted = true; ClosePipe(input);
        }
        void Drain(IntPtr pipe, bool standardError)
        {
            for (int i = 0; i < 16; i++)
            {
                uint available;
                if (!LaunchNative.PeekNamedPipe(pipe,IntPtr.Zero,0,IntPtr.Zero,out available,IntPtr.Zero))
                { if (Marshal.GetLastWin32Error() == 109) return; throw new ObservationFault("observer.pipe_failed"); }
                if (available == 0) return;
                var buffer = new byte[Math.Min(4096u,available)]; uint read;
                Native.Require(LaunchNative.ReadFile(pipe,buffer,(uint)buffer.Length,out read,IntPtr.Zero));
                if (read == 0) throw new ObservationFault("observer.pipe_failed");
                if (standardError) errorBytes += (int)read; else stdout.Write(buffer,0,(int)read);
                if (stdout.Length > 65536 || errorBytes > 65536) throw new ObservationFault("observer.output_limit");
            }
        }
        static Dictionary<uint,uint> Parents()
        {
            var result = new Dictionary<uint,uint>(); IntPtr snapshot = LaunchNative.CreateToolhelp32Snapshot(2,0);
            Native.Require(snapshot != new IntPtr(-1));
            try
            {
                var entry = new LaunchNative.ProcessEntry { size = (uint)Marshal.SizeOf(typeof(LaunchNative.ProcessEntry)) };
                bool more = LaunchNative.Process32First(snapshot,ref entry);
                while (more)
                {
                    if (result.Count >= 65536) throw new ObservationFault("observer.buffer_invalid");
                    result.Add(entry.pid,entry.parent); more = LaunchNative.Process32Next(snapshot,ref entry);
                }
                if (Marshal.GetLastWin32Error() != 18) throw new ObservationFault("observer.native_read_failed");
            }
            finally { if (!Native.CloseHandle(snapshot)) throw new ObservationFault("observer.handle_cleanup_failed"); }
            return result;
        }
        public MemberSample[] Poll()
        {
            Drain(output,false); Drain(error,true);
            Dictionary<uint,uint> parents = Parents();
            foreach (uint pid in job.Members())
            {
                if (pid == launcher.pid || known.ContainsKey(pid)) continue;
                var reader = new NativeProcessReader(pid,plan.Package);
                try
                {
                    var identity = reader.Identity(); uint parent;
                    if (!parents.TryGetValue(pid,out parent) || parent != launcher.pid || !job.Contains(reader.Handle) ||
                        identity.Created < LauncherIdentity.Created || !String.Equals(identity.Image,plan.Python,StringComparison.OrdinalIgnoreCase))
                        throw new ObservationFault("observer.ancestry");
                    var expected = new ExpectedProcess { Identity = identity,User = plan.User,Package = plan.Package,Capabilities = expectedCapabilities };
                    if (reader.Exited())
                    {
                        known.Add(pid,new KnownMember { Reader = reader,Identity = identity,Parent = parent,
                            Evidence = new EvidenceResult { ExitObserved = true,ChildExitCode = reader.ExitCode(),Reason = "observer.exited_before_token" } });
                        reader = null; continue;
                    }
                    TokenEvidence token = reader.Token();
                    var cached = new CachedTokenReader(reader,token);
                    EvidenceResult evidence = token.AapAllowed ? ObservationPolicy.CaptureOrdinaryControl(cached,expected) : ObservationPolicy.Capture(cached,expected);
                    var item = new KnownMember { Reader = reader,Identity = identity,Parent = parent,Token = token,Evidence = evidence };
                    known.Add(pid,item); reader = null;
                    if (!token.AapAllowed && evidence.ProfileMatched) item.Command = new CommandProbe(pid,plan.ChildCommand);
                }
                finally { if (reader != null) reader.Dispose(); }
            }
            var samples = new List<MemberSample>();
            foreach (var item in known.Values)
            {
                if (!item.Reader.Exited() && !job.Contains(item.Reader.Handle)) throw new ObservationFault("observer.ancestry");
                if (item.Token != null)
                    item.Evidence = ObservationPolicy.FinishExit(item.Reader,new ExpectedProcess { Identity = item.Identity,User = plan.User,Package = plan.Package,Capabilities = expectedCapabilities },item.Evidence);
                samples.Add(new MemberSample { Identity = item.Reader.Identity(),ParentPid = item.Parent,InJob = true,
                    Token = item.Token,Evidence = item.Evidence,Exited = item.Reader.Exited(),
                    CommandReadComplete = item.Command != null && item.Command.Done,CommandMatched = item.Command != null && item.Command.Done && item.Command.Matched });
            }
            return samples.ToArray();
        }
        public bool FreshBeacon
        {
            get
            {
                string path = Path.Combine(plan.State,"python-startup.json");
                if (!File.Exists(path)) return false; Plain(path);
                byte[] expected = Encoding.ASCII.GetBytes("{\"schema\":\"maya.python_entry.v1\",\"status\":\"python_entered\",\"production_qualified\":false}\n");
                using (var stream = File.OpenRead(path))
                {
                    if (stream.Length != expected.Length) throw new ObservationFault("observer.beacon_invalid");
                    foreach (byte value in expected) if (stream.ReadByte() != value) throw new ObservationFault("observer.beacon_invalid");
                    if (stream.ReadByte() != -1) throw new ObservationFault("observer.beacon_invalid");
                }
                return true;
            }
        }
        public bool InputsUnchanged { get { VerifyInputs(false); return true; } }
        public bool MayaReturnMatches(uint childCode)
        {
            Drain(output,false); Drain(error,true);
            return ObserverProtocol.MayaReturnMatches(stdout.ToArray(),childCode);
        }
        public void Pause() { Thread.Sleep(10); }
        public static bool ValidLayout()
        {
            return ObservationLayout.ValidX64() && Marshal.SizeOf(typeof(LaunchNative.Startup)) == 104 &&
                Marshal.SizeOf(typeof(LaunchNative.StartupEx)) == 112 && Marshal.SizeOf(typeof(LaunchNative.ProcessInfo)) == 24 &&
                Marshal.SizeOf(typeof(LaunchNative.SecurityAttributes)) == 24 && Marshal.SizeOf(typeof(LaunchNative.ProcessEntry)) == 568;
        }
        public bool TerminateAndConfirm()
        {
            bool terminated = true;
            try
            {
                if (launcher.process != IntPtr.Zero && !attached)
                {
                    Native.Require(LaunchNative.TerminateProcess(launcher.process,1));
                    terminated = Native.WaitForSingleObject(launcher.process,(uint)ObservationBudget.Remaining(Elapsed)) == 0;
                }
                if (job != null) terminated &= job.TerminateAndConfirm(clock);
            }
            finally
            {
                stopWatchdog = true;
                if (watchdog != null && !watchdog.Join(ObservationBudget.Remaining(Elapsed))) terminated = false;
            }
            long auxiliaryDeadline = Math.Min(ObservationBudget.TotalMilliseconds,Elapsed + ObservationBudget.CleanupReserveMilliseconds);
            while (!AuxiliaryWorkComplete && Elapsed < auxiliaryDeadline) Thread.Sleep(10);
            return terminated && !watchdogFailed && AuxiliaryWorkComplete && Elapsed < ObservationBudget.TotalMilliseconds;
        }

        sealed class CachedTokenReader : IProcessEvidenceReader
        {
            readonly NativeProcessReader reader; readonly TokenEvidence token;
            public CachedTokenReader(NativeProcessReader value, TokenEvidence observed) { reader = value; token = observed; }
            public ProcessIdentity Identity() { return reader.Identity(); }
            public TokenEvidence Token() { return token; }
            public bool Exited() { return reader.Exited(); }
            public uint ExitCode() { return reader.ExitCode(); }
        }
        public void Dispose()
        {
            if (disposed) return; disposed = true; bool success = true;
            foreach (var item in known.Values)
            {
                // A stuck PID-based query must not outlive the handle that pins its process identity.
                if (item.Command != null && !item.Command.Done) { success = false; continue; }
                try { item.Reader.Dispose(); } catch (Exception) { success = false; }
            }
            if (launcherReader != null) try { launcherReader.Dispose(); } catch (Exception) { success = false; }
            foreach (IntPtr handle in pipes) success &= Native.CloseHandle(handle); pipes.Clear();
            if (launcher.thread != IntPtr.Zero) success &= Native.CloseHandle(launcher.thread);
            if (launcher.process != IntPtr.Zero) success &= Native.CloseHandle(launcher.process);
            // Never recycle a job handle while the deadline watcher may still be using it.
            if (watchdog != null && watchdog.IsAlive) success = false;
            else if (job != null) try { job.Dispose(); } catch (Exception) { success = false; }
            stdout.Dispose();
            if (!success) throw new ObservationFault("observer.handle_cleanup_failed");
        }
    }

    static class LaunchNative
    {
        [StructLayout(LayoutKind.Sequential)] public struct SecurityAttributes { public uint size; public IntPtr descriptor; public int inherit; }
        [StructLayout(LayoutKind.Sequential)] public struct ProcessInfo { public IntPtr process,thread; public uint pid,tid; }
        [StructLayout(LayoutKind.Sequential,CharSet=CharSet.Unicode)] public struct Startup
        {
            public uint size; public IntPtr reserved,desktop,title; public uint x,y,width,height,xChars,yChars,fill,flags;
            public ushort show,reservedSize; public IntPtr reservedBytes,input,output,error;
        }
        [StructLayout(LayoutKind.Sequential)] public struct StartupEx { public Startup startup; public IntPtr attributes; }
        [StructLayout(LayoutKind.Sequential,CharSet=CharSet.Unicode)] public struct ProcessEntry
        {
            public uint size,usage,pid; public UIntPtr heap; public uint module,threads,parent; public int priority; public uint flags;
            [MarshalAs(UnmanagedType.ByValTStr,SizeConst=260)] public string image;
        }
        [DllImport("userenv.dll",CharSet=CharSet.Unicode,ExactSpelling=true)] public static extern int DeriveAppContainerSidFromAppContainerName(string name,out IntPtr sid);
        [DllImport("advapi32.dll")] public static extern IntPtr FreeSid(IntPtr sid);
        [DllImport("kernelbase.dll",CharSet=CharSet.Unicode,ExactSpelling=true,SetLastError=true)] public static extern bool DeriveCapabilitySidsFromName(string name,out IntPtr groups,out uint groupCount,out IntPtr caps,out uint capCount);
        [DllImport("kernel32.dll",SetLastError=true)] public static extern bool CreatePipe(out IntPtr read,out IntPtr write,ref SecurityAttributes security,uint bytes);
        [DllImport("kernel32.dll",SetLastError=true)] public static extern bool SetHandleInformation(IntPtr handle,uint mask,uint flags);
        [DllImport("kernel32.dll",SetLastError=true)] public static extern bool InitializeProcThreadAttributeList(IntPtr list,int count,uint flags,ref UIntPtr bytes);
        [DllImport("kernel32.dll",SetLastError=true)] public static extern bool UpdateProcThreadAttribute(IntPtr list,uint flags,IntPtr key,IntPtr value,UIntPtr bytes,IntPtr previous,IntPtr returned);
        [DllImport("kernel32.dll")] public static extern void DeleteProcThreadAttributeList(IntPtr list);
        [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] public static extern bool CreateProcessW(string application,StringBuilder command,IntPtr processSecurity,IntPtr threadSecurity,bool inherit,uint flags,IntPtr environment,string cwd,ref StartupEx startup,out ProcessInfo process);
        [DllImport("kernel32.dll",SetLastError=true)] public static extern uint ResumeThread(IntPtr thread);
        [DllImport("kernel32.dll",SetLastError=true)] public static extern bool ReadFile(IntPtr file,byte[] data,uint bytes,out uint read,IntPtr overlapped);
        [DllImport("kernel32.dll",SetLastError=true)] public static extern bool WriteFile(IntPtr file,byte[] data,uint bytes,out uint written,IntPtr overlapped);
        [DllImport("kernel32.dll",SetLastError=true)] public static extern bool PeekNamedPipe(IntPtr pipe,IntPtr data,uint bytes,IntPtr read,out uint available,IntPtr remaining);
        [DllImport("kernel32.dll",SetLastError=true)] public static extern IntPtr CreateToolhelp32Snapshot(uint flags,uint pid);
        [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] public static extern bool Process32First(IntPtr snapshot,ref ProcessEntry entry);
        [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] public static extern bool Process32Next(IntPtr snapshot,ref ProcessEntry entry);
        [DllImport("kernel32.dll",SetLastError=true)] public static extern bool TerminateProcess(IntPtr process,uint code);
    }
}
