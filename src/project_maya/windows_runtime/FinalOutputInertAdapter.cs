#if MAYA_FINAL_OUTPUT_INERT_FIXTURE
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Web.Script.Serialization;

namespace ProjectMaya.WindowsRuntime
{
    internal sealed class FinalOutputInertAdapter
    {
        internal const string Destination = "synthetic:fake-operator";
        static readonly UTF8Encoding Utf8 = new UTF8Encoding(false, true);
        static readonly string[] DeliveryStages = {"egress_intent", "dispatch_outcome", "runtime_release_intent", "runtime_delivery"};
        readonly object gate = new object();
        readonly string attempt, channel, actor, service, delivery, finish, requestHash, responseHash, outputHash;
        readonly int requestBytes, responseBytes;
        readonly byte[] expected;
        readonly Func<long> clock;
        readonly Action<byte[]> appendAndFlush;
        readonly Func<byte[]> readJournal;
        readonly long pending, window;
        readonly bool loseAck;
        long last = -1, epoch, permitEpoch, deadline;
        bool allowed, cancelled;
        string consent, state = "awaiting_evidence";
        int effects;

        // Only fixed fixture inputs reach this constructor; no real sink callback exists.
        internal FinalOutputInertAdapter(string attempt, string channel, string actor, string service, string delivery,
            string finish, byte[] request, byte[] response, byte[] output, Func<long> clock, long pendingTicks,
            long releaseTicks, Action<byte[]> appendAndFlush, Func<byte[]> readJournal, bool loseAck = false)
        {
            foreach (string id in new[]{attempt, service, delivery, finish}) Require(Hex(id,32));
            Require(Hex(channel,64) && actor != null && actor.Length<=192 && Regex.IsMatch(actor,"\\Awindows:S-1-5-(?:[0-9]+-)*[0-9]+\\z"));
            Require(new HashSet<string>(new[]{attempt, service, delivery, finish}).Count == 4);
            Require(Bounded(request) && Bounded(response) && Bounded(output) && pendingTicks > 0 && releaseTicks > 0);
            Require(clock != null && appendAndFlush != null && readJournal != null);
            this.attempt=attempt; this.channel=channel; this.actor=actor; this.service=service; this.delivery=delivery; this.finish=finish;
            requestHash=BridgeHostFiles.Hash(request); responseHash=BridgeHostFiles.Hash(response); outputHash=BridgeHostFiles.Hash(output);
            requestBytes=request.Length; responseBytes=response.Length; expected=(byte[])output.Clone();
            this.clock=clock; this.appendAndFlush=appendAndFlush; this.readJournal=readJournal; this.loseAck=loseAck;
            pending=checked(Now()+pendingTicks); window=releaseTicks;
        }

        static bool Bounded(byte[] value) { return value!=null && value.Length>0 && value.Length<=4096; }
        static bool Hex(string value,int count) { return value!=null && value.Length==count && Regex.IsMatch(value,"\\A[0-9a-f]+\\z"); }
        static void Require(bool ok) { if(!ok) throw new StartupFailure("inert_output_evidence"); }
        static void Exact(Dictionary<string,object> actual, Dictionary<string,object> expected)
        {
            Require(actual!=null && actual.Count==expected.Count);
            foreach(var pair in expected)
                Require(actual.ContainsKey(pair.Key) && object.Equals(actual[pair.Key],pair.Value));
        }
        long Now() { long value=clock(); Require(value>=0 && value>=last); last=value; return value; }
        internal int FakeEffects { get { lock(gate) return effects; } }
        internal void SetPolicy(bool allow) { lock(gate) { epoch=checked(epoch+1); allowed=allow; } }
        internal void CancelOrWithdraw() { lock(gate) { epoch=checked(epoch+1); cancelled=true; } }

        internal bool Admit(byte[] seal, byte[] prefix, byte[] candidate, bool trustedNaturalExit, bool verifiedDeliveryAndChild)
        {
            lock(gate)
            {
                if(state!="awaiting_evidence")
                {
                    if(state=="admitted" || state=="permitted") state="terminal_no_publication";
                    return false;
                }
                try
                {
                    Require(!cancelled && Now()<pending && trustedNaturalExit && verifiedDeliveryAndChild &&
                        Bounded(candidate) && expected.SequenceEqual(candidate) && seal!=null && seal.Length<=4096 &&
                        prefix!=null && prefix.Length>0 && prefix.Length<=131072);
                    // Snapshot untrusted byte arrays before hashing and parsing.
                    prefix=(byte[])prefix.Clone(); seal=(byte[])seal.Clone();
                    Exact(StrictJson.Parse(seal),new Dictionary<string,object>{
                        {"v",1},{"type","model_output_evidence_sealed"},{"attempt",attempt},{"request_id",finish},
                        {"channel",channel},{"delivery_id",delivery},{"audit_sha256",BridgeHostFiles.Hash(prefix)}});
                    VerifyPrefix(prefix);
                    state="admitted"; return true;
                }
                catch(Exception) { state="terminal_no_publication"; return false; }
            }
        }

        void VerifyPrefix(byte[] raw)
        {
            var lines=Utf8.GetString(raw).Split('\n');
            Require(lines.Length==5 && lines[4]=="");
            DateTimeOffset prior=DateTimeOffset.MinValue;
            for(int i=0;i<4;i++)
            {
                string stage="model_bridge."+DeliveryStages[i];
                var record=StrictJson.Parse(Utf8.GetBytes(lines[i]));
                object time, metadata;
                Require(record.TryGetValue("timestamp",out time));
                Require(record.TryGetValue("metadata",out metadata));
                DateTimeOffset stamp;
                Require(DateTimeOffset.TryParseExact(time as string,new[]{"yyyy-MM-dd'T'HH:mm:sszzz","yyyy-MM-dd'T'HH:mm:ss'Z'"},
                    CultureInfo.InvariantCulture,DateTimeStyles.AssumeUniversal,out stamp) && stamp.Offset==TimeSpan.Zero && stamp>=prior);
                prior=stamp;
                Exact(record,new Dictionary<string,object>{{"schema_version",1},{"timestamp",time},{"event_type",stage},
                    {"decision","allow"},{"reason_code",stage},{"actor_id",actor},{"capability",i<2?"model.egress":"model.output"},
                    {"target","model:maya-offline-fixture"},{"operation",i<2?"infer":"disclose"},
                    {"data_classification","internal-synthetic"},{"idempotency_key",null},{"metadata",metadata}});
                var fields=new Dictionary<string,object>{{"attempt",attempt},{"request_id",service},{"route","maya.offline.model.v1"},
                    {"endpoint","https://maya-offline-model.invalid/v1/chat/completions"},{"model","maya-offline-wire-v1"},
                    {"destination",i<2?"provider":"runtime:"+attempt},{"request_sha256",requestHash},
                    {"response_sha256",i==0?"":responseHash},{"request_bytes",requestBytes.ToString(CultureInfo.InvariantCulture)},
                    {"response_bytes",i==0?"0":responseBytes.ToString(CultureInfo.InvariantCulture)},{"output_sha256",outputHash},
                    {"dispatches",i==0?"0":"1"},{"real_inference","false"}};
                if(i==3) fields.Add("coordinator_request_id",delivery);
                Exact(metadata as Dictionary<string,object>,fields);
            }
        }

        // These are trusted, separately scoped fixture consent inputs, not a launch-consent flag.
        internal bool Authorize(string consentId, string consentAttempt, string consentChannel, string consentActor,
            string digest, int length, string destination, long consentUntil)
        {
            lock(gate)
            {
                if(state!="admitted") return false;
                try
                {
                    long now=Now();
                    Require(!cancelled && allowed && now<pending && now<consentUntil && Hex(consentId,32) &&
                        attempt==consentAttempt && channel==consentChannel && actor==consentActor &&
                        outputHash==digest && expected.Length==length && destination==Destination);
                    consent=consentId; permitEpoch=epoch;
                    deadline=Math.Min(Math.Min(pending,consentUntil),checked(now+window));
                    state="permitted"; return true;
                }
                catch(Exception) { state="terminal_no_publication"; return false; }
            }
        }

        byte[] Record(string name)
        {
            var data=new Dictionary<string,object>{{"v",1},{"event",name},{"attempt",attempt},{"channel",channel},
                {"actor",actor},{"delivery_id",delivery},{"request_sha256",requestHash},{"response_sha256",responseHash},
                {"output_sha256",outputHash},{"output_bytes",expected.Length},{"destination",Destination},{"consent_id",consent},
                {"epoch",permitEpoch},{"deadline",deadline}};
            return Utf8.GetBytes(new JavaScriptSerializer().Serialize(data)+"\n");
        }

        void CheckJournal(byte[] expectedBytes)
        {
            var actual=readJournal();
            Require(actual!=null && actual.Length<=16384 && expectedBytes.SequenceEqual(actual));
        }

        bool Live()
        {
            long now=Now();
            return !cancelled && allowed && epoch==permitEpoch && now<deadline;
        }

        internal string Release()
        {
            lock(gate)
            {
                if(state!="permitted") return state;
                state="consumed";
                byte[] intent;
                try
                {
                    Require(Live());
                    CheckJournal(new byte[0]);
                    intent=Record("release_intent"); appendAndFlush((byte[])intent.Clone()); CheckJournal(intent);
                    if(!Live())
                    {
                        byte[] stop=Record("pre_effect_stop"); appendAndFlush((byte[])stop.Clone());
                        CheckJournal(intent.Concat(stop).ToArray());
                        return state="terminal_no_publication";
                    }
                }
                catch(Exception) { return state="terminal_no_publication"; }

                // Acceptance is the local fake effect, ordered under the same lock as revocation.
                effects++;
                if(loseAck) return state="terminal_delivery_unknown";
                try
                {
                    byte[] confirmed=Record("delivery_confirmed"); appendAndFlush((byte[])confirmed.Clone());
                    CheckJournal(intent.Concat(confirmed).ToArray());
                    return state="confirmed";
                }
                catch(Exception) { return state="terminal_delivery_unknown"; }
            }
        }
    }
}
#endif
