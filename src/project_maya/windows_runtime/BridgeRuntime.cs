using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Security.Principal;
using System.Text;

namespace ProjectMaya.WindowsRuntime
{
    internal sealed class BridgeRuntime : IDisposable
    {
        internal static readonly string[] Cases = {"N01","N02","N03","N04","N05","N06","N07","N08","N10","N12"};
        readonly string directory, attempt, channelId, documentHash;
        readonly SecurityIdentifier user;
        readonly WindowsIsolation worker;
        BridgeChannel workerChannel, childChannel;
        readonly Dictionary<string, object> record;
        bool stopped;
        internal BridgeRuntime(string directory, string attempt, SecurityIdentifier user, Dictionary<string, object> record)
        {
            this.directory = directory; this.attempt = attempt; this.user = user; this.record = record;
            channelId = BridgeHostFiles.RandomHex(32);
            documentHash = BridgeHostFiles.Prepare(directory, attempt, user, channelId);
            worker = new WindowsIsolation("Maya.BridgeWorker."+attempt);
        }
        internal static void Shape(Dictionary<string, object> data, params string[] keys)
        {
            if (data == null || data.Count != keys.Length) throw new StartupFailure("bridge_shape");
            foreach (string key in keys) if (!data.ContainsKey(key)) throw new StartupFailure("bridge_shape");
        }
        void Identity(Dictionary<string, object> message, string kind)
        {
            if (!message.ContainsKey("v") || !1.Equals(message["v"]) || !message.ContainsKey("type") || !kind.Equals(message["type"]) ||
                !message.ContainsKey("attempt") || !attempt.Equals(message["attempt"])) throw new StartupFailure("bridge_identity");
        }
        Dictionary<string, object> Message(string kind)
        { return new Dictionary<string, object> {{"v",1},{"type",kind},{"attempt",attempt}}; }
        internal void PrepareWorker()
        {
            worker.StartWorker(directory, attempt, user);
            record["bridge_worker_pid"] = worker.ChildPid;
            record["bridge_worker_token_verified"] = worker.ReducedLaunchTokenVerified;
            workerChannel = new BridgeChannel(worker.BridgeOutput, worker.BridgeInput);
            worker.ResumeBridge();
            var ready = workerChannel.Read(5000); Shape(ready,"v","type","attempt","pid"); Identity(ready,"ready");
            if (!checked((int)worker.ChildPid).Equals(ready["pid"])) throw new StartupFailure("bridge_worker_pid_mismatch");
            BridgeHostFiles.Recheck(directory, user);
            record["bridge_worker_ready"] = true;
        }
        internal uint Run(WindowsIsolation child)
        {
            childChannel = new BridgeChannel(child.BridgeOutput, child.BridgeInput);
            var time = Stopwatch.StartNew();
            Func<int> left = delegate { int value = 30000 - checked((int)time.ElapsedMilliseconds); if (value <= 0) throw new StartupFailure("bridge_deadline"); return value; };
            child.ResumeBridge();
            var hello = childChannel.Read(left()); Shape(hello,"v","type","attempt"); Identity(hello,"hello");
            record["bridge_python_entry_observed"] = true;
            var ready = childChannel.Read(left()); Shape(ready,"v","type","attempt","constructor_verified"); Identity(ready,"ready");
            if (!true.Equals(ready["constructor_verified"])) throw new StartupFailure("bridge_constructor");
            var observations = new List<object>(); record["bridge_cases"] = observations;
            var requestIds = new List<string>();
            int releases = 0, reads = 0;
            foreach (string current in Cases)
            {
                string requestId = BridgeHostFiles.RandomHex(16);
                requestIds.Add(requestId);
                var issue = Message("issue"); issue["request_id"] = requestId; issue["case"] = current;
                workerChannel.Write(issue, Math.Min(2000,left()));
                var grantReply = workerChannel.Read(Math.Min(2000,left()));
                Shape(grantReply,"v","type","attempt","request_id","grant"); Identity(grantReply,"grant_reply");
                if (!requestId.Equals(grantReply["request_id"])) throw new StartupFailure("bridge_worker_request_binding");
                var grant = grantReply["grant"] as Dictionary<string,object>;
                Shape(grant,"v","type","attempt","lease","ttl_ms","next_seq","operation","resource"); Identity(grant,"grant");
                if (!2000.Equals(grant["ttl_ms"]) || !(grant["next_seq"] is int) ||
                    !"document.read".Equals(grant["operation"]) || !"maya.synthetic.document.v1".Equals(grant["resource"]))
                    throw new StartupFailure("bridge_grant");
                var control = Message("case"); control["case"] = current; control["grant"] = grant;
                childChannel.Write(control, Math.Min(2000,left()));
                Dictionary<string,object> childDone = null;
                var dispatch = Message(current == "N02" ? "no_request" : "dispatch"); dispatch["request_id"] = requestId;
                if (current == "N02") childDone = childChannel.Read(left());
                else dispatch["request"] = childChannel.Read(left());
                workerChannel.Write(dispatch, Math.Min(2000,left()));
                var reply = workerChannel.Read(Math.Min(2000,left()));
                Shape(reply,"v","type","attempt","request_id","response","effects"); Identity(reply,"dispatch_reply");
                if (!requestId.Equals(reply["request_id"])) throw new StartupFailure("bridge_worker_reply_binding");
                var effects = reply["effects"] as Dictionary<string,object>;
                Shape(effects,"case","opens","reads","prepared_releases","prepared_content_bytes");
                int expectedRead = current == "N01" || current == "N10" ? 1 : 0;
                int expectedRelease = current == "N01" ? 1 : 0;
                if (!current.Equals(effects["case"]) || !expectedRead.Equals(effects["opens"]) || !expectedRead.Equals(effects["reads"]) ||
                    !expectedRelease.Equals(effects["prepared_releases"]) || !(effects["prepared_content_bytes"] is int) ||
                    (expectedRelease == 0 && !0.Equals(effects["prepared_content_bytes"]))) throw new StartupFailure("bridge_effect_mismatch");
                reads += expectedRead;
                record["bridge_document_reads"] = reads;
                if (current != "N02")
                {
                    var response = reply["response"] as Dictionary<string,object>;
                    Shape(response,"v","type","attempt","seq","status","code","data"); Identity(response,"response");
                    if (!grant["next_seq"].Equals(response["seq"])) throw new StartupFailure("bridge_response_sequence");
                    if (expectedRelease == 1)
                    {
                        var content = response["data"] as Dictionary<string,object>; Shape(content,"text");
                        byte[] text = content["text"] is string ? Encoding.UTF8.GetBytes((string)content["text"]) : new byte[0];
                        if (!"ok".Equals(response["status"]) || !"bridge.document_read".Equals(response["code"]) ||
                            text.Length < 1 || text.Length > 1024 || BridgeHostFiles.Hash(text) != documentHash ||
                            !text.Length.Equals(effects["prepared_content_bytes"])) throw new StartupFailure("bridge_content_mismatch");
                        record["bridge_release_attempted"] = true;
                    }
                    else if (!"denied".Equals(response["status"]) || response["data"] != null || !"bridge.denied".Equals(response["code"]))
                        throw new StartupFailure("bridge_denial_mismatch");
                    childChannel.Write(response, Math.Min(2000,left()));
                    releases += expectedRelease;
                    record["bridge_document_releases"] = releases;
                    childDone = childChannel.Read(left());
                }
                else if (reply["response"] != null) throw new StartupFailure("bridge_unexpected_response");
                Shape(childDone,"v","type","attempt","case","passed","digest","bytes"); Identity(childDone,"case_complete");
                if (!current.Equals(childDone["case"]) || !true.Equals(childDone["passed"]) ||
                    !(current == "N01" ? documentHash.Equals(childDone["digest"]) && effects["prepared_content_bytes"].Equals(childDone["bytes"]) :
                    "".Equals(childDone["digest"]) && 0.Equals(childDone["bytes"]))) throw new StartupFailure("bridge_child_case_mismatch");
                var observed = Message("delivery_result"); observed["request_id"] = requestId; observed["case"] = current; observed["delivered"] = current == "N01";
                workerChannel.Write(observed, Math.Min(2000,left()));
                var ack = workerChannel.Read(Math.Min(2000,left())); Shape(ack,"v","type","attempt","request_id"); Identity(ack,"delivery_ack");
                if (!requestId.Equals(ack["request_id"])) throw new StartupFailure("bridge_delivery_ack");
                observations.Add(new Dictionary<string,object> {{"case",current},{"host_effects_match",true},
                    {"child_observation_matches",true},{"reads",expectedRead},{"releases",expectedRelease}});
            }
            var complete = childChannel.Read(left()); Shape(complete,"v","type","attempt","report"); Identity(complete,"child_complete");
            var report = complete["report"] as Dictionary<string,object>;
            Shape(report,"schema","attempt","completed","constructor_verified","sdk_closed","config_unchanged",
                "distributions_verified","origins_verified","zero_model_calls","snapshots","captured_output_bytes","reason_type");
            if (!"maya.authorization_bridge.child.v1".Equals(report["schema"]) || !attempt.Equals(report["attempt"]) ||
                !"".Equals(report["reason_type"]) || !(report["captured_output_bytes"] is int) ||
                (int)report["captured_output_bytes"] < 0 || (int)report["captured_output_bytes"] > 65536 ||
                !(report["snapshots"] is List<object>) || ((List<object>)report["snapshots"]).Count != 0) throw new StartupFailure("bridge_child_report");
            foreach (string flag in new[] {"completed","constructor_verified","sdk_closed","config_unchanged","distributions_verified","origins_verified","zero_model_calls"})
                if (!true.Equals(report[flag])) throw new StartupFailure("bridge_child_predicate");
            record["bridge_child_report_untrusted"] = report;
            workerChannel.Write(Message("shutdown"), Math.Min(2000,left()));
            var ended = workerChannel.Read(Math.Min(2000,left())); Shape(ended,"v","type","attempt","results"); Identity(ended,"worker_complete");
            var results = ended["results"] as List<object>;
            if (results == null || results.Count != Cases.Length) throw new StartupFailure("bridge_worker_final_count");
            child.CloseBridgeInput(); worker.CloseBridgeInput();
            childChannel.Eof(left()); workerChannel.Eof(Math.Min(2000,left()));
            child.WaitBridge((uint)left()); worker.WaitBridge((uint)Math.Min(2000,left()));
            BridgeHostFiles.Recheck(directory,user);
            byte[] audit;
            using(var source = File.OpenRead(Path.Combine(directory,"host","audit.jsonl")))
            using(var copy = new MemoryStream())
            {
                byte[] buffer = new byte[4096]; int count;
                while((count=source.Read(buffer,0,buffer.Length))>0)
                { if(copy.Length+count>131072) throw new StartupFailure("bridge_audit_size"); copy.Write(buffer,0,count); }
                audit=copy.ToArray();
            }
            record["bridge_audit_events_verified"] = BridgeAuditAdmission.Verify(audit,attempt,"windows:"+user.Value,documentHash,requestIds);
            record["bridge_audit_sha256"] = BridgeHostFiles.Hash(audit);
            record["bridge_worker_exit_hex"] = "0x00000000";
            record["bridge_document_reads"] = reads; record["bridge_document_releases"] = releases;
            record["bridge_evidence_matches"] = reads == 2 && releases == 1;
            return child.ExitCode.Value;
        }
        internal void Stop()
        {
            worker.CloseBridgeInput(); worker.Stop();
            if (workerChannel != null) workerChannel.Dispose();
            if (childChannel != null) childChannel.Dispose();
            stopped = true; record["bridge_worker_stopped"] = true;
            BridgeHostFiles.Recheck(directory,user);
        }
        public void Dispose() { worker.Dispose(); if (!stopped) record["bridge_worker_cleanup_uncertain"] = true; }
    }
}
