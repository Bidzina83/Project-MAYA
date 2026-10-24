using System;
using System.Collections.Generic;
using System.IO;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;
using ProjectMaya.WindowsRuntime;

internal static class BridgeFixtures
{
    sealed class GateStream : Stream
    {
        internal readonly ManualResetEvent Gate = new ManualResetEvent(false);
        public override bool CanRead { get { return true; } } public override bool CanWrite { get { return true; } }
        public override bool CanSeek { get { return false; } } public override long Length { get { throw new NotSupportedException(); } }
        public override long Position { get { throw new NotSupportedException(); } set { throw new NotSupportedException(); } }
        public override int Read(byte[] buffer,int offset,int count) { Gate.WaitOne(); return 0; }
        public override void Write(byte[] buffer,int offset,int count) { Gate.WaitOne(); }
        public override void Flush() { }
        public override long Seek(long x,SeekOrigin y) { throw new NotSupportedException(); }
        public override void SetLength(long x) { throw new NotSupportedException(); }
    }
    static int checks;
    static void Check(bool value) { checks++; if (!value) throw new Exception("bridge fixture "+checks); }
    static void Reject(Action action)
    { bool rejected=false; try { action(); } catch { rejected=true; } Check(rejected); }
    static int Main()
    {
        foreach (string invalid in new[] { "", "[]", "{}{}", "{\"x\":1,\"x\":2}", "{\"x\":NaN}", "{\"x\":Infinity}",
            "{\"x\":1.0}", "{\"x\":01}", "{\"x\":+1}", "{\"x\":2147483648}", "{\"x\":'str'}", "{\"x\":\"\\x20\"}",
            "{\"x\":\"\\ud800\"}", "{\"x\":true,}", "{\"x\":\"\n\"}", "\uFEFF{}", "{\"x\":[[[[[[[[[]]]]]]]]]}" })
            Reject(delegate { StrictJson.Parse(Encoding.UTF8.GetBytes(invalid)); });
        Reject(delegate { StrictJson.Parse(new byte[] {255}); });
        var parsed = StrictJson.Parse(Encoding.UTF8.GetBytes("{\"x\":true,\"n\":null,\"a\":[1,-2,0],\"s\":\"\\u0061\\n\"}"));
        Check(true.Equals(parsed["x"])); Check(parsed["n"]==null); Check(((List<object>)parsed["a"]).Count==3); Check("a\n".Equals(parsed["s"]));
        var message = new Dictionary<string,object> {{"v",1},{"type","fixture"},{"attempt",new string('a',32)}};
        byte[] frame = BridgeChannel.Encode(message);
        Check(BitConverter.ToInt32(frame,0)==frame.Length-4);
        using(var destination=new MemoryStream())
        using(var channel=new BridgeChannel(new MemoryStream(frame),destination))
        {
            Check("fixture".Equals(channel.Read(1000)["type"])); channel.Write(message,1000);
            Check(Convert.ToBase64String(frame)==Convert.ToBase64String(destination.ToArray()));
            Reject(delegate {channel.Read(1000);});
        }
        foreach(uint length in new uint[] {0,8193,uint.MaxValue})
            using(var channel=new BridgeChannel(new MemoryStream(BitConverter.GetBytes(length)),new MemoryStream()))
                Reject(delegate {channel.Read(1000);});
        var blockedRead = new GateStream();
        using(var channel = new BridgeChannel(blockedRead,new MemoryStream()))
        { Reject(delegate {channel.Read(30);}); blockedRead.Gate.Set(); }
        var blockedWrite = new GateStream();
        using(var channel = new BridgeChannel(new MemoryStream(),blockedWrite))
        { Reject(delegate {channel.Write(message,30);}); blockedWrite.Gate.Set(); }
        for(int size=0;size<frame.Length;size++)
        {
            byte[] truncated=new byte[size]; Array.Copy(frame,truncated,size);
            using(var channel=new BridgeChannel(new MemoryStream(truncated),new MemoryStream()))
                Reject(delegate {channel.Read(1000);});
        }
        Reject(delegate {BridgeRuntime.Shape(new Dictionary<string,object>{{"extra",1}},"v");});
        var user=new SecurityIdentifier("S-1-5-21-1-2-3-500");
        var directory=BridgeHostFiles.DirectoryAcl(user); BridgeHostFiles.Verify(directory,user,true); Check(true);
        var file=BridgeHostFiles.FileAcl(user); BridgeHostFiles.Verify(file,user,false); Check(true);
        directory.AddAccessRule(new FileSystemAccessRule(new SecurityIdentifier("S-1-15-2-1"),FileSystemRights.Read,AccessControlType.Allow));
        Reject(delegate {BridgeHostFiles.Verify(directory,user,true);});
        file.AddAccessRule(new FileSystemAccessRule(new SecurityIdentifier("S-1-1-0"),FileSystemRights.Read,AccessControlType.Allow));
        Reject(delegate {BridgeHostFiles.Verify(file,user,false);});
        Check(BridgeRuntime.Cases.Length==10);
        Check(string.Join(",",BridgeRuntime.Cases)=="N01,N02,N03,N04,N05,N06,N07,N08,N10,N12");
        Check(ProtectedPython.Version=="0.2.0-bridge-document.2");
        foreach (bool low in new[] { false, true })
        foreach (bool folder in new[] { false, true })
        {
            string sid = low ? "LW" : "ME", flags = folder ? "OICI" : "";
            Native.VerifyLabel(new RawSecurityDescriptor("S:(ML;"+flags+";NW;;;"+sid+")"), low, folder); Check(true);
            Reject(delegate { Native.VerifyLabel(new RawSecurityDescriptor("S:(ML;"+flags+";NW;;;"+(low?"ME":"LW")+")"), low, folder); });
            Reject(delegate { Native.VerifyLabel(new RawSecurityDescriptor("S:(ML;"+(folder?"":"OICI")+";NW;;;"+sid+")"), low, folder); });
            Reject(delegate { Native.VerifyLabel(new RawSecurityDescriptor("S:(ML;"+flags+";NR;;;"+sid+")"), low, folder); });
            Reject(delegate { Native.VerifyLabel(new RawSecurityDescriptor("S:"), low, folder); });
        }
        foreach(string path in new[] {"bridge_child_entry.py","bridge_worker_entry.py","bridge-contract.json","project_maya/bridge/worker.py","hermes_memory_check.py"})
            Check(ProductFiles.PayloadPath(path)==path.Replace('/',Path.DirectorySeparatorChar));
        var ids = new List<string>(); var events = new List<Dictionary<string,object>>(); string attempt = new string('a',32), hash = new string('b',64);
        for(int i=0;i<BridgeRuntime.Cases.Length;i++)
        {
            string current=BridgeRuntime.Cases[i]; ids.Add((i+1).ToString("x32"));
            string[] stages=current=="N01"?new[]{"read_intent","release_intent","delivery_observed"}:current=="N02"?new[]{"delivery_observed"}:
                current=="N10"?new[]{"read_intent","denied","delivery_observed"}:new[]{"denied","delivery_observed"};
            foreach(string stage in stages)
            {
                bool release=stage=="release_intent" || stage=="delivery_observed" || stage=="denied" && current=="N10";
                bool denied=stage=="denied" || stage=="delivery_observed" && current!="N01";
                var metadata=new Dictionary<string,object>{{"attempt",attempt},{"request_id",(i+100).ToString("x32")}};
                if(stage=="delivery_observed") metadata["coordinator_request_id"]=ids[i];
                else if(stage!="denied") { metadata["seq"]="1"; metadata["response_sha256"]=stage=="release_intent"?hash:""; metadata["document_resource"]="maya.synthetic.document.v1"; }
                events.Add(new Dictionary<string,object>{{"schema_version",1},{"timestamp","2026-10-23T00:00:00Z"},{"event_type","bridge."+stage},
                    {"decision",denied?"deny":"allow"},{"reason_code",stage=="delivery_observed"?current=="N01"?"bridge.sent":"bridge.withheld":"bridge."+stage},
                    {"actor_id","windows:"+user.Value},{"capability",release?"file.disclose":"file.read"},
                    {"target",release?"runtime:"+attempt:"maya.synthetic.document.v1"},{"operation",release?"release":"read"},
                    {"data_classification","internal-synthetic"},{"idempotency_key",null},{"metadata",metadata}});
            }
        }
        Func<byte[]> auditBytes=delegate { var text=new StringBuilder(); foreach(var item in events) text.Append(new JavaScriptSerializer().Serialize(item)).Append('\n'); return Encoding.UTF8.GetBytes(text.ToString()); };
        Check(BridgeAuditAdmission.Verify(auditBytes(),attempt,"windows:"+user.Value,hash,ids)==21);
        Reject(delegate {BridgeAuditAdmission.Verify(auditBytes(),attempt,"wrong",hash,ids);});
        Reject(delegate {BridgeAuditAdmission.Verify(auditBytes(),attempt,"windows:"+user.Value,new string('c',64),ids);});
        foreach(string key in new List<string>(events[0].Keys))
        { object old=events[0][key]; events[0].Remove(key); Reject(delegate {BridgeAuditAdmission.Verify(auditBytes(),attempt,"windows:"+user.Value,hash,ids);}); events[0][key]=old; }
        events[0]["target"]="runtime:"+attempt;
        Reject(delegate {BridgeAuditAdmission.Verify(auditBytes(),attempt,"windows:"+user.Value,hash,ids);});
        events[0]["target"]="maya.synthetic.document.v1";
        events.RemoveAt(events.Count-1);
        Reject(delegate {BridgeAuditAdmission.Verify(auditBytes(),attempt,"windows:"+user.Value,hash,ids);});
        Console.WriteLine(checks+" inert bridge codec/descriptor checks passed"); return 0;
    }
}
