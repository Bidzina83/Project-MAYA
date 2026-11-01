using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;

namespace ProjectMaya.WindowsRuntime
{
    internal static class ModelExpiryAdmission
    {
        internal static bool Enabled { get {
#if HERMES_MODEL_EXPIRY
            return true;
#else
            return false;
#endif
        } }
        internal static long WaitBeforeBegin(Func<int> budget)
        {
            var clock=Stopwatch.StartNew();
            return WaitCore(()=>clock.ElapsedMilliseconds,Thread.Sleep,budget);
        }
        // Pure scheduling core for inert clocks; native entry always uses Stopwatch.
        internal static long WaitCore(Func<long> elapsed,Action<int> sleep,Func<int> budget)
        {
            long previous=-1;
            for(int steps=0;steps<512;steps++)
            {
                long now=elapsed();
                if(now<0 || now<previous || now>30000)throw new StartupFailure("expiry_clock_invalid");
                long remaining=Math.Max(0,2100-now);
                if(budget()<=remaining+2000)throw new StartupFailure("expiry_wait_budget");
                if(now>=2100)return now;
                previous=now;sleep((int)Math.Min(25,remaining));
            }
            throw new StartupFailure("expiry_clock_stalled");
        }
        internal static string Elapsed(Dictionary<string,object> evidence)
        {
            object value;
            if(evidence==null || !evidence.TryGetValue("worker_elapsed_ms",out value) || !(value is string))
                throw new StartupFailure("expiry_elapsed_missing");
            int n;string text=(string)value;
            if(!Regex.IsMatch(text,"\\A[0-9]{4,5}\\z") || !Int32.TryParse(text,NumberStyles.None,CultureInfo.InvariantCulture,out n) ||
                n<2000 || n>30000 || n.ToString(CultureInfo.InvariantCulture)!=text)throw new StartupFailure("expiry_elapsed_bound");
            return text;
        }
        internal static Dictionary<string,object> Metadata(string attempt,string requestId,string commandId,string lease,byte[] body,string outputHash,string elapsed)
        {
            Elapsed(new Dictionary<string,object>{{"worker_elapsed_ms",elapsed}});
            ModelBodyAdmission.Envelope(new Dictionary<string,object>{{"v",1},{"type","model_request"},{"attempt",attempt},
                {"route","maya.offline.model.v1"},{"lease",lease},{"seq",1},{"method","POST"},{"path","/v1/chat/completions"},
                {"body",new UTF8Encoding(false,true).GetString(body)}},attempt,lease,body);
            foreach(string id in new[]{attempt,requestId,commandId})if(id==null || !Regex.IsMatch(id,"\\A[0-9a-f]{32}\\z"))throw new StartupFailure("expiry_ID");
            if(body.Length<1 || body.Length>4096 || outputHash==null || !Regex.IsMatch(outputHash,"\\A[0-9a-f]{64}\\z"))throw new StartupFailure("expiry_body_bound");
            var parsed=StrictJson.Parse(body);BridgeRuntime.Shape(parsed,"messages","model","max_tokens","stream");
            var messages=parsed["messages"] as List<object>;
            if(!"maya-offline-wire-v1".Equals(parsed["model"]) || !32.Equals(parsed["max_tokens"]) || !false.Equals(parsed["stream"]) ||
                messages==null || messages.Count!=2)throw new StartupFailure("expiry_request_shape");
            for(int i=0;i<2;i++)
            {
                var item=messages[i] as Dictionary<string,object>;BridgeRuntime.Shape(item,"role","content");
                if(!(i==0?"system":"user").Equals(item["role"]) || !(item["content"] is string) || ((string)item["content"]).Length==0)
                    throw new StartupFailure("expiry_message_shape");
            }
            string hash=BridgeHostFiles.Hash(body),size=body.Length.ToString(CultureInfo.InvariantCulture);
            return new Dictionary<string,object>{
                {"validation_schema","maya.model.lease_expiry.v1"},{"case","M04a"},{"stage","lease_expired"},
                {"attempt",attempt},{"request_id",requestId},{"coordinator_request_id",commandId},
                {"route","maya.offline.model.v1"},{"endpoint","https://maya-offline-model.invalid/v1/chat/completions"},
                {"model","maya-offline-wire-v1"},{"destination","provider"},{"request_sha256",hash},{"request_bytes",size},
                {"observed_request_sha256",hash},{"observed_request_bytes",size},{"lease_sha256",BridgeHostFiles.Hash(Encoding.ASCII.GetBytes(lease))},
                {"grant_ttl_ms","2000"},{"worker_elapsed_ms",elapsed},{"phase_before","issued"},{"closed_before","false"},
                {"revoked_before","false"},{"expiry_observed","true"},{"request_preflight_verified","true"},
                {"request_validated","false"},{"gateway_calls","0"},{"dispatch_attempted","false"},{"response_sha256",""},
                {"response_bytes","0"},{"output_sha256",outputHash},{"dispatches","0"},{"runtime_prepared","0"},
                {"runtime_released","0"},{"operator_prepared","0"},{"operator_released","0"},{"real_inference","false"}
            };
        }
    }
}
