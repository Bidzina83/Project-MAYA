using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Security.Principal;
using System.Text;
using System.Web.Script.Serialization;

namespace ProjectMaya.WindowsRuntime
{
    internal static class ModelHostFiles
    {
        internal static string Prepare(string directory, string attempt, SecurityIdentifier user, string channel, string canary, string output)
        {
            string host=Path.Combine(directory,"host");ProductFiles.NoLinks(host);
            if(Directory.Exists(host)||File.Exists(host))throw new StartupFailure("model_host_already_exists");
            Directory.CreateDirectory(host,BridgeHostFiles.DirectoryAcl(user));Native.SetLabel(host,false);
            BridgeHostFiles.Verify(Directory.GetAccessControl(host),user,true);
            var rules=new[] {
                new Dictionary<string,object>{{"capability","model.egress"},{"target","model:maya-offline-fixture"},{"operation","infer"},{"actor_id","windows:"+user.Value}},
                new Dictionary<string,object>{{"capability","model.output"},{"target","model:maya-offline-fixture"},{"operation","disclose"},{"actor_id","windows:"+user.Value}}
            };
            var json=new JavaScriptSerializer();
            BridgeHostFiles.Write(Path.Combine(host,"request.json"),new byte[0],user);
            BridgeHostFiles.Write(Path.Combine(host,"audit.jsonl"),new byte[0],user);
            BridgeHostFiles.Write(Path.Combine(host,"policy.json"),Encoding.UTF8.GetBytes(json.Serialize(new Dictionary<string,object>{{"allow",rules}})),user);
            string day=DateTime.UtcNow.ToString("yyyy-MM-dd",CultureInfo.InvariantCulture);
            BridgeHostFiles.Write(Path.Combine(host,"worker.json"),Encoding.UTF8.GetBytes(json.Serialize(new Dictionary<string,object> {
                {"operator_sid",user.Value},{"attempt",attempt},{"channel_id",channel},{"utc_day",day},{"canary",canary},{"fixture_text",output}
            })),user);
            Recheck(directory,user);return day;
        }
        internal static void Recheck(string directory, SecurityIdentifier user)
        {
            string host=Path.Combine(directory,"host");ProductFiles.NoLinks(host);
            BridgeHostFiles.Verify(Directory.GetAccessControl(host),user,true);
            if(Directory.GetFileSystemEntries(host).Length!=4)throw new StartupFailure("model_host_inventory");
            foreach(string name in new[]{"request.json","policy.json","worker.json","audit.jsonl"})
            {
                string path=Path.Combine(host,name);ProductFiles.NoLinks(path);
                BridgeHostFiles.Verify(File.GetAccessControl(path),user,false);
            }
        }
        internal static byte[] ReadBounded(string path, int limit)
        {
            ProductFiles.NoLinks(path);
            using(var stream=new FileStream(path,FileMode.Open,FileAccess.Read,FileShare.None))
            using(var copy=new MemoryStream())
            {
                byte[] buffer=new byte[4096];int n;
                while((n=stream.Read(buffer,0,buffer.Length))>0)
                {if(copy.Length+n>limit)throw new StartupFailure("model_host_read_limit");copy.Write(buffer,0,n);}
                return copy.ToArray();
            }
        }
    }
}
