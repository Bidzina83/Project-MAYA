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
        bool startupFailed;

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
            try
            {
            record["model_stage"]="worker_start";
            worker.StartModelWorker(directory,attempt,user);
            record["model_worker_pid"]=worker.ChildPid;record["model_worker_token_verified"]=worker.ReducedLaunchTokenVerified;
            workerChannel=new BridgeChannel(worker.BridgeOutput,worker.BridgeInput);worker.ResumeBridge();
            record["model_stage"]="worker_ready_wait";
            var ready=workerChannel.Read(5000);
            record["model_stage"]="worker_ready_validate";
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
            catch
            {
                startupFailed=true;
                RecordWorkerSnapshot("model_worker_before_cleanup","before_job_stop");
                throw;
            }
        }
        void RecordWorkerSnapshot(string key,string phase)
        {
            if(!ModelValidationAdmission.Enabled)return;
            try
            {
                var snapshot=worker.SnapshotBridgeStartup();snapshot["observation_phase"]=phase;
                snapshot["channel_failure_category"]=workerChannel==null?null:workerChannel.FailureCategory;
                snapshot["channel_read_progress"]=workerChannel==null?null:workerChannel.SnapshotReadProgress();
                record[key]=snapshot;
            }
            catch {record[key]=new Dictionary<string,object>{{"observation_phase",phase},{"diagnostic_state","snapshot_unavailable"}};}
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
            var issue=Command("model_issue");
            var issued=Reply(issue,"model_grant_reply",rpc(),"grant");
            Dictionary<string,object> revokeExpected=null;string revokeId=null,revokeAge=null;
            Dictionary<string,object> savedReplayRequest=null;string replayLease=null;
            if(ModelExpiryAdmission.Enabled || ModelRevocationAdmission.Enabled || ModelReplayAdmission.Enabled || ModelBudgetAdmission.Enabled || ModelRecreateAdmission.Enabled || ModelOutputDenialAdmission.Enabled || ModelMalformedAdmission.Enabled || ModelOversizedAdmission.Enabled || ModelAllowlistAdmission.Enabled)
            {
                var grant=issued["grant"] as Dictionary<string,object>;
                BridgeRuntime.Shape(grant,"v","type","attempt","route","lease","seq","ttl_ms","request_sha256");Identity(grant,"model_grant");
                if(!1.Equals(grant["seq"]) || !2000.Equals(grant["ttl_ms"]) || !"maya.offline.model.v1".Equals(grant["route"]) ||
                    !BridgeHostFiles.Hash(expectedRequest).Equals(grant["request_sha256"]) || !(grant["lease"] is string) ||
                    !System.Text.RegularExpressions.Regex.IsMatch((string)grant["lease"],"\\A[0-9a-f]{64}\\z"))throw new StartupFailure(ModelRecreateAdmission.Enabled?"recreate_grant_binding":ModelBudgetAdmission.Enabled?"budget_grant_binding":ModelReplayAdmission.Enabled?"replay_grant_binding":ModelRevocationAdmission.Enabled?"revoke_grant_binding":"expiry_grant_binding");
                if(ModelExpiryAdmission.Enabled)
                {
                record["model_stage"]="expiry_wait_before_begin";
                record["model_coordinator_wait_ms"]=ModelExpiryAdmission.WaitBeforeBegin(
                    ()=>Math.Min(left(),22000-checked((int)watch.ElapsedMilliseconds)));
                record["model_expiry_wait_outside_RPC"]=true;
                }
                else if(ModelRevocationAdmission.Enabled)
                {
                    record["model_stage"]="revoke_before_begin";
                    var revoke=Command("model_revoke");revoke["lease"]=grant["lease"];revokeId=(string)revoke["request_id"];
                    if(revokeId.Equals(issue["request_id"]))throw new StartupFailure("revoke_command_collision");
                    var ack=Reply(revoke,"model_revoke_ack",rpc(),"evidence");
                    var evidence=ack["evidence"] as Dictionary<string,object>;
                    revokeAge=ModelRevocationAdmission.Age(evidence,"worker_elapsed_ms");
                    revokeExpected=ModelRevocationAdmission.Metadata(attempt,requestId,revokeId,"",(string)grant["lease"],
                        expectedRequest,BridgeHostFiles.Hash(Encoding.UTF8.GetBytes(output)),revokeAge,revokeAge);
                    ModelValidationAdmission.Evidence(evidence,revokeExpected);
                    record["model_revoke_command_id"]=revokeId;record["model_revoke_elapsed_ms"]=revokeAge;
                    record["model_revoke_ack_verified"]=true;
                }
            }
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
            if(ModelReplayAdmission.Enabled || ModelBudgetAdmission.Enabled || ModelRecreateAdmission.Enabled)
            {
                replayLease=(string)((Dictionary<string,object>)issued["grant"])["lease"];
                ModelBodyAdmission.Envelope(request,attempt,replayLease,expectedRequest);
                savedReplayRequest=new Dictionary<string,object>(request);
                record["model_native_body_verified"]=true;record["model_native_envelope_verified"]=true;
            }
            var dispatch=Command("model_dispatch");dispatch["request"]=request;
            if(ModelOutputDenialAdmission.Enabled)
            {
                string lease=(string)((Dictionary<string,object>)issued["grant"])["lease"];
                ModelBodyAdmission.Envelope(request,attempt,lease,expectedRequest);
                record["model_native_body_verified"]=true;record["model_native_envelope_verified"]=true;
            }
            if(ModelRevocationAdmission.Enabled)
            {
                if(dispatch["request_id"].Equals(issue["request_id"]) || dispatch["request_id"].Equals(revokeId))
                    throw new StartupFailure("revoke_dispatch_collision");
                return RunRevocation(child,dispatch,request,(string)((Dictionary<string,object>)issued["grant"])["lease"],
                    revokeId,revokeAge,revokeExpected,rpc,left);
            }
            if(ModelExpiryAdmission.Enabled)
                return RunExpiry(child,dispatch,request,(string)((Dictionary<string,object>)issued["grant"])["lease"],rpc,left);
            if(ModelRouteAdmission.Enabled || ModelAttemptAdmission.Enabled || ModelBodyAdmission.Enabled)
            {
                var grant=issued["grant"] as Dictionary<string,object>;
                BridgeRuntime.Shape(grant,"v","type","attempt","route","lease","seq","ttl_ms","request_sha256");
                Identity(grant,"model_grant");
                if(!1.Equals(grant["seq"]) || !2000.Equals(grant["ttl_ms"]) || !"maya.offline.model.v1".Equals(grant["route"]) ||
                    !BridgeHostFiles.Hash(expectedRequest).Equals(grant["request_sha256"]) || !(grant["lease"] is string))
                    throw new StartupFailure("route_host_grant");
                return RunValidation(child,dispatch,request,rpc,left,(string)grant["lease"]);
            }
            if(ModelValidationAdmission.Enabled && !ModelReplayAdmission.Enabled && !ModelBudgetAdmission.Enabled && !ModelRecreateAdmission.Enabled && !ModelOutputDenialAdmission.Enabled && !ModelMalformedAdmission.Enabled && !ModelOversizedAdmission.Enabled && !ModelAllowlistAdmission.Enabled && !ModelFinalAdmission.Enabled)return RunValidation(child,dispatch,request,rpc,left);
            if(ModelAllowlistAdmission.Enabled)return RunAllowlist(child,dispatch,rpc,left);
            if(ModelOversizedAdmission.Enabled)return RunOversized(child,dispatch,rpc,left);
            if(ModelMalformedAdmission.Enabled)return RunMalformed(child,dispatch,rpc,left);
            if(ModelOutputDenialAdmission.Enabled)return RunOutputDenial(child,dispatch,rpc,left);
            if(ModelDenialAdmission.Enabled)return RunDenial(child,dispatch,rpc,left);
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
            var runtimeAck=Reply(runtime,"model_runtime_ack",rpc(),ModelReplayAdmission.Enabled ?
                new[]{"confirmed_runtime_releases","delivery_elapsed_ms"}:new[]{"confirmed_runtime_releases"});
            if(!1.Equals(runtimeAck["confirmed_runtime_releases"]))throw new StartupFailure("model_runtime_ack");
            if(ModelReplayAdmission.Enabled)
                return RunReplay(child,savedReplayRequest,replayLease,(string)issue["request_id"],(string)dispatch["request_id"],
                    (string)runtime["request_id"],runtimeAck,responseBytes,rpc,left);
            if(ModelBudgetAdmission.Enabled || ModelRecreateAdmission.Enabled)
                return RunBudget(child,(string)issue["request_id"],(string)dispatch["request_id"],(string)runtime["request_id"],responseBytes,rpc,left);
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
            if(ModelFinalAdmission.Enabled)return RunFinalText(child,(string)runtime["request_id"],(string)final["text"],rpc,left);
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
        uint RunFinalText(WindowsIsolation child,string deliveryId,string nativeText,Func<int> rpc,Func<int> left)
        {
            record["model_stage"]="fixed_final_text_derivation";
            record["model_request_validated"]=true;record["model_response_validated"]=true;
            record["model_gateway_calls"]=2;record["model_gateway_denied"]=false;
            record["model_dispatch_attempted"]=true;record["model_dispatch_uncertain"]=true;
            record["model_operator_publications"]=0;
            record["model_native_final_verified"]=true;
            var prepare=Command("model_prepare_final");prepare["text"]=ModelFinalAdmission.Mutate(nativeText);
            record["model_final_command_id"]=prepare["request_id"];
            record["model_runtime_delivery_command_id"]=deliveryId;
            var denied=Reply(prepare,"model_final_observed",rpc(),"guard","effects");
            var guard=denied["guard"] as Dictionary<string,object>;
            bool guardAllowed=ModelFinalGuardAdmission.Validate(guard,attempt,deliveryId,(string)prepare["request_id"]);
            record["model_final_guard_diagnostic"]=guard;
            if(!guardAllowed || denied["effects"]==null)
            {
                if(denied["effects"]!=null)throw new StartupFailure("model_final_guard_unexpected_effects");
                record["model_stage"]="final_guard_diagnostic_blocked";
                throw new StartupFailure(guardAllowed?"model_final_evidence_unavailable":"model_final_guard_rejected");
            }
            var effects=denied["effects"] as Dictionary<string,object>;
            ModelFinalAdmission.Effects(effects,expectedRequest,output,deliveryId,(string)prepare["request_id"]);
            record["model_final_validation_stage"]="operator_text";
            foreach(string name in new[]{"original_text_sha256","original_text_bytes","observed_text_sha256","observed_text_bytes",
                "response_sha256","response_bytes","prepared_operator_releases","confirmed_operator_releases"})
                record["model_"+name]=effects[name];
            child.CloseBridgeInput();worker.CloseBridgeInput();childChannel.Eof(left());workerChannel.Eof(rpc());
            child.WaitBridge((uint)left());worker.WaitBridge((uint)rpc());ModelHostFiles.Recheck(directory,user);
            byte[] audit=ModelHostFiles.ReadBounded(Path.Combine(directory,"host","audit.jsonl"),131072);
            byte[] response=ModelOutputDenialAdmission.ExpectedResponse(output);
            record["model_audit_events_verified"]=ModelFinalAuditAdmission.Verify(audit,attempt,"windows:"+user.Value,requestId,
                BridgeHostFiles.Hash(expectedRequest),expectedRequest.Length,BridgeHostFiles.Hash(response),response.Length,
                BridgeHostFiles.Hash(Encoding.UTF8.GetBytes(output)),deliveryId);
            record["model_audit_sha256"]=BridgeHostFiles.Hash(audit);record["model_worker_exit_hex"]="0x00000000";
            record["model_evidence_matches"]=true;record["model_final_text_evidence_matches"]=true;
            record["model_stage"]="expected_final_text_rejection_complete";return child.ExitCode.Value;
        }
        internal void Stop()
        {
            worker.CloseBridgeInput();
            try{worker.Stop();}
            finally{if(startupFailed)RecordWorkerSnapshot("model_worker_after_stop","after_job_stop_attempt_not_natural_exit_evidence");}
            if(workerChannel!=null)workerChannel.Dispose();if(childChannel!=null)childChannel.Dispose();
            stopped=true;record["model_worker_stopped"]=true;ModelHostFiles.Recheck(directory,user);
        }
        uint RunAllowlist(WindowsIsolation child,Dictionary<string,object> dispatch,Func<int> rpc,Func<int> left)
        {
            record["model_stage"]="response_allowlist_rejection";
            var denied=Reply(dispatch,"model_response_allowlist_rejected",rpc(),"effects");
            ModelAllowlistAdmission.Effects(denied["effects"] as Dictionary<string,object>,expectedRequest,output);
            record["model_request_validated"]=true;record["model_response_validated"]=false;
            record["model_gateway_denied"]=false;record["model_gateway_calls"]=1;record["model_dispatch_attempted"]=true;
            record["model_synthetic_dispatches"]=1;record["model_dispatch_uncertain"]=true;
            record["model_runtime_pipe_writes"]=0;record["model_operator_publications"]=0;
            byte[] expectedResponse=ModelOutputDenialAdmission.ExpectedResponse(output);
            record["model_expected_response_sha256"]=BridgeHostFiles.Hash(expectedResponse);
            record["model_expected_response_bytes"]=expectedResponse.Length;
            var effects=denied["effects"] as Dictionary<string,object>;
            record["model_response_validation_stage"]="response_allowlist";
            record["model_observed_response_sha256"]=effects["observed_response_sha256"];
            record["model_observed_response_bytes"]=effects["observed_response_bytes"];
            record["model_validated_response_sha256"]="";record["model_validated_response_bytes"]=0;
            var control=Message("model_denied");control["seq"]=1;control["case"]="M07c";control["reason"]="response_allowlist_rejected";
            record["model_denial_control_release_attempted"]=true;
            childChannel.Write(control,rpc());record["model_denial_control_pipe_writes"]=1;
            var final=childChannel.Read(left());BridgeRuntime.Shape(final,"v","type","attempt","report");Identity(final,"model_child_denied");
            var report=final["report"] as Dictionary<string,object>;ModelAllowlistAdmission.Child(report,attempt);
            record["model_child_report_untrusted"]=report;
            child.CloseBridgeInput();worker.CloseBridgeInput();childChannel.Eof(left());workerChannel.Eof(rpc());
            child.WaitBridge((uint)left());worker.WaitBridge((uint)rpc());ModelHostFiles.Recheck(directory,user);
            byte[] audit=ModelHostFiles.ReadBounded(Path.Combine(directory,"host","audit.jsonl"),131072);
            record["model_audit_events_verified"]=ModelAllowlistAdmission.Audit(audit,"windows:"+user.Value,attempt,requestId,expectedRequest,output);
            record["model_audit_sha256"]=BridgeHostFiles.Hash(audit);record["model_worker_exit_hex"]="0x00000000";
            record["model_evidence_matches"]=true;record["model_allowlist_evidence_matches"]=true;
            record["model_stage"]="expected_response_allowlist_rejection_complete";return child.ExitCode.Value;
        }
        uint RunOversized(WindowsIsolation child,Dictionary<string,object> dispatch,Func<int> rpc,Func<int> left)
        {
            record["model_stage"]="response_size_rejection";
            var denied=Reply(dispatch,"model_response_size_rejected",rpc(),"effects");
            ModelOversizedAdmission.Effects(denied["effects"] as Dictionary<string,object>,expectedRequest,output);
            record["model_request_validated"]=true;record["model_response_validated"]=false;
            record["model_gateway_denied"]=false;record["model_gateway_calls"]=1;record["model_dispatch_attempted"]=true;
            record["model_synthetic_dispatches"]=1;record["model_dispatch_uncertain"]=true;
            record["model_runtime_pipe_writes"]=0;record["model_operator_publications"]=0;
            byte[] expectedResponse=ModelOutputDenialAdmission.ExpectedResponse(output);
            record["model_expected_response_sha256"]=BridgeHostFiles.Hash(expectedResponse);
            record["model_expected_response_bytes"]=expectedResponse.Length;
            var effects=denied["effects"] as Dictionary<string,object>;
            record["model_response_validation_stage"]="response_size";
            record["model_observed_response_sha256"]=effects["observed_response_sha256"];
            record["model_observed_response_bytes"]=effects["observed_response_bytes"];
            record["model_validated_response_sha256"]="";record["model_validated_response_bytes"]=0;
            var control=Message("model_denied");control["seq"]=1;control["case"]="M07b";control["reason"]="response_size_rejected";
            record["model_denial_control_release_attempted"]=true;
            childChannel.Write(control,rpc());record["model_denial_control_pipe_writes"]=1;
            var final=childChannel.Read(left());BridgeRuntime.Shape(final,"v","type","attempt","report");Identity(final,"model_child_denied");
            var report=final["report"] as Dictionary<string,object>;ModelOversizedAdmission.Child(report,attempt);
            record["model_child_report_untrusted"]=report;
            child.CloseBridgeInput();worker.CloseBridgeInput();childChannel.Eof(left());workerChannel.Eof(rpc());
            child.WaitBridge((uint)left());worker.WaitBridge((uint)rpc());ModelHostFiles.Recheck(directory,user);
            byte[] audit=ModelHostFiles.ReadBounded(Path.Combine(directory,"host","audit.jsonl"),131072);
            record["model_audit_events_verified"]=ModelOversizedAdmission.Audit(audit,"windows:"+user.Value,attempt,requestId,expectedRequest,output);
            record["model_audit_sha256"]=BridgeHostFiles.Hash(audit);record["model_worker_exit_hex"]="0x00000000";
            record["model_evidence_matches"]=true;record["model_oversized_evidence_matches"]=true;
            record["model_stage"]="expected_response_size_rejection_complete";return child.ExitCode.Value;
        }
        uint RunMalformed(WindowsIsolation child,Dictionary<string,object> dispatch,Func<int> rpc,Func<int> left)
        {
            record["model_stage"]="response_json_rejection";
            var denied=Reply(dispatch,"model_response_json_rejected",rpc(),"effects");
            ModelMalformedAdmission.Effects(denied["effects"] as Dictionary<string,object>,expectedRequest,output);
            record["model_request_validated"]=true;record["model_response_validated"]=false;
            record["model_gateway_denied"]=false;record["model_gateway_calls"]=1;record["model_dispatch_attempted"]=true;
            record["model_synthetic_dispatches"]=1;record["model_dispatch_uncertain"]=true;
            record["model_runtime_pipe_writes"]=0;record["model_operator_publications"]=0;
            byte[] expectedResponse=ModelOutputDenialAdmission.ExpectedResponse(output);
            record["model_expected_response_sha256"]=BridgeHostFiles.Hash(expectedResponse);
            record["model_expected_response_bytes"]=expectedResponse.Length;
            var effects=denied["effects"] as Dictionary<string,object>;
            record["model_response_validation_stage"]="response_json";
            record["model_observed_response_sha256"]=effects["observed_response_sha256"];
            record["model_observed_response_bytes"]=effects["observed_response_bytes"];
            record["model_validated_response_sha256"]="";record["model_validated_response_bytes"]=0;
            var control=Message("model_denied");control["seq"]=1;control["case"]="M07a";control["reason"]="response_json_rejected";
            record["model_denial_control_release_attempted"]=true;
            childChannel.Write(control,rpc());record["model_denial_control_pipe_writes"]=1;
            var final=childChannel.Read(left());BridgeRuntime.Shape(final,"v","type","attempt","report");Identity(final,"model_child_denied");
            var report=final["report"] as Dictionary<string,object>;ModelMalformedAdmission.Child(report,attempt);
            record["model_child_report_untrusted"]=report;
            child.CloseBridgeInput();worker.CloseBridgeInput();childChannel.Eof(left());workerChannel.Eof(rpc());
            child.WaitBridge((uint)left());worker.WaitBridge((uint)rpc());ModelHostFiles.Recheck(directory,user);
            byte[] audit=ModelHostFiles.ReadBounded(Path.Combine(directory,"host","audit.jsonl"),131072);
            record["model_audit_events_verified"]=ModelMalformedAdmission.Audit(audit,"windows:"+user.Value,attempt,requestId,expectedRequest,output);
            record["model_audit_sha256"]=BridgeHostFiles.Hash(audit);record["model_worker_exit_hex"]="0x00000000";
            record["model_evidence_matches"]=true;record["model_malformed_evidence_matches"]=true;
            record["model_stage"]="expected_response_json_rejection_complete";return child.ExitCode.Value;
        }
        uint RunOutputDenial(WindowsIsolation child,Dictionary<string,object> dispatch,Func<int> rpc,Func<int> left)
        {
            record["model_stage"]="gateway_runtime_output_denial";
            var denied=Reply(dispatch,"model_runtime_output_denied",rpc(),"effects");
            ModelOutputDenialAdmission.Effects(denied["effects"] as Dictionary<string,object>,expectedRequest,output);
            record["model_request_validated"]=true;record["model_response_validated"]=true;
            record["model_gateway_denied"]=true;record["model_gateway_calls"]=2;record["model_dispatch_attempted"]=true;
            record["model_synthetic_dispatches"]=1;record["model_dispatch_uncertain"]=true;
            record["model_runtime_pipe_writes"]=0;record["model_operator_publications"]=0;
            byte[] expectedResponse=ModelOutputDenialAdmission.ExpectedResponse(output);
            record["model_expected_response_sha256"]=BridgeHostFiles.Hash(expectedResponse);
            record["model_expected_response_bytes"]=expectedResponse.Length;
            var control=Message("model_denied");control["seq"]=1;control["case"]="M06";control["reason"]="gateway_runtime_output_denied";
            record["model_denial_control_release_attempted"]=true;
            childChannel.Write(control,rpc());record["model_denial_control_pipe_writes"]=1;
            var final=childChannel.Read(left());BridgeRuntime.Shape(final,"v","type","attempt","report");Identity(final,"model_child_denied");
            var report=final["report"] as Dictionary<string,object>;ModelOutputDenialAdmission.Child(report,attempt);
            record["model_child_report_untrusted"]=report;
            child.CloseBridgeInput();worker.CloseBridgeInput();childChannel.Eof(left());workerChannel.Eof(rpc());
            child.WaitBridge((uint)left());worker.WaitBridge((uint)rpc());ModelHostFiles.Recheck(directory,user);
            byte[] audit=ModelHostFiles.ReadBounded(Path.Combine(directory,"host","audit.jsonl"),131072);
            record["model_audit_events_verified"]=ModelOutputDenialAdmission.Audit(audit,"windows:"+user.Value,attempt,requestId,expectedRequest,output);
            record["model_audit_sha256"]=BridgeHostFiles.Hash(audit);record["model_worker_exit_hex"]="0x00000000";
            record["model_evidence_matches"]=true;record["model_output_denial_evidence_matches"]=true;
            record["model_stage"]="expected_runtime_output_denial_complete";return child.ExitCode.Value;
        }
        uint RunDenial(WindowsIsolation child,Dictionary<string,object> dispatch,Func<int> rpc,Func<int> left)
        {
            record["model_stage"]="gateway_egress_denial";
            var denied=Reply(dispatch,"model_egress_denied",rpc(),"effects");
            ModelDenialAdmission.Effects(denied["effects"] as Dictionary<string,object>);
            record["model_gateway_denied"]=true;record["model_request_validated"]=true;
            record["model_synthetic_dispatches"]=0;record["model_runtime_pipe_writes"]=0;
            record["model_operator_publications"]=0;
            var control=Message("model_denied");control["seq"]=1;control["case"]="M02";control["reason"]="gateway_egress_denied";
            childChannel.Write(control,rpc());
            var final=childChannel.Read(left());BridgeRuntime.Shape(final,"v","type","attempt","report");Identity(final,"model_child_denied");
            var report=final["report"] as Dictionary<string,object>;ModelDenialAdmission.Child(report,attempt);
            record["model_child_report_untrusted"]=report;
            record["model_stage"]="denial_process_exit";
            child.CloseBridgeInput();worker.CloseBridgeInput();childChannel.Eof(left());workerChannel.Eof(rpc());
            child.WaitBridge((uint)left());worker.WaitBridge((uint)rpc());ModelHostFiles.Recheck(directory,user);
            record["model_stage"]="denial_audit_readback";
            byte[] audit=ModelHostFiles.ReadBounded(Path.Combine(directory,"host","audit.jsonl"),131072);
            record["model_audit_events_verified"]=ModelDenialAdmission.Audit(audit,attempt,"windows:"+user.Value,requestId,
                BridgeHostFiles.Hash(expectedRequest),expectedRequest.Length,BridgeHostFiles.Hash(Encoding.UTF8.GetBytes(output)));
            record["model_audit_sha256"]=BridgeHostFiles.Hash(audit);record["model_worker_exit_hex"]="0x00000000";
            record["model_evidence_matches"]=true;record["model_denial_evidence_matches"]=true;
            record["model_stage"]="expected_denial_complete";return child.ExitCode.Value;
        }
        uint RunValidation(WindowsIsolation child,Dictionary<string,object> dispatch,Dictionary<string,object> nativeRequest,Func<int> rpc,Func<int> left,string lease=null)
        {
            bool route=ModelRouteAdmission.Enabled,wrongAttempt=ModelAttemptAdmission.Enabled,wrongBody=ModelBodyAdmission.Enabled;
            bool envelope=route || wrongAttempt;
            record["model_stage"]=wrongBody?"fixed_wrong_body_derivation":wrongAttempt?"fixed_wrong_attempt_derivation":route?"fixed_wrong_route_derivation":"fixed_wrong_model_derivation";
            record["model_native_body_verified"]=true;
            if(wrongBody){ModelBodyAdmission.Envelope(nativeRequest,attempt,lease,expectedRequest);record["model_native_envelope_verified"]=true;}
            byte[] mutant=wrongBody?ModelBodyAdmission.Mutate(expectedRequest):envelope?expectedRequest:ModelValidationAdmission.Mutate(expectedRequest);
            var changed=wrongAttempt?ModelAttemptAdmission.Mutate(nativeRequest,attempt,lease,expectedRequest):
                route?ModelRouteAdmission.Mutate(nativeRequest,attempt,lease,expectedRequest):new Dictionary<string,object>(nativeRequest);
            if(!envelope)changed["body"]=Encoding.UTF8.GetString(mutant);dispatch["request"]=changed;
            string outputHash=BridgeHostFiles.Hash(Encoding.UTF8.GetBytes(output));
            var expected=wrongBody?ModelBodyAdmission.Metadata(attempt,requestId,(string)dispatch["request_id"],expectedRequest,outputHash):
                wrongAttempt?ModelAttemptAdmission.Metadata(attempt,requestId,(string)dispatch["request_id"],lease,expectedRequest,outputHash):
                route?ModelRouteAdmission.Metadata(attempt,requestId,(string)dispatch["request_id"],lease,expectedRequest,outputHash):
                ModelValidationAdmission.Metadata(attempt,requestId,(string)dispatch["request_id"],expectedRequest,outputHash);
            if(envelope)
            {
                record["model_native_envelope_verified"]=true;
                foreach(string key in new[]{"original_projection_sha256","original_projection_bytes","mutated_projection_sha256","mutated_projection_bytes","projection_schema",wrongAttempt?"observed_attempt":"observed_route"})
                    record["model_"+key]=expected[key];
            }
            record["model_mutated_request_sha256"]=BridgeHostFiles.Hash(mutant);record["model_mutated_request_bytes"]=mutant.Length;
            record["model_validation_command_id"]=dispatch["request_id"];record["model_stage"]=wrongBody?"worker_body_validation":wrongAttempt?"worker_attempt_validation":route?"worker_route_validation":"worker_model_validation";
            var reply=Reply(dispatch,wrongBody?"model_body_rejected":wrongAttempt?"model_attempt_rejected":route?"model_route_rejected":"model_validation_rejected",rpc(),"evidence");
            ModelValidationAdmission.Evidence(reply["evidence"] as Dictionary<string,object>,expected);
            record["model_validation_stage"]=wrongBody?"request_body":wrongAttempt?"request_attempt":route?"request_route":"request_model";record["model_gateway_calls"]=0;
            record["model_synthetic_dispatches"]=0;record["model_runtime_pipe_writes"]=0;record["model_operator_publications"]=0;
            var control=Message("model_denied");control["seq"]=1;control["case"]=wrongBody?"M03d":wrongAttempt?"M03c":route?"M03b":"M03a";
            control["reason"]=wrongBody?"request_body_rejected":wrongAttempt?"request_attempt_rejected":route?"request_route_rejected":"request_model_rejected";
            record["model_stage"]="validation_child_close";
            childChannel.Write(control,rpc());
            var final=childChannel.Read(left());BridgeRuntime.Shape(final,"v","type","attempt","report");Identity(final,"model_child_denied");
            var report=final["report"] as Dictionary<string,object>;
            ModelDenialAdmission.Child(report,attempt,wrongBody?"maya.offline.model.body_validation.child.v1":wrongAttempt?"maya.offline.model.attempt_validation.child.v1":route?"maya.offline.model.route_validation.child.v1":"maya.offline.model.validation.child.v1");record["model_child_report_untrusted"]=report;
            record["model_stage"]="validation_process_exit";
            child.CloseBridgeInput();worker.CloseBridgeInput();childChannel.Eof(left());workerChannel.Eof(rpc());
            child.WaitBridge((uint)left());worker.WaitBridge((uint)rpc());ModelHostFiles.Recheck(directory,user);
            record["model_stage"]="validation_audit_readback";
            byte[] audit=ModelHostFiles.ReadBounded(Path.Combine(directory,"host","audit.jsonl"),131072);
            record["model_audit_events_verified"]=ModelValidationAdmission.Audit(audit,"windows:"+user.Value,expected,route,wrongAttempt,wrongBody);
            record["model_audit_sha256"]=BridgeHostFiles.Hash(audit);record["model_worker_exit_hex"]="0x00000000";
            record["model_evidence_matches"]=true;record["model_validation_evidence_matches"]=true;
            if(route)record["model_route_evidence_matches"]=true;
            if(wrongAttempt)record["model_attempt_evidence_matches"]=true;
            if(wrongBody)record["model_body_evidence_matches"]=true;
            record["model_stage"]="expected_validation_rejection_complete";return child.ExitCode.Value;
        }
        uint RunExpiry(WindowsIsolation child,Dictionary<string,object> dispatch,Dictionary<string,object> nativeRequest,string lease,Func<int> rpc,Func<int> left)
        {
            ModelBodyAdmission.Envelope(nativeRequest,attempt,lease,expectedRequest);
            record["model_native_body_verified"]=true;record["model_native_envelope_verified"]=true;
            record["model_stage"]="worker_lease_expiry";
            var reply=Reply(dispatch,"model_lease_expired",rpc(),"evidence");
            var evidence=reply["evidence"] as Dictionary<string,object>;
            string age=ModelExpiryAdmission.Elapsed(evidence);
            var expected=ModelExpiryAdmission.Metadata(attempt,requestId,(string)dispatch["request_id"],lease,expectedRequest,
                BridgeHostFiles.Hash(Encoding.UTF8.GetBytes(output)),age);
            ModelValidationAdmission.Evidence(evidence,expected);
            record["model_worker_elapsed_ms"]=age;record["model_validation_command_id"]=dispatch["request_id"];
            record["model_validation_stage"]="lease_expired";record["model_gateway_calls"]=0;
            record["model_synthetic_dispatches"]=0;record["model_runtime_pipe_writes"]=0;record["model_operator_publications"]=0;
            var control=Message("model_denied");control["seq"]=1;control["case"]="M04a";control["reason"]="lease_expired";
            childChannel.Write(control,rpc());record["model_stage"]="expiry_child_close";
            var final=childChannel.Read(left());BridgeRuntime.Shape(final,"v","type","attempt","report");Identity(final,"model_child_denied");
            var report=final["report"] as Dictionary<string,object>;
            ModelDenialAdmission.Child(report,attempt,"maya.offline.model.expiry.child.v1");record["model_child_report_untrusted"]=report;
            record["model_stage"]="expiry_process_exit";
            child.CloseBridgeInput();worker.CloseBridgeInput();childChannel.Eof(left());workerChannel.Eof(rpc());
            child.WaitBridge((uint)left());worker.WaitBridge((uint)rpc());ModelHostFiles.Recheck(directory,user);
            byte[] audit=ModelHostFiles.ReadBounded(Path.Combine(directory,"host","audit.jsonl"),131072);
            record["model_audit_events_verified"]=ModelValidationAdmission.Audit(audit,"windows:"+user.Value,expected,false,false,false,true);
            record["model_audit_sha256"]=BridgeHostFiles.Hash(audit);record["model_worker_exit_hex"]="0x00000000";
            record["model_evidence_matches"]=true;record["model_expiry_evidence_matches"]=true;
            record["model_stage"]="expected_lease_expiry_complete";return child.ExitCode.Value;
        }
        uint RunRevocation(WindowsIsolation child,Dictionary<string,object> dispatch,Dictionary<string,object> nativeRequest,
            string lease,string revokeId,string revokeAge,Dictionary<string,object> first,Func<int> rpc,Func<int> left)
        {
            ModelBodyAdmission.Envelope(nativeRequest,attempt,lease,expectedRequest);
            record["model_native_body_verified"]=true;record["model_native_envelope_verified"]=true;
            record["model_stage"]="worker_lease_revocation";
            var reply=Reply(dispatch,"model_lease_revoked",rpc(),"evidence");
            var evidence=reply["evidence"] as Dictionary<string,object>;
            string age=ModelRevocationAdmission.Age(evidence,"worker_elapsed_ms");
            var expected=ModelRevocationAdmission.Metadata(attempt,requestId,revokeId,(string)dispatch["request_id"],lease,
                expectedRequest,BridgeHostFiles.Hash(Encoding.UTF8.GetBytes(output)),revokeAge,age);
            ModelValidationAdmission.Evidence(evidence,expected);
            record["model_worker_elapsed_ms"]=age;record["model_validation_command_id"]=dispatch["request_id"];
            record["model_validation_stage"]="lease_revoked";record["model_gateway_calls"]=0;
            record["model_synthetic_dispatches"]=0;record["model_runtime_pipe_writes"]=0;record["model_operator_publications"]=0;
            var control=Message("model_denied");control["seq"]=1;control["case"]="M04b";control["reason"]="lease_revoked";
            childChannel.Write(control,rpc());record["model_stage"]="revocation_child_close";
            var final=childChannel.Read(left());BridgeRuntime.Shape(final,"v","type","attempt","report");Identity(final,"model_child_denied");
            var report=final["report"] as Dictionary<string,object>;
            ModelDenialAdmission.Child(report,attempt,"maya.offline.model.revocation.child.v1");record["model_child_report_untrusted"]=report;
            record["model_stage"]="revocation_process_exit";
            child.CloseBridgeInput();worker.CloseBridgeInput();childChannel.Eof(left());workerChannel.Eof(rpc());
            child.WaitBridge((uint)left());worker.WaitBridge((uint)rpc());ModelHostFiles.Recheck(directory,user);
            byte[] audit=ModelHostFiles.ReadBounded(Path.Combine(directory,"host","audit.jsonl"),131072);
            record["model_audit_events_verified"]=ModelRevocationAdmission.Audit(audit,"windows:"+user.Value,first,expected);
            record["model_audit_sha256"]=BridgeHostFiles.Hash(audit);record["model_worker_exit_hex"]="0x00000000";
            record["model_evidence_matches"]=true;record["model_revocation_evidence_matches"]=true;
            record["model_stage"]="expected_lease_revocation_complete";return child.ExitCode.Value;
        }
        uint RunReplay(WindowsIsolation child,Dictionary<string,object> saved,string lease,string issueId,string firstId,
            string deliveryId,Dictionary<string,object> ack,byte[] response,Func<int> rpc,Func<int> left)
        {
            string deliveryAge=ModelReplayAdmission.Age(ack,"delivery_elapsed_ms");
            ModelBodyAdmission.Envelope(saved,attempt,lease,expectedRequest);
            var replay=Command("model_dispatch");replay["request"]=new Dictionary<string,object>(saved);
            string replayId=(string)replay["request_id"];
            if(new HashSet<string>{issueId,firstId,deliveryId,replayId}.Count!=4)throw new StartupFailure("replay_command_collision");
            record["model_stage"]="worker_consumed_replay";
            var reply=Reply(replay,"model_lease_consumed",rpc(),"evidence");
            var evidence=reply["evidence"] as Dictionary<string,object>;
            string age=ModelReplayAdmission.Age(evidence,"worker_elapsed_ms");
            var expected=ModelReplayAdmission.Metadata(attempt,requestId,firstId,deliveryId,replayId,lease,expectedRequest,response,
                BridgeHostFiles.Hash(Encoding.UTF8.GetBytes(output)),deliveryAge,age);
            ModelValidationAdmission.Evidence(evidence,expected);
            record["model_first_dispatch_command_id"]=firstId;record["model_runtime_delivery_command_id"]=deliveryId;
            record["model_validation_command_id"]=replayId;record["model_validation_stage"]="lease_consumed";
            record["model_delivery_elapsed_ms"]=deliveryAge;record["model_worker_elapsed_ms"]=age;
            record["model_gateway_calls"]=2;record["model_replay_gateway_calls"]=0;record["model_replay_dispatches"]=0;
            record["model_replay_runtime_pipe_writes"]=0;record["model_operator_publications"]=0;
            record["model_stage"]="replay_positive_child_close";
            var final=childChannel.Read(left());BridgeRuntime.Shape(final,"v","type","attempt","text","report");Identity(final,"model_child_complete");
            if(!output.Equals(final["text"]))throw new StartupFailure("replay_final_mismatch");
            var report=final["report"] as Dictionary<string,object>;ModelReplayAdmission.Child(report,attempt);
            record["model_child_report_untrusted"]=report;
            child.CloseBridgeInput();worker.CloseBridgeInput();childChannel.Eof(left());workerChannel.Eof(rpc());
            child.WaitBridge((uint)left());worker.WaitBridge((uint)rpc());ModelHostFiles.Recheck(directory,user);
            byte[] audit=ModelHostFiles.ReadBounded(Path.Combine(directory,"host","audit.jsonl"),131072);
            record["model_audit_events_verified"]=ModelReplayAdmission.Audit(audit,"windows:"+user.Value,expected);
            record["model_audit_sha256"]=BridgeHostFiles.Hash(audit);record["model_worker_exit_hex"]="0x00000000";
            record["model_evidence_matches"]=true;record["model_replay_evidence_matches"]=true;
            record["model_stage"]="expected_consumed_replay_complete";return child.ExitCode.Value;
        }
        uint RunBudget(WindowsIsolation child,string issue,string first,string delivery,byte[] response,Func<int> rpc,Func<int> left)
        {
            bool recreate=ModelRecreateAdmission.Enabled;
            if(issue==first || issue==delivery || first==delivery)throw new StartupFailure(recreate?"recreate_command_collision":"budget_command_collision");
            record["model_stage"]=recreate?"recreate_adapter_probe":"adapter_probe";
            var probe=Command("model_adapter_probe");string probeId=(string)probe["request_id"];
            if(probeId==issue || probeId==first || probeId==delivery)throw new StartupFailure(recreate?"recreate_command_collision":"budget_command_collision");
            childChannel.Write(probe,rpc());
            // The only next child frame may be completion, never another model request.
            var final=childChannel.Read(left());BridgeRuntime.Shape(final,"v","type","attempt","text","report");Identity(final,"model_child_complete");
            if(!output.Equals(final["text"]))throw new StartupFailure(recreate?"recreate_final_mismatch":"budget_final_mismatch");
            var report=final["report"] as Dictionary<string,object>;if(recreate)ModelRecreateAdmission.Child(report,attempt,probeId,expectedRequest);
            else ModelBudgetAdmission.Child(report,attempt,probeId,expectedRequest);
            record["model_child_report_untrusted"]=report;
            child.CloseBridgeInput();childChannel.Eof(left());child.WaitBridge((uint)left());
            var finish=Command("model_adapter_finish");string finishId=(string)finish["request_id"];
            if(finishId==issue || finishId==first || finishId==delivery || finishId==probeId)throw new StartupFailure(recreate?"recreate_command_collision":"budget_command_collision");
            finish["delivery_command_id"]=delivery;
            var complete=Reply(finish,"model_adapter_complete",rpc(),"effects");
            if(recreate)ModelRecreateAdmission.Effects(complete["effects"] as Dictionary<string,object>,expectedRequest,response,delivery);
            else ModelBudgetAdmission.Effects(complete["effects"] as Dictionary<string,object>,expectedRequest,response,delivery);
            worker.CloseBridgeInput();workerChannel.Eof(rpc());worker.WaitBridge((uint)rpc());ModelHostFiles.Recheck(directory,user);
            byte[] audit=ModelHostFiles.ReadBounded(Path.Combine(directory,"host","audit.jsonl"),131072);
            if(recreate)
                record["model_audit_events_verified"]=ModelRecreateAdmission.Audit(audit,"windows:"+user.Value,attempt,requestId,expectedRequest,response,output,delivery);
            else
                record["model_audit_events_verified"]=ModelBudgetAdmission.Audit(audit,"windows:"+user.Value,attempt,requestId,expectedRequest,response,output,delivery);
            record["model_audit_sha256"]=BridgeHostFiles.Hash(audit);record["model_worker_exit_hex"]="0x00000000";
            record["model_gateway_calls"]=2;record["model_additional_pipe_requests"]=0;record["model_additional_dispatches"]=0;
            record["model_additional_runtime_writes"]=0;record["model_operator_publications"]=0;
            if(recreate)record["model_additional_gateway_calls"]=0;
            record["model_probe_command_id"]=probeId;record["model_terminal_command_id"]=finishId;
            record["model_evidence_matches"]=true;record[recreate?"model_recreate_evidence_matches":"model_adapter_budget_evidence_matches"]=true;
            record["model_stage"]=recreate?"expected_recreated_client_budget_complete":"expected_adapter_budget_complete";return child.ExitCode.Value;
        }
        public void Dispose(){worker.Dispose();if(!stopped)record["model_worker_cleanup_uncertain"]=true;}
    }
}
