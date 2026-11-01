using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using System.Web.Script.Serialization;

namespace ProjectMaya.WindowsRuntime
{
    internal static class ModelValidationAdmission
    {
        internal static bool Enabled { get {
#if HERMES_MODEL_VALIDATION
            return true;
#else
            return false;
#endif
        } }
        internal static byte[] Mutate(byte[] original)
        {
            if(original==null || original.Length<1 || original.Length>4096)throw new StartupFailure("validation_request_bound");
            string text=new UTF8Encoding(false,true).GetString(original);
            var body=StrictJson.Parse(original);BridgeRuntime.Shape(body,"messages","model","max_tokens","stream");
            const string tail=",\"model\":\"maya-offline-wire-v1\",\"max_tokens\":32,\"stream\":false}";
            if(!"maya-offline-wire-v1".Equals(body["model"]) || !32.Equals(body["max_tokens"]) ||
                !false.Equals(body["stream"]) || !text.EndsWith(tail,StringComparison.Ordinal))throw new StartupFailure("validation_request_shape");
            // The pinned serializer suffix fixes the top-level field, preserving
            // every other byte. This is not a text-wide substitution.
            string changed=text.Substring(0,text.Length-tail.Length)+tail.Replace("wire-v1","wire-v0");
            byte[] mutant=Encoding.UTF8.GetBytes(changed);var parsed=StrictJson.Parse(mutant);
            var json=new JavaScriptSerializer();parsed["model"]=body["model"];
            if(mutant.Length!=original.Length || json.Serialize(parsed)!=json.Serialize(body))throw new StartupFailure("validation_single_mutation");
            return mutant;
        }
        internal static Dictionary<string,object> Metadata(string attempt,string requestId,string commandId,byte[] original,string outputHash)
        {
            byte[] mutant=Mutate(original);
            foreach(string value in new[]{attempt,requestId,commandId})
                if(value==null || !System.Text.RegularExpressions.Regex.IsMatch(value,"\\A[0-9a-f]{32}\\z"))throw new StartupFailure("validation_identity");
            if(outputHash==null || !System.Text.RegularExpressions.Regex.IsMatch(outputHash,"\\A[0-9a-f]{64}\\z"))throw new StartupFailure("validation_output_hash");
            return new Dictionary<string,object> {
                {"attempt",attempt},{"request_id",requestId},{"route","maya.offline.model.v1"},
                {"endpoint","https://maya-offline-model.invalid/v1/chat/completions"},{"model","maya-offline-wire-v1"},
                {"destination","provider"},{"request_sha256",BridgeHostFiles.Hash(original)},
                {"request_bytes",original.Length.ToString(CultureInfo.InvariantCulture)},{"response_sha256",""},{"response_bytes","0"},
                {"output_sha256",outputHash},{"dispatches","0"},{"real_inference","false"},
                {"validation_schema","maya.model.validation.v1"},{"case","M03a"},{"stage","request_model"},
                {"coordinator_request_id",commandId},{"mutated_sha256",BridgeHostFiles.Hash(mutant)},
                {"mutated_bytes",mutant.Length.ToString(CultureInfo.InvariantCulture)},{"observed_model","maya-offline-wire-v0"},
                {"gateway_calls","0"},{"dispatch_attempted","false"},{"runtime_prepared","0"},{"runtime_released","0"},
                {"operator_prepared","0"},{"operator_released","0"}
            };
        }
        internal static void Evidence(Dictionary<string,object> actual,Dictionary<string,object> expected)
        {
            if(actual==null || actual.Count!=expected.Count)throw new StartupFailure("validation_evidence_shape");
            foreach(var item in expected)
                if(!actual.ContainsKey(item.Key) || !item.Value.Equals(actual[item.Key]))throw new StartupFailure("validation_evidence_binding");
        }
        internal static int Audit(byte[] raw,string actor,Dictionary<string,object> expected,bool route=false,bool attempt=false,bool body=false,bool expiry=false)
        {
            if((route?1:0)+(attempt?1:0)+(body?1:0)+(expiry?1:0)>1)throw new StartupFailure("validation_case_conflict");
            if(raw==null || raw.Length<1 || raw.Length>131072 || actor==null ||
                !System.Text.RegularExpressions.Regex.IsMatch(actor,"\\Awindows:S-1-5-(?:[0-9]+-)*[0-9]+\\z"))throw new StartupFailure("validation_audit_bound");
            string[] lines=new UTF8Encoding(false,true).GetString(raw).Split('\n');
            if(lines.Length!=2 || lines[1]!="")throw new StartupFailure("validation_audit_count");
            var record=StrictJson.Parse(Encoding.UTF8.GetBytes(lines[0]));
            BridgeRuntime.Shape(record,"schema_version","timestamp","event_type","decision","reason_code","actor_id",
                "capability","target","operation","data_classification","idempotency_key","metadata");
            var fields=new Dictionary<string,object> {
                {"schema_version",1},{"event_type",expiry ? "model_bridge.lease_expired" : body ? "model_bridge.body_rejected" : attempt ? "model_bridge.attempt_rejected" : route ? "model_bridge.route_rejected" : "model_bridge.validation_rejected"},{"decision","deny"},
                {"reason_code",expiry ? "model_bridge.lease_expired" : body ? "model_bridge.wrong_body" : attempt ? "model_bridge.wrong_attempt" : route ? "model_bridge.wrong_route" : "model_bridge.wrong_model"},{"actor_id",actor},{"capability","model.egress"},
                {"target","model:maya-offline-fixture"},{"operation","infer"},{"data_classification","internal-synthetic"},{"idempotency_key",null}
            };
            foreach(var item in fields)if(!Object.Equals(item.Value,record[item.Key]))throw new StartupFailure("validation_audit_field");
            DateTimeOffset stamp;
            if(!(record["timestamp"] is string) || !DateTimeOffset.TryParseExact((string)record["timestamp"],
                new[]{"yyyy-MM-dd'T'HH:mm:sszzz","yyyy-MM-dd'T'HH:mm:ss'Z'"},CultureInfo.InvariantCulture,
                DateTimeStyles.AssumeUniversal,out stamp) || stamp.Offset!=TimeSpan.Zero)throw new StartupFailure("validation_audit_time");
            Evidence(record["metadata"] as Dictionary<string,object>,expected);return 1;
        }
    }
}
