// VM-only entry point. Compiling this file does not authorize execution or provisioning.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Management;
using System.Reflection;
using System.Security.Principal;
using Microsoft.Win32;
using Maya.GateA.Observation;

namespace Maya.GateA.Host
{
    public sealed class WindowsHostEnvironment : IHostEnvironment
    {
        readonly string manifestPath;
        public WindowsHostEnvironment(string path) { manifestPath = path; }
        public DateTime UtcNow { get { return DateTime.UtcNow; } }
        static void Require(bool value) { if (!value) throw new InvalidOperationException(); }
        static ManagementObjectCollection Query(string scope, string text)
        {
            using (var search = new ManagementObjectSearcher(scope,text,new EnumerationOptions { ReturnImmediately = false,Timeout = TimeSpan.FromSeconds(2) }))
                return search.Get();
        }
        public void Verify(HostManifest manifest)
        {
            Require(Environment.OSVersion.Platform == PlatformID.Win32NT && Environment.Is64BitProcess);
            Require(Environment.CurrentDirectory == @"C:\MayaGateA" && Environment.SystemDirectory.Equals(@"C:\Windows\System32",StringComparison.OrdinalIgnoreCase));
            string host = Assembly.GetExecutingAssembly().Location;
            Require(host == @"C:\MayaGateA\observer\Maya.GateA.ObserverHost.exe" && HostFiles.HashFile(host) == manifest.ExecutableHash);
            string library = typeof(Supervision).Assembly.Location;
            Require(library == @"C:\MayaGateA\observer\Maya.GateA.Supervision.dll" && HostFiles.HashFile(library) == HostManifest.LibraryHash);
            Require(HostFiles.HashFile(manifestPath) == manifest.Hash);
            string authorization = Path.GetDirectoryName(manifestPath);
            foreach (string name in HostManifest.RecordNames)
                Require(HostFiles.HashFile(Path.Combine(authorization,name + ".json")) == manifest.RecordHash(name));
            using (var process = Process.GetCurrentProcess()) Require(process.SessionId == manifest.Session);
            using (var identity = WindowsIdentity.GetCurrent())
            {
                Require(identity.User.Value == manifest.User && identity.Name.StartsWith(Environment.MachineName + "\\",StringComparison.OrdinalIgnoreCase));
                Require(new WindowsPrincipal(identity).IsInRole(WindowsBuiltInRole.Administrator));
            }
            using (var version = Registry.LocalMachine.OpenSubKey(@"SOFTWARE\Microsoft\Windows NT\CurrentVersion"))
            using (var bios = Registry.LocalMachine.OpenSubKey(@"HARDWARE\DESCRIPTION\System\BIOS"))
                Require(version != null && bios != null && (string)version.GetValue("CurrentBuildNumber") == "26300" &&
                    Convert.ToInt32(version.GetValue("UBR")) == 9711 && (string)version.GetValue("EditionID") == "Professional" &&
                    (string)bios.GetValue("SystemProductName") == "Virtual Machine");
            using (var rows = Query("root\\cimv2","SELECT UUID FROM Win32_ComputerSystemProduct"))
            {
                int count = 0;
                foreach (ManagementObject row in rows) using (row)
                { count++; Require(Guid.Parse((string)row["UUID"]).ToString("D") == manifest.Vm); }
                Require(count == 1);
            }
            var adapters = new HashSet<string>(StringComparer.Ordinal);
            using (var rows = Query("root\\StandardCimv2","SELECT InterfaceGuid,InterfaceType,InterfaceAdminStatus FROM MSFT_NetAdapter"))
                foreach (ManagementObject row in rows) using (row)
                {
                    if (Convert.ToUInt32(row["InterfaceType"]) == 24) continue;
                    Require(row["InterfaceAdminStatus"] != null && Convert.ToUInt32(row["InterfaceAdminStatus"]) == 2);
                    Require(row["InterfaceGuid"] is string && adapters.Count < 64);
                    Require(adapters.Add(Guid.Parse((string)row["InterfaceGuid"]).ToString("D")));
                }
            Require(adapters.Count != 0 && adapters.SetEquals(manifest.Adapters));
        }
    }

    public static class ObserverHostProgram
    {
        public static int Main(string[] args)
        {
            HostResult result;
            try
            {
                if (args.Length != 6 || args[0] != "--case" || args[2] != "--manifest" || args[4] != "--manifest-sha256" ||
                    args[1].Length != 1 || "ABCD".IndexOf(args[1],StringComparison.Ordinal) < 0 || Console.IsInputRedirected)
                    throw new InvalidOperationException();
                string expected = @"C:\MayaGateA\observer\authorization\" + args[1] + @"\execution.json";
                if (args[3] != expected) throw new InvalidOperationException();
                HostManifest manifest = HostManifest.Parse(HostFiles.Read(expected),args[5],args[1]);
                result = HostController.Run(manifest,new WindowsHostEnvironment(expected),new FileAttemptJournal(@"C:\MayaGateA\observer\attempts"),
                    delegate(string challenge) { Console.WriteLine(challenge); return Console.ReadLine() == challenge; },
                    delegate(LaunchPlan plan, Func<bool> permission) { return Supervision.Run(plan,new NativeSupervisionBackend(permission)); });
            }
            catch { result = HostResult.Blocked("host.preflight_blocked"); }
            Console.WriteLine(result.Json); return result.ExitCode;
        }
    }
}
