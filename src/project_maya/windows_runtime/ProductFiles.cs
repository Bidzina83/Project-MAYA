using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Reflection;
using System.Security.AccessControl;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;
using System.Web.Script.Serialization;

namespace ProjectMaya.WindowsRuntime
{
    internal sealed class PayloadFile
    {
        public string path { get; set; }
        public string sha256 { get; set; }
        public long size { get; set; }
    }
    internal sealed class PayloadIndex
    {
        public string zip_sha256 { get; set; }
        public string python_version { get; set; }
        public List<PayloadFile> files { get; set; }
    }

    internal static class ProductFiles
    {
        internal static readonly string Root = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData), "MayaProtectedPython-Startup1");
        static readonly SecurityIdentifier Admin = new SecurityIdentifier("S-1-5-32-544");
        static readonly SecurityIdentifier System = new SecurityIdentifier("S-1-5-18");
        static readonly SecurityIdentifier Users = new SecurityIdentifier("S-1-5-32-545");
        const InheritanceFlags Both = InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit;

        internal static void NoLinks(string path)
        {
            string absolute = Path.GetFullPath(path);
            for (string cursor = absolute; cursor != null; cursor = Path.GetDirectoryName(cursor))
                if ((Directory.Exists(cursor) || File.Exists(cursor)) &&
                    (File.GetAttributes(cursor) & FileAttributes.ReparsePoint) != 0)
                    throw new StartupFailure("reparse_path_rejected");
        }
        static DirectorySecurity BaseSecurity()
        {
            var acl = new DirectorySecurity(); acl.SetAccessRuleProtection(true, false);
            acl.SetOwner(Admin); acl.SetGroup(Admin);
            Allow(acl, Admin, FileSystemRights.FullControl, Both, PropagationFlags.None);
            Allow(acl, System, FileSystemRights.FullControl, Both, PropagationFlags.None);
            return acl;
        }
        static void Allow(DirectorySecurity acl, SecurityIdentifier who, FileSystemRights rights,
            InheritanceFlags inheritance, PropagationFlags propagation)
        {
            acl.AddAccessRule(new FileSystemAccessRule(who, rights, inheritance, propagation, AccessControlType.Allow));
        }
        internal static DirectorySecurity RootSecurity()
        {
            var acl = BaseSecurity(); Allow(acl, Users, FileSystemRights.Traverse, InheritanceFlags.None, PropagationFlags.None);
            return acl;
        }
        internal static void VerifyRoot()
        {
            NoLinks(Root);
            const AccessControlSections sections = AccessControlSections.Access | AccessControlSections.Owner | AccessControlSections.Group;
            VerifyRootDescriptor(Directory.GetAccessControl(Root, sections));
        }
        internal static void VerifyRootDescriptor(DirectorySecurity acl)
        {
            if (!acl.AreAccessRulesProtected || !acl.GetOwner(typeof(SecurityIdentifier)).Equals(Admin) ||
                !acl.GetGroup(typeof(SecurityIdentifier)).Equals(Admin)) throw new StartupFailure("product_root_permissions_mismatch");
            var rules = acl.GetAccessRules(true, true, typeof(SecurityIdentifier));
            if (rules.Count != 3) throw new StartupFailure("product_root_permissions_mismatch");
            var seen = new HashSet<string>();
            foreach (FileSystemAccessRule rule in rules)
            {
                string who = rule.IdentityReference.Value;
                if (!seen.Add(who) || rule.IsInherited || rule.AccessControlType != AccessControlType.Allow ||
                    rule.PropagationFlags != PropagationFlags.None) throw new StartupFailure("product_root_permissions_mismatch");
                if (who == Admin.Value || who == System.Value)
                {
                    if (rule.FileSystemRights != FileSystemRights.FullControl || rule.InheritanceFlags != Both)
                        throw new StartupFailure("product_root_permissions_mismatch");
                }
                else if (who != Users.Value || rule.FileSystemRights != (FileSystemRights.Traverse | FileSystemRights.Synchronize) ||
                    rule.InheritanceFlags != InheritanceFlags.None) throw new StartupFailure("product_root_permissions_mismatch");
            }
        }
        internal static void EnsureRoot()
        {
            NoLinks(Root);
            if (!Directory.Exists(Root)) Directory.CreateDirectory(Root, RootSecurity());
            VerifyRoot();
        }
        internal static void CreateAttempt(string directory, SecurityIdentifier user)
        {
            NoLinks(directory);
            if (Directory.Exists(directory) || File.Exists(directory)) throw new StartupFailure("attempt_already_exists");
            var acl = BaseSecurity(); Allow(acl, user, FileSystemRights.ReadAndExecute, Both, PropagationFlags.None);
            Directory.CreateDirectory(directory, acl);
        }
        internal static string HashFile(string path)
        {
            NoLinks(path); using (var file = File.OpenRead(path)) return Hash(file);
        }
        static string Hash(Stream stream)
        {
            using (var sha = SHA256.Create()) return BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", "").ToLowerInvariant();
        }
        internal static string PayloadPath(string relative)
        {
            if (String.IsNullOrEmpty(relative) || relative.Length > 220 || relative.Contains("\\") || relative.Contains(":") || relative.StartsWith("/"))
                throw new StartupFailure("payload_path_rejected");
            foreach (string part in relative.Split('/'))
            {
                string stem = part.Split('.')[0].ToUpperInvariant();
                if (part.Length == 0 || part == "." || part == ".." || part.EndsWith(".") || part.EndsWith(" ") ||
                    part.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0 ||
                    stem == "CON" || stem == "PRN" || stem == "AUX" || stem == "NUL" ||
                    (stem.Length == 4 && (stem.StartsWith("COM") || stem.StartsWith("LPT")) && stem[3] >= '0' && stem[3] <= '9'))
                    throw new StartupFailure("payload_path_rejected");
            }
            if (relative != "startup_check.py" && relative != "containment_check.py" && !relative.StartsWith("python/", StringComparison.Ordinal) &&
                !relative.StartsWith("notices/", StringComparison.Ordinal)) throw new StartupFailure("payload_scope_rejected");
            return relative.Replace('/', Path.DirectorySeparatorChar);
        }
        internal static PayloadIndex ReadIndex(Stream stream)
        {
            PayloadIndex index;
            using (var reader = new StreamReader(stream, Encoding.UTF8))
                index = new JavaScriptSerializer { MaxJsonLength = 1024 * 1024 }.Deserialize<PayloadIndex>(reader.ReadToEnd());
            if (index == null || index.python_version != "3.13.14" || index.files == null ||
                index.files.Count < 3 || index.files.Count > 2000 || !Digest(index.zip_sha256))
                throw new StartupFailure("payload_index_rejected");
            var names = new HashSet<string>(StringComparer.OrdinalIgnoreCase); long total = 0;
            foreach (var file in index.files)
            {
                PayloadPath(file.path);
                if (!names.Add(file.path) || !Digest(file.sha256) || file.size < 0 || file.size > 32 * 1024 * 1024)
                    throw new StartupFailure("payload_inventory_rejected");
                total = checked(total + file.size);
                if (total > 256 * 1024 * 1024) throw new StartupFailure("payload_size_rejected");
            }
            if (!names.Contains("python/python.exe") || !names.Contains("python/python313.dll") || !names.Contains("startup_check.py"))
                throw new StartupFailure("payload_required_file_missing");
            return index;
        }
        static bool Digest(string text)
        {
            return text != null && text.Length == 64 && text.All(c => c >= '0' && c <= '9' || c >= 'a' && c <= 'f');
        }
        internal static void ExtractPayload(string directory)
        {
            var assembly = Assembly.GetExecutingAssembly(); PayloadIndex index;
            using (var manifest = assembly.GetManifestResourceStream("MayaPython.payload-index.json"))
            {
                if (manifest == null) throw new StartupFailure("embedded_index_missing");
                index = ReadIndex(manifest);
            }
            using (var payload = assembly.GetManifestResourceStream("MayaPython.payload.zip"))
            {
                if (payload == null || Hash(payload) != index.zip_sha256) throw new StartupFailure("embedded_payload_hash_mismatch");
                payload.Position = 0;
                using (var zip = new ZipArchive(payload, ZipArchiveMode.Read))
                {
                    if (zip.Entries.Count != index.files.Count) throw new StartupFailure("embedded_payload_inventory_mismatch");
                    string runtime = Path.Combine(directory, "runtime"); Directory.CreateDirectory(runtime);
                    var entries = new Dictionary<string, ZipArchiveEntry>(StringComparer.OrdinalIgnoreCase);
                    foreach (var entry in zip.Entries)
                    {
                        PayloadPath(entry.FullName);
                        if (entries.ContainsKey(entry.FullName)) throw new StartupFailure("duplicate_archive_path");
                        entries.Add(entry.FullName, entry);
                    }
                    foreach (var file in index.files)
                    {
                        ZipArchiveEntry entry;
                        if (!entries.TryGetValue(file.path, out entry) || entry.Length != file.size)
                            throw new StartupFailure("embedded_file_missing");
                        string destination = Path.Combine(runtime, PayloadPath(file.path));
                        Directory.CreateDirectory(Path.GetDirectoryName(destination)); NoLinks(destination);
                        using (var input = entry.Open())
                        using (var output = new FileStream(destination, FileMode.CreateNew, FileAccess.Write, FileShare.None))
                        {
                            byte[] buffer = new byte[8192]; long count = 0; int got;
                            while ((got = input.Read(buffer, 0, buffer.Length)) > 0)
                            {
                                count += got;
                                if (count > file.size) throw new StartupFailure("embedded_file_size_mismatch");
                                output.Write(buffer, 0, got);
                            }
                            if (count != file.size) throw new StartupFailure("embedded_file_size_mismatch");
                            output.Flush(true);
                        }
                        if (HashFile(destination) != file.sha256) throw new StartupFailure("embedded_file_hash_mismatch");
                    }
                }
            }
        }
        internal static void Grant(string directory, SecurityIdentifier package, SecurityIdentifier user)
        {
            string runtime = Path.Combine(directory, "runtime"), state = Path.Combine(directory, "state");
            NoLinks(directory);
            AdminOwnTree(runtime);
            var top = Directory.GetAccessControl(directory);
            Allow(top, package, FileSystemRights.Traverse, InheritanceFlags.None, PropagationFlags.None);
            Directory.SetAccessControl(directory, top);
            Directory.SetAccessControl(runtime, RuntimeSecurity(package, user));
            var write = StateSecurity(package, user);
            FileSystemRights rw = FileSystemRights.Read | FileSystemRights.Write | FileSystemRights.Delete |
                FileSystemRights.DeleteSubdirectoriesAndFiles | FileSystemRights.Synchronize;
            if (Directory.Exists(state)) throw new StartupFailure("private_state_already_exists");
            Directory.CreateDirectory(state, write);
            Native.SetLabel(state, true);
            VerifyGrant(runtime, package, FileSystemRights.ReadAndExecute | FileSystemRights.Synchronize);
            VerifyGrant(state, package, rw | FileSystemRights.Traverse);
            if (Directory.GetFileSystemEntries(state).Length != 0) throw new StartupFailure("private_state_not_empty");
        }
        static void AdminOwnTree(string path)
        {
            NoLinks(path);
            if (Directory.Exists(path))
            {
                var owner = new DirectorySecurity(); owner.SetOwner(Admin);
                Directory.SetAccessControl(path, owner);
                if (!Directory.GetAccessControl(path, AccessControlSections.Owner).GetOwner(typeof(SecurityIdentifier)).Equals(Admin))
                    throw new StartupFailure("runtime_owner_mismatch");
                foreach (string child in Directory.GetFileSystemEntries(path)) AdminOwnTree(child);
            }
            else
            {
                var owner = new FileSecurity(); owner.SetOwner(Admin);
                File.SetAccessControl(path, owner);
                if (!File.GetAccessControl(path, AccessControlSections.Owner).GetOwner(typeof(SecurityIdentifier)).Equals(Admin))
                    throw new StartupFailure("runtime_owner_mismatch");
            }
        }
        internal static DirectorySecurity RuntimeSecurity(SecurityIdentifier package, SecurityIdentifier user)
        {
            var read = BaseSecurity();
            Allow(read, user, FileSystemRights.ReadAndExecute, Both, PropagationFlags.None);
            Allow(read, package, FileSystemRights.ReadAndExecute, Both, PropagationFlags.None);
            return read;
        }
        internal static DirectorySecurity StateSecurity(SecurityIdentifier package, SecurityIdentifier user)
        {
            var write = BaseSecurity(); Allow(write, user, FileSystemRights.Modify, Both, PropagationFlags.None);
            FileSystemRights rw = FileSystemRights.Read | FileSystemRights.Write | FileSystemRights.Delete |
                FileSystemRights.DeleteSubdirectoriesAndFiles | FileSystemRights.Synchronize;
            Allow(write, package, rw | FileSystemRights.Traverse, InheritanceFlags.ContainerInherit, PropagationFlags.None);
            Allow(write, package, rw, InheritanceFlags.ObjectInherit, PropagationFlags.InheritOnly);
            return write;
        }
        static void VerifyGrant(string directory, SecurityIdentifier package, FileSystemRights rights)
        {
            var rules = Directory.GetAccessControl(directory).GetAccessRules(true, true, typeof(SecurityIdentifier));
            bool found = false;
            foreach (FileSystemAccessRule rule in rules)
                if (rule.IdentityReference.Equals(package) && rule.PropagationFlags == PropagationFlags.None &&
                    rule.AccessControlType == AccessControlType.Allow && rule.FileSystemRights == rights) found = true;
            if (!found) throw new StartupFailure("package_file_grant_not_verified");
        }
        internal static void Revoke(string directory, SecurityIdentifier package)
        {
            CheckTreeNoLinks(directory);
            foreach (string path in new[] { Path.Combine(directory, "runtime"), Path.Combine(directory, "state"), directory })
            {
                if (!Directory.Exists(path)) continue;
                NoLinks(path);
                var acl = Directory.GetAccessControl(path); acl.PurgeAccessRules(package); Directory.SetAccessControl(path, acl);
            }
            string state = Path.Combine(directory, "state");
            if (Directory.Exists(state)) Native.SetLabel(state, false);
            CheckRevoked(directory, package);
        }
        static void CheckTreeNoLinks(string path)
        {
            NoLinks(path);
            if (Directory.Exists(path)) foreach (string child in Directory.GetFileSystemEntries(path)) CheckTreeNoLinks(child);
        }
        static void CheckRevoked(string path, SecurityIdentifier package)
        {
            NoLinks(path);
            bool folder = Directory.Exists(path);
            var rules = folder ? Directory.GetAccessControl(path).GetAccessRules(true, true, typeof(SecurityIdentifier)) :
                File.GetAccessControl(path).GetAccessRules(true, true, typeof(SecurityIdentifier));
            foreach (FileSystemAccessRule rule in rules)
                if (rule.IdentityReference.Equals(package)) throw new StartupFailure("package_file_grant_remains");
            if (folder) foreach (string child in Directory.GetFileSystemEntries(path)) CheckRevoked(child, package);
        }
    }
}
