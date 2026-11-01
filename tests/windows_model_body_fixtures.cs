using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Web.Script.Serialization;
using ProjectMaya.WindowsRuntime;

internal static class ModelBodyFixtures
{
    static int checks;
    static void Check(bool value){checks++;if(!value)throw new Exception("M03d fixture "+checks);}
    static void Reject(Action action){bool rejected=false;try{action();}catch{rejected=true;}Check(rejected);}
    static int Main(string[] args)
    {
        string attempt=new string('a',32),request=new string('b',32),command=new string('c',32),output=new string('d',64);
        string actor="windows:S-1-5-21-1-2-3-500";
        var vector=new JavaScriptSerializer().Deserialize<Dictionary<string,object>>(File.ReadAllText(args[0]));
        byte[] original=Convert.FromBase64String((string)vector["original_base64"]);
        Check(Convert.ToBase64String(ModelBodyAdmission.Mutate(original))==(string)vector["mutated_base64"]);
        foreach(object value in (System.Collections.IEnumerable)vector["controls"])
        {
            var item=(Dictionary<string,object>)value;
            byte[] input=Convert.FromBase64String((string)item["original"]);
            Check(Convert.ToBase64String(ModelBodyAdmission.Mutate(input))==(string)item["mutant"]);
        }
        Reject(()=>ModelBodyAdmission.Mutate(Encoding.UTF8.GetBytes("{}")));
        Reject(()=>ModelBodyAdmission.Mutate(new byte[4097]));
        string lease=new string('e',64);
        var envelope=new Dictionary<string,object>{{"v",1},{"type","model_request"},{"attempt",attempt},{"route","maya.offline.model.v1"},
            {"lease",lease},{"seq",1},{"method","POST"},{"path","/v1/chat/completions"},{"body",Encoding.UTF8.GetString(original)}};
        ModelBodyAdmission.Envelope(envelope,attempt,lease,original);Check(true);
        foreach(string key in new List<string>(envelope.Keys))
        {object old=envelope[key];envelope[key]="wrong";Reject(()=>ModelBodyAdmission.Envelope(envelope,attempt,lease,original));envelope[key]=old;}
        var metadata=ModelBodyAdmission.Metadata(attempt,request,command,original,output);
        ModelValidationAdmission.Evidence(metadata,vector["metadata"] as Dictionary<string,object>);Check(true);
        ModelValidationAdmission.Evidence(new Dictionary<string,object>(metadata),metadata);Check(true);
        var record=new Dictionary<string,object> {
            {"schema_version",1},{"timestamp","2026-10-31T12:00:00+00:00"},{"event_type","model_bridge.body_rejected"},
            {"decision","deny"},{"reason_code","model_bridge.wrong_body"},{"actor_id",actor},{"capability","model.egress"},
            {"target","model:maya-offline-fixture"},{"operation","infer"},{"data_classification","internal-synthetic"},
            {"idempotency_key",null},{"metadata",new Dictionary<string,object>(metadata)}
        };
        Func<byte[]> raw=()=>Encoding.UTF8.GetBytes(new JavaScriptSerializer().Serialize(record)+"\n");
        Func<byte[],int> verify=bytes=>ModelValidationAdmission.Audit(bytes,actor,metadata,false,false,true);
        Check(verify(raw())==1);
        Reject(()=>ModelValidationAdmission.Audit(raw(),actor,metadata));
        foreach(string key in new List<string>(record.Keys))
        {
            object old=record[key];record.Remove(key);Reject(()=>verify(raw()));record[key]=old;
            record[key]="wrong";Reject(()=>verify(raw()));record[key]=old;
        }
        var observed=(Dictionary<string,object>)record["metadata"];
        foreach(string key in new List<string>(observed.Keys))
        {
            object old=observed[key];observed[key]="wrong";Reject(()=>verify(raw()));observed[key]=old;
            observed.Remove(key);Reject(()=>verify(raw()));observed[key]=old;
        }
        observed["extra"]="wrong";Reject(()=>verify(raw()));observed.Remove("extra");
        observed["gateway_calls"]=0;Reject(()=>verify(raw()));observed["gateway_calls"]="0";
        record["schema_version"]=true;Reject(()=>verify(raw()));record["schema_version"]=1;
        record["timestamp"]="2026-02-30T12:00:00Z";Reject(()=>verify(raw()));
        record["timestamp"]="2026-10-31T12:00:00+04:00";Reject(()=>verify(raw()));record["timestamp"]="2026-10-31T12:00:00Z";
        byte[] full=raw(),shorter=new byte[full.Length-1];Array.Copy(full,shorter,shorter.Length);
        Reject(()=>verify(shorter));Reject(()=>verify(Encoding.UTF8.GetBytes(Encoding.UTF8.GetString(full)+Encoding.UTF8.GetString(full))));
        Reject(()=>verify(new byte[]{255,10}));Reject(()=>verify(new byte[131073]));
        Reject(()=>ModelBodyAdmission.Metadata(attempt,request,"wrong",original,output));
        Reject(()=>ModelBodyAdmission.Metadata(attempt,request,command,original,"wrong"));
#if HERMES_MODEL_BODY
        Check(ModelBodyAdmission.Enabled);Check(!ModelDenialAdmission.Enabled);
        Check(ProtectedPython.Version=="0.2.1-offline-body.1");
        Check(ProtectedPython.Scope=="offline-hermes-body-validation-v1");
        Check(ProtectedPython.Consent.Contains("WORKER validation"));Check(ProtectedPython.Consent.Contains("NO external inference"));
        foreach(string file in new[]{"model_body_child_entry.py","model_body_worker_entry.py"})Check(ProductFiles.PayloadPath(file)==file);
        foreach(string file in new[]{"model_deny_child_entry.py","model_deny_worker_entry.py","model_attempt_child_entry.py","model_attempt_worker_entry.py"})Reject(()=>ProductFiles.PayloadPath(file));
#else
        Check(!ModelBodyAdmission.Enabled);
        foreach(string file in new[]{"model_body_child_entry.py","model_body_worker_entry.py"})Reject(()=>ProductFiles.PayloadPath(file));
#endif
        Console.WriteLine(checks+" inert M03d validation checks passed");return 0;
    }
}
