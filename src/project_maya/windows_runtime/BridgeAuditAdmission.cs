using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace ProjectMaya.WindowsRuntime
{
    internal static class BridgeAuditAdmission
    {
        internal static int Verify(byte[] raw, string attempt, string actor, string documentHash, List<string> requests)
        {
            if (raw.Length < 1 || raw.Length > 131072 || requests.Count != 10) throw new StartupFailure("bridge_audit_size");
            string text = new UTF8Encoding(false,true).GetString(raw);
            if (!text.EndsWith("\n",StringComparison.Ordinal)) throw new StartupFailure("bridge_audit_partial");
            string[] lines = text.Split('\n'); int position = 0; var uniqueRequests = new HashSet<string>();
            for (int i=0;i<BridgeRuntime.Cases.Length;i++)
            {
                string current = BridgeRuntime.Cases[i];
                string[] events = current=="N01" ? new[] {"read_intent","release_intent","delivery_observed"} :
                    current=="N02" ? new[] {"delivery_observed"} : current=="N10" ?
                    new[] {"read_intent","denied","delivery_observed"} : new[] {"denied","delivery_observed"};
                string leaseRequest = null;
                foreach (string stage in events)
                {
                    if (position >= lines.Length-1) throw new StartupFailure("bridge_audit_missing");
                    var item = StrictJson.Parse(Encoding.UTF8.GetBytes(lines[position++].TrimEnd('\r')));
                    BridgeRuntime.Shape(item,"schema_version","timestamp","event_type","decision","reason_code","actor_id",
                        "capability","target","operation","data_classification","idempotency_key","metadata");
                    var metadata = item["metadata"] as Dictionary<string,object>;
                    if (metadata==null || !metadata.ContainsKey("attempt") || !attempt.Equals(metadata["attempt"]) ||
                        !metadata.ContainsKey("request_id") || !(metadata["request_id"] is string) ||
                        !System.Text.RegularExpressions.Regex.IsMatch((string)metadata["request_id"],"\\A[0-9a-f]{32}\\z"))
                        throw new StartupFailure("bridge_audit_identity");
                    if (leaseRequest==null) leaseRequest=(string)metadata["request_id"];
                    DateTimeOffset timestamp;
                    if (!leaseRequest.Equals(metadata["request_id"]) || !1.Equals(item["schema_version"]) ||
                        !actor.Equals(item["actor_id"]) || !"internal-synthetic".Equals(item["data_classification"]) ||
                        !((string)item["event_type"]).Equals("bridge."+stage) || item["idempotency_key"]!=null ||
                        !(item["timestamp"] is string) || !DateTimeOffset.TryParseExact((string)item["timestamp"],
                        new[] {"yyyy-MM-dd'T'HH:mm:sszzz","yyyy-MM-dd'T'HH:mm:ss'Z'"}, System.Globalization.CultureInfo.InvariantCulture,
                        System.Globalization.DateTimeStyles.AssumeUniversal, out timestamp) || timestamp.Offset != TimeSpan.Zero)
                        throw new StartupFailure("bridge_audit_binding");
                    bool disclose = stage=="release_intent" || stage=="delivery_observed" || stage=="denied" && current=="N10";
                    string target = disclose ? "runtime:"+attempt : "maya.synthetic.document.v1";
                    string operation = disclose ? "release" : "read";
                    bool denied = stage=="denied" || stage=="delivery_observed" && current!="N01";
                    string reason = stage=="delivery_observed" ? current=="N01" ? "bridge.sent" : "bridge.withheld" : "bridge."+stage;
                    if (!(disclose?"file.disclose":"file.read").Equals(item["capability"]) ||
                        !target.Equals(item["target"]) || !operation.Equals(item["operation"]) ||
                        !(denied?"deny":"allow").Equals(item["decision"]) || !reason.Equals(item["reason_code"]))
                        throw new StartupFailure("bridge_audit_decision");
                    if (stage=="delivery_observed")
                    {
                        BridgeRuntime.Shape(metadata,"attempt","request_id","coordinator_request_id");
                        if (!requests[i].Equals(metadata["coordinator_request_id"])) throw new StartupFailure("bridge_audit_request");
                    }
                    else if (stage=="denied") BridgeRuntime.Shape(metadata,"attempt","request_id");
                    else
                    {
                        BridgeRuntime.Shape(metadata,"attempt","request_id","seq","response_sha256","document_resource");
                        int sequence;
                        if (!(metadata["seq"] is string) || !int.TryParse((string)metadata["seq"],out sequence) || sequence<1 || sequence>16 ||
                            !"maya.synthetic.document.v1".Equals(metadata["document_resource"]) ||
                            !(stage=="release_intent"?documentHash:"").Equals(metadata["response_sha256"])) throw new StartupFailure("bridge_audit_content");
                    }
                }
                if (!uniqueRequests.Add(leaseRequest)) throw new StartupFailure("bridge_audit_replayed_identity");
            }
            if (position != lines.Length-1) throw new StartupFailure("bridge_audit_extra");
            return position;
        }
    }
}
