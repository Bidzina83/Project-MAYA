using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Text;
using System.Threading;

namespace ProjectMaya.WindowsRuntime
{
    internal sealed partial class WindowsIsolation
    {
        internal IntPtr BridgeInput;
        internal IntPtr BridgeOutput { get { return readOutput; } }
        internal void StartWorker(string directory, string run, SecurityIdentifier user)
        {
            job = CreateJobObject(IntPtr.Zero, null); Native.Require(job != IntPtr.Zero, "bridge_worker_job");
            var limits = new JobLimits { basic = new BasicLimits { flags = 0x2000 | 8, activeProcessLimit = 1 } };
            Native.Require(SetInformationJobObject(job, 9, ref limits, (uint)Marshal.SizeOf(typeof(JobLimits))), "bridge_worker_job_limits");
            IntPtr attributes = IntPtr.Zero, environment = IntPtr.Zero, token = IntPtr.Zero;
            bool ready = false; var allocations = new List<IntPtr>(); var handles = new List<IntPtr>();
            try
            {
                UIntPtr size = UIntPtr.Zero; InitializeProcThreadAttributeList(IntPtr.Zero, 3, 0, ref size);
                attributes = Marshal.AllocHGlobal(checked((int)size.ToUInt64()));
                Native.Require(InitializeProcThreadAttributeList(attributes, 3, 0, ref size), "bridge_worker_attributes"); ready = true;
                IntPtr policy = Allocate(allocations, 4); Marshal.WriteInt32(policy, 1); Attribute(attributes, 0x2000E, policy, 4);
                IntPtr jobs = Allocate(allocations, IntPtr.Size); Marshal.WriteIntPtr(jobs, job); Attribute(attributes, 0x2000D, jobs, IntPtr.Size);
                var sa = new SecurityAttributes { size = (uint)Marshal.SizeOf(typeof(SecurityAttributes)), inherit = 1 };
                IntPtr inputRead, inputWrite, outputWrite, errorWrite;
                Native.Require(CreatePipe(out inputRead, out inputWrite, ref sa, 0), "worker_stdin"); handles.Add(inputRead); handles.Add(inputWrite);
                Native.Require(CreatePipe(out readOutput, out outputWrite, ref sa, 0), "worker_stdout"); handles.Add(outputWrite);
                Native.Require(CreatePipe(out readError, out errorWrite, ref sa, 0), "worker_stderr"); handles.Add(errorWrite);
                foreach (IntPtr h in new[] { inputWrite, readOutput, readError }) Native.Require(SetHandleInformation(h, 1, 0), "worker_private_handle");
                IntPtr inherited = Allocate(allocations, 3 * IntPtr.Size);
                Marshal.WriteIntPtr(inherited, inputRead); Marshal.WriteIntPtr(inherited, IntPtr.Size, outputWrite); Marshal.WriteIntPtr(inherited, 2 * IntPtr.Size, errorWrite);
                Attribute(attributes, 0x20002, inherited, 3 * IntPtr.Size);
                string runtime = Path.Combine(directory, "runtime"), host = Path.Combine(directory, "host");
                string python = Path.Combine(runtime, "python", "python.exe"), entry = Path.Combine(runtime, "bridge_worker_entry.py");
                string windows = Environment.GetFolderPath(Environment.SpecialFolder.Windows);
                string env = "HERMES_DISABLE_LAZY_INSTALLS=1\0HERMES_HOME=" + host + "\0LOCALAPPDATA=" + host +
                    "\0PATH=" + Path.Combine(runtime, "python") + ";" + Environment.SystemDirectory + "\0SYSTEMROOT=" + windows +
                    "\0TEMP=" + host + "\0TMP=" + host + "\0USERPROFILE=" + host + "\0WINDIR=" + windows + "\0\0";
                environment = Marshal.StringToHGlobalUni(env);
                var startup = new StartupEx { startup = new Startup { size = (uint)Marshal.SizeOf(typeof(StartupEx)), flags = 0x100,
                    input = inputRead, output = outputWrite, error = errorWrite }, attributes = attributes };
                token = CreateReducedLaunchToken(user);
                Native.Require(CreateProcessAsUserW(token, python, new StringBuilder(Quote(python) + " -I -S -B " + Quote(entry) + " " + run),
                    IntPtr.Zero, IntPtr.Zero, true, LaunchCreationFlags, environment, host, ref startup, out child), "bridge_worker_create");
                IntPtr actual = IntPtr.Zero;
                try
                {
                    Native.Require(OpenProcessToken(child.process, 8, out actual), "bridge_worker_token");
                    long notify; Native.Require(LookupPrivilegeValueW(null, "SeChangeNotifyPrivilege", out notify), "worker_notify_privilege");
                    VerifyReducedLaunchToken(actual, user, ReadLaunchScalar(token, 12, GetTokenInformation), notify, GetTokenInformation);
                }
                finally { if (actual != IntPtr.Zero) Native.CloseHandle(actual); }
                ReducedLaunchTokenVerified = true;
                BridgeInput = inputWrite; handles.Remove(inputWrite);
            }
            finally
            {
                if (token != IntPtr.Zero) Native.CloseHandle(token);
                foreach (IntPtr h in handles) Native.CloseHandle(h);
                if (ready) DeleteProcThreadAttributeList(attributes);
                if (attributes != IntPtr.Zero) Marshal.FreeHGlobal(attributes);
                foreach (IntPtr memory in allocations) Marshal.FreeHGlobal(memory);
                if (environment != IntPtr.Zero) Marshal.FreeHGlobal(environment);
            }
        }
        internal void ResumeBridge()
        {
            errorThread = new Thread(delegate() {
                try
                {
                    using (var stream = new FileStream(new Microsoft.Win32.SafeHandles.SafeFileHandle(readError, false), FileAccess.Read))
                    {
                        byte[] buffer = new byte[1024]; int count;
                        while ((count = stream.Read(buffer, 0, buffer.Length)) > 0)
                        { StderrBytes += count; if (StderrBytes > 4096) throw new StartupFailure("bridge_stderr_limit"); }
                    }
                }
                catch { captureFailed = true; if (job != IntPtr.Zero) TerminateJobObject(job, 1); }
            });
            errorThread.IsBackground = true; errorThread.Start();
            if (ResumeThread(child.thread) != 1) throw new StartupFailure("bridge_resume_failed");
            Resumed = true;
        }
        internal void WaitBridge(uint milliseconds)
        {
            if (WaitForSingleObject(child.process, milliseconds) != 0) throw new StartupFailure("bridge_exit_timeout");
            uint code; Native.Require(GetExitCodeProcess(child.process, out code), "bridge_exit_code"); ExitCode = code;
            if (!errorThread.Join(1000) || captureFailed || StderrBytes != 0) throw new StartupFailure("bridge_stderr_rejected");
            if (code != 0) throw new StartupFailure("bridge_exit_failed");
        }
        internal void CloseBridgeInput()
        {
            if (BridgeInput != IntPtr.Zero) { Native.CloseHandle(BridgeInput); BridgeInput = IntPtr.Zero; }
        }
    }
}
