using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Web.Script.Serialization;
using ProjectMaya.WindowsRuntime;

internal static class ExpiryFixtures
{
    static int checks;
    static void Check(bool ok){checks++;if(!ok)throw new Exception("Expiry fixture "+checks);}
    static void Reject(Action action){bool rejected=false;try{action();}catch{rejected=true;}Check(rejected);}
    static int Main(string[] args)
    {
        var vector=new JavaScriptSerializer().Deserialize<Dictionary<string,object>>(File.ReadAllText(args[0]));
        byte[] body=Convert.FromBase64String((string)vector["body"]);
        string attempt=new string('a',32),request=new string('b',32),command=new string('c',32),lease=new string('e',64),output=new string('d',64);
        string actor="windows:S-1-5-21-1-2-3-500";
        var expected=ModelExpiryAdmission.Metadata(attempt,request,command,lease,body,output,"2100");
        ModelValidationAdmission.Evidence(expected,vector["metadata"] as Dictionary<string,object>);Check(true);
        foreach(object value in new object[]{2000,true,null,"02000","1999","30001","2000.0","+2000","2000\n"})
            Reject(()=>ModelExpiryAdmission.Elapsed(new Dictionary<string,object>{{"worker_elapsed_ms",value}}));
        foreach(string value in new[]{"2000","2100","30000"})Check(ModelExpiryAdmission.Elapsed(new Dictionary<string,object>{{"worker_elapsed_ms",value}})==value);
        long tick=0;int sleeps=0;
        long waited=ModelExpiryAdmission.WaitCore(()=>tick,n=>{Check(n>0 && n<=25);tick+=n;sleeps++;},()=>22000-(int)tick);
        Check(waited==2100);Check(sleeps==84);
        Reject(()=>ModelExpiryAdmission.WaitCore(()=>0,n=>{},()=>4100));
        Reject(()=>ModelExpiryAdmission.WaitCore(()=>-1,n=>{},()=>22000));
        Reject(()=>ModelExpiryAdmission.WaitCore(()=>30001,n=>{},()=>22000));
        Reject(()=>ModelExpiryAdmission.WaitCore(()=>0,n=>{},()=>22000));
        tick=0;Reject(()=>ModelExpiryAdmission.WaitCore(()=>tick,n=>tick=-1,()=>22000));
        tick=0;Reject(()=>ModelExpiryAdmission.WaitCore(()=>tick,n=>tick=30001,()=>22000));
        tick=0;Reject(()=>ModelExpiryAdmission.WaitCore(()=>tick,n=>tick=22000,()=>22000-(int)tick));
        var record=vector["audit"] as Dictionary<string,object>;
        Func<byte[]> raw=()=>Encoding.UTF8.GetBytes(new JavaScriptSerializer().Serialize(record)+"\n");
        Func<byte[],int> audit=bytes=>ModelValidationAdmission.Audit(bytes,actor,expected,false,false,false,true);
        Check(audit(raw())==1);Reject(()=>ModelValidationAdmission.Audit(raw(),actor,expected));
        Reject(()=>ModelValidationAdmission.Audit(raw(),actor,expected,true,false,false,true));
        foreach(string key in new List<string>(record.Keys))
        {object old=record[key];record.Remove(key);Reject(()=>audit(raw()));record[key]=old;record[key]="wrong";Reject(()=>audit(raw()));record[key]=old;}
        var meta=record["metadata"] as Dictionary<string,object>;
        foreach(string key in new List<string>(meta.Keys))
        {object old=meta[key];meta.Remove(key);Reject(()=>audit(raw()));meta[key]=old;meta[key]="wrong";Reject(()=>audit(raw()));meta[key]=old;}
        meta["worker_elapsed_ms"]="2101";Reject(()=>audit(raw()));meta["worker_elapsed_ms"]="2100";
        meta["gateway_calls"]=0;Reject(()=>audit(raw()));meta["gateway_calls"]="0";
        meta["extra"]="wrong";Reject(()=>audit(raw()));meta.Remove("extra");
        foreach(string stamp in new[]{"2026-02-30T00:00:00Z","2026-10-31T00:00:00+04:00"}){record["timestamp"]=stamp;Reject(()=>audit(raw()));}
        record["timestamp"]="2026-10-31T00:00:00Z";
        record["schema_version"]=true;Reject(()=>audit(raw()));record["schema_version"]=1;
        byte[] full=raw(),shorter=new byte[full.Length-1];Array.Copy(full,shorter,shorter.Length);
        Reject(()=>audit(shorter));Reject(()=>audit(Encoding.UTF8.GetBytes(Encoding.UTF8.GetString(full)+Encoding.UTF8.GetString(full))));
        Reject(()=>audit(new byte[131073]));Reject(()=>audit(new byte[]{255,10}));
        Reject(()=>ModelExpiryAdmission.Metadata(attempt,request,"wrong",lease,body,output,"2100"));
        Reject(()=>ModelExpiryAdmission.Metadata(attempt,request,command,"wrong",body,output,"2100"));
#if HERMES_MODEL_EXPIRY
        Check(ModelExpiryAdmission.Enabled);Check(ModelValidationAdmission.Enabled);Check(!ModelBodyAdmission.Enabled);
        Check(ProtectedPython.Version=="0.2.1-offline-expiry.1");Check(ProtectedPython.Scope=="offline-hermes-lease-expiry-v1");
        Check(ProtectedPython.Consent.Contains("BEFORE model_begin"));Check(ProtectedPython.Consent.Contains("NO external inference"));
        foreach(string file in new[]{"model_expiry_child_entry.py","model_expiry_worker_entry.py","model_validation_worker_entry.py"})Check(ProductFiles.PayloadPath(file)==file);
        foreach(string file in new[]{"model_body_child_entry.py","model_body_worker_entry.py"})Reject(()=>ProductFiles.PayloadPath(file));
#else
        Check(!ModelExpiryAdmission.Enabled);
        foreach(string file in new[]{"model_expiry_child_entry.py","model_expiry_worker_entry.py"})Reject(()=>ProductFiles.PayloadPath(file));
#endif
        Console.WriteLine(checks+" inert M04a expiry checks passed");return 0;
    }
}
