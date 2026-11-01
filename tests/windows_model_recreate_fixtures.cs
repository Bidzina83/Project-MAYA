using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Web.Script.Serialization;
using ProjectMaya.WindowsRuntime;

internal static class RecreateFixtures
{
    static int checks;
    static readonly JavaScriptSerializer Json=new JavaScriptSerializer();
    static void Check(bool ok){if(!ok)throw new Exception("fixture assertion");checks++;}
    static void Denied(Action action){bool denied=false;try{action();}catch(StartupFailure){denied=true;}Check(denied);}
    static Dictionary<string,object> Clone(Dictionary<string,object> item){return StrictJson.Parse(Encoding.UTF8.GetBytes(Json.Serialize(item)));}
    static byte[] Ledger(List<object> records){var b=new StringBuilder();foreach(var item in records)b.Append(Json.Serialize(item)).Append('\n');return Encoding.UTF8.GetBytes(b.ToString());}
    static int Main(string[] args)
    {
        var vector=Json.DeserializeObject(File.ReadAllText(args[0])) as Dictionary<string,object>;
        var records=new List<object>((object[])vector["records"]);
        byte[] body=Convert.FromBase64String((string)vector["body"]),response=Convert.FromBase64String((string)vector["response"]);
        string actor=(string)vector["actor"],attempt=(string)vector["attempt"],service=(string)vector["service"],delivery=(string)vector["delivery"],output=(string)vector["output"];
        Func<byte[],int> audit=raw=>ModelRecreateAdmission.Audit(raw,actor,attempt,service,body,response,output,delivery);
        Check(audit(Ledger(records))==4);
        for(int i=0;i<4;i++)
        {
            var original=records[i] as Dictionary<string,object>;
            foreach(string key in original.Keys)
            {
                var changed=Clone(original);changed[key]="wrong";var list=new List<object>(records);list[i]=changed;
                Denied(()=>audit(Ledger(list)));
                changed=Clone(original);changed.Remove(key);list=new List<object>(records);list[i]=changed;
                Denied(()=>audit(Ledger(list)));
            }
            var metadata=original["metadata"] as Dictionary<string,object>;
            foreach(string key in metadata.Keys)
            {
                var changed=Clone(original);((Dictionary<string,object>)changed["metadata"])[key]="wrong";
                var list=new List<object>(records);list[i]=changed;Denied(()=>audit(Ledger(list)));
            }
        }
        var missing=new List<object>(records);missing.RemoveAt(3);Denied(()=>audit(Ledger(missing)));
        var extra=new List<object>(records);extra.Add(records[3]);Denied(()=>audit(Ledger(extra)));
        var reversed=new List<object>(records);reversed.Reverse();Denied(()=>audit(Ledger(reversed)));
        var wrongTime=new List<object>(records);var first=Clone((Dictionary<string,object>)records[0]);first["timestamp"]="9999-01-01T00:00:00Z";wrongTime[0]=first;Denied(()=>audit(Ledger(wrongTime)));
        var effects=StrictJson.Parse(Encoding.UTF8.GetBytes(Json.Serialize(vector["effects"])));
        effects["case"]="M05b";
        ModelRecreateAdmission.Effects(effects,body,response,delivery);Check(true);
        foreach(string key in effects.Keys){var changed=Clone(effects);changed[key]="wrong";Denied(()=>ModelRecreateAdmission.Effects(changed,body,response,delivery));}
        var report=new Dictionary<string,object>{{"schema","maya.offline.model.recreate.child.v1"},{"attempt",attempt},{"completed",true},
            {"native_constructor",true},{"native_conversation",true},{"sdk_closed",true},{"origins_verified",true},{"distributions_verified",true},
            {"config_unchanged",true},{"model_requests",1},{"client_objects",3},{"real_inference",false},{"reason_type",""},{"probe_command_id","f0000000000000000000000000000000"},
            {"probe",new Dictionary<string,object>{{"case","M05b"},{"boundary","adapter_consumed_budget"},{"transport_attempts",2},{"model_requests",1},
                {"completed_exchanges",1},{"budget_rejections",1},{"distinct_new_clients",true},{"same_consumed_adapter",true},{"request_sha256",BridgeHostFiles.Hash(body)},{"request_bytes",body.Length}}},
            {"probe_lifecycle",new Dictionary<string,object>{{"schema","maya.model.recreate.lifecycle.v1"},{"stage","complete"},{"failure_stage",""},
                {"armed",true},{"hook_calls",1},{"close_delegations",1},{"owner_thread_verified",true},{"used_client_verified",true},
                {"native_close_verified",true},{"probe_after_native_close",true},{"new_clients_distinct",true},{"same_adapter_verified",true},{"new_client_close_verified",true}}}};
        Action<Dictionary<string,object>> child=r=>ModelRecreateAdmission.Child(r,attempt,"f0000000000000000000000000000000",body);
        child(report);Check(true);
        foreach(string key in report.Keys){var changed=Clone(report);changed[key]="wrong";Denied(()=>child(changed));}
        foreach(string key in ((Dictionary<string,object>)report["probe"]).Keys){var changed=Clone(report);((Dictionary<string,object>)changed["probe"])[key]="wrong";Denied(()=>child(changed));}
        foreach(string key in ((Dictionary<string,object>)report["probe_lifecycle"]).Keys)
        {
            var changed=Clone(report);((Dictionary<string,object>)changed["probe_lifecycle"])[key]="wrong";Denied(()=>child(changed));
            changed=Clone(report);((Dictionary<string,object>)changed["probe_lifecycle"]).Remove(key);Denied(()=>child(changed));
        }
        var legacy=Clone(report);legacy["schema"]="maya.offline.model.budget.child.v1";Denied(()=>child(legacy));

        foreach(string section in new[]{"outer","probe","probe_lifecycle"})
        {
            var source=section=="outer"?report:(Dictionary<string,object>)report[section];
            foreach(string key in source.Keys)
            {
                var changed=Clone(report);var target=section=="outer"?changed:(Dictionary<string,object>)changed[section];
                target.Remove(key);Denied(()=>child(changed));
                changed=Clone(report);target=section=="outer"?changed:(Dictionary<string,object>)changed[section];
                target[key]=null;Denied(()=>child(changed));
                if(source[key] is bool){changed=Clone(report);target=section=="outer"?changed:(Dictionary<string,object>)changed[section];target[key]=!(bool)source[key];Denied(()=>child(changed));}
                if(source[key] is int && key!="client_objects"){changed=Clone(report);target=section=="outer"?changed:(Dictionary<string,object>)changed[section];target[key]=(int)source[key]+1;Denied(()=>child(changed));}
            }
            var added=Clone(report);(section=="outer"?added:(Dictionary<string,object>)added[section])["extra"]=true;Denied(()=>child(added));
        }
        foreach(int count in new[]{0,1,2,9}){var changed=Clone(report);changed["client_objects"]=count;Denied(()=>child(changed));}
        foreach(int count in new[]{3,8}){var changed=Clone(report);changed["client_objects"]=count;child(changed);Check(true);}
        foreach(string key in effects.Keys){var changed=Clone(effects);changed.Remove(key);Denied(()=>ModelRecreateAdmission.Effects(changed,body,response,delivery));}
        var addedEffects=Clone(effects);addedEffects["extra"]=0;Denied(()=>ModelRecreateAdmission.Effects(addedEffects,body,response,delivery));
        var oldCase=Clone(report);oldCase["schema"]="maya.offline.model.budget.child.v2";Denied(()=>child(oldCase));
        Denied(()=>ModelBudgetAdmission.Child(report,attempt,"f0000000000000000000000000000000",body));

#if HERMES_MODEL_RECREATE
        Check(!ModelBudgetAdmission.Enabled);
        Check(System.Diagnostics.FileVersionInfo.GetVersionInfo(typeof(RecreateFixtures).Assembly.Location).FileVersion=="0.2.1.14");
        Check(ModelRecreateAdmission.Enabled);Check(ProtectedPython.Version=="0.2.1-offline-recreate.1");Check(ProtectedPython.Scope=="offline-hermes-recreated-client-budget-v1");
        foreach(string path in new[]{"model_recreate_child_entry.py","model_recreate_worker_entry.py","model_validation_worker_entry.py"})Check(ProductFiles.PayloadPath(path)==path);
        foreach(string path in new[]{"model_budget_child_entry.py","model_budget_worker_entry.py","model_replay_child_entry.py","model_replay_worker_entry.py"})Denied(()=>ProductFiles.PayloadPath(path));
#else
        Check(!ModelRecreateAdmission.Enabled);
        foreach(string path in new[]{"model_recreate_child_entry.py","model_recreate_worker_entry.py"})Denied(()=>ProductFiles.PayloadPath(path));
#endif
        Console.WriteLine("Recreate inert checks: "+checks);return 0;
    }
}
