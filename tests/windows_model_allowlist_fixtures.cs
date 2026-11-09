using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Web.Script.Serialization;
using ProjectMaya.WindowsRuntime;

internal static class AllowlistFixtures
{
    static int checks;
    static readonly JavaScriptSerializer Json=new JavaScriptSerializer();
    static void Check(bool ok){if(!ok)throw new Exception("M06 fixture assertion "+checks);checks++;}
    static void Denied(Action action){bool denied=false;try{action();}catch(StartupFailure){denied=true;}Check(denied);}
    static Dictionary<string,object> Clone(Dictionary<string,object> value){return StrictJson.Parse(Encoding.UTF8.GetBytes(Json.Serialize(value)));}
    static byte[] Ledger(List<object> values){var text=new StringBuilder();foreach(var value in values)text.Append(Json.Serialize(value)).Append('\n');return Encoding.UTF8.GetBytes(text.ToString());}
    static int Main(string[] args)
    {
        var vector=Json.DeserializeObject(File.ReadAllText(args[0])) as Dictionary<string,object>;
        byte[] body=Convert.FromBase64String((string)vector["body"]),response=Convert.FromBase64String((string)vector["response"]);
        string actor=(string)vector["actor"],attempt=(string)vector["attempt"],service=(string)vector["service"],output=(string)vector["output"];
        var rules=ModelHostFiles.Rules(actor);
        foreach(var rule in rules)
        {
            Check(rule.Count==4);Check(actor.Equals(rule["actor_id"]));Check("model:maya-offline-fixture".Equals(rule["target"]));
            Check(("model.egress".Equals(rule["capability"])?"infer":"disclose").Equals(rule["operation"]));
        }
#if HERMES_MODEL_OUTPUT_DENY
        Check(rules.Length==1 && "model.egress".Equals(rules[0]["capability"]));
#elif HERMES_MODEL_DENY
        Check(rules.Length==1 && "model.output".Equals(rules[0]["capability"]));
#else
        Check(rules.Length==2 && "model.egress".Equals(rules[0]["capability"]) && "model.output".Equals(rules[1]["capability"]));
#endif
        Check(Convert.ToBase64String(ModelOutputDenialAdmission.ExpectedResponse(output))==Convert.ToBase64String(response));
        foreach(string value in new[]{null,"",output+"\n",output.ToUpperInvariant(),"arbitrary response",output.Substring(1)})
            Denied(()=>ModelOutputDenialAdmission.ExpectedResponse(value));
        var records=new List<object>((object[])vector["records"]);
        Func<byte[],int> audit=raw=>ModelAllowlistAdmission.Audit(raw,actor,attempt,service,body,output);
        Check(audit(Ledger(records))==2);
        for(int i=0;i<records.Count;i++)
        {
            var original=records[i] as Dictionary<string,object>;
            foreach(string key in original.Keys)
            {
                var changed=Clone(original);changed[key]="wrong";var list=new List<object>(records);list[i]=changed;Denied(()=>audit(Ledger(list)));
                changed=Clone(original);changed.Remove(key);list=new List<object>(records);list[i]=changed;Denied(()=>audit(Ledger(list)));
                changed=Clone(original);changed[key]=null;list=new List<object>(records);list[i]=changed;
                if(key!="idempotency_key")Denied(()=>audit(Ledger(list)));
            }
            var meta=original["metadata"] as Dictionary<string,object>;
            foreach(string key in meta.Keys)
            {
                var changed=Clone(original);((Dictionary<string,object>)changed["metadata"])[key]="wrong";
                var list=new List<object>(records);list[i]=changed;Denied(()=>audit(Ledger(list)));
                changed=Clone(original);((Dictionary<string,object>)changed["metadata"]).Remove(key);
                list=new List<object>(records);list[i]=changed;Denied(()=>audit(Ledger(list)));
            }
        }
        var missing=new List<object>(records);missing.RemoveAt(1);Denied(()=>audit(Ledger(missing)));
        var extra=new List<object>(records);extra.Add(records[1]);Denied(()=>audit(Ledger(extra)));
        var reversed=new List<object>(records);reversed.Reverse();Denied(()=>audit(Ledger(reversed)));
        byte[] unterminated=Ledger(records);Array.Resize(ref unterminated,unterminated.Length-1);Denied(()=>audit(unterminated));
        var time=new List<object>(records);var late=Clone((Dictionary<string,object>)records[0]);late["timestamp"]="9999-01-01T00:00:00Z";time[0]=late;Denied(()=>audit(Ledger(time)));
        var effects=StrictJson.Parse(Encoding.UTF8.GetBytes(Json.Serialize(vector["effects"])));
        Action<Dictionary<string,object>> admit=e=>ModelAllowlistAdmission.Effects(e,body,output);
        admit(effects);Check(effects.Count==25);
        foreach(string key in effects.Keys)
        {
            var changed=Clone(effects);changed[key]="wrong";Denied(()=>admit(changed));
            changed=Clone(effects);changed.Remove(key);Denied(()=>admit(changed));
            changed=Clone(effects);changed[key]=null;Denied(()=>admit(changed));
            if(effects[key] is bool){changed=Clone(effects);changed[key]=!(bool)effects[key];Denied(()=>admit(changed));}
            if(effects[key] is int){changed=Clone(effects);changed[key]=(int)effects[key]+1;Denied(()=>admit(changed));}
        }
        var added=Clone(effects);added["body"]="forbidden";Denied(()=>admit(added));
        var report=new Dictionary<string,object>{{"schema","maya.offline.model.allowlist_response.child.v1"},{"attempt",attempt},
            {"completed",true},{"native_constructor",true},{"native_conversation",false},{"sdk_closed",true},
            {"origins_verified",true},{"distributions_verified",true},{"config_unchanged",true},{"model_requests",1},
            {"client_objects",2},{"real_inference",false},{"reason_type",""},{"denial_observed",true}};
        Action<Dictionary<string,object>> child=r=>ModelAllowlistAdmission.Child(r,attempt);
        child(report);Check(true);
        foreach(string key in report.Keys)
        {
            var changed=Clone(report);changed[key]="wrong";Denied(()=>child(changed));
            changed=Clone(report);changed.Remove(key);Denied(()=>child(changed));
            changed=Clone(report);changed[key]=null;Denied(()=>child(changed));
            if(report[key] is bool){changed=Clone(report);changed[key]=!(bool)report[key];Denied(()=>child(changed));}
        }
        foreach(int count in new[]{0,1,9}){var changed=Clone(report);changed["client_objects"]=count;Denied(()=>child(changed));}
        var addedReport=Clone(report);addedReport["extra"]=0;Denied(()=>child(addedReport));
        var m02=Clone(report);m02["schema"]="maya.offline.model.denial.child.v1";Denied(()=>child(m02));
        Denied(()=>ModelDenialAdmission.Child(report,attempt));
#if HERMES_MODEL_ALLOWLIST
        Check(ModelAllowlistAdmission.Enabled && !ModelDenialAdmission.Enabled && !ModelRecreateAdmission.Enabled);
        Check(ProtectedPython.Version=="0.2.1-offline-allowlist.1");
        Check(ProtectedPython.Scope=="offline-hermes-response-allowlist-rejection-v1");
        Check(System.Diagnostics.FileVersionInfo.GetVersionInfo(typeof(AllowlistFixtures).Assembly.Location).FileVersion=="0.2.1.18");
        foreach(string path in new[]{"model_allowlist_child_entry.py","model_allowlist_worker_entry.py"})Check(ProductFiles.PayloadPath(path)==path);
        foreach(string path in new[]{"model_malformed_child_entry.py","model_malformed_worker_entry.py","model_output_deny_child_entry.py","model_output_deny_worker_entry.py","model_recreate_child_entry.py","model_recreate_worker_entry.py","model_budget_child_entry.py","model_budget_worker_entry.py","model_deny_child_entry.py","model_deny_worker_entry.py"})
            Denied(()=>ProductFiles.PayloadPath(path));
#else
        Check(!ModelAllowlistAdmission.Enabled);
        foreach(string path in new[]{"model_allowlist_child_entry.py","model_allowlist_worker_entry.py"})Denied(()=>ProductFiles.PayloadPath(path));
#endif
        Console.WriteLine("Malformed inert checks: "+checks);
        return 0;
    }
}
