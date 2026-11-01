using System;
using System.Collections.Generic;

namespace ProjectMaya.WindowsRuntime
{
    internal static class ModelRecreateAdmission
    {
        internal static bool Enabled { get {
#if HERMES_MODEL_RECREATE
            return true;
#else
            return false;
#endif
        } }
        internal static void Child(Dictionary<string,object> report,string attempt,string probeId,byte[] body)
        {
            BridgeRuntime.Shape(report,"schema","attempt","completed","native_constructor","native_conversation","sdk_closed","origins_verified",
                "distributions_verified","config_unchanged","model_requests","client_objects","real_inference","reason_type","probe_command_id","probe","probe_lifecycle");
            if(!"maya.offline.model.recreate.child.v1".Equals(report["schema"]) || !attempt.Equals(report["attempt"]) ||
                !probeId.Equals(report["probe_command_id"]) || !1.Equals(report["model_requests"]) || !(report["client_objects"] is int) ||
                (int)report["client_objects"]<3 || (int)report["client_objects"]>8 || !false.Equals(report["real_inference"]) ||
                !"".Equals(report["reason_type"]))throw new StartupFailure("recreate_child_report");
            foreach(string flag in new[]{"completed","native_constructor","native_conversation","sdk_closed","origins_verified","distributions_verified","config_unchanged"})
                if(!true.Equals(report[flag]))throw new StartupFailure("recreate_child_postcondition");
            var probe=report["probe"] as Dictionary<string,object>;
            ModelValidationAdmission.Evidence(probe,new Dictionary<string,object>{{"case","M05b"},{"boundary","adapter_consumed_budget"},
                {"transport_attempts",2},{"model_requests",1},{"completed_exchanges",1},{"budget_rejections",1},{"distinct_new_clients",true},{"same_consumed_adapter",true},
                {"request_sha256",BridgeHostFiles.Hash(body)},{"request_bytes",body.Length}});
            ModelValidationAdmission.Evidence(report["probe_lifecycle"] as Dictionary<string,object>,new Dictionary<string,object>{
                {"schema","maya.model.recreate.lifecycle.v1"},{"stage","complete"},{"failure_stage",""},{"armed",true},
                {"hook_calls",1},{"close_delegations",1},{"owner_thread_verified",true},{"used_client_verified",true},
                {"native_close_verified",true},{"probe_after_native_close",true},{"new_clients_distinct",true},{"same_adapter_verified",true},{"new_client_close_verified",true}});
        }
        internal static void Effects(Dictionary<string,object> effects,byte[] body,byte[] response,string delivery)
        {
            ModelValidationAdmission.Evidence(effects,new Dictionary<string,object>{{"case","M05b"},{"gateway_calls",2},{"dispatches",1},
                {"confirmed_runtime_releases",1},{"confirmed_operator_releases",0},{"real_inference",false},
                {"request_sha256",BridgeHostFiles.Hash(body)},{"response_sha256",BridgeHostFiles.Hash(response)},{"delivery_command_id",delivery}});
        }
        internal static int Audit(byte[] raw,string actor,string attempt,string service,byte[] body,byte[] response,string output,string delivery)
        {
            return ModelBudgetAdmission.Audit(raw,actor,attempt,service,body,response,output,delivery);
        }
    }
}

