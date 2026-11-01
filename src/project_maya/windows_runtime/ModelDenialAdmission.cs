using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace ProjectMaya.WindowsRuntime
{
    internal static class ModelDenialAdmission
    {
        internal static bool Enabled { get {
#if HERMES_MODEL_DENY
            return true;
#else
            return false;
#endif
        } }
        internal static void Effects(Dictionary<string,object> effects)
        {
            BridgeRuntime.Shape(effects,"case","boundary","request_validated","gateway_denied","dispatches",
                "confirmed_runtime_releases","confirmed_operator_releases","real_inference");
            if(!"M02".Equals(effects["case"]) || !"gateway_egress".Equals(effects["boundary"]) ||
                !true.Equals(effects["request_validated"]) || !true.Equals(effects["gateway_denied"]) ||
                !0.Equals(effects["dispatches"]) || !0.Equals(effects["confirmed_runtime_releases"]) ||
                !0.Equals(effects["confirmed_operator_releases"]) || !false.Equals(effects["real_inference"]))
                throw new StartupFailure("model_denial_effects");
        }
        internal static void Child(Dictionary<string,object> report,string attempt,string schema="maya.offline.model.denial.child.v1")
        {
            BridgeRuntime.Shape(report,"schema","attempt","completed","native_constructor","native_conversation","sdk_closed",
                "origins_verified","distributions_verified","config_unchanged","model_requests","client_objects",
                "real_inference","reason_type","denial_observed");
            if(!schema.Equals(report["schema"]) || !attempt.Equals(report["attempt"]) ||
                !false.Equals(report["native_conversation"]) || !false.Equals(report["real_inference"]) ||
                !"".Equals(report["reason_type"]) || !1.Equals(report["model_requests"]) ||
                !(report["client_objects"] is int) || (int)report["client_objects"]<2 || (int)report["client_objects"]>8)
                throw new StartupFailure("model_denial_child");
            foreach(string flag in new[]{"completed","native_constructor","sdk_closed","origins_verified",
                "distributions_verified","config_unchanged","denial_observed"})
                if(!true.Equals(report[flag]))throw new StartupFailure("model_denial_child");
        }
        internal static int Audit(byte[] raw,string attempt,string actor,string requestId,string requestHash,int requestBytes,string outputHash)
        {
            foreach(string value in new[]{attempt,requestId})
                if(value==null || !Regex.IsMatch(value,"\\A[0-9a-f]{32}\\z"))throw new StartupFailure("model_denial_identity");
            foreach(string value in new[]{requestHash,outputHash})
                if(value==null || !Regex.IsMatch(value,"\\A[0-9a-f]{64}\\z"))throw new StartupFailure("model_denial_digest");
            if(raw==null || raw.Length<1 || raw.Length>131072 || requestBytes<1 || requestBytes>4096 ||
                actor==null || !Regex.IsMatch(actor,"\\Awindows:S-1-5-(?:[0-9]+-)*[0-9]+\\z"))throw new StartupFailure("model_denial_bounds");
            string text=new UTF8Encoding(false,true).GetString(raw);string[] lines=text.Split('\n');
            if(lines.Length!=2 || lines[1]!="")throw new StartupFailure("model_denial_count");
            var record=StrictJson.Parse(Encoding.UTF8.GetBytes(lines[0]));
            BridgeRuntime.Shape(record,"schema_version","timestamp","event_type","decision","reason_code","actor_id",
                "capability","target","operation","data_classification","idempotency_key","metadata");
            var expected=new Dictionary<string,object> {
                {"schema_version",1},{"event_type","model_bridge.denied"},{"decision","deny"},{"reason_code","model_bridge.denied"},
                {"actor_id",actor},{"capability","model.egress"},{"target","model:maya-offline-fixture"},{"operation","infer"},
                {"data_classification","internal-synthetic"},{"idempotency_key",null}
            };
            foreach(var item in expected)
                if(!Object.Equals(item.Value,record[item.Key]))throw new StartupFailure("model_denial_audit_record");
            DateTimeOffset stamp;
            if(!(record["timestamp"] is string) || !DateTimeOffset.TryParseExact((string)record["timestamp"],
                new[]{"yyyy-MM-dd'T'HH:mm:sszzz","yyyy-MM-dd'T'HH:mm:ss'Z'"},CultureInfo.InvariantCulture,
                DateTimeStyles.AssumeUniversal,out stamp) || stamp.Offset!=TimeSpan.Zero)throw new StartupFailure("model_denial_time");
            var metadata=record["metadata"] as Dictionary<string,object>;
            expected=new Dictionary<string,object> {
                {"attempt",attempt},{"request_id",requestId},{"route","maya.offline.model.v1"},
                {"endpoint","https://maya-offline-model.invalid/v1/chat/completions"},{"model","maya-offline-wire-v1"},
                {"destination","provider"},{"request_sha256",requestHash},{"response_sha256",""},
                {"request_bytes",requestBytes.ToString(CultureInfo.InvariantCulture)},{"response_bytes","0"},
                {"output_sha256",outputHash},{"dispatches","0"},{"real_inference","false"}
            };
            if(metadata==null || metadata.Count!=expected.Count)throw new StartupFailure("model_denial_metadata");
            foreach(var item in expected)
                if(!metadata.ContainsKey(item.Key) || !item.Value.Equals(metadata[item.Key]))throw new StartupFailure("model_denial_binding");
            return 1;
        }
    }
}
