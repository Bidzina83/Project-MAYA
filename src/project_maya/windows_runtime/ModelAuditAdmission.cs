using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace ProjectMaya.WindowsRuntime
{
    internal static class ModelAuditAdmission
    {
        internal static readonly string[] Stages = {"egress_intent", "dispatch_outcome", "runtime_release_intent",
            "runtime_delivery", "operator_release_intent", "operator_delivery"};
        internal static int Verify(byte[] raw, string attempt, string actor, string serviceRequest,
            string requestHash, int requestBytes, string responseHash, int responseBytes, string outputHash,
            string runtimeConfirmation, string operatorConfirmation)
        {
            foreach (string value in new[] {attempt, serviceRequest, runtimeConfirmation, operatorConfirmation})
                if (value == null || !Regex.IsMatch(value, "\\A[0-9a-f]{32}\\z")) throw new StartupFailure("model_audit_identity");
            foreach (string value in new[] {requestHash, responseHash, outputHash})
                if (value == null || !Regex.IsMatch(value, "\\A[0-9a-f]{64}\\z")) throw new StartupFailure("model_audit_digest");
            if (raw == null || raw.Length < 1 || raw.Length > 131072 || requestBytes < 1 || requestBytes > 4096 ||
                responseBytes < 1 || responseBytes > 4096 || runtimeConfirmation == operatorConfirmation ||
                actor == null || !Regex.IsMatch(actor, "\\Awindows:S-1-5-(?:[0-9]+-)*[0-9]+\\z"))
                throw new StartupFailure("model_audit_bounds");
            string text = new UTF8Encoding(false,true).GetString(raw);
            string[] lines = text.Split('\n');
            if (!text.EndsWith("\n",StringComparison.Ordinal) || lines.Length != Stages.Length+1)
                throw new StartupFailure("model_audit_count");
            DateTimeOffset? previous = null;
            for (int i=0;i<Stages.Length;i++)
            {
                var record = StrictJson.Parse(Encoding.UTF8.GetBytes(lines[i]));
                BridgeRuntime.Shape(record,"schema_version","timestamp","event_type","decision","reason_code","actor_id",
                    "capability","target","operation","data_classification","idempotency_key","metadata");
                string destination = i<2 ? "provider" : i<4 ? "runtime:"+attempt : "operator";
                if (!1.Equals(record["schema_version"]) || !actor.Equals(record["actor_id"]) ||
                    !("model_bridge."+Stages[i]).Equals(record["event_type"]) ||
                    !("model_bridge."+Stages[i]).Equals(record["reason_code"]) || !"allow".Equals(record["decision"]) ||
                    !(i<2?"model.egress":"model.output").Equals(record["capability"]) ||
                    !"model:maya-offline-fixture".Equals(record["target"]) ||
                    !(i<2?"infer":"disclose").Equals(record["operation"]) ||
                    !"internal-synthetic".Equals(record["data_classification"]) || record["idempotency_key"] != null)
                    throw new StartupFailure("model_audit_record");
                DateTimeOffset stamp;
                if (!(record["timestamp"] is string) || !DateTimeOffset.TryParseExact((string)record["timestamp"],
                    new[] {"yyyy-MM-dd'T'HH:mm:sszzz","yyyy-MM-dd'T'HH:mm:ss'Z'"}, CultureInfo.InvariantCulture,
                    DateTimeStyles.AssumeUniversal, out stamp) || stamp.Offset != TimeSpan.Zero ||
                    previous.HasValue && stamp < previous.Value) throw new StartupFailure("model_audit_timestamp");
                previous = stamp;
                var expected = new Dictionary<string, object> {
                    {"attempt",attempt},{"request_id",serviceRequest},{"route","maya.offline.model.v1"},
                    {"endpoint","https://maya-offline-model.invalid/v1/chat/completions"},{"model","maya-offline-wire-v1"},
                    {"destination",destination},{"request_sha256",requestHash},{"response_sha256",i==0?"":responseHash},
                    {"request_bytes",requestBytes.ToString(CultureInfo.InvariantCulture)},
                    {"response_bytes",i==0?"0":responseBytes.ToString(CultureInfo.InvariantCulture)},
                    {"output_sha256",outputHash},{"dispatches",i==0?"0":"1"},{"real_inference","false"}
                };
                if (i==3 || i==5) expected["coordinator_request_id"] = i==3?runtimeConfirmation:operatorConfirmation;
                var metadata = record["metadata"] as Dictionary<string,object>;
                if (metadata == null || metadata.Count != expected.Count) throw new StartupFailure("model_audit_metadata");
                foreach (var item in expected)
                    if (!metadata.ContainsKey(item.Key) || !item.Value.Equals(metadata[item.Key]))
                        throw new StartupFailure("model_audit_binding");
            }
            return Stages.Length;
        }
    }
}
