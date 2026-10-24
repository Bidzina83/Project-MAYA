using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Security.Principal;
using System.Text;

namespace ProjectMaya.WindowsRuntime
{
    // Source candidate. No existing profile selects these entries automatically.
    internal sealed class ModelBridgeRuntime : IDisposable
    {
        readonly string directory, attempt, canary, output;
        readonly SecurityIdentifier user;
        readonly WindowsIsolation worker;
        readonly Dictionary<string,object> record;
        readonly Action<string,int> publish;
        BridgeChannel workerChannel, childChannel;
        byte[] expectedRequest;
        string requestId;
        bool stopped;

        internal ModelBridgeRuntime(string directory, string attempt, SecurityIdentifier user,
            Dictionary<string,object> record, Action<string,int> publish)
        {
            if(publish==null)throw new StartupFailure("model_operator_delivery_unavailable");
            this.directory=directory;this.attempt=attempt;this.user=user;this.record=record;this.publish=publish;
            record["model_stage"]="host_setup";
            canary=BridgeHostFiles.RandomHex(32);output="MAYA_OFFLINE_MODEL_OK:"+BridgeHostFiles.RandomHex(16);
            ModelHostFiles.Prepare(directory,attempt,user,BridgeHostFiles.RandomHex(32),canary,output);
            worker=new WindowsIsolation("Maya.ModelWorker."+attempt);
        }
        Dictionary<string,object> Message(string type)
        {return new Dictionary<string,object>{{"v",1},{"type",type},{"attempt",attempt}};}
        Dictionary<string,object> Command(string type)
        {var m=Message(type);m["request_id"]=BridgeHostFiles.RandomHex(16);return m;}
        void Identity(Dictionary<string,object> m,string type)
        {
            if(m==null || !m.ContainsKey("v") || !1.Equals(m["v"]) || !m.ContainsKey("type") || !type.Equals(m["type"]) ||
                !m.ContainsKey("attempt") || !attempt.Equals(m["attempt"]))throw new StartupFailure("model_identity");
        }
        Dictionary<string,object> Reply(Dictionary<string,object> command,string type, int timeout,params string[] fields)
        {
            var time=Stopwatch.StartNew();workerChannel.Write(command,timeout);
            int remaining=timeout-checked((int)time.ElapsedMilliseconds);
            if(remaining<=0)throw new StartupFailure("model_rpc_deadline");
            var reply=workerChannel.Read(remaining);
            var keys=new List<string>{"v","type","attempt","request_id"};keys.AddRange(fields);
            BridgeRuntime.Shape(reply,keys.ToArray());Identity(reply,type);
            if(!command["request_id"].Equals(reply["request_id"]))throw new StartupFailure("model_request_binding");
            return reply;
        }
        internal void PrepareWorker()
        {
            record["model_stage"]="worker_start";
            worker.StartModelWorker(directory,attempt,user);
            record["model_worker_pid"]=worker.ChildPid;record["model_worker_token_verified"]=worker.ReducedLaunchTokenVerified;
            workerChannel=new BridgeChannel(worker.BridgeOutput,worker.BridgeInput);worker.ResumeBridge();
            var ready=workerChannel.Read(5000);
            BridgeRuntime.Shape(ready,"v","type","attempt","pid","request_sha256","request_bytes","service_request_id","real_inference");
            Identity(ready,"model_worker_ready");
            if(!checked((int)worker.ChildPid).Equals(ready["pid"]) || !false.Equals(ready["real_inference"]))throw new StartupFailure("model_worker_ready");
            ModelHostFiles.Recheck(directory,user);
            expectedRequest=ModelHostFiles.ReadBounded(Path.Combine(directory,"host","request.json"),4096);
            if(expectedRequest.Length<1 || !expectedRequest.Length.Equals(ready["request_bytes"]) ||
                !BridgeHostFiles.Hash(expectedRequest).Equals(ready["request_sha256"]) || !(ready["service_request_id"] is string))
                throw new StartupFailure("model_expected_request");
            requestId=(string)ready["service_request_id"];
            record["model_expected_request_sha256"]=BridgeHostFiles.Hash(expectedRequest);
            record["model_expected_request_bytes"]=expectedRequest.Length;record["model_worker_ready"]=true;
            record["model_stage"]="worker_ready";
        }
        internal uint Run(WindowsIsolation child)
        {
            childChannel=new BridgeChannel(child.BridgeOutput,child.BridgeInput);
            var watch=Stopwatch.StartNew();
            Func<int> left=delegate {int n=30000-checked((int)watch.ElapsedMilliseconds);if(n<=0)throw new StartupFailure("model_deadline");return n;};
            Func<int> rpc=delegate {return Math.Min(2000,left());};
            record["model_stage"]="child_hello";
            child.ResumeBridge();var hello=childChannel.Read(left());BridgeRuntime.Shape(hello,"v","type","attempt");Identity(hello,"model_child_hello");
            record["model_python_entry_observed"]=true;
            record["model_stage"]="native_constructor";
            var ready=childChannel.Read(left());BridgeRuntime.Shape(ready,"v","type","attempt","native_constructor");Identity(ready,"model_child_ready");
            if(!true.Equals(ready["native_constructor"]))throw new StartupFailure("model_native_constructor");
            record["model_stage"]="admission";
            var issued=Reply(Command("model_issue"),"model_grant_reply",rpc(),"grant");
            var begin=Message("model_begin");begin["canary"]=canary;begin["grant"]=issued["grant"];childChannel.Write(begin,rpc());
            record["model_stage"]="native_request";
            var request=childChannel.Read(left());
            if(request.ContainsKey("body") && request["body"] is string)
            {
                byte[] observed=Encoding.UTF8.GetBytes((string)request["body"]);
                record["model_observed_request_sha256"]=BridgeHostFiles.Hash(observed);record["model_observed_request_bytes"]=observed.Length;
            }
            if(!request.ContainsKey("body") || !(request["body"] is string) ||
                BridgeHostFiles.Hash(Encoding.UTF8.GetBytes((string)request["body"]))!=BridgeHostFiles.Hash(expectedRequest))
                throw new StartupFailure("model_child_request_mismatch");
            record["model_stage"]="worker_dispatch";
            var dispatch=Command("model_dispatch");dispatch["request"]=request;
            var reply=Reply(dispatch,"model_dispatch_reply",rpc(),"response","dispatches","prepared_runtime_releases","confirmed_runtime_releases");
            if(!1.Equals(reply["dispatches"]) || !1.Equals(reply["prepared_runtime_releases"]) || !0.Equals(reply["confirmed_runtime_releases"]))
                throw new StartupFailure("model_effect_mismatch");
            record["model_synthetic_dispatches"]=1;
            var response=reply["response"] as Dictionary<string,object>;
            BridgeRuntime.Shape(response,"v","type","attempt","seq","status","body","response_sha256");Identity(response,"model_response");
            if(!1.Equals(response["seq"]) || !"ok".Equals(response["status"]) || !(response["body"] is string))throw new StartupFailure("model_response");
            byte[] responseBytes=Encoding.UTF8.GetBytes((string)response["body"]);
            if(responseBytes.Length<1 || responseBytes.Length>4096 || !BridgeHostFiles.Hash(responseBytes).Equals(response["response_sha256"]))
                throw new StartupFailure("model_response_digest");
            var parsed=StrictJson.Parse(responseBytes);
            BridgeRuntime.Shape(parsed,"id","object","created","model","choices","usage");
            if(!"maya-offline-synthetic".Equals(parsed["id"]) || !"chat.completion".Equals(parsed["object"]) ||
                !0.Equals(parsed["created"]) || !"maya-offline-wire-v1".Equals(parsed["model"]))throw new StartupFailure("model_response_shape");
            var choices=parsed.ContainsKey("choices")?parsed["choices"] as List<object>:null;
            var choice=choices!=null && choices.Count==1?choices[0] as Dictionary<string,object>:null;
            var message=choice!=null && choice.ContainsKey("message")?choice["message"] as Dictionary<string,object>:null;
            BridgeRuntime.Shape(choice,"index","message","finish_reason");BridgeRuntime.Shape(message,"role","content");
            var usage=parsed["usage"] as Dictionary<string,object>;BridgeRuntime.Shape(usage,"prompt_tokens","completion_tokens","total_tokens");
            if(!0.Equals(choice["index"]) || !"stop".Equals(choice["finish_reason"]) || !"assistant".Equals(message["role"]) ||
                !0.Equals(usage["prompt_tokens"]) || !0.Equals(usage["completion_tokens"]) || !0.Equals(usage["total_tokens"]))
                throw new StartupFailure("model_response_shape");
            if(message==null || !message.ContainsKey("content") || !output.Equals(message["content"]))throw new StartupFailure("model_output_mismatch");
            record["model_stage"]="runtime_release";
            record["model_runtime_release_attempted"]=true;childChannel.Write(response,rpc());
            record["model_runtime_pipe_writes"]=1;
            var receipt=childChannel.Read(left());BridgeRuntime.Shape(receipt,"v","type","attempt","response_sha256","bytes");Identity(receipt,"model_runtime_receipt");
            if(!response["response_sha256"].Equals(receipt["response_sha256"]) || !responseBytes.Length.Equals(receipt["bytes"]))throw new StartupFailure("model_runtime_receipt");
            var runtime=Command("model_runtime_delivered");runtime["response_sha256"]=response["response_sha256"];
            var runtimeAck=Reply(runtime,"model_runtime_ack",rpc(),"confirmed_runtime_releases");
            if(!1.Equals(runtimeAck["confirmed_runtime_releases"]))throw new StartupFailure("model_runtime_ack");
            record["model_stage"]="native_final";
            var final=childChannel.Read(left());BridgeRuntime.Shape(final,"v","type","attempt","text","report");Identity(final,"model_child_complete");
            if(!output.Equals(final["text"]))throw new StartupFailure("model_final_mismatch");
            var report=final["report"] as Dictionary<string,object>;
            BridgeRuntime.Shape(report,"schema","attempt","completed","native_constructor","native_conversation","sdk_closed","origins_verified",
                "distributions_verified","config_unchanged","model_requests","client_objects","real_inference","reason_type");
            if(!"maya.offline.model.child.v1".Equals(report["schema"]) || !attempt.Equals(report["attempt"]) ||
                !1.Equals(report["model_requests"]) || !(report["client_objects"] is int) || (int)report["client_objects"]<2 ||
                (int)report["client_objects"]>8 || !false.Equals(report["real_inference"]) || !"".Equals(report["reason_type"]))throw new StartupFailure("model_child_report");
            foreach(string flag in new[]{"completed","native_constructor","native_conversation","sdk_closed","origins_verified","distributions_verified","config_unchanged"})
                if(!true.Equals(report[flag]))throw new StartupFailure("model_child_postcondition");
            record["model_child_report_untrusted"]=report;
            record["model_stage"]="operator_validation";
            var prepare=Command("model_prepare_final");prepare["text"]=final["text"];
            var prepared=Reply(prepare,"model_final_prepared",rpc(),"text","prepared_operator_releases","confirmed_operator_releases");
            if(!output.Equals(prepared["text"]) || !1.Equals(prepared["prepared_operator_releases"]) || !0.Equals(prepared["confirmed_operator_releases"]))
                throw new StartupFailure("model_operator_preparation");
            record["model_stage"]="operator_publication";
            record["model_operator_release_attempted"]=true;publish(output,rpc());record["model_operator_publications"]=1;
            var delivered=Command("model_operator_delivered");delivered["text_sha256"]=BridgeHostFiles.Hash(Encoding.UTF8.GetBytes(output));
            var operatorAck=Reply(delivered,"model_operator_ack",rpc(),"confirmed_operator_releases");
            if(!1.Equals(operatorAck["confirmed_operator_releases"]))throw new StartupFailure("model_operator_ack");
            record["model_stage"]="worker_shutdown";
            var complete=Reply(Command("model_shutdown"),"model_worker_complete",rpc(),"effects");
            var effects=complete["effects"] as Dictionary<string,object>;
            BridgeRuntime.Shape(effects,"dispatches","confirmed_runtime_releases","confirmed_operator_releases","real_inference");
            if(!1.Equals(effects["dispatches"]) || !1.Equals(effects["confirmed_runtime_releases"]) ||
                !1.Equals(effects["confirmed_operator_releases"]) || !false.Equals(effects["real_inference"]))throw new StartupFailure("model_final_effects");
            record["model_stage"]="process_exit";
            child.CloseBridgeInput();worker.CloseBridgeInput();childChannel.Eof(left());workerChannel.Eof(rpc());
            child.WaitBridge((uint)left());worker.WaitBridge((uint)rpc());ModelHostFiles.Recheck(directory,user);
            record["model_stage"]="audit_readback";
            byte[] audit=ModelHostFiles.ReadBounded(Path.Combine(directory,"host","audit.jsonl"),131072);
            record["model_audit_events_verified"]=ModelAuditAdmission.Verify(audit,attempt,"windows:"+user.Value,requestId,
                BridgeHostFiles.Hash(expectedRequest),expectedRequest.Length,BridgeHostFiles.Hash(responseBytes),responseBytes.Length,
                BridgeHostFiles.Hash(Encoding.UTF8.GetBytes(output)),(string)runtime["request_id"],(string)delivered["request_id"]);
            record["model_audit_sha256"]=BridgeHostFiles.Hash(audit);record["model_worker_exit_hex"]="0x00000000";
            record["model_evidence_matches"]=true;record["real_inference"]=false;record["model_stage"]="complete";return child.ExitCode.Value;
        }
        internal void Stop()
        {
            worker.CloseBridgeInput();worker.Stop();if(workerChannel!=null)workerChannel.Dispose();if(childChannel!=null)childChannel.Dispose();
            stopped=true;record["model_worker_stopped"]=true;ModelHostFiles.Recheck(directory,user);
        }
        public void Dispose(){worker.Dispose();if(!stopped)record["model_worker_cleanup_uncertain"]=true;}
    }
}
