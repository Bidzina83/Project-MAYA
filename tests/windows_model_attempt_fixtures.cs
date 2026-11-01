using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Web.Script.Serialization;
using ProjectMaya.WindowsRuntime;

internal static class ModelAttemptFixtures
{
    static int checks;
    static void Check(bool value){checks++;if(!value)throw new Exception("M03c fixture "+checks);}
    static void Reject(Action action){bool rejected=false;try{action();}catch{rejected=true;}Check(rejected);}
    static int Main(string[] args)
    {
        // The trusted fixture bundles several bounded messages; it is not one pipe frame.
        var vector=new JavaScriptSerializer().Deserialize<Dictionary<string,object>>(File.ReadAllText(args[0]));
        string attempt=(string)vector["attempt"],lease=(string)vector["lease"],request=(string)vector["request_id"],
            command=(string)vector["command_id"],output=(string)vector["output_hash"],actor=(string)vector["actor"];
        byte[] body=Convert.FromBase64String((string)vector["body_base64"]);
        var original=StrictJson.Parse(Encoding.UTF8.GetBytes(new JavaScriptSerializer().Serialize(vector["original"])));
        var mutant=ModelAttemptAdmission.Mutate(original,attempt,lease,body);
        foreach(string key in original.Keys)Check(Object.Equals(original[key],mutant[key])==(key!="attempt"));
        Check(ModelAttemptAdmission.Mismatch(attempt).Equals(mutant["attempt"]));
        foreach(string key in new List<string>(original.Keys))
        {
            object old=original[key];original.Remove(key);Reject(()=>ModelAttemptAdmission.Mutate(original,attempt,lease,body));original[key]=old;
            original[key]="wrong";Reject(()=>ModelAttemptAdmission.Mutate(original,attempt,lease,body));original[key]=old;
        }
        original["extra"]=1;Reject(()=>ModelAttemptAdmission.Mutate(original,attempt,lease,body));original.Remove("extra");
        original["v"]=true;Reject(()=>ModelAttemptAdmission.Mutate(original,attempt,lease,body));original["v"]=1;
        Check(Convert.ToBase64String(ModelAttemptAdmission.Projection(attempt,lease,body,false))==(string)vector["original_projection_base64"]);
        Check(Convert.ToBase64String(ModelAttemptAdmission.Projection(attempt,lease,body,true))==(string)vector["mutated_projection_base64"]);
        var expected=ModelAttemptAdmission.Metadata(attempt,request,command,lease,body,output);
        var python=vector["metadata"] as Dictionary<string,object>;
        ModelValidationAdmission.Evidence(expected,python);Check(true);
        var record=vector["audit"] as Dictionary<string,object>;
        Func<byte[]> raw=()=>Encoding.UTF8.GetBytes(new JavaScriptSerializer().Serialize(record)+"\n");
        Func<byte[],int> audit=bytes=>ModelValidationAdmission.Audit(bytes,actor,expected,false,true);
        Check(audit(raw())==1);
        foreach(string key in new List<string>(record.Keys))
        {
            object old=record[key];record.Remove(key);Reject(()=>audit(raw()));record[key]=old;
            record[key]="wrong";Reject(()=>audit(raw()));record[key]=old;
        }
        var metadata=record["metadata"] as Dictionary<string,object>;
        foreach(string key in new List<string>(metadata.Keys))
        {
            object old=metadata[key];metadata.Remove(key);Reject(()=>audit(raw()));metadata[key]=old;
            metadata[key]="wrong";Reject(()=>audit(raw()));metadata[key]=old;
        }
        metadata["extra"]="wrong";Reject(()=>audit(raw()));metadata.Remove("extra");
        metadata["gateway_calls"]=0;Reject(()=>audit(raw()));metadata["gateway_calls"]="0";
        record["schema_version"]=true;Reject(()=>audit(raw()));record["schema_version"]=1;
        Reject(()=>ModelValidationAdmission.Audit(raw(),actor,expected));
        foreach(string stamp in new[]{"2026-02-30T00:00:00Z","2026-10-31T00:00:00+04:00","garbage"})
        {record["timestamp"]=stamp;Reject(()=>audit(raw()));}
        record["timestamp"]="2026-10-31T00:00:00Z";
        byte[] full=raw(),shorter=new byte[full.Length-1];Array.Copy(full,shorter,shorter.Length);
        Reject(()=>audit(shorter));Reject(()=>audit(Encoding.UTF8.GetBytes(Encoding.UTF8.GetString(full)+Encoding.UTF8.GetString(full))));
        Reject(()=>audit(new byte[131073]));Reject(()=>audit(new byte[]{255,10}));
        Reject(()=>ModelAttemptAdmission.Metadata(attempt,request,"wrong",lease,body,output));
        Reject(()=>ModelAttemptAdmission.Metadata(attempt,request,command,"wrong",body,output));
        Reject(()=>ModelAttemptAdmission.Projection(attempt,lease,new byte[4097],false));
        Reject(()=>ModelAttemptAdmission.Projection(attempt,lease,Encoding.UTF8.GetBytes("{}"),false));
        var child=new Dictionary<string,object> {
            {"schema","maya.offline.model.attempt_validation.child.v1"},{"attempt",attempt},{"completed",true},
            {"native_constructor",true},{"native_conversation",false},{"sdk_closed",true},{"origins_verified",true},
            {"distributions_verified",true},{"config_unchanged",true},{"model_requests",1},{"client_objects",2},
            {"real_inference",false},{"reason_type",""},{"denial_observed",true}
        };
        Action admitChild=()=>ModelDenialAdmission.Child(child,attempt,"maya.offline.model.attempt_validation.child.v1");
        admitChild();Check(true);Reject(()=>ModelDenialAdmission.Child(child,attempt));
        foreach(string key in new List<string>(child.Keys))
        {
            object old=child[key];child.Remove(key);Reject(admitChild);child[key]=old;
            child[key]="wrong";Reject(admitChild);child[key]=old;
        }
#if HERMES_MODEL_ATTEMPT
        Check(ModelAttemptAdmission.Enabled);Check(ModelValidationAdmission.Enabled);Check(!ModelDenialAdmission.Enabled);
        Check(ProtectedPython.Version=="0.2.1-offline-attempt.1");Check(ProtectedPython.Scope=="offline-hermes-attempt-validation-v1");
        Check(ProtectedPython.Consent.Contains("ONLY the first hex digit"));Check(ProtectedPython.Consent.Contains("NO external inference"));
        foreach(string file in new[]{"model_attempt_child_entry.py","model_attempt_worker_entry.py","model_validation_worker_entry.py"})
            Check(ProductFiles.PayloadPath(file)==file);
        foreach(string file in new[]{"model_deny_child_entry.py","model_deny_worker_entry.py"})Reject(()=>ProductFiles.PayloadPath(file));
#else
        Check(!ModelAttemptAdmission.Enabled);
        foreach(string file in new[]{"model_attempt_child_entry.py","model_attempt_worker_entry.py"})Reject(()=>ProductFiles.PayloadPath(file));
#endif
        foreach(char digit in "0123456789abcdef")Check(ModelAttemptAdmission.Mismatch(digit+new string('f',31))==(digit=='0'?"1":"0")+new string('f',31));
        Reject(()=>ModelAttemptAdmission.Mismatch("A"+new string('a',31)));
        Reject(()=>ModelValidationAdmission.Audit(raw(),actor,expected,true,true));
        Console.WriteLine(checks+" inert M03c attempt checks passed");return 0;
    }
}
