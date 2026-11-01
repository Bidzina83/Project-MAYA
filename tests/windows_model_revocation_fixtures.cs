using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Web.Script.Serialization;
using ProjectMaya.WindowsRuntime;

internal static class RevocationFixtures
{
    static int checks;
    static void Check(bool ok){checks++;if(!ok)throw new Exception("Revocation fixture "+checks);}
    static void Reject(Action action){bool rejected=false;try{action();}catch{rejected=true;}Check(rejected);}
    static int Main(string[] args)
    {
        var json=new JavaScriptSerializer();
        var vector=json.Deserialize<Dictionary<string,object>>(File.ReadAllText(args[0]));
        byte[] body=Convert.FromBase64String((string)vector["body"]);
        string attempt=new string('a',32),request=new string('b',32),revoke=new string('c',32),lease=new string('e',64),output=new string('d',64),dispatch=new string('f',32);
        string actor="windows:S-1-5-21-1-2-3-500";
        var first=ModelRevocationAdmission.Metadata(attempt,request,revoke,"",lease,body,output,"100","100");
        var second=ModelRevocationAdmission.Metadata(attempt,request,revoke,dispatch,lease,body,output,"100","800");
        Check(first.Count==39 && second.Count==39);
        ModelValidationAdmission.Evidence(first,vector["first"] as Dictionary<string,object>);Check(true);
        ModelValidationAdmission.Evidence(second,vector["second"] as Dictionary<string,object>);Check(true);
        foreach(object value in new object[]{0,true,null,"00","0200","2000","-1","1.0","+1","1\n","1e2"})
            Reject(()=>ModelRevocationAdmission.Age(new Dictionary<string,object>{{"age",value}},"age"));
        foreach(string value in new[]{"0","1","1999"})Check(ModelRevocationAdmission.Age(new Dictionary<string,object>{{"age",value}},"age")==value);
        Reject(()=>ModelRevocationAdmission.Age(null,"age"));Reject(()=>ModelRevocationAdmission.Age(new Dictionary<string,object>(),"age"));
        Reject(()=>ModelRevocationAdmission.Metadata(attempt,request,revoke,dispatch,lease,body,output,"100","99"));
        Reject(()=>ModelRevocationAdmission.Metadata(attempt,request,revoke,"",lease,body,output,"100","101"));
        Reject(()=>ModelRevocationAdmission.Metadata(attempt,request,revoke,revoke,lease,body,output,"100","800"));
        Reject(()=>ModelRevocationAdmission.Metadata(attempt,request,"wrong",dispatch,lease,body,output,"100","800"));
        Reject(()=>ModelRevocationAdmission.Metadata(attempt,request,revoke,dispatch,"wrong",body,output,"100","800"));
        Reject(()=>ModelRevocationAdmission.Metadata(attempt,request,revoke,dispatch,lease,body,"wrong","100","800"));
        Reject(()=>ModelRevocationAdmission.Metadata(attempt,request,revoke,dispatch,lease,null,output,"100","800"));
        var records=new List<Dictionary<string,object>>();
        foreach(object item in (IEnumerable)vector["records"])records.Add((Dictionary<string,object>)item);
        Func<byte[]> raw=()=>Encoding.UTF8.GetBytes(json.Serialize(records[0])+"\n"+json.Serialize(records[1])+"\n");
        Func<byte[],int> audit=bytes=>ModelRevocationAdmission.Audit(bytes,actor,first,second);
        Check(audit(raw())==2);Reject(()=>ModelValidationAdmission.Audit(raw(),actor,second));
        foreach(var record in records)
        {
            foreach(string key in new List<string>(record.Keys))
            {object old=record[key];record.Remove(key);Reject(()=>audit(raw()));record[key]=old;record[key]="wrong";Reject(()=>audit(raw()));record[key]=old;}
            var metadata=record["metadata"] as Dictionary<string,object>;
            foreach(string key in new List<string>(metadata.Keys))
            {object old=metadata[key];metadata.Remove(key);Reject(()=>audit(raw()));metadata[key]=old;metadata[key]="wrong";Reject(()=>audit(raw()));metadata[key]=old;}
            metadata["extra"]="wrong";Reject(()=>audit(raw()));metadata.Remove("extra");
            metadata["gateway_calls"]=0;Reject(()=>audit(raw()));metadata["gateway_calls"]="0";
            record["extra"]=false;Reject(()=>audit(raw()));record.Remove("extra");
            record["schema_version"]=true;Reject(()=>audit(raw()));record["schema_version"]=1;
            foreach(string stamp in new[]{"2026-02-30T00:00:00Z","2026-10-31T00:00:00+04:00"})
            {record["timestamp"]=stamp;Reject(()=>audit(raw()));}
            record["timestamp"]="2026-10-31T00:00:00Z";
        }
        string one=json.Serialize(records[0])+"\n",two=json.Serialize(records[1])+"\n",full=one+two;
        foreach(string text in new[]{"",one,two,two+one,one+one,full+one,full.TrimEnd('\n'),
            full.Replace("\"schema_version\":1","\"schema_version\":true"),
            full.Replace("\"decision\":\"deny\"","\"decision\":\"deny\",\"decision\":\"deny\"")})Reject(()=>audit(Encoding.UTF8.GetBytes(text)));
        Reject(()=>audit(new byte[131073]));Reject(()=>audit(new byte[]{255,10,10}));
        Reject(()=>ModelRevocationAdmission.Audit(raw(),"wrong",first,second));
#if HERMES_MODEL_REVOKE
        Check(ModelRevocationAdmission.Enabled);Check(ModelValidationAdmission.Enabled);Check(!ModelExpiryAdmission.Enabled);
        Check(ProtectedPython.Version=="0.2.1-offline-revocation.1");Check(ProtectedPython.Scope=="offline-hermes-lease-revocation-v1");
        Check(ProtectedPython.Consent.Contains("BEFORE model_begin"));Check(ProtectedPython.Consent.Contains("Two exact audit records"));
        foreach(string file in new[]{"model_revoke_child_entry.py","model_revoke_worker_entry.py","model_validation_worker_entry.py"})Check(ProductFiles.PayloadPath(file)==file);
        foreach(string file in new[]{"model_expiry_child_entry.py","model_expiry_worker_entry.py"})Reject(()=>ProductFiles.PayloadPath(file));
#else
        Check(!ModelRevocationAdmission.Enabled);
        foreach(string file in new[]{"model_revoke_child_entry.py","model_revoke_worker_entry.py"})Reject(()=>ProductFiles.PayloadPath(file));
#endif
        Console.WriteLine(checks+" inert M04b revocation checks passed");return 0;
    }
}
