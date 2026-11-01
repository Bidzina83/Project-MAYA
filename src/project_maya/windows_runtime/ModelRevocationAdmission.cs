using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace ProjectMaya.WindowsRuntime
{
    internal static class ModelRevocationAdmission
    {
        internal static bool Enabled { get {
#if HERMES_MODEL_REVOKE
            return true;
#else
            return false;
#endif
        } }
        internal static string Age(Dictionary<string,object> evidence,string key)
        {
            object value;
            if(evidence==null || !evidence.TryGetValue(key,out value) || !(value is string))throw new StartupFailure("revoke_age_missing");
            string text=(string)value;int n;
            if(!Regex.IsMatch(text,"\\A(?:0|[1-9][0-9]{0,3})\\z") ||
                !Int32.TryParse(text,NumberStyles.None,CultureInfo.InvariantCulture,out n) || n>=2000)
                throw new StartupFailure("revoke_age_bound");
            return text;
        }
        internal static Dictionary<string,object> Metadata(string attempt,string requestId,string revokeId,string dispatchId,
            string lease,byte[] body,string outputHash,string revokeAge,string age)
        {
            Age(new Dictionary<string,object>{{"age",age}},"age");Age(new Dictionary<string,object>{{"age",revokeAge}},"age");
            bool rejection=dispatchId!="";
            if(Int32.Parse(age,CultureInfo.InvariantCulture)<Int32.Parse(revokeAge,CultureInfo.InvariantCulture) ||
                (!rejection && age!=revokeAge))throw new StartupFailure("revoke_age_order");
            foreach(string id in new[]{attempt,requestId,revokeId})
                if(id==null || !Regex.IsMatch(id,"\\A[0-9a-f]{32}\\z"))throw new StartupFailure("revoke_ID");
            if(dispatchId==null || (rejection && (!Regex.IsMatch(dispatchId,"\\A[0-9a-f]{32}\\z") || dispatchId==revokeId)))
                throw new StartupFailure("revoke_dispatch_ID");
            if(body==null || body.Length<1 || body.Length>4096 || outputHash==null || !Regex.IsMatch(outputHash,"\\A[0-9a-f]{64}\\z"))
                throw new StartupFailure("revoke_body_bound");
            ModelBodyAdmission.Envelope(new Dictionary<string,object>{{"v",1},{"type","model_request"},{"attempt",attempt},
                {"route","maya.offline.model.v1"},{"lease",lease},{"seq",1},{"method","POST"},{"path","/v1/chat/completions"},
                {"body",new UTF8Encoding(false,true).GetString(body)}},attempt,lease,body);
            var parsed=StrictJson.Parse(body);BridgeRuntime.Shape(parsed,"messages","model","max_tokens","stream");
            var messages=parsed["messages"] as List<object>;
            if(!"maya-offline-wire-v1".Equals(parsed["model"]) || !32.Equals(parsed["max_tokens"]) || !false.Equals(parsed["stream"]) ||
                messages==null || messages.Count!=2)throw new StartupFailure("revoke_request_shape");
            for(int i=0;i<2;i++)
            {
                var item=messages[i] as Dictionary<string,object>;BridgeRuntime.Shape(item,"role","content");
                if(!(i==0?"system":"user").Equals(item["role"]) || !(item["content"] is string) || ((string)item["content"]).Length==0)
                    throw new StartupFailure("revoke_message_shape");
            }
            string hash=BridgeHostFiles.Hash(body),size=body.Length.ToString(CultureInfo.InvariantCulture);
            return new Dictionary<string,object>{
                {"validation_schema","maya.model.lease_revocation.v1"},{"case","M04b"},{"stage",rejection?"lease_revoked":"revoke_applied"},
                {"attempt",attempt},{"request_id",requestId},{"coordinator_request_id",rejection?dispatchId:revokeId},
                {"revoke_command_id",revokeId},{"dispatch_command_id",dispatchId},{"route","maya.offline.model.v1"},
                {"endpoint","https://maya-offline-model.invalid/v1/chat/completions"},{"model","maya-offline-wire-v1"},{"destination","provider"},
                {"request_sha256",hash},{"request_bytes",size},{"observed_request_sha256",rejection?hash:""},{"observed_request_bytes",rejection?size:"0"},
                {"lease_sha256",BridgeHostFiles.Hash(Encoding.ASCII.GetBytes(lease))},{"grant_ttl_ms","2000"},
                {"worker_elapsed_ms",age},{"revoke_elapsed_ms",revokeAge},{"phase_before","issued"},{"closed_before","false"},
                {"revoked_before",rejection?"true":"false"},{"revoked_after","true"},{"grant_unexpired","true"},
                {"original_guard_rejected",rejection?"true":"false"},{"request_preflight_verified",rejection?"true":"false"},
                {"request_validated","false"},{"gateway_calls","0"},{"dispatch_attempted","false"},{"response_sha256",""},{"response_bytes","0"},
                {"output_sha256",outputHash},{"dispatches","0"},{"runtime_prepared","0"},{"runtime_released","0"},
                {"operator_prepared","0"},{"operator_released","0"},{"real_inference","false"}
            };
        }
        internal static int Audit(byte[] raw,string actor,Dictionary<string,object> first,Dictionary<string,object> second)
        {
            if(raw==null || raw.Length<1 || raw.Length>131072 || actor==null ||
                !Regex.IsMatch(actor,"\\Awindows:S-1-5-(?:[0-9]+-)*[0-9]+\\z"))throw new StartupFailure("revoke_audit_bound");
            string[] lines=new UTF8Encoding(false,true).GetString(raw).Split('\n');
            if(lines.Length!=3 || lines[2]!="")throw new StartupFailure("revoke_audit_count");
            for(int i=0;i<2;i++)
            {
                var record=StrictJson.Parse(Encoding.UTF8.GetBytes(lines[i]));
                BridgeRuntime.Shape(record,"schema_version","timestamp","event_type","decision","reason_code","actor_id", "capability",
                    "target","operation","data_classification","idempotency_key","metadata");
                string eventName="model_bridge."+(i==0?"grant_revoked":"lease_revoked");
                var expected=new Dictionary<string,object>{{"schema_version",1},{"event_type",eventName},{"decision","deny"},
                    {"reason_code",eventName},{"actor_id",actor},{"capability","model.egress"},{"target","model:maya-offline-fixture"},
                    {"operation","infer"},{"data_classification","internal-synthetic"},{"idempotency_key",null}};
                foreach(var field in expected)if(!Object.Equals(field.Value,record[field.Key]))throw new StartupFailure("revoke_audit_field");
                DateTimeOffset stamp;
                if(!(record["timestamp"] is string) || !DateTimeOffset.TryParseExact((string)record["timestamp"],
                    new[]{"yyyy-MM-dd'T'HH:mm:sszzz","yyyy-MM-dd'T'HH:mm:ss'Z'"},CultureInfo.InvariantCulture,
                    DateTimeStyles.AssumeUniversal,out stamp) || stamp.Offset!=TimeSpan.Zero)throw new StartupFailure("revoke_audit_time");
                ModelValidationAdmission.Evidence(record["metadata"] as Dictionary<string,object>,i==0?first:second);
            }
            return 2;
        }
    }
}
