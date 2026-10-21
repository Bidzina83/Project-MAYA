using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.IO.MemoryMappedFiles;
using System.Net;
using System.Net.Sockets;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Text;
using System.Threading;
using Microsoft.Win32.SafeHandles;

namespace ProjectMaya.WindowsRuntime
{
    internal sealed class ContainmentScreen : IDisposable
    {
        internal const string Schema = "maya.protected_python.screen.v1";
        internal static readonly string[] Stores = { "document", "memory", "business", "policy", "audit", "secret" };
        readonly string directory, run, fixture, state;
        readonly SecurityIdentifier package, user;
        readonly Dictionary<string, string> hashes = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        readonly List<Endpoint> endpoints = new List<Endpoint>();
        MemoryMappedFile mapping;
        int unauthorized, listenerFailure;
        bool prepared;
        volatile int childPid;
        UdpEvidence udpEvidence;
        internal void ConfigureUdp(WindowsIsolation isolation, Dictionary<string, object> record)
        {
            var ids = isolation.VerifiedNetworkIds();
            var inventory = new List<Dictionary<string, object>>();
            foreach (var pair in ids) inventory.Add(new Dictionary<string, object> {
                {"filter_id", pair.Key.ToString()}, {"filter_guid", isolation.NetworkFilterKey(pair.Value).ToString()},
                {"layer_guid", WindowsIsolation.NetworkLayer(pair.Value).ToString()}, {"package_sid", package.Value} });
            record["screen_udp_filter_inventory"] = inventory;
            udpEvidence = new UdpEvidence(Path.Combine(directory, "runtime", "python", "python.exe"),
                package, ids);
        }
        internal void BindChild(int pid) { if (pid <= 0) throw new StartupFailure("udp_child_identity"); childPid = pid; }
        internal Dictionary<string, object> Plan { get; private set; }
        internal string Stage { get; set; }
        internal Dictionary<string, string> AclInventory()
        {
            var result = new Dictionary<string, string>();
            foreach (string path in new[] { Path.Combine(directory, "runtime"), Environment.SystemDirectory })
            {
                ProductFiles.NoLinks(path);
                string descriptor = Directory.GetAccessControl(path, AccessControlSections.Access)
                    .GetSecurityDescriptorSddlForm(AccessControlSections.Access);
                if (descriptor.Length > 8192) throw new StartupFailure("screen_acl_inventory_size");
                result.Add(path, descriptor);
            }
            return result;
        }

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.U1)]
        static extern bool CreateSymbolicLinkW(string name, string target, uint flags);
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        static extern IntPtr CreateFileW(string path, uint access, uint share, IntPtr security, uint creation, uint flags, IntPtr template);
        [DllImport("kernel32.dll", SetLastError = true)]
        static extern bool DeviceIoControl(IntPtr handle, uint code, byte[] input, int inputSize,
            byte[] output, int outputSize, out int returned, IntPtr overlapped);
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        static extern bool RemoveDirectoryW(string path);
        [DllImport("kernel32.dll", SetLastError = true)]
        static extern IntPtr OpenProcess(uint access, bool inherit, int pid);
        [DllImport("advapi32.dll", SetLastError = true)]
        static extern bool OpenProcessToken(IntPtr process, uint access, out IntPtr token);

        internal ContainmentScreen(string directory, string run, SecurityIdentifier package, SecurityIdentifier user)
        {
            this.directory = directory; this.run = run; this.package = package; this.user = user;
            fixture = Path.Combine(directory, "screen-fixtures"); state = Path.Combine(directory, "state");
            Stage = "screen_not_started";
        }

        internal sealed class AdsRequest
        {
            internal readonly string BasePath, Path;
            internal readonly uint Access, Disposition;
            internal const uint Share = 1, Flags = 0x80;
            internal AdsRequest(string directory, bool write)
            {
                BasePath = System.IO.Path.GetFullPath(System.IO.Path.Combine(directory,
                    "screen-fixtures", "document", "canary.txt"));
                Path = BasePath + ":maya-screen";
                Access = write ? 0x40000000u : 0x80000000u;
                Disposition = write ? 1u : 3u; // CREATE_NEW / OPEN_EXISTING; no overwrite fallback.
            }
        }

        static FileStream OpenAds(string directory, bool write)
        {
            var request = new AdsRequest(directory, write);
            ProductFiles.NoLinks(request.BasePath);
            IntPtr raw = CreateFileW(request.Path, request.Access, AdsRequest.Share,
                IntPtr.Zero, request.Disposition, AdsRequest.Flags, IntPtr.Zero);
            Native.Require(raw != new IntPtr(-1) && raw != IntPtr.Zero, write ? "screen_ads_create" : "screen_ads_read");
            var handle = new SafeFileHandle(raw, true);
            try { return new FileStream(handle, write ? FileAccess.Write : FileAccess.Read); }
            catch { handle.Dispose(); throw; }
        }

        internal static void WriteAdsContents(Stream stream, string nonce)
        {
            ProtectedPython.ExpectedBeacon(nonce); // Reuse the fixed attempt-ID validation.
            byte[] bytes = Encoding.ASCII.GetBytes(nonce);
            stream.Write(bytes, 0, bytes.Length);
        }

        internal static bool AdsContentsMatch(Stream stream, string nonce)
        {
            ProtectedPython.ExpectedBeacon(nonce);
            byte[] bytes = new byte[33]; int count = 0, read;
            while (count < bytes.Length && (read = stream.Read(bytes, count, bytes.Length - count)) != 0) count += read;
            if (count != nonce.Length) return false;
            for (int i = 0; i < count; i++) if (bytes[i] != (byte)nonce[i]) return false;
            return true;
        }

        internal static Dictionary<string, ContainmentEvidence.Requirement> Requirements()
        {
            var result = new Dictionary<string, ContainmentEvidence.Requirement>(StringComparer.Ordinal);
            Action<string, string, bool> add = (id, family, allowed) =>
                result.Add(id, new ContainmentEvidence.Requirement(family, allowed));
            add("C01.private", "C01", true); add("C01.runtime_write", "C01", false);
            foreach (string store in Stores)
                foreach (string op in new[] { "read", "write", "create", "delete" }) add("C02." + store + "." + op, "C02", false);
            add("C03.public", "C03", true); add("C03.metadata", "C03", true);
            foreach (string route in new[] { "absolute", "traversal", "ads", "symlink", "junction" }) add("C04." + route, "C04", false);
            foreach (string transport in new[] { "4tcp", "4udp", "6tcp", "6udp" })
                foreach (string op in transport.EndsWith("udp", StringComparison.Ordinal) ? new[] { "send", "receive" } : new[] { "connect", "bind" })
                    add("C05." + transport + "." + op, "C05", false);
            add("C06.token_facts", "C06", true);
            foreach (string op in new[] { "process_access", "host_token", "spawn" }) add("C06." + op, "C06", false);
            add("C07.handles", "C07", true); add("C07.mapping", "C07", false);
            add("C08.cleanup", "C08", true);
            return result;
        }
        internal static HashSet<int> DeniedErrors(string id)
        {
            if (id == "C06.spawn") return new HashSet<int> { 5, 367 }; // ERROR_CHILD_PROCESS_BLOCKED.
            return new HashSet<int> { id.StartsWith("C05.", StringComparison.Ordinal) ? 10013 : 5 };
        }

        void SaveCanary(string path, string contents)
        {
            ProductFiles.NoLinks(path);
            using (var stream = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.Read))
            {
                byte[] bytes = Encoding.ASCII.GetBytes(contents); stream.Write(bytes, 0, bytes.Length); stream.Flush(true);
            }
            hashes.Add(path, ProductFiles.HashFile(path));
        }

        internal void Prepare()
        {
            Stage = "fixture_root";
            ProductFiles.NoLinks(fixture);
            if (Directory.Exists(fixture)) throw new StartupFailure("screen_fixtures_exist");
            // Only this new fixture root gets the traverse grant; protected children reset inheritance.
            Directory.CreateDirectory(fixture, ProductFiles.RuntimeSecurity(package, user));
            var protectedPaths = new Dictionary<string, string>();
            foreach (string store in Stores)
            {
                Stage = "protected_" + store;
                string root = Path.Combine(fixture, store);
                Directory.CreateDirectory(root, PrivateSecurity(user));
                string path = Path.Combine(root, "canary.txt"); SaveCanary(path, run);
                protectedPaths.Add(store, path);
                string positivePath = Path.Combine(root, "host-positive.txt");
                using (var positive = new FileStream(positivePath, FileMode.CreateNew, FileAccess.ReadWrite, FileShare.None))
                {
                    positive.WriteByte(1); positive.Position = 0;
                    if (positive.ReadByte() != 1) throw new StartupFailure("screen_file_positive");
                }
                File.Delete(positivePath);
                if (File.Exists(positivePath)) throw new StartupFailure("screen_file_delete_positive");
            }
            string document = protectedPaths["document"];
            Stage = "ads_create";
            using (var ads = OpenAds(directory, true)) { WriteAdsContents(ads, run); ads.Flush(true); }
            Stage = "runtime_canary";
            string runtimeCanary = Path.Combine(directory, "runtime", "screen-runtime-canary.txt");
            SaveCanary(runtimeCanary, run);
            Stage = "public_canary";
            string publicPath = Path.Combine(fixture, "public-control.txt"); SaveCanary(publicPath, run);
            Stage = "public_canary_permissions";
            var publicAcl = new FileSecurity(); publicAcl.SetAccessRuleProtection(true, false);
            publicAcl.SetOwner(new SecurityIdentifier("S-1-5-32-544"));
            foreach (string sid in new[] { "S-1-5-32-544", "S-1-5-18", user.Value })
                publicAcl.AddAccessRule(new FileSystemAccessRule(new SecurityIdentifier(sid), FileSystemRights.FullControl, AccessControlType.Allow));
            publicAcl.AddAccessRule(new FileSystemAccessRule(new SecurityIdentifier("S-1-15-2-1"), FileSystemRights.Read, AccessControlType.Allow));
            File.SetAccessControl(publicPath, publicAcl);
            string routes = Path.Combine(fixture, "routes"); Directory.CreateDirectory(routes, ProductFiles.RuntimeSecurity(package, user));
            string symbolic = Path.Combine(routes, "symbolic"), junction = Path.Combine(routes, "junction");
            Stage = "symlink_create";
            Native.Require(CreateSymbolicLinkW(symbolic, Path.GetDirectoryName(document), 1), "screen_symlink_create");
            Stage = "junction_create";
            Directory.CreateDirectory(junction, ProductFiles.RuntimeSecurity(package, user));
            CreateJunction(junction, Path.GetDirectoryName(document));
            string mappingName = "Local\\MayaScreen." + run;
            Stage = "mapping_permissions";
            var security = new MemoryMappedFileSecurity(); security.SetAccessRuleProtection(true, false);
            security.SetOwner(new SecurityIdentifier("S-1-5-32-544"));
            security.SetGroup(new SecurityIdentifier("S-1-5-32-544"));
            foreach (string sid in new[] { "S-1-5-32-544", "S-1-5-18", user.Value })
                security.AddAccessRule(new AccessRule<MemoryMappedFileRights>(new SecurityIdentifier(sid), MemoryMappedFileRights.FullControl, AccessControlType.Allow));
            Stage = "mapping_create";
            mapping = MemoryMappedFile.CreateNew(mappingName, 4096, MemoryMappedFileAccess.ReadWrite,
                MemoryMappedFileOptions.None, security, HandleInheritability.None);
            Stage = "mapping_positive_control";
            using (var view = mapping.CreateViewAccessor()) view.Write(0, 12345);
            using (var positive = MemoryMappedFile.OpenExisting(mappingName, MemoryMappedFileRights.Read))
            using (var view = positive.CreateViewAccessor(0, 4, MemoryMappedFileAccess.Read))
                if (view.ReadInt32(0) != 12345) throw new StartupFailure("screen_mapping_positive");
            Stage = "host_process_token_positive_control";
            IntPtr process = OpenProcess(0x2A | 0x1000, false, Process.GetCurrentProcess().Id), token = IntPtr.Zero;
            Native.Require(process != IntPtr.Zero, "screen_host_process_positive");
            try { Native.Require(OpenProcessToken(process, 0x22, out token), "screen_host_token_positive"); }
            finally { if (token != IntPtr.Zero) Native.CloseHandle(token); Native.CloseHandle(process); }
            var ports = new Dictionary<string, int>();
            foreach (int family in new[] { 4, 6 })
                foreach (bool tcp in new[] { true, false })
                {
                    Stage = "endpoint_" + family + (tcp ? "tcp" : "udp");
                    var endpoint = new Endpoint(this, family, tcp); endpoints.Add(endpoint);
                    ports.Add(family + (tcp ? "tcp" : "udp"), endpoint.Port);
                    endpoint.PositiveControl();
                }
            Stage = "plan_assembly";
            Plan = new Dictionary<string, object> {
                {"schema", Schema}, {"nonce", run}, {"host_pid", Process.GetCurrentProcess().Id},
                {"runtime", Path.Combine(directory, "runtime")}, {"runtime_canary", runtimeCanary},
                {"protected", protectedPaths}, {"public", publicPath}, {"mapping", mappingName}, {"ports", ports},
                {"routes", new Dictionary<string, string> {
                    {"absolute", document}, {"traversal", Path.Combine(state, "..", "screen-fixtures", "document", "canary.txt")},
                    {"ads", document + ":maya-screen"}, {"symlink", Path.Combine(symbolic, "canary.txt")},
                    {"junction", Path.Combine(junction, "canary.txt")}}}
            };
            prepared = true;
            Stage = "fixtures_prepared";
        }

        internal static DirectorySecurity PrivateSecurity(SecurityIdentifier user)
        {
            var acl = new DirectorySecurity(); acl.SetAccessRuleProtection(true, false);
            var admin = new SecurityIdentifier("S-1-5-32-544"); acl.SetOwner(admin); acl.SetGroup(admin);
            foreach (SecurityIdentifier who in new[] { admin, new SecurityIdentifier("S-1-5-18"), user })
                acl.AddAccessRule(new FileSystemAccessRule(who, FileSystemRights.FullControl,
                    InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit, PropagationFlags.None, AccessControlType.Allow));
            return acl;
        }

        static byte[] JunctionData(string target)
        {
            string substitute = "\\??\\" + target;
            byte[] first = Encoding.Unicode.GetBytes(substitute), second = Encoding.Unicode.GetBytes(target);
            using (var stream = new MemoryStream())
            using (var writer = new BinaryWriter(stream))
            {
                writer.Write(0xA0000003u); writer.Write((ushort)(8 + first.Length + second.Length + 4)); writer.Write((ushort)0);
                writer.Write((ushort)0); writer.Write((ushort)first.Length);
                writer.Write((ushort)(first.Length + 2)); writer.Write((ushort)second.Length);
                writer.Write(first); writer.Write((ushort)0); writer.Write(second); writer.Write((ushort)0);
                return stream.ToArray();
            }
        }

        static void CreateJunction(string path, string target)
        {
            IntPtr handle = CreateFileW(path, 0x40000000, 7, IntPtr.Zero, 3, 0x02200000, IntPtr.Zero);
            Native.Require(handle != new IntPtr(-1), "screen_junction_open");
            try
            {
                byte[] data = JunctionData(target); int returned;
                Native.Require(DeviceIoControl(handle, 0x000900A4, data, data.Length, null, 0, out returned, IntPtr.Zero), "screen_junction_set");
            }
            finally { Native.CloseHandle(handle); }
        }

        internal void WritePlan(long[] handles)
        {
            if (!prepared || handles == null || handles.Length != 3) throw new StartupFailure("screen_plan_prerequisite");
            Plan.Add("handles", handles);
            ProtectedPython.SaveRecord(Path.Combine(state, "screen-plan.json"), Plan);
        }

        void Unauthorized()
        {
            Interlocked.Exchange(ref unauthorized, 1);
            try { File.WriteAllText(Path.Combine(state, "screen-stop.txt"), run); }
            catch (Exception) { Interlocked.Exchange(ref listenerFailure, 1); }
        }

        internal void RecordNetworkEvidence(Dictionary<string, object> record)
        {
            record["screen_host_unauthorized_network_effect"] = Interlocked.CompareExchange(ref unauthorized, 0, 0) != 0;
            record["screen_listener_capture_complete"] = Interlocked.CompareExchange(ref listenerFailure, 0, 0) == 0;
        }

        internal Dictionary<string, string> Collect(Dictionary<string, object> record)
        {
            Stage = "fixture_postconditions";
            var observed = new Dictionary<string, string>(StringComparer.Ordinal);
            bool unchanged = true;
            foreach (var pair in hashes)
            {
                ProductFiles.NoLinks(pair.Key);
                if (!File.Exists(pair.Key) || new FileInfo(pair.Key).Length != run.Length || ProductFiles.HashFile(pair.Key) != pair.Value) unchanged = false;
            }
            foreach (string store in Stores)
            {
                string root = Path.Combine(fixture, store);
                ProductFiles.NoLinks(root);
                if (Directory.GetFileSystemEntries(root).Length != 1) unchanged = false;
            }
            record["screen_host_postconditions"] = unchanged;
            try
            {
                Stage = "ads_readback";
                using (var ads = OpenAds(directory, false)) if (!AdsContentsMatch(ads, run)) unchanged = false;
            }
            catch (IOException) { unchanged = false; }
            catch (UnauthorizedAccessException) { unchanged = false; }
            catch (StartupFailure error)
            {
                if (!error.Message.StartsWith("screen_ads_read:win32_", StringComparison.Ordinal)) throw;
                unchanged = false;
                record["screen_ads_readback_reason_code"] = ProtectedPython.FailureCode(error);
                ProtectedPython.RecordStageFailure(record, "screen_ads_readback_failure", Stage, error);
            }
            record["screen_host_postconditions"] = unchanged;
            Stage = "endpoint_post_controls";
            foreach (Endpoint endpoint in endpoints) endpoint.PositiveControl();
            foreach (Endpoint endpoint in endpoints) endpoint.Dispose();
            if (!unchanged || Interlocked.CompareExchange(ref unauthorized, 0, 0) != 0)
                observed["host.effect"] = "failed";
            record["screen_host_positive_controls"] = true;
            var sends = new List<Dictionary<string, object>>();
            foreach (Endpoint endpoint in endpoints) if (!endpoint.Tcp) sends.Add(new Dictionary<string, object> {
                {"family", endpoint.Family}, {"source_port", endpoint.PortValue},
                {"child_port_owner_verified_before_send", endpoint.InboundPort != 0}, {"target_port", endpoint.InboundPort} });
            record["screen_udp_host_sends"] = sends;
            record["screen_host_postconditions"] = unchanged;
            RecordNetworkEvidence(record);
            Stage = "report_admission";
            if (udpEvidence != null) udpEvidence.Collect(record);
            string path = Path.Combine(state, "screen-result.json"); ProductFiles.NoLinks(path);
            using (var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.None))
            {
                if (stream.Length > ContainmentEvidence.MaximumReportBytes) throw new StartupFailure("screen_report_size");
                byte[] bytes = new byte[checked((int)stream.Length)];
                int at = 0, got;
                while (at < bytes.Length && (got = stream.Read(bytes, at, bytes.Length - at)) != 0) at += got;
                if (at != bytes.Length) throw new StartupFailure("screen_report_short_read");
                foreach (byte value in bytes) if (value > 127) throw new StartupFailure("screen_report_encoding");
                var root = ScreenJson.Read(Encoding.ASCII.GetString(bytes));
                RequireKeys(root, "schema", "nonce", "rows", "udp");
                var udp = ReadUdpDetails(root["udp"] as ArrayList);
                if ((string)root["schema"] != Schema || (string)root["nonce"] != run) throw new StartupFailure("screen_report_identity");
                var required = Requirements(); var rows = root["rows"] as ArrayList;
                if (rows == null || rows.Count > required.Count - 1) throw new StartupFailure("screen_report_rows");
                foreach (object value in rows)
                {
                    var row = value as Dictionary<string, object>; RequireKeys(row, "id", "outcome", "error", "bytes");
                    string id = row["id"] as string, outcome = row["outcome"] as string;
                    ContainmentEvidence.Requirement requirement;
                    if (id == null || id == "C08.cleanup" || !required.TryGetValue(id, out requirement) || observed.ContainsKey(id))
                        throw new StartupFailure("screen_report_case");
                    if (!(row["error"] is int) || !(row["bytes"] is int) || (int)row["bytes"] < 0 || (int)row["bytes"] > 65536 ||
                        (int)row["error"] < 0 || (outcome != "allowed" && outcome != "denied" && outcome != "effect" && outcome != "inconclusive"))
                        throw new StartupFailure("screen_report_value");
                    var item = new ContainmentEvidence.Observation {
                        Family = requirement.Family, Probe = id, PositiveControlVerified = prepared,
                        AttemptObserved = true, UnauthorizedEffect = outcome == "effect", ExplicitDenial = outcome == "denied",
                        AllowedEffectVerified = outcome == "allowed", CaptureComplete = listenerFailure == 0,
                        HostPostconditionVerified = unchanged, NativeError = (int)row["error"],
                        Unsupported = outcome == "inconclusive", TimedOut = false
                    };
                    // Denials are case-bound. Silence, namespace misses and unknown
                    // child-policy errors remain inconclusive; 367 is spawn-only.
                    var errors = DeniedErrors(id);
                    observed.Add(id, ContainmentEvidence.Classify(item, requirement.ExpectedAllowed, errors));
                    if (id.Contains("udp."))
                    {
                        Dictionary<string, object> detail;
                        if (!udp.TryGetValue(id, out detail)) throw new StartupFailure("screen_udp_detail_missing");
                        int family = id.StartsWith("C05.4", StringComparison.Ordinal) ? 4 : 6;
                        bool receive = id.EndsWith("receive", StringComparison.Ordinal);
                        int local = (int)detail["local_port"], remote = (int)detail["remote_port"];
                        bool source = false;
                        foreach (Endpoint endpoint in endpoints)
                            if (endpoint.Family == family && !endpoint.Tcp && endpoint.PortValue == remote)
                                source = !receive || endpoint.InboundPort == local;
                        observed[id] = UdpCaseStatus(receive, outcome, (int)row["bytes"], detail,
                            source, unchanged && listenerFailure == 0,
                            udpEvidence != null && udpEvidence.Denied(family, receive, local, remote));
                    }
                }
                record["screen_child_observations_untrusted"] = rows;
                record["screen_udp_details_untrusted"] = root["udp"];
            }
            return observed;
        }

        internal static string UdpCaseStatus(bool receive, string outcome, int bytes,
            Dictionary<string, object> detail, bool source, bool controls, bool matchingDrop)
        {
            // A received packet is a failure even with incomplete denial evidence.
            if (outcome == "effect" || (int)detail["received_bytes"] > 0) return "failed";
            bool usable = source && controls && (int)detail["local_port"] >= 1024 &&
                (int)detail["bind_error"] == 0 && (outcome == "denied" || outcome == "inconclusive") &&
                (receive ? (int)detail["sent_bytes"] == 0 :
                    ((int)detail["sent_bytes"] == 0 || (int)detail["sent_bytes"] == 38)) &&
                bytes == (int)detail[receive ? "received_bytes" : "sent_bytes"];
            return usable && matchingDrop ? "observed_denied" : "inconclusive";
        }

        internal static Dictionary<string, Dictionary<string, object>> ReadUdpDetails(ArrayList rows)
        {
            if (rows == null || rows.Count > 4) throw new StartupFailure("screen_udp_details");
            var result = new Dictionary<string, Dictionary<string, object>>(StringComparer.Ordinal);
            foreach (object value in rows)
            {
                var row = value as Dictionary<string, object>;
                RequireKeys(row, "id", "local_port", "remote_port", "sent_bytes", "received_bytes", "bind_error");
                string id = row["id"] as string;
                if (id != "C05.4udp.send" && id != "C05.4udp.receive" && id != "C05.6udp.send" && id != "C05.6udp.receive")
                    throw new StartupFailure("screen_udp_case");
                foreach (string key in new[] { "local_port", "remote_port", "sent_bytes", "received_bytes", "bind_error" })
                    if (!(row[key] is int) || (int)row[key] < 0 || (int)row[key] > 65535) throw new StartupFailure("screen_udp_value");
                if (result.ContainsKey(id)) throw new StartupFailure("screen_udp_duplicate");
                result.Add(id, row);
            }
            return result;
        }

        internal static void RequireKeys(Dictionary<string, object> map, params string[] keys)
        {
            if (map == null || map.Count != keys.Length) throw new StartupFailure("screen_report_keys");
            foreach (string key in keys) if (!map.ContainsKey(key)) throw new StartupFailure("screen_report_keys");
        }

        internal static string Finish(Dictionary<string, string> observations, bool cleanup)
        {
            foreach (string status in observations.Values) if (status == "failed") return "failed";
            observations["C08.cleanup"] = cleanup ? "observed_allowed" : "inconclusive";
            return ContainmentEvidence.Summarize(observations, Requirements(), cleanup);
        }

        internal void Cleanup()
        {
            Stage = "endpoint_mapping_stop";
            Dispose();
            // Deterministic names allow version-bound recovery without following aliases.
            foreach (string name in new[] { "symbolic", "junction" })
            {
                Stage = "alias_" + name + "_cleanup";
                string path = Path.Combine(fixture, "routes", name);
                ProductFiles.NoLinks(Path.GetDirectoryName(path));
                FileAttributes attributes;
                try { attributes = File.GetAttributes(path); }
                catch (FileNotFoundException) { continue; }
                catch (DirectoryNotFoundException) { continue; }
                if ((attributes & FileAttributes.ReparsePoint) == 0)
                {
                    // Partial junction setup may leave a real, empty directory.
                    if (name != "junction" || Directory.GetFileSystemEntries(path).Length != 0)
                        throw new StartupFailure("screen_alias_cleanup_identity");
                }
                else VerifyAlias(path, name, Path.Combine(fixture, "document"));
                // RemoveDirectory removes the link object itself, never its target.
                Native.Require(RemoveDirectoryW(path), "screen_alias_remove");
            }
            if (Directory.Exists(fixture))
            {
                Stage = "fixture_grant_revocation";
                foreach (string path in new[] { fixture, Path.Combine(fixture, "routes") })
                {
                    if (!Directory.Exists(path)) continue; ProductFiles.NoLinks(path);
                    var acl = Directory.GetAccessControl(path); acl.PurgeAccessRules(package); Directory.SetAccessControl(path, acl);
                }
                string pathPublic = Path.Combine(fixture, "public-control.txt");
                if (File.Exists(pathPublic))
                {
                    Stage = "public_grant_revocation";
                    ProductFiles.NoLinks(pathPublic); var acl = File.GetAccessControl(pathPublic);
                    acl.PurgeAccessRules(new SecurityIdentifier("S-1-15-2-1")); File.SetAccessControl(pathPublic, acl);
                    foreach (FileSystemAccessRule rule in File.GetAccessControl(pathPublic).GetAccessRules(true, true, typeof(SecurityIdentifier)))
                        if (rule.IdentityReference.Value == "S-1-15-2-1") throw new StartupFailure("screen_public_grant_remains");
                }
            }
            try
            {
                Stage = "mapping_absence_check";
                using (MemoryMappedFile.OpenExisting("Local\\MayaScreen." + run, MemoryMappedFileRights.Read))
                    throw new StartupFailure("screen_mapping_remains");
            }
            catch (FileNotFoundException) { }
            Stage = "fixture_cleanup_complete";
            // Protected canaries/reports remain as inert evidence, like the runtime files.
        }

        static void VerifyAlias(string path, string name, string target)
        {
            IntPtr handle = CreateFileW(path, 0, 7, IntPtr.Zero, 3, 0x02200000, IntPtr.Zero);
            Native.Require(handle != new IntPtr(-1), "screen_alias_verify_open");
            try
            {
                byte[] data = new byte[16384]; int count;
                Native.Require(DeviceIoControl(handle, 0x000900A8, null, 0, data, data.Length, out count, IntPtr.Zero), "screen_alias_verify_read");
                if (count < 16 || BitConverter.ToUInt16(data, 4) != count - 8) throw new StartupFailure("screen_alias_verify_size");
                if (name == "junction")
                {
                    byte[] expected = JunctionData(target);
                    if (count != expected.Length) throw new StartupFailure("screen_alias_verify_target");
                    for (int i = 0; i < count; i++) if (data[i] != expected[i]) throw new StartupFailure("screen_alias_verify_target");
                }
                else
                {
                    if (count < 20 || BitConverter.ToUInt32(data, 0) != 0xA000000Cu || BitConverter.ToUInt32(data, 16) != 0)
                        throw new StartupFailure("screen_alias_verify_tag");
                    int offset = BitConverter.ToUInt16(data, 8), size = BitConverter.ToUInt16(data, 10);
                    if ((size & 1) != 0 || offset + size > count - 20 ||
                        Encoding.Unicode.GetString(data, 20 + offset, size) != "\\??\\" + target)
                        throw new StartupFailure("screen_alias_verify_target");
                }
            }
            finally { Native.CloseHandle(handle); }
        }

        public void Dispose()
        {
            Exception failure = null;
            if (udpEvidence != null)
            {
                try { udpEvidence.Dispose(); udpEvidence = null; } catch (Exception error) { failure = error; }
            }
            foreach (Endpoint endpoint in endpoints)
                try { endpoint.Dispose(); } catch (Exception error) { if (failure == null) failure = error; }
            if (mapping != null)
            {
                try { mapping.Dispose(); mapping = null; } catch (Exception error) { if (failure == null) failure = error; }
            }
            if (failure != null) throw new StartupFailure("screen_resource_stop_uncertain");
        }

        sealed class Endpoint : IDisposable
        {
            readonly ContainmentScreen owner;
            readonly Socket server;
            readonly bool tcp;
            internal readonly int Family;
            internal bool Tcp { get { return tcp; } }
            internal readonly int PortValue;
            internal int InboundPort { get; private set; }
            readonly string controlNonce = Guid.NewGuid().ToString("N");
            readonly Thread worker;
            readonly AutoResetEvent positive = new AutoResetEvent(false);
            volatile bool stopping;
            internal int Port { get { return PortValue; } }
            internal Endpoint(ContainmentScreen owner, int family, bool tcp)
            {
                this.owner = owner; this.tcp = tcp; Family = family;
                server = new Socket(family == 4 ? AddressFamily.InterNetwork : AddressFamily.InterNetworkV6,
                    tcp ? SocketType.Stream : SocketType.Dgram, tcp ? ProtocolType.Tcp : ProtocolType.Udp);
                try
                {
                    server.ExclusiveAddressUse = true;
                    server.Bind(new IPEndPoint(family == 4 ? IPAddress.Loopback : IPAddress.IPv6Loopback, 0));
                    PortValue = ((IPEndPoint)server.LocalEndPoint).Port;
                    if (tcp) server.Listen(4);
                    worker = new Thread(Observe); worker.IsBackground = true; worker.Start();
                }
                catch { server.Dispose(); positive.Dispose(); throw; }
            }
            void Observe()
            {
                byte[] buffer = new byte[128];
                try
                {
                    while (!stopping)
                    {
                        if (!tcp)
                        {
                            TryInbound();
                            if (!server.Poll(20000, SelectMode.SelectRead)) continue;
                        }
                        int count;
                        EndPoint peer = new IPEndPoint(Family == 4 ? IPAddress.Loopback : IPAddress.IPv6Loopback, 0);
                        if (tcp)
                        {
                            using (Socket connection = server.Accept())
                            {
                                connection.ReceiveTimeout = 500; count = 0;
                                while (count < 5)
                                { int read = connection.Receive(buffer, count, 5 - count, SocketFlags.None); if (read == 0) break; count += read; }
                                int wanted = Encoding.ASCII.GetString(buffer, 0, count) == "host:" ? 37 : 38;
                                while (count < wanted)
                                { int read = connection.Receive(buffer, count, wanted - count, SocketFlags.None); if (read == 0) break; count += read; }
                            }
                        }
                        else count = server.ReceiveFrom(buffer, ref peer);
                        string message = Encoding.ASCII.GetString(buffer, 0, count);
                        if (message == "host:" + controlNonce)
                        {
                            if (!tcp && server.SendTo(buffer, 0, count, SocketFlags.None, peer) != count)
                                throw new StartupFailure("screen_udp_control_reply");
                            positive.Set();
                        }
                        else owner.Unauthorized();
                    }
                }
                catch (Exception) { if (!stopping) Interlocked.Exchange(ref owner.listenerFailure, 1); }
            }
            void TryInbound()
            {
                if (InboundPort != 0 || owner.childPid <= 0) return;
                string path = Path.Combine(owner.state, "udp" + Family + "-request.txt");
                if (!File.Exists(path)) return;
                ProductFiles.NoLinks(path);
                byte[] bytes = new byte[40]; int count;
                using (var input = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
                {
                    if (input.Length < 34 || input.Length > 38) return;
                    count = input.Read(bytes, 0, bytes.Length);
                }
                string text = Encoding.ASCII.GetString(bytes, 0, count); int port;
                if (!text.StartsWith(owner.run + ":", StringComparison.Ordinal) ||
                    !Int32.TryParse(text.Substring(33), System.Globalization.NumberStyles.None,
                        System.Globalization.CultureInfo.InvariantCulture, out port) || port < 1024 || port > 65535) return;
                // An untrusted port request is not authority to contact another process.
                if (!UdpOwner.Verified(Family, port, owner.childPid)) return;
                byte[] data = Encoding.ASCII.GetBytes("host-inbound:" + controlNonce);
                if (server.SendTo(data, new IPEndPoint(Family == 4 ? IPAddress.Loopback : IPAddress.IPv6Loopback, port)) != data.Length)
                    throw new StartupFailure("screen_udp_inbound_short_send");
                InboundPort = port;
            }
            internal void PositiveControl()
            {
                using (var client = new Socket(server.AddressFamily, server.SocketType, server.ProtocolType))
                {
                    client.SendTimeout = 500; client.ReceiveTimeout = 500;
                    IAsyncResult connect = client.BeginConnect(server.LocalEndPoint, null, null);
                    using (WaitHandle wait = connect.AsyncWaitHandle)
                    {
                        if (!wait.WaitOne(500)) throw new StartupFailure("screen_endpoint_connect_budget");
                        client.EndConnect(connect);
                    }
                    byte[] data = Encoding.ASCII.GetBytes("host:" + controlNonce);
                    if (client.Send(data) != data.Length || !positive.WaitOne(1000)) throw new StartupFailure("screen_endpoint_control");
                    if (!tcp)
                    {
                        byte[] reply = new byte[128]; int length = client.Receive(reply);
                        if (Encoding.ASCII.GetString(reply, 0, length) != "host:" + controlNonce)
                            throw new StartupFailure("screen_udp_bidirectional_control");
                    }
                }
            }
            public void Dispose()
            {
                if (stopping) return; stopping = true; server.Dispose();
                if (!worker.Join(1500)) throw new StartupFailure("screen_endpoint_stop");
                positive.Dispose();
            }
        }
    }

    // The report grammar intentionally permits only small ASCII objects, arrays,
    // unescaped strings and nonnegative integers. Duplicate keys never overwrite.
    internal sealed class ScreenJson
    {
        readonly string text; int at;
        ScreenJson(string text) { this.text = text; }
        internal static Dictionary<string, object> Read(string text)
        {
            if (text == null || text.Length > ContainmentEvidence.MaximumReportBytes) throw new StartupFailure("screen_json_size");
            var parser = new ScreenJson(text); var result = parser.Value(0) as Dictionary<string, object>;
            parser.Space(); if (parser.at != text.Length || result == null) throw new StartupFailure("screen_json_trailing");
            return result;
        }
        void Space() { while (at < text.Length && (text[at] == ' ' || text[at] == '\r' || text[at] == '\n' || text[at] == '\t')) at++; }
        void Need(char value) { Space(); if (at >= text.Length || text[at++] != value) throw new StartupFailure("screen_json_syntax"); }
        string Text()
        {
            Need('"'); int start = at;
            while (at < text.Length && text[at] != '"')
            { if (text[at] < 32 || text[at] > 126 || text[at] == '\\' || at - start > 100) throw new StartupFailure("screen_json_string"); at++; }
            string result = text.Substring(start, at - start); Need('"'); return result;
        }
        object Value(int depth)
        {
            Space(); if (depth > 5 || at >= text.Length) throw new StartupFailure("screen_json_depth");
            if (text[at] == '"') return Text();
            if (text[at] == '{')
            {
                at++; var map = new Dictionary<string, object>(StringComparer.Ordinal); Space();
                if (at < text.Length && text[at] == '}') { at++; return map; }
                while (true)
                {
                    string key = Text(); Need(':'); if (map.ContainsKey(key)) throw new StartupFailure("screen_json_duplicate");
                    map.Add(key, Value(depth + 1)); Space(); if (at < text.Length && text[at] == '}') { at++; return map; } Need(',');
                }
            }
            if (text[at] == '[')
            {
                at++; var list = new ArrayList(); Space(); if (at < text.Length && text[at] == ']') { at++; return list; }
                while (true)
                {
                    if (list.Count >= 128) throw new StartupFailure("screen_json_array"); list.Add(Value(depth + 1));
                    Space(); if (at < text.Length && text[at] == ']') { at++; return list; } Need(',');
                }
            }
            int start = at; while (at < text.Length && text[at] >= '0' && text[at] <= '9') at++;
            int number;
            if (start == at || (at - start > 1 && text[start] == '0') || !Int32.TryParse(text.Substring(start, at - start), out number))
                throw new StartupFailure("screen_json_number");
            return number;
        }
    }
}
