using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace ProjectMaya.WindowsRuntime
{
    internal static class ModelOutputDenialAdmission
    {
        internal static bool Enabled { get {
#if HERMES_MODEL_OUTPUT_DENY
            return true;
#else
            return false;
#endif
        } }
        internal static byte[] ExpectedResponse(string output)
        {
            if(output==null || !Regex.IsMatch(output,"\\AMAYA_OFFLINE_MODEL_OK:[0-9a-f]{32}\\z"))
                throw new StartupFailure("output_denial_oracle");
            return Encoding.ASCII.GetBytes("{\"id\":\"maya-offline-synthetic\",\"object\":\"chat.completion\",\"created\":0,\"model\":\"maya-offline-wire-v1\",\"choices\":[{\"index\":0,\"message\":{\"role\":\"assistant\",\"content\":\""+output+"\"},\"finish_reason\":\"stop\"}],\"usage\":{\"prompt_tokens\":0,\"completion_tokens\":0,\"total_tokens\":0}}");
        }
        internal static void Effects(Dictionary<string,object> effects,byte[] body,string output)
        {
            byte[] response=ExpectedResponse(output);
            ModelValidationAdmission.Evidence(effects,new Dictionary<string,object>{
                {"case","M06"},{"boundary","gateway_runtime_output"},{"request_validated",true},
                {"response_validated",true},{"gateway_denied",true},{"gateway_calls",2},{"dispatch_attempted",true},
                {"dispatches",1},{"prepared_runtime_releases",0},{"confirmed_runtime_releases",0},
                {"prepared_operator_releases",0},{"confirmed_operator_releases",0},{"real_inference",false},
                {"uncertain",true},{"request_sha256",BridgeHostFiles.Hash(body)},{"request_bytes",body.Length},
                {"response_sha256",BridgeHostFiles.Hash(response)},{"response_bytes",response.Length}});
        }
        internal static void Child(Dictionary<string,object> report,string attempt)
        {
            ModelDenialAdmission.Child(report,attempt,"maya.offline.model.output_denial.child.v1");
        }
        internal static int Audit(byte[] raw,string actor,string attempt,string service,byte[] body,string output)
        {
            byte[] response=ExpectedResponse(output);
            foreach(string id in new[]{attempt,service})
                if(id==null || !Regex.IsMatch(id,"\\A[0-9a-f]{32}\\z"))throw new StartupFailure("output_denial_audit_ID");
            if(raw==null || raw.Length<1 || raw.Length>131072 || actor==null ||
                !Regex.IsMatch(actor,"\\Awindows:S-1-5-(?:[0-9]+-)*[0-9]+\\z") || body==null || body.Length<1 || body.Length>4096 ||
                response==null || response.Length<1 || response.Length>4096 || output==null ||
                Encoding.UTF8.GetByteCount(output)<1 || Encoding.UTF8.GetByteCount(output)>1024)throw new StartupFailure("output_denial_audit_bound");
            string[] lines=new UTF8Encoding(false,true).GetString(raw).Split('\n');
            if(lines.Length!=4 || lines[3]!="")throw new StartupFailure("output_denial_audit_count");
            string[] stages={"egress_intent","dispatch_outcome","denied"};
            DateTimeOffset? previous=null;
            for(int i=0;i<3;i++)
            {
                var record=StrictJson.Parse(Encoding.UTF8.GetBytes(lines[i]));
                BridgeRuntime.Shape(record,"schema_version","timestamp","event_type","decision","reason_code","actor_id","capability",
                    "target","operation","data_classification","idempotency_key","metadata");
                string name="model_bridge."+stages[i];
                var expected=new Dictionary<string,object>{{"schema_version",1},{"event_type",name},{"decision",i<2?"allow":"deny"},{"reason_code",name},
                    {"actor_id",actor},{"capability",i<2?"model.egress":"model.output"},{"target","model:maya-offline-fixture"},
                    {"operation",i<2?"infer":"disclose"},{"data_classification","internal-synthetic"},{"idempotency_key",null}};
                foreach(var field in expected)if(!Object.Equals(field.Value,record[field.Key]))throw new StartupFailure("output_denial_audit_field");
                DateTimeOffset stamp;
                if(!(record["timestamp"] is string) || !DateTimeOffset.TryParseExact((string)record["timestamp"],
                    new[]{"yyyy-MM-dd'T'HH:mm:sszzz","yyyy-MM-dd'T'HH:mm:ss'Z'"},CultureInfo.InvariantCulture,
                    DateTimeStyles.AssumeUniversal,out stamp) || stamp.Offset!=TimeSpan.Zero || previous.HasValue && stamp<previous.Value)
                    throw new StartupFailure("output_denial_audit_time");
                previous=stamp;
                var meta=new Dictionary<string,object>{{"attempt",attempt},{"request_id",service},{"route","maya.offline.model.v1"},
                    {"endpoint","https://maya-offline-model.invalid/v1/chat/completions"},{"model","maya-offline-wire-v1"},
                    {"destination",i<2?"provider":"runtime:"+attempt},{"request_sha256",BridgeHostFiles.Hash(body)},
                    {"request_bytes",body.Length.ToString(CultureInfo.InvariantCulture)},{"response_sha256",i==0?"":BridgeHostFiles.Hash(response)},
                    {"response_bytes",i==0?"0":response.Length.ToString(CultureInfo.InvariantCulture)},
                    {"output_sha256",BridgeHostFiles.Hash(Encoding.UTF8.GetBytes(output))},{"dispatches",i==0?"0":"1"},{"real_inference","false"}};
                ModelValidationAdmission.Evidence(record["metadata"] as Dictionary<string,object>,meta);
            }
            return 3;
        }
    }
}
