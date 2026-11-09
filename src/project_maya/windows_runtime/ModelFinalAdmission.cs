using System;
using System.Collections.Generic;
using System.Text;
using System.Text.RegularExpressions;

namespace ProjectMaya.WindowsRuntime
{
    internal static class ModelFinalAdmission
    {
        internal static bool Enabled { get {
#if HERMES_MODEL_FINAL
            return true;
#else
            return false;
#endif
        } }
        internal static string Mutate(string text)
        {
            ModelOutputDenialAdmission.ExpectedResponse(text);
            return text.Substring(0,text.Length-1)+(text.EndsWith("0",StringComparison.Ordinal)?"1":"0");
        }
        internal static void Effects(Dictionary<string,object> effects,byte[] body,string output,string delivery,string command)
        {
            foreach(string id in new[]{delivery,command})
                if(id==null || !Regex.IsMatch(id,"\\A[0-9a-f]{32}\\z"))throw new StartupFailure("final_command_ID");
            if(delivery==command || body==null || body.Length<1 || body.Length>4096)throw new StartupFailure("final_binding");
            byte[] response=ModelOutputDenialAdmission.ExpectedResponse(output),normal=Encoding.UTF8.GetBytes(output),
                fault=Encoding.UTF8.GetBytes(Mutate(output));
            ModelValidationAdmission.Evidence(effects,new Dictionary<string,object>{
                {"case","M08"},{"boundary","operator_text"},{"request_validated",true},{"response_validated",true},
                {"gateway_calls",2},{"dispatch_attempted",true},{"dispatches",1},{"uncertain",true},
                {"validation_stage","operator_text"},{"runtime_delivery_command_id",delivery},{"final_command_id",command},
                {"request_sha256",BridgeHostFiles.Hash(body)},{"request_bytes",body.Length},
                {"response_sha256",BridgeHostFiles.Hash(response)},{"response_bytes",response.Length},
                {"original_text_sha256",BridgeHostFiles.Hash(normal)},{"original_text_bytes",normal.Length},
                {"observed_text_sha256",BridgeHostFiles.Hash(fault)},{"observed_text_bytes",fault.Length},
                {"prepared_runtime_releases",1},{"confirmed_runtime_releases",1},
                {"prepared_operator_releases",0},{"confirmed_operator_releases",0},
                {"egress_gateway_denied",false},{"runtime_output_gateway_denied",false},{"real_inference",false}});
        }
    }
}
