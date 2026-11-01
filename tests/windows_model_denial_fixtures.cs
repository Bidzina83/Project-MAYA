using System;
using System.Collections.Generic;
using System.Text;
using System.Web.Script.Serialization;
using ProjectMaya.WindowsRuntime;

internal static class ModelDenialFixtures
{
    static int checks;
    static void Check(bool ok){checks++;if(!ok)throw new Exception("M02 fixture "+checks);}
    static void Reject(Action action){bool rejected=false;try{action();}catch{rejected=true;}Check(rejected);}
    static int Main()
    {
        string attempt=new string('a',32), request=new string('b',32), hash=new string('c',64), output=new string('d',64);
        string actor="windows:S-1-5-21-1-2-3-500";
        var metadata=new Dictionary<string,object> {
            {"attempt",attempt},{"request_id",request},{"route","maya.offline.model.v1"},
            {"endpoint","https://maya-offline-model.invalid/v1/chat/completions"},{"model","maya-offline-wire-v1"},
            {"destination","provider"},{"request_sha256",hash},{"response_sha256",""},{"request_bytes","2618"},
            {"response_bytes","0"},{"output_sha256",output},{"dispatches","0"},{"real_inference","false"}
        };
        var record=new Dictionary<string,object> {
            {"schema_version",1},{"timestamp","2026-10-24T12:00:00+00:00"},{"event_type","model_bridge.denied"},
            {"decision","deny"},{"reason_code","model_bridge.denied"},{"actor_id",actor},{"capability","model.egress"},
            {"target","model:maya-offline-fixture"},{"operation","infer"},{"data_classification","internal-synthetic"},
            {"idempotency_key",null},{"metadata",metadata}
        };
        Func<byte[]> raw=()=>Encoding.UTF8.GetBytes(new JavaScriptSerializer().Serialize(record)+"\n");
        Func<byte[],int> verify=bytes=>ModelDenialAdmission.Audit(bytes,attempt,actor,request,hash,2618,output);
        Check(verify(raw())==1);
        foreach(string key in new List<string>(record.Keys))
        {
            object old=record[key];record.Remove(key);Reject(()=>verify(raw()));record[key]=old;
            record[key]="wrong";Reject(()=>verify(raw()));record[key]=old;
        }
        foreach(string key in new List<string>(metadata.Keys))
        {
            object old=metadata[key];metadata[key]="wrong";Reject(()=>verify(raw()));metadata[key]=old;
            metadata.Remove(key);Reject(()=>verify(raw()));metadata[key]=old;
        }
        record["schema_version"]=true;Reject(()=>verify(raw()));record["schema_version"]=1;
        record["timestamp"]="2026-02-30T12:00:00Z";Reject(()=>verify(raw()));
        record["timestamp"]="2026-10-24T12:00:00+04:00";Reject(()=>verify(raw()));
        record["timestamp"]="2026-10-24T12:00:00+00:00";
        byte[] full=raw(), partial=new byte[full.Length-1];Array.Copy(full,partial,partial.Length);
        Reject(()=>verify(partial));Reject(()=>verify(Encoding.UTF8.GetBytes(Encoding.UTF8.GetString(full)+Encoding.UTF8.GetString(full))));
        Reject(()=>verify(new byte[131073]));Reject(()=>verify(new byte[]{255,10}));
        Reject(()=>ModelDenialAdmission.Audit(full,attempt,actor,request,hash,0,output));
        Reject(()=>ModelDenialAdmission.Audit(full,"wrong",actor,request,hash,2618,output));
        var effects=new Dictionary<string,object> {
            {"case","M02"},{"boundary","gateway_egress"},{"request_validated",true},{"gateway_denied",true},
            {"dispatches",0},{"confirmed_runtime_releases",0},{"confirmed_operator_releases",0},{"real_inference",false}
        };
        ModelDenialAdmission.Effects(effects);Check(true);
        foreach(string key in new List<string>(effects.Keys))
        {
            object old=effects[key];effects[key]="wrong";Reject(()=>ModelDenialAdmission.Effects(effects));effects[key]=old;
            effects.Remove(key);Reject(()=>ModelDenialAdmission.Effects(effects));effects[key]=old;
        }
        effects["dispatches"]=false;Reject(()=>ModelDenialAdmission.Effects(effects));effects["dispatches"]=0;
        effects["unexpected"]=true;Reject(()=>ModelDenialAdmission.Effects(effects));effects.Remove("unexpected");
        var report=new Dictionary<string,object> {
            {"schema","maya.offline.model.denial.child.v1"},{"attempt",attempt},{"completed",true},
            {"native_constructor",true},{"native_conversation",false},{"sdk_closed",true},{"origins_verified",true},
            {"distributions_verified",true},{"config_unchanged",true},{"model_requests",1},{"client_objects",2},
            {"real_inference",false},{"reason_type",""},{"denial_observed",true}
        };
        ModelDenialAdmission.Child(report,attempt);Check(true);
        foreach(string key in new List<string>(report.Keys))
        {
            object old=report[key];report[key]="wrong";Reject(()=>ModelDenialAdmission.Child(report,attempt));report[key]=old;
            report.Remove(key);Reject(()=>ModelDenialAdmission.Child(report,attempt));report[key]=old;
        }
        report["client_objects"]=9;Reject(()=>ModelDenialAdmission.Child(report,attempt));report["client_objects"]=2;
        report["model_requests"]=true;Reject(()=>ModelDenialAdmission.Child(report,attempt));report["model_requests"]=1;
#if HERMES_MODEL_DENY
        Check(ModelDenialAdmission.Enabled);
        Check(ProtectedPython.Version=="0.2.1-offline-denial.1");
        Check(ProtectedPython.Scope=="offline-hermes-model-denial-v1");
        Check(ProtectedPython.Consent.Contains("zero synthetic provider dispatches"));
        Check(ProtectedPython.Consent.Contains("NO external inference"));
        foreach(string name in new[]{"model_deny_child_entry.py","model_deny_worker_entry.py"})Check(ProductFiles.PayloadPath(name)==name);
#else
        Check(!ModelDenialAdmission.Enabled);
        foreach(string name in new[]{"model_deny_child_entry.py","model_deny_worker_entry.py"})Reject(()=>ProductFiles.PayloadPath(name));
#endif
        Console.WriteLine(checks+" inert M02 admission checks passed");return 0;
    }
}
