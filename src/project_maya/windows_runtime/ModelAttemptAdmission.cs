using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace ProjectMaya.WindowsRuntime
{
    internal static class ModelAttemptAdmission
    {
        internal static bool Enabled { get {
#if HERMES_MODEL_ATTEMPT
            return true;
#else
            return false;
#endif
        } }
        const string Route="maya.offline.model.v1";
        internal static string Mismatch(string attempt)
        {
            if(attempt==null || !Regex.IsMatch(attempt,"\\A[0-9a-f]{32}\\z"))throw new StartupFailure("attempt_identity");
            return (attempt[0]=='0' ? "1" : "0")+attempt.Substring(1);
        }
        internal static Dictionary<string,object> Mutate(Dictionary<string,object> original,string attempt,string lease,byte[] body)
        {
            BridgeRuntime.Shape(original,"v","type","attempt","route","lease","seq","method","path","body");
            if(!1.Equals(original["v"]) || !1.Equals(original["seq"]) || !"model_request".Equals(original["type"]) ||
                !attempt.Equals(original["attempt"]) || !Route.Equals(original["route"]) || !lease.Equals(original["lease"]) ||
                !"POST".Equals(original["method"]) || !"/v1/chat/completions".Equals(original["path"]) ||
                !new UTF8Encoding(false,true).GetString(body).Equals(original["body"]))throw new StartupFailure("attempt_original_binding");
            Projection(attempt,lease,body,false);
            var mutant=new Dictionary<string,object>(original);mutant["attempt"]=Mismatch(attempt);return mutant;
        }
        internal static byte[] Projection(string attempt,string lease,byte[] body,bool mutant)
        {
            if(attempt==null || !Regex.IsMatch(attempt,"\\A[0-9a-f]{32}\\z") || lease==null ||
                !Regex.IsMatch(lease,"\\A[0-9a-f]{64}\\z") || body==null || body.Length<1 || body.Length>4096)
                throw new StartupFailure("attempt_projection_bound");
            var parsed=StrictJson.Parse(body);BridgeRuntime.Shape(parsed,"messages","model","max_tokens","stream");
            if(!"maya-offline-wire-v1".Equals(parsed["model"]) || !32.Equals(parsed["max_tokens"]) || !false.Equals(parsed["stream"]))
                throw new StartupFailure("attempt_projection_body");
            return Encoding.ASCII.GetBytes("maya.model.attempt_projection.v1\n1\nmodel_request\n"+(mutant?Mismatch(attempt):attempt)+"\n"+Route+"\n"+
                BridgeHostFiles.Hash(Encoding.ASCII.GetBytes(lease))+"\n1\nPOST\n/v1/chat/completions\n"+BridgeHostFiles.Hash(body)+"\n"+
                body.Length.ToString(CultureInfo.InvariantCulture)+"\n");
        }
        internal static Dictionary<string,object> Metadata(string attempt,string requestId,string commandId,string lease,byte[] body,string outputHash)
        {
            foreach(string value in new[]{requestId,commandId})if(value==null || !Regex.IsMatch(value,"\\A[0-9a-f]{32}\\z"))
                throw new StartupFailure("attempt_identity");
            if(outputHash==null || !Regex.IsMatch(outputHash,"\\A[0-9a-f]{64}\\z"))throw new StartupFailure("attempt_output_hash");
            byte[] original=Projection(attempt,lease,body,false),mutant=Projection(attempt,lease,body,true);
            return new Dictionary<string,object> {
                {"attempt",attempt},{"request_id",requestId},{"route",Route},
                {"endpoint","https://maya-offline-model.invalid/v1/chat/completions"},{"model","maya-offline-wire-v1"},
                {"destination","provider"},{"request_sha256",BridgeHostFiles.Hash(body)},{"request_bytes",body.Length.ToString(CultureInfo.InvariantCulture)},
                {"response_sha256",""},{"response_bytes","0"},{"output_sha256",outputHash},{"dispatches","0"},{"real_inference","false"},
                {"validation_schema","maya.model.attempt_validation.v1"},{"case","M03c"},{"stage","request_attempt"},
                {"coordinator_request_id",commandId},{"projection_schema","maya.model.attempt_projection.v1"},
                {"original_projection_sha256",BridgeHostFiles.Hash(original)},{"original_projection_bytes",original.Length.ToString(CultureInfo.InvariantCulture)},
                {"mutated_projection_sha256",BridgeHostFiles.Hash(mutant)},{"mutated_projection_bytes",mutant.Length.ToString(CultureInfo.InvariantCulture)},
                {"observed_attempt",Mismatch(attempt)},{"mutated_request_sha256",BridgeHostFiles.Hash(body)},{"mutated_request_bytes",body.Length.ToString(CultureInfo.InvariantCulture)},
                {"gateway_calls","0"},{"dispatch_attempted","false"},{"runtime_prepared","0"},{"runtime_released","0"},
                {"operator_prepared","0"},{"operator_released","0"}
            };
        }
    }
}
