using System;
using System.Collections.Generic;
using System.IO;
using System.Security.AccessControl;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;
using System.Web.Script.Serialization;

namespace ProjectMaya.WindowsRuntime
{
    internal static class BridgeHostFiles
    {
        static readonly SecurityIdentifier Admin = new SecurityIdentifier("S-1-5-32-544"), System = new SecurityIdentifier("S-1-5-18");
        internal static string RandomHex(int count)
        { byte[] bytes = new byte[count]; using (var random = RandomNumberGenerator.Create()) random.GetBytes(bytes); return BitConverter.ToString(bytes).Replace("-", "").ToLowerInvariant(); }
        internal static string Hash(byte[] bytes)
        { using (var hash = SHA256.Create()) return BitConverter.ToString(hash.ComputeHash(bytes)).Replace("-", "").ToLowerInvariant(); }
        internal static DirectorySecurity DirectoryAcl(SecurityIdentifier user)
        {
            var acl = new DirectorySecurity(); acl.SetAccessRuleProtection(true, false); acl.SetOwner(Admin); acl.SetGroup(Admin);
            foreach (var sid in new[] { Admin, System, user }) acl.AddAccessRule(new FileSystemAccessRule(sid, FileSystemRights.FullControl,
                InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit, PropagationFlags.None, AccessControlType.Allow));
            return acl;
        }
        internal static FileSecurity FileAcl(SecurityIdentifier user)
        {
            var acl = new FileSecurity(); acl.SetAccessRuleProtection(true, false); acl.SetOwner(Admin); acl.SetGroup(Admin);
            foreach (var sid in new[] { Admin, System, user }) acl.AddAccessRule(new FileSystemAccessRule(sid, FileSystemRights.FullControl, AccessControlType.Allow));
            return acl;
        }
        internal static void Verify(FileSystemSecurity acl, SecurityIdentifier user, bool folder)
        {
            if (!acl.AreAccessRulesProtected || !acl.GetOwner(typeof(SecurityIdentifier)).Equals(Admin) ||
                !acl.GetGroup(typeof(SecurityIdentifier)).Equals(Admin)) throw new StartupFailure("bridge_host_acl_rejected");
            var allowed = new HashSet<string> { Admin.Value, System.Value, user.Value };
            var rules = acl.GetAccessRules(true, true, typeof(SecurityIdentifier));
            if (rules.Count != 3) throw new StartupFailure("bridge_host_acl_rejected");
            foreach (FileSystemAccessRule rule in rules)
                if (!allowed.Remove(rule.IdentityReference.Value) || rule.IsInherited || rule.AccessControlType != AccessControlType.Allow ||
                    rule.FileSystemRights != FileSystemRights.FullControl || rule.PropagationFlags != PropagationFlags.None ||
                    rule.InheritanceFlags != (folder ? InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit : InheritanceFlags.None))
                    throw new StartupFailure("bridge_host_acl_rejected");
        }
        static void Write(string path, byte[] content, SecurityIdentifier user)
        {
            ProductFiles.NoLinks(path);
            using (var file = new FileStream(path, FileMode.CreateNew, FileSystemRights.Write, FileShare.None, 4096, FileOptions.None, FileAcl(user)))
            { file.Write(content, 0, content.Length); file.Flush(true); }
            Native.SetLabel(path, false);
            Verify(File.GetAccessControl(path), user, false);
        }
        internal static string Prepare(string directory, string attempt, SecurityIdentifier user, string channel)
        {
            string host = Path.Combine(directory, "host"); ProductFiles.NoLinks(host);
            if (Directory.Exists(host) || File.Exists(host)) throw new StartupFailure("bridge_host_already_exists");
            Directory.CreateDirectory(host, DirectoryAcl(user)); Native.SetLabel(host, false);
            Verify(Directory.GetAccessControl(host), user, true);
            byte[] document = Encoding.ASCII.GetBytes("MAYA synthetic protected document " + RandomHex(32));
            string digest = Hash(document), actor = "windows:" + user.Value;
            var rules = new[] {
                new Dictionary<string, object> {{"capability","file.read"},{"target","maya.synthetic.document.v1"},{"operation","read"},{"actor_id",actor}},
                new Dictionary<string, object> {{"capability","file.disclose"},{"target","runtime:"+attempt},{"operation","release"},{"actor_id",actor}}
            };
            var json = new JavaScriptSerializer();
            Write(Path.Combine(host, "document.txt"), document, user);
            Write(Path.Combine(host, "policy.json"), Encoding.UTF8.GetBytes(json.Serialize(new Dictionary<string, object>{{"allow",rules}})), user);
            Write(Path.Combine(host, "audit.jsonl"), new byte[0], user);
            Write(Path.Combine(host, "worker.json"), Encoding.UTF8.GetBytes(json.Serialize(new Dictionary<string, object> {
                {"operator_sid",user.Value},{"attempt",attempt},{"channel_id",channel},{"document_sha256",digest}})), user);
            return digest;
        }
        internal static void Recheck(string directory, SecurityIdentifier user)
        {
            string host = Path.Combine(directory, "host"); ProductFiles.NoLinks(host);
            Verify(Directory.GetAccessControl(host), user, true);
            if (Directory.GetFileSystemEntries(host).Length != 4) throw new StartupFailure("bridge_host_inventory");
            foreach (string name in new[] { "document.txt", "policy.json", "audit.jsonl", "worker.json" })
            { string path = Path.Combine(host, name); ProductFiles.NoLinks(path); Verify(File.GetAccessControl(path), user, false); }
        }
    }
}
