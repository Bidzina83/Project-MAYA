using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Web.Script.Serialization;
using ProjectMaya.WindowsRuntime;

internal static class ReplayFixtures
{
    static int checks;
    static void Check(bool ok){checks++;if(!ok)throw new Exception("Replay fixture "+checks);}
    static void Reject(Action action){bool rejected=false;try{action();}catch{rejected=true;}Check(rejected);}
    static int Main(string[] args)
    {
        var json=new JavaScriptSerializer();var vector=json.Deserialize<Dictionary<string,object>>(File.ReadAllText(args[0]));
        byte[] body=Convert.FromBase64String((string)vector["body"]),response=Convert.FromBase64String((string)vector["response"]);
        string attempt=new string('a',32),service=new string('b',32),first=new string('c',32),delivery=new string('d',32),replay=new string('f',32),lease=new string('e',64);
        string output=(string)vector["output_sha256"],actor="windows:S-1-5-21-1-2-3-500";
        var expected=ModelReplayAdmission.Metadata(attempt,service,first,delivery,replay,lease,body,response,output,"600","800");
        Check(expected.Count==50);ModelValidationAdmission.Evidence(expected,vector["metadata"] as Dictionary<string,object>);Check(true);
        var records=new List<Dictionary<string,object>>();foreach(object item in (IEnumerable)vector["records"])records.Add((Dictionary<string,object>)item);
        Func<byte[]> raw=()=>Encoding.UTF8.GetBytes(String.Join("\n",records.ConvertAll(r=>json.Serialize(r)))+"\n");
        Func<byte[],int> audit=bytes=>ModelReplayAdmission.Audit(bytes,actor,expected);
        Check(audit(raw())==5);
        Reject(()=>ModelAuditAdmission.Verify(raw(),attempt,actor,service,BridgeHostFiles.Hash(body),body.Length,
            BridgeHostFiles.Hash(response),response.Length,output,delivery,new string('9',32)));
        foreach(var record in records)
        {
            foreach(string key in new List<string>(record.Keys))
            {object old=record[key];record.Remove(key);Reject(()=>audit(raw()));record[key]=old;record[key]="wrong";Reject(()=>audit(raw()));record[key]=old;}
            var meta=record["metadata"] as Dictionary<string,object>;
            foreach(string key in new List<string>(meta.Keys))
            {object old=meta[key];meta.Remove(key);Reject(()=>audit(raw()));meta[key]=old;meta[key]="wrong";Reject(()=>audit(raw()));meta[key]=old;}
            meta["extra"]="wrong";Reject(()=>audit(raw()));meta.Remove("extra");
            record["schema_version"]=true;Reject(()=>audit(raw()));record["schema_version"]=1;
            record["timestamp"]="2026-02-30T00:00:00Z";Reject(()=>audit(raw()));record["timestamp"]="2026-10-31T00:00:00Z";
        }
        records[0]["timestamp"]="2026-11-01T00:00:00Z";Reject(()=>audit(raw()));records[0]["timestamp"]="2026-10-31T00:00:00Z";
        string full=Encoding.UTF8.GetString(raw()),one=json.Serialize(records[0])+"\n";
        foreach(string text in new[]{"",full.TrimEnd('\n'),full+one,one+full,full.Replace("\"schema_version\":1","\"schema_version\":true"),
            full.Replace("\"decision\":\"allow\"","\"decision\":\"allow\",\"decision\":\"allow\"")})Reject(()=>audit(Encoding.UTF8.GetBytes(text)));
        Reject(()=>audit(new byte[131073]));Reject(()=>audit(new byte[]{255,10}));
        var temp=records[0];records[0]=records[4];records[4]=temp;Reject(()=>audit(raw()));records[4]=records[0];records[0]=temp;
        foreach(object value in new object[]{null,true,800,"0800","2000","-1","1.0","1\n"})
            Reject(()=>ModelReplayAdmission.Age(new Dictionary<string,object>{{"age",value}},"age"));
        foreach(string value in new[]{"0","1","1999"})Check(ModelReplayAdmission.Age(new Dictionary<string,object>{{"age",value}},"age")==value);
        Reject(()=>ModelReplayAdmission.Metadata(attempt,service,first,delivery,replay,lease,body,response,output,"600","599"));
        Reject(()=>ModelReplayAdmission.Metadata(attempt,service,first,delivery,first,lease,body,response,output,"600","800"));
        Reject(()=>ModelReplayAdmission.Metadata(attempt,service,first,delivery,replay,"bad",body,response,output,"600","800"));
        var child=new Dictionary<string,object>{{"schema","maya.offline.model.child.v1"},{"attempt",attempt},{"completed",true},
            {"native_constructor",true},{"native_conversation",true},{"sdk_closed",true},{"origins_verified",true},
            {"distributions_verified",true},{"config_unchanged",true},{"model_requests",1},{"client_objects",2},{"real_inference",false},{"reason_type",""}};
        ModelReplayAdmission.Child(child,attempt);Check(true);
        foreach(string key in new List<string>(child.Keys))
        {object old=child[key];child.Remove(key);Reject(()=>ModelReplayAdmission.Child(child,attempt));child[key]=old;child[key]="wrong";Reject(()=>ModelReplayAdmission.Child(child,attempt));child[key]=old;}
        child["denial_observed"]=true;Reject(()=>ModelReplayAdmission.Child(child,attempt));child.Remove("denial_observed");
#if HERMES_MODEL_REPLAY
        Check(ModelReplayAdmission.Enabled);Check(ModelValidationAdmission.Enabled);Check(!ModelRevocationAdmission.Enabled);
        Check(ProtectedPython.Version=="0.2.1-offline-replay.1");Check(ProtectedPython.Scope=="offline-hermes-consumed-lease-v1");
        Check(ProtectedPython.Consent.Contains("POSITIVE"));Check(ProtectedPython.Consent.Contains("NEW trusted command ID"));
        foreach(string file in new[]{"model_replay_child_entry.py","model_replay_worker_entry.py","model_validation_worker_entry.py"})Check(ProductFiles.PayloadPath(file)==file);
        foreach(string file in new[]{"model_revoke_child_entry.py","model_revoke_worker_entry.py"})Reject(()=>ProductFiles.PayloadPath(file));
#else
        Check(!ModelReplayAdmission.Enabled);foreach(string file in new[]{"model_replay_child_entry.py","model_replay_worker_entry.py"})Reject(()=>ProductFiles.PayloadPath(file));
#endif
        Console.WriteLine(checks+" inert M04c replay checks passed");return 0;
    }
}
