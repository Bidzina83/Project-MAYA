using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace ProjectMaya.WindowsRuntime
{
    internal static class ModelMalformedAdmission
    {
        internal static bool Enabled { get {
#if HERMES_MODEL_MALFORMED
            return true;
#else
            return false;
#endif
        } }
        internal static void Effects(Dictionary<string,object> effects,byte[] body,string output)
        {
            byte[] expected=ModelOutputDenialAdmission.ExpectedResponse(output);
            ModelValidationAdmission.Evidence(effects,new Dictionary<string,object>{
                {"case","M07a"},{"boundary","response_json"},{"request_validated",true},{"egress_allowed",true},
                {"gateway_calls",1},{"dispatch_attempted",true},{"dispatches",1},{"response_validated",false},
                {"validation_stage","response_json"},{"observed_response_sha256",BridgeHostFiles.Hash(Encoding.ASCII.GetBytes("{"))},
                {"observed_response_bytes",1},{"response_sha256",""},{"response_bytes",0},
                {"expected_response_sha256",BridgeHostFiles.Hash(expected)},{"expected_response_bytes",expected.Length},
                {"prepared_runtime_releases",0},{"confirmed_runtime_releases",0},{"prepared_operator_releases",0},
                {"confirmed_operator_releases",0},{"real_inference",false},{"uncertain",true},
                {"request_sha256",BridgeHostFiles.Hash(body)},{"request_bytes",body.Length},
                {"egress_gateway_denied",false},{"runtime_output_gateway_denied",false}});
        }
        internal static void Child(Dictionary<string,object> report,string attempt)
        {
            ModelDenialAdmission.Child(report,attempt,"maya.offline.model.malformed_response.child.v1");
        }
        internal static int Audit(byte[] raw,string actor,string attempt,string service,byte[] body,string output)
        {
            ModelOutputDenialAdmission.ExpectedResponse(output);
            foreach(string id in new[]{attempt,service})
                if(id==null || !Regex.IsMatch(id,"\\A[0-9a-f]{32}\\z"))throw new StartupFailure("malformed_audit_ID");
            if(raw==null || raw.Length<1 || raw.Length>131072 || actor==null ||
                !Regex.IsMatch(actor,"\\Awindows:S-1-5-(?:[0-9]+-)*[0-9]+\\z") || body==null || body.Length<1 || body.Length>4096 ||
                output==null ||
                Encoding.UTF8.GetByteCount(output)<1 || Encoding.UTF8.GetByteCount(output)>1024)throw new StartupFailure("malformed_audit_bound");
            string[] lines=new UTF8Encoding(false,true).GetString(raw).Split('\n');
            if(lines.Length!=3 || lines[2]!="")throw new StartupFailure("malformed_audit_count");
            string[] stages={"egress_intent","denied"};
            DateTimeOffset? previous=null;
            for(int i=0;i<2;i++)
            {
                var record=StrictJson.Parse(Encoding.UTF8.GetBytes(lines[i]));
                BridgeRuntime.Shape(record,"schema_version","timestamp","event_type","decision","reason_code","actor_id","capability",
                    "target","operation","data_classification","idempotency_key","metadata");
                string name="model_bridge."+stages[i];
                var expected=new Dictionary<string,object>{{"schema_version",1},{"event_type",name},{"decision",i==0?"allow":"deny"},{"reason_code",name},
                    {"actor_id",actor},{"capability","model.egress"},{"target","model:maya-offline-fixture"},
                    {"operation","infer"},{"data_classification","internal-synthetic"},{"idempotency_key",null}};
                foreach(var field in expected)if(!Object.Equals(field.Value,record[field.Key]))throw new StartupFailure("malformed_audit_field");
                DateTimeOffset stamp;
                if(!(record["timestamp"] is string) || !DateTimeOffset.TryParseExact((string)record["timestamp"],
                    new[]{"yyyy-MM-dd'T'HH:mm:sszzz","yyyy-MM-dd'T'HH:mm:ss'Z'"},CultureInfo.InvariantCulture,
                    DateTimeStyles.AssumeUniversal,out stamp) || stamp.Offset!=TimeSpan.Zero || previous.HasValue && stamp<previous.Value)
                    throw new StartupFailure("malformed_audit_time");
                previous=stamp;
                var meta=new Dictionary<string,object>{{"attempt",attempt},{"request_id",service},{"route","maya.offline.model.v1"},
                    {"endpoint","https://maya-offline-model.invalid/v1/chat/completions"},{"model","maya-offline-wire-v1"},
                    {"destination","provider"},{"request_sha256",BridgeHostFiles.Hash(body)},
                    {"request_bytes",body.Length.ToString(CultureInfo.InvariantCulture)},{"response_sha256",""},
                    {"response_bytes","0"},
                    {"output_sha256",BridgeHostFiles.Hash(Encoding.UTF8.GetBytes(output))},{"dispatches",i==0?"0":"1"},{"real_inference","false"}};
                ModelValidationAdmission.Evidence(record["metadata"] as Dictionary<string,object>,meta);
            }
            return 2;
        }
    }
}
