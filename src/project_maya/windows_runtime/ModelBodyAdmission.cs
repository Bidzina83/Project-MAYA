using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using System.Web.Script.Serialization;

namespace ProjectMaya.WindowsRuntime
{
    internal static class ModelBodyAdmission
    {
        internal static bool Enabled { get {
#if HERMES_MODEL_BODY
            return true;
#else
            return false;
#endif
        } }
        internal static void Envelope(Dictionary<string,object> original,string attempt,string lease,byte[] body)
        {
            BridgeRuntime.Shape(original,"v","type","attempt","route","lease","seq","method","path","body");
            if(!1.Equals(original["v"]) || !1.Equals(original["seq"]) || !"model_request".Equals(original["type"]) ||
                !attempt.Equals(original["attempt"]) || !"maya.offline.model.v1".Equals(original["route"]) || !lease.Equals(original["lease"]) ||
                !"POST".Equals(original["method"]) || !"/v1/chat/completions".Equals(original["path"]) ||
                !new UTF8Encoding(false,true).GetString(body).Equals(original["body"]) ||
                !System.Text.RegularExpressions.Regex.IsMatch(lease,"\\A[0-9a-f]{64}\\z"))throw new StartupFailure("body_original_envelope");
        }
        internal static byte[] Mutate(byte[] original)
        {
            if(original==null || original.Length<1 || original.Length>4096)throw new StartupFailure("body_request_bound");
            var body=StrictJson.Parse(original);BridgeRuntime.Shape(body,"messages","model","max_tokens","stream");
            var messages=body["messages"] as List<object>;
            if(!"maya-offline-wire-v1".Equals(body["model"]) || !32.Equals(body["max_tokens"]) || !false.Equals(body["stream"]) ||
                messages==null || messages.Count!=2)throw new StartupFailure("body_request_shape");
            var system=messages[0] as Dictionary<string,object>;var user=messages[1] as Dictionary<string,object>;
            BridgeRuntime.Shape(system,"role","content");BridgeRuntime.Shape(user,"role","content");
            if(!"system".Equals(system["role"]) || !(system["content"] is string) || ((string)system["content"]).Length==0 ||
                !"user".Equals(user["role"]) || !(user["content"] is string))throw new StartupFailure("body_message_shape");
            string content=(string)user["content"];
            if(!System.Text.RegularExpressions.Regex.IsMatch(content,"\\AMAYA_OFFLINE_MODEL_REQUEST:[0-9a-f]{64}\\z"))
                throw new StartupFailure("body_canary_shape");
            string text=new UTF8Encoding(false,true).GetString(original);
            string start="{\"role\":\"user\",\"content\":\"";
            string tail=start+content+"\"}],\"model\":\"maya-offline-wire-v1\",\"max_tokens\":32,\"stream\":false}";
            if(!text.EndsWith(tail,StringComparison.Ordinal))throw new StartupFailure("body_serializer_shape");
            int position=text.Length-tail.Length+start.Length+content.Length-1;
            char digit=text[position]=='0'?'1':'0';
            byte[] mutant=Encoding.UTF8.GetBytes(text.Substring(0,position)+digit+text.Substring(position+1));
            var parsed=StrictJson.Parse(mutant);var changedMessages=parsed["messages"] as List<object>;
            var changedUser=changedMessages[1] as Dictionary<string,object>;changedUser["content"]=content;
            var json=new JavaScriptSerializer();
            if(mutant.Length!=original.Length || json.Serialize(parsed)!=json.Serialize(body))throw new StartupFailure("body_single_mutation");
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
                {"validation_schema","maya.model.body_validation.v1"},{"case","M03d"},{"stage","request_body"},
                {"coordinator_request_id",commandId},{"mutated_sha256",BridgeHostFiles.Hash(mutant)},
                {"mutated_bytes",mutant.Length.ToString(CultureInfo.InvariantCulture)},{"observed_model","maya-offline-wire-v1"},{"mutation_field","messages[1].content.canary.last_hex"},{"mutation_rule","last_digit_0_to_1_otherwise_to_0"},
                {"gateway_calls","0"},{"dispatch_attempted","false"},{"runtime_prepared","0"},{"runtime_released","0"},
                {"operator_prepared","0"},{"operator_released","0"}
            };
        }
    }
}
