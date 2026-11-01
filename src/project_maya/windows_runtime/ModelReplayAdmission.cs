using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace ProjectMaya.WindowsRuntime
{
    internal static class ModelReplayAdmission
    {
        internal static bool Enabled { get {
#if HERMES_MODEL_REPLAY
            return true;
#else
            return false;
#endif
        } }
        internal static string Age(Dictionary<string,object> evidence,string key)
        {return ModelRevocationAdmission.Age(evidence,key);}
        internal static Dictionary<string,object> Metadata(string attempt,string service,string first,string delivery,string replay,
            string lease,byte[] body,byte[] response,string output,string deliveryAge,string age)
        {
            Age(new Dictionary<string,object>{{"age",age}},"age");Age(new Dictionary<string,object>{{"age",deliveryAge}},"age");
            foreach(string id in new[]{attempt,service,first,delivery,replay})
                if(id==null || !Regex.IsMatch(id,"\\A[0-9a-f]{32}\\z"))throw new StartupFailure("replay_ID");
            if(first==delivery || first==replay || delivery==replay ||
                Int32.Parse(age,CultureInfo.InvariantCulture)<Int32.Parse(deliveryAge,CultureInfo.InvariantCulture))throw new StartupFailure("replay_binding");
            if(body==null || body.Length<1 || body.Length>4096 || response==null || response.Length<1 || response.Length>4096 ||
                output==null || !Regex.IsMatch(output,"\\A[0-9a-f]{64}\\z"))throw new StartupFailure("replay_bound");
            ModelBodyAdmission.Envelope(new Dictionary<string,object>{{"v",1},{"type","model_request"},{"attempt",attempt},
                {"route","maya.offline.model.v1"},{"lease",lease},{"seq",1},{"method","POST"},{"path","/v1/chat/completions"},
                {"body",new UTF8Encoding(false,true).GetString(body)}},attempt,lease,body);
            StrictJson.Parse(response);
            var parsed=StrictJson.Parse(body);BridgeRuntime.Shape(parsed,"messages","model","max_tokens","stream");
            var messages=parsed["messages"] as List<object>;
            if(!"maya-offline-wire-v1".Equals(parsed["model"]) || !32.Equals(parsed["max_tokens"]) || !false.Equals(parsed["stream"]) ||
                messages==null || messages.Count!=2)throw new StartupFailure("replay_request_shape");
            for(int i=0;i<2;i++)
            {
                var item=messages[i] as Dictionary<string,object>;BridgeRuntime.Shape(item,"role","content");
                if(!(i==0?"system":"user").Equals(item["role"]) || !(item["content"] is string) || ((string)item["content"]).Length==0)
                    throw new StartupFailure("replay_message_shape");
            }
            string hash=BridgeHostFiles.Hash(body),size=body.Length.ToString(CultureInfo.InvariantCulture);
            return new Dictionary<string,object>{
                {"validation_schema","maya.model.lease_replay.v1"},{"case","M04c"},{"stage","lease_consumed"},
                {"attempt",attempt},{"request_id",service},{"coordinator_request_id",replay},{"first_dispatch_command_id",first},
                {"runtime_delivery_command_id",delivery},{"replay_command_id",replay},{"route","maya.offline.model.v1"},
                {"endpoint","https://maya-offline-model.invalid/v1/chat/completions"},{"model","maya-offline-wire-v1"},{"destination","provider"},
                {"request_sha256",hash},{"request_bytes",size},{"observed_request_sha256",hash},{"observed_request_bytes",size},
                {"lease_sha256",BridgeHostFiles.Hash(Encoding.ASCII.GetBytes(lease))},{"response_sha256",BridgeHostFiles.Hash(response)},
                {"response_bytes",response.Length.ToString(CultureInfo.InvariantCulture)},{"output_sha256",output},{"grant_ttl_ms","2000"},
                {"delivery_elapsed_ms",deliveryAge},{"worker_elapsed_ms",age},{"phase_before","runtime_delivered"},
                {"closed_before","false"},{"revoked_before","false"},{"grant_unexpired","true"},{"original_guard_rejected","true"},
                {"original_denial_uncertain","true"},{"request_validated","true"},{"replay_request_preflight_verified","true"},
                {"replay_request_validated","false"},{"gateway_calls","2"},{"gateway_calls_before","2"},{"gateway_calls_after","2"},
                {"replay_gateway_delta","0"},{"dispatch_attempted","true"},{"replay_dispatch_attempted","false"},
                {"dispatches","1"},{"dispatches_before","1"},{"dispatches_after","1"},{"replay_dispatch_delta","0"},
                {"runtime_prepared","1"},{"runtime_released","1"},{"replay_runtime_delta","0"},
                {"operator_prepared","0"},{"operator_released","0"},{"replay_operator_delta","0"},{"real_inference","false"}
            };
        }
        internal static void Child(Dictionary<string,object> report,string attempt)
        {
            BridgeRuntime.Shape(report,"schema","attempt","completed","native_constructor","native_conversation","sdk_closed","origins_verified",
                "distributions_verified","config_unchanged","model_requests","client_objects","real_inference","reason_type");
            if(!"maya.offline.model.child.v1".Equals(report["schema"]) || !attempt.Equals(report["attempt"]) ||
                !1.Equals(report["model_requests"]) || !(report["client_objects"] is int) || (int)report["client_objects"]<2 ||
                (int)report["client_objects"]>8 || !false.Equals(report["real_inference"]) || !"".Equals(report["reason_type"]))throw new StartupFailure("replay_child_report");
            foreach(string flag in new[]{"completed","native_constructor","native_conversation","sdk_closed","origins_verified","distributions_verified","config_unchanged"})
                if(!true.Equals(report[flag]))throw new StartupFailure("replay_child_postcondition");
        }
        internal static int Audit(byte[] raw,string actor,Dictionary<string,object> fifth)
        {
            if(raw==null || raw.Length<1 || raw.Length>131072 || actor==null ||
                !Regex.IsMatch(actor,"\\Awindows:S-1-5-(?:[0-9]+-)*[0-9]+\\z") || fifth==null || fifth.Count!=50)throw new StartupFailure("replay_audit_bound");
            string[] lines=new UTF8Encoding(false,true).GetString(raw).Split('\n');
            if(lines.Length!=6 || lines[5]!="")throw new StartupFailure("replay_audit_count");
            string[] stages={"egress_intent","dispatch_outcome","runtime_release_intent","runtime_delivery","lease_consumed"};
            DateTimeOffset? previous=null;
            for(int i=0;i<5;i++)
            {
                var record=StrictJson.Parse(Encoding.UTF8.GetBytes(lines[i]));
                BridgeRuntime.Shape(record,"schema_version","timestamp","event_type","decision","reason_code","actor_id","capability",
                    "target","operation","data_classification","idempotency_key","metadata");
                bool egress=i<2 || i==4;string eventName="model_bridge."+stages[i];
                var expected=new Dictionary<string,object>{{"schema_version",1},{"event_type",eventName},{"decision",i==4?"deny":"allow"},
                    {"reason_code",eventName},{"actor_id",actor},{"capability",egress?"model.egress":"model.output"},
                    {"target","model:maya-offline-fixture"},{"operation",egress?"infer":"disclose"},
                    {"data_classification","internal-synthetic"},{"idempotency_key",null}};
                foreach(var field in expected)if(!Object.Equals(field.Value,record[field.Key]))throw new StartupFailure("replay_audit_field");
                DateTimeOffset stamp;
                if(!(record["timestamp"] is string) || !DateTimeOffset.TryParseExact((string)record["timestamp"],
                    new[]{"yyyy-MM-dd'T'HH:mm:sszzz","yyyy-MM-dd'T'HH:mm:ss'Z'"},CultureInfo.InvariantCulture,
                    DateTimeStyles.AssumeUniversal,out stamp) || stamp.Offset!=TimeSpan.Zero || previous.HasValue && stamp<previous.Value)
                    throw new StartupFailure("replay_audit_time");
                previous=stamp;
                var meta=new Dictionary<string,object>();
                foreach(string key in new[]{"attempt","request_id","route","endpoint","model","request_sha256","request_bytes","response_sha256","response_bytes","output_sha256","real_inference"})
                    meta[key]=fifth[key];
                meta["destination"]=i<2?"provider":"runtime:"+(string)fifth["attempt"];meta["dispatches"]=i==0?"0":"1";
                if(i==0){meta["response_sha256"]="";meta["response_bytes"]="0";}
                if(i==3)meta["coordinator_request_id"]=fifth["runtime_delivery_command_id"];
                ModelValidationAdmission.Evidence(record["metadata"] as Dictionary<string,object>,i==4?fifth:meta);
            }
            return 5;
        }
    }
}
