using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace ProjectMaya.WindowsRuntime
{
    internal static class ModelBudgetAdmission
    {
        internal static bool Enabled { get {
#if HERMES_MODEL_BUDGET
            return true;
#else
            return false;
#endif
        } }
        internal static void Child(Dictionary<string,object> report,string attempt,string probeId,byte[] body)
        {
            BridgeRuntime.Shape(report,"schema","attempt","completed","native_constructor","native_conversation","sdk_closed","origins_verified",
                "distributions_verified","config_unchanged","model_requests","client_objects","real_inference","reason_type","probe_command_id","probe","probe_lifecycle");
            if(!"maya.offline.model.budget.child.v2".Equals(report["schema"]) || !attempt.Equals(report["attempt"]) ||
                !probeId.Equals(report["probe_command_id"]) || !1.Equals(report["model_requests"]) || !(report["client_objects"] is int) ||
                (int)report["client_objects"]<2 || (int)report["client_objects"]>8 || !false.Equals(report["real_inference"]) ||
                !"".Equals(report["reason_type"]))throw new StartupFailure("budget_child_report");
            foreach(string flag in new[]{"completed","native_constructor","native_conversation","sdk_closed","origins_verified","distributions_verified","config_unchanged"})
                if(!true.Equals(report[flag]))throw new StartupFailure("budget_child_postcondition");
            var probe=report["probe"] as Dictionary<string,object>;
            ModelValidationAdmission.Evidence(probe,new Dictionary<string,object>{{"case","M05a"},{"boundary","adapter_consumed_budget"},
                {"transport_attempts",2},{"model_requests",1},{"completed_exchanges",1},{"budget_rejections",1},{"same_used_client",true},
                {"request_sha256",BridgeHostFiles.Hash(body)},{"request_bytes",body.Length}});
            ModelValidationAdmission.Evidence(report["probe_lifecycle"] as Dictionary<string,object>,new Dictionary<string,object>{
                {"schema","maya.model.adapter_budget.lifecycle.v1"},{"stage","complete"},{"failure_stage",""},{"armed",true},
                {"hook_calls",1},{"close_delegations",1},{"owner_thread_verified",true},{"used_client_verified",true},
                {"native_close_verified",true},{"probe_before_native_close",true}});
        }
        internal static void Effects(Dictionary<string,object> effects,byte[] body,byte[] response,string delivery)
        {
            ModelValidationAdmission.Evidence(effects,new Dictionary<string,object>{{"case","M05a"},{"gateway_calls",2},{"dispatches",1},
                {"confirmed_runtime_releases",1},{"confirmed_operator_releases",0},{"real_inference",false},
                {"request_sha256",BridgeHostFiles.Hash(body)},{"response_sha256",BridgeHostFiles.Hash(response)},{"delivery_command_id",delivery}});
        }
        internal static int Audit(byte[] raw,string actor,string attempt,string service,byte[] body,byte[] response,string output,string delivery)
        {
            foreach(string id in new[]{attempt,service,delivery})
                if(id==null || !Regex.IsMatch(id,"\\A[0-9a-f]{32}\\z"))throw new StartupFailure("budget_audit_ID");
            if(raw==null || raw.Length<1 || raw.Length>131072 || actor==null ||
                !Regex.IsMatch(actor,"\\Awindows:S-1-5-(?:[0-9]+-)*[0-9]+\\z") || body==null || body.Length<1 || body.Length>4096 ||
                response==null || response.Length<1 || response.Length>4096 || output==null ||
                Encoding.UTF8.GetByteCount(output)<1 || Encoding.UTF8.GetByteCount(output)>1024)throw new StartupFailure("budget_audit_bound");
            string[] lines=new UTF8Encoding(false,true).GetString(raw).Split('\n');
            if(lines.Length!=5 || lines[4]!="")throw new StartupFailure("budget_audit_count");
            string[] stages={"egress_intent","dispatch_outcome","runtime_release_intent","runtime_delivery"};
            DateTimeOffset? previous=null;
            for(int i=0;i<4;i++)
            {
                var record=StrictJson.Parse(Encoding.UTF8.GetBytes(lines[i]));
                BridgeRuntime.Shape(record,"schema_version","timestamp","event_type","decision","reason_code","actor_id","capability",
                    "target","operation","data_classification","idempotency_key","metadata");
                string name="model_bridge."+stages[i];
                var expected=new Dictionary<string,object>{{"schema_version",1},{"event_type",name},{"decision","allow"},{"reason_code",name},
                    {"actor_id",actor},{"capability",i<2?"model.egress":"model.output"},{"target","model:maya-offline-fixture"},
                    {"operation",i<2?"infer":"disclose"},{"data_classification","internal-synthetic"},{"idempotency_key",null}};
                foreach(var field in expected)if(!Object.Equals(field.Value,record[field.Key]))throw new StartupFailure("budget_audit_field");
                DateTimeOffset stamp;
                if(!(record["timestamp"] is string) || !DateTimeOffset.TryParseExact((string)record["timestamp"],
                    new[]{"yyyy-MM-dd'T'HH:mm:sszzz","yyyy-MM-dd'T'HH:mm:ss'Z'"},CultureInfo.InvariantCulture,
                    DateTimeStyles.AssumeUniversal,out stamp) || stamp.Offset!=TimeSpan.Zero || previous.HasValue && stamp<previous.Value)
                    throw new StartupFailure("budget_audit_time");
                previous=stamp;
                var meta=new Dictionary<string,object>{{"attempt",attempt},{"request_id",service},{"route","maya.offline.model.v1"},
                    {"endpoint","https://maya-offline-model.invalid/v1/chat/completions"},{"model","maya-offline-wire-v1"},
                    {"destination",i<2?"provider":"runtime:"+attempt},{"request_sha256",BridgeHostFiles.Hash(body)},
                    {"request_bytes",body.Length.ToString(CultureInfo.InvariantCulture)},{"response_sha256",i==0?"":BridgeHostFiles.Hash(response)},
                    {"response_bytes",i==0?"0":response.Length.ToString(CultureInfo.InvariantCulture)},
                    {"output_sha256",BridgeHostFiles.Hash(Encoding.UTF8.GetBytes(output))},{"dispatches",i==0?"0":"1"},{"real_inference","false"}};
                if(i==3)meta["coordinator_request_id"]=delivery;
                ModelValidationAdmission.Evidence(record["metadata"] as Dictionary<string,object>,meta);
            }
            return 4;
        }
    }
}
