using System;
using System.Collections.Generic;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;
using ProjectMaya.WindowsRuntime;

internal static class ModelAuditFixtures
{
    static int checks;
    static void Check(bool value) { checks++; if(!value) throw new Exception("model audit fixture "+checks); }
    static void Reject(Action action) { bool caught=false; try {action();} catch {caught=true;} Check(caught); }
    static int Main()
    {
        string attempt=new string('a',32), request=new string('b',32), actor="windows:S-1-5-21-1-2-3-500";
        string requestHash=new string('c',64), responseHash=new string('d',64), outputHash=new string('e',64);
        string runtimeId=new string('1',32), operatorId=new string('2',32);
        var records=new List<Dictionary<string,object>>();
        for(int i=0;i<6;i++)
        {
            var metadata=new Dictionary<string,object> {
                {"attempt",attempt},{"request_id",request},{"route","maya.offline.model.v1"},
                {"endpoint","https://maya-offline-model.invalid/v1/chat/completions"},{"model","maya-offline-wire-v1"},
                {"destination",i<2?"provider":i<4?"runtime:"+attempt:"operator"},
                {"request_sha256",requestHash},{"response_sha256",i==0?"":responseHash},
                {"request_bytes","2048"},{"response_bytes",i==0?"0":"512"},{"output_sha256",outputHash},
                {"dispatches",i==0?"0":"1"},{"real_inference","false"}
            };
            if(i==3 || i==5) metadata["coordinator_request_id"]=i==3?runtimeId:operatorId;
            records.Add(new Dictionary<string,object> {
                {"schema_version",1},{"timestamp","2026-10-24T12:00:00+00:00"},
                {"event_type","model_bridge."+ModelAuditAdmission.Stages[i]},
                {"reason_code","model_bridge."+ModelAuditAdmission.Stages[i]},
                {"decision","allow"},{"actor_id",actor},{"capability",i<2?"model.egress":"model.output"},
                {"target","model:maya-offline-fixture"},{"operation",i<2?"infer":"disclose"},
                {"data_classification","internal-synthetic"},{"idempotency_key",null},{"metadata",metadata}
            });
        }
        Func<byte[]> raw=delegate {var b=new StringBuilder();foreach(var r in records)b.Append(new JavaScriptSerializer().Serialize(r)).Append('\n');return Encoding.UTF8.GetBytes(b.ToString());};
        Func<byte[],int> verify=delegate(byte[] bytes) {return ModelAuditAdmission.Verify(bytes,attempt,actor,request,requestHash,2048,responseHash,512,outputHash,runtimeId,operatorId);};
        Check(verify(raw())==6);
        foreach(var record in records)
        {
            foreach(string key in new List<string>(record.Keys))
            {
                object value=record[key]; record.Remove(key); Reject(delegate {verify(raw());}); record[key]=value;
            }
            var metadata=(Dictionary<string,object>)record["metadata"];
            foreach(string key in new List<string>(metadata.Keys))
            {
                object value=metadata[key]; metadata[key]="wrong"; Reject(delegate {verify(raw());}); metadata[key]=value;
            }
        }
        records[0]["schema_version"]=true; Reject(delegate {verify(raw());}); records[0]["schema_version"]=1;
        records[0]["timestamp"]="2026-10-24T12:00:00+04:00"; Reject(delegate {verify(raw());});
        records[0]["timestamp"]="2026-10-24T12:00:00+00:00";
        Reject(delegate {verify(new byte[131073]);});
        byte[] complete=raw(), partial=new byte[complete.Length-1];Array.Copy(complete,partial,partial.Length);
        Reject(delegate {verify(partial);});
        Reject(delegate {ModelAuditAdmission.Verify(complete,attempt,actor,request,requestHash,2048,responseHash,512,outputHash,runtimeId,runtimeId);});
        records.Reverse();Reject(delegate {verify(raw());});records.Reverse();
        records.Add(records[5]);Reject(delegate {verify(raw());});records.RemoveAt(6);
        records.RemoveAt(5);Reject(delegate {verify(raw());});
        int publications=0;
        ModelPublication.Run(action=>action(),delegate {publications++;},100);
        Check(publications==1);
        Action queued=null;
        Reject(delegate {ModelPublication.Run(action=>queued=action,delegate {publications++;},10);});
        Check(queued!=null);queued();Check(publications==1);
        Reject(delegate {ModelPublication.Run(action=>action(),delegate {throw new Exception("not public");},100);});
        Reject(delegate {ModelPublication.Run(action=>action(),delegate {},0);});
        Reject(delegate {ModelPublication.Run(action=>action(),delegate {},2001);});
        var entered=new ManualResetEvent(false);var release=new ManualResetEvent(false);Thread publisher=null;
        bool uncertain=false;
        try
        {
            ModelPublication.Run(action=>{publisher=new Thread(()=>action());publisher.Start();if(!entered.WaitOne(1000))throw new Exception();},
                delegate {entered.Set();release.WaitOne();},10);
        }
        catch(StartupFailure error){uncertain=error.Message=="model_operator_publication_uncertain";}
        finally{release.Set();if(publisher!=null)Check(publisher.Join(1000));entered.Dispose();release.Dispose();}
        Check(uncertain);
#if HERMES_MODEL
        Check(ProtectedPython.Version=="0.2.1-offline-model.1");
        Check(ProtectedPython.Scope=="offline-hermes-model-wire-v1");
        Check(ProtectedPython.Consent.Contains("NO external inference"));
        foreach(string file in new[]{"model_child_entry.py","model_worker_entry.py","model-contract.json","model-config.json","model-native-literals.json"})
            Check(ProductFiles.PayloadPath(file)==file);
#else
        foreach(string file in new[]{"model_child_entry.py","model_worker_entry.py","model-contract.json","model-config.json","model-native-literals.json"})
            Reject(delegate {ProductFiles.PayloadPath(file);});
#endif
        Console.WriteLine(checks+" inert model audit checks passed");return 0;
    }
}
