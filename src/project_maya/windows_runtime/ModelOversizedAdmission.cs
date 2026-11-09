using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace ProjectMaya.WindowsRuntime
{
    internal static class ModelOversizedAdmission
    {
        internal static bool Enabled { get {
#if HERMES_MODEL_OVERSIZED
            return true;
#else
            return false;
#endif
        } }
        internal static void Effects(Dictionary<string,object> effects,byte[] body,string output)
        {
            byte[] expected=ModelOutputDenialAdmission.ExpectedResponse(output);
            ModelValidationAdmission.Evidence(effects,new Dictionary<string,object>{
                {"case","M07b"},{"boundary","response_size"},{"request_validated",true},{"egress_allowed",true},
                {"gateway_calls",1},{"dispatch_attempted",true},{"dispatches",1},{"response_validated",false},
                {"validation_stage","response_size"},{"observed_response_sha256",BridgeHostFiles.Hash(Encoding.ASCII.GetBytes("{\"x\":\"" + new string('a',4089) + "\"}"))},
                {"observed_response_bytes",4097},{"response_sha256",""},{"response_bytes",0},
                {"expected_response_sha256",BridgeHostFiles.Hash(expected)},{"expected_response_bytes",expected.Length},
                {"prepared_runtime_releases",0},{"confirmed_runtime_releases",0},{"prepared_operator_releases",0},
                {"confirmed_operator_releases",0},{"real_inference",false},{"uncertain",true},
                {"request_sha256",BridgeHostFiles.Hash(body)},{"request_bytes",body.Length},
                {"egress_gateway_denied",false},{"runtime_output_gateway_denied",false}});
        }
        internal static void Child(Dictionary<string,object> report,string attempt)
        {
            ModelDenialAdmission.Child(report,attempt,"maya.offline.model.oversized_response.child.v1");
        }
        internal static int Audit(byte[] raw,string actor,string attempt,string service,byte[] body,string output)
        {
            return ModelMalformedAdmission.Audit(raw,actor,attempt,service,body,output);
        }
    }
}
