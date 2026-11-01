using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Web.Script.Serialization;
using ProjectMaya.WindowsRuntime;

internal static class ModelValidationFixtures
{
    static int checks;
    static void Check(bool value){checks++;if(!value)throw new Exception("M03a fixture "+checks);}
    static void Reject(Action action){bool rejected=false;try{action();}catch{rejected=true;}Check(rejected);}
    static int Main(string[] args)
    {
        string attempt=new string('a',32),request=new string('b',32),command=new string('c',32),output=new string('d',64);
        string actor="windows:S-1-5-21-1-2-3-500";
        byte[] original=Encoding.UTF8.GetBytes("{\"messages\":[{\"role\":\"user\",\"content\":\"caf\u00e9 maya-offline-wire-v1\"}],\"model\":\"maya-offline-wire-v1\",\"max_tokens\":32,\"stream\":false}");
        byte[] mutant=ModelValidationAdmission.Mutate(original);
        string changed=Encoding.UTF8.GetString(mutant);
        Check(changed.Contains("caf\u00e9 maya-offline-wire-v1"));
        Check(changed.Contains("\"model\":\"maya-offline-wire-v0\""));Check(original.Length==mutant.Length);
        Reject(()=>ModelValidationAdmission.Mutate(Encoding.UTF8.GetBytes(changed.Replace("tokens\":32","tokens\":31"))));
        Reject(()=>ModelValidationAdmission.Mutate(Encoding.UTF8.GetBytes("{}")));
        Reject(()=>ModelValidationAdmission.Mutate(mutant));Reject(()=>ModelValidationAdmission.Mutate(new byte[4097]));
        if(args.Length==1)
        {
            var vector=StrictJson.Parse(File.ReadAllBytes(args[0]));
            byte[] native=Convert.FromBase64String((string)vector["original_base64"]);
            byte[] expected=Convert.FromBase64String((string)vector["mutated_base64"]);
            byte[] actual=ModelValidationAdmission.Mutate(native);
            Check(Convert.ToBase64String(actual)==Convert.ToBase64String(expected));
            Check(BridgeHostFiles.Hash(actual)==(string)vector["mutated_sha256"]);
        }
        var metadata=ModelValidationAdmission.Metadata(attempt,request,command,original,output);
        ModelValidationAdmission.Evidence(new Dictionary<string,object>(metadata),metadata);Check(true);
        var record=new Dictionary<string,object> {
            {"schema_version",1},{"timestamp","2026-10-31T12:00:00+00:00"},{"event_type","model_bridge.validation_rejected"},
            {"decision","deny"},{"reason_code","model_bridge.wrong_model"},{"actor_id",actor},{"capability","model.egress"},
            {"target","model:maya-offline-fixture"},{"operation","infer"},{"data_classification","internal-synthetic"},
            {"idempotency_key",null},{"metadata",new Dictionary<string,object>(metadata)}
        };
        Func<byte[]> raw=()=>Encoding.UTF8.GetBytes(new JavaScriptSerializer().Serialize(record)+"\n");
        Func<byte[],int> verify=bytes=>ModelValidationAdmission.Audit(bytes,actor,metadata);
        Check(verify(raw())==1);
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
        Reject(()=>ModelValidationAdmission.Metadata(attempt,request,"wrong",original,output));
        Reject(()=>ModelValidationAdmission.Metadata(attempt,request,command,original,"wrong"));
#if HERMES_MODEL_VALIDATION
        Check(ModelValidationAdmission.Enabled);Check(!ModelDenialAdmission.Enabled);
        Check(ProtectedPython.Version=="0.2.1-offline-validation.2");
        Check(ProtectedPython.Scope=="offline-hermes-model-validation-v1");
        Check(ProtectedPython.Consent.Contains("WORKER validation"));Check(ProtectedPython.Consent.Contains("NO external inference"));
        foreach(string file in new[]{"model_validation_child_entry.py","model_validation_worker_entry.py"})Check(ProductFiles.PayloadPath(file)==file);
        foreach(string file in new[]{"model_deny_child_entry.py","model_deny_worker_entry.py"})Reject(()=>ProductFiles.PayloadPath(file));
#else
        Check(!ModelValidationAdmission.Enabled);
        foreach(string file in new[]{"model_validation_child_entry.py","model_validation_worker_entry.py"})Reject(()=>ProductFiles.PayloadPath(file));
#endif
        Console.WriteLine(checks+" inert M03a validation checks passed");return 0;
    }
}
