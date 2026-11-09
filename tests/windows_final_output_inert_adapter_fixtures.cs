using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using ProjectMaya.WindowsRuntime;

internal static class FinalOutputInertAdapterFixtures
{
    static readonly string Attempt=new string('a',32), Channel=new string('b',64), Service=new string('c',32),
        Delivery=new string('d',32), Finish=new string('e',32), Consent=new string('f',32);
    const string Actor="windows:S-1-5-21-500";
    static readonly byte[] Request=Bytes("request"), Response=Bytes("response"), Output=Bytes("output");
    static byte[] Bytes(string s) { return Encoding.UTF8.GetBytes(s); }
    static string Hash(byte[] b) { return BridgeHostFiles.Hash(b); }
    static string Json(object o) { return new JavaScriptSerializer().Serialize(o); }
    static int checks;
    static void Check(bool ok) { checks++; if(!ok) throw new Exception("Assertion "+checks); }

    sealed class Fixture
    {
        internal long Tick;
        internal int Reads, Appends;
        internal readonly MemoryStream Journal=new MemoryStream();
        internal Action<int> OnAppend=delegate {};
        internal Action<int> OnRead=delegate {};
        internal readonly FinalOutputInertAdapter Owner;
        internal Fixture(bool lose=false, string attempt=null, bool protectedJournal=false)
        {
            Action<byte[]> append=b=>{OnAppend(++Appends);Journal.Write(b,0,b.Length);};
            Func<byte[]> read=()=>{OnRead(++Reads);return Journal.ToArray();};
            if(protectedJournal)
            {
                var handle=new object();
                var identity=new InertOpenedIdentity("parent","volume","release-file","descriptor");
                var writer=append; var reader=read;
                var journal=new InertProtectedJournal(handle,identity,
                    h=>new InertOpenedObservation(h,identity,(int)Journal.Length,createdNew:true),
                    (h,b)=>{writer(b);return b.Length;},h=>true,(h,n)=>reader());
                append=journal.AppendAndFlush; read=journal.Read;
            }
            Owner=new FinalOutputInertAdapter(attempt??Attempt,Channel,Actor,Service,Delivery,Finish,Request,Response,Output,
                ()=>Tick,10,3,append,read,lose);
            Owner.SetPolicy(true);
        }
        internal bool Admit(byte[] prefix=null, string altered=null, bool exit=true, bool prior=true, byte[] candidate=null)
        {
            prefix=prefix??Prefix();
            var seal=new Dictionary<string,object>{{"v",1},{"type","model_output_evidence_sealed"},{"attempt",Attempt},
                {"request_id",Finish},{"channel",Channel},{"delivery_id",Delivery},{"audit_sha256",Hash(prefix)}};
            if(altered!=null) seal[altered]="wrong";
            return Owner.Admit(Bytes(Json(seal)),prefix,candidate??Output,exit,prior);
        }
        internal bool Permit(long expires=20,string destination=FinalOutputInertAdapter.Destination, string digest=null)
        {return Owner.Authorize(Consent,Attempt,Channel,Actor,digest??Hash(Output),Output.Length,destination,expires);}
    }

    static byte[] Prefix()
    {
        var lines=new List<string>();
        var stages=new[]{"egress_intent","dispatch_outcome","runtime_release_intent","runtime_delivery"};
        for(int i=0;i<4;i++)
        {
            string stage="model_bridge."+stages[i];
            var metadata=new Dictionary<string,object>{{"attempt",Attempt},{"request_id",Service},{"route","maya.offline.model.v1"},
                {"endpoint","https://maya-offline-model.invalid/v1/chat/completions"},{"model","maya-offline-wire-v1"},
                {"destination",i<2?"provider":"runtime:"+Attempt},{"request_sha256",Hash(Request)},
                {"response_sha256",i==0?"":Hash(Response)},{"request_bytes",Request.Length.ToString()},
                {"response_bytes",i==0?"0":Response.Length.ToString()},{"output_sha256",Hash(Output)},
                {"dispatches",i==0?"0":"1"},{"real_inference","false"}};
            if(i==3) metadata.Add("coordinator_request_id",Delivery);
            lines.Add(Json(new Dictionary<string,object>{{"schema_version",1},{"timestamp","2026-11-09T00:00:00Z"},
                {"event_type",stage},{"decision","allow"},{"reason_code",stage},{"actor_id",Actor},
                {"capability",i<2?"model.egress":"model.output"},{"target","model:maya-offline-fixture"},
                {"operation",i<2?"infer":"disclose"},{"data_classification","internal-synthetic"},
                {"idempotency_key",null},{"metadata",metadata}}));
        }
        return Bytes(string.Join("\n",lines)+"\n");
    }

    static void Block(Fixture f) {Check(f.Owner.Release()=="terminal_no_publication");Check(f.Owner.FakeEffects==0);}

    static void RejectIo(Action action)
    {
        try { action(); }
        catch(IOException) { Check(true); return; }
        Check(false);
    }

    static void HandleCases()
    {
        var identity=new InertOpenedIdentity("parent","volume","file","descriptor");
        var handle=new object();
        foreach(string fault in new[]{"handle","parent","volume","file","descriptor","links","directory","remote",
            "reparse","unpinned","sharing","inherit","existing","nonempty"})
        {
            var badIdentity=new InertOpenedIdentity(fault=="parent"?"other":"parent",fault=="volume"?"other":"volume",
                fault=="file"?"other":"file",fault=="descriptor"?"other":"descriptor");
            RejectIo(()=>new InertProtectedJournal(handle,identity,h=>new InertOpenedObservation(
                fault=="handle"?new object():h,badIdentity,fault=="nonempty"?1:0,fault=="links"?2:1,
                fault!="directory",fault!="remote",fault=="reparse",fault!="unpinned",fault!="sharing",fault=="inherit",fault!="existing"),
                (h,b)=>{throw new Exception("Unexpected write");},h=>true,(h,n)=>new byte[n]));
        }
        foreach(string fault in new[]{"none","short-write","flush","swap","short-read","grow-on-read"})
        {
            var buffer=new MemoryStream(); bool swapped=false;
            var journal=new InertProtectedJournal(handle,identity,h=>new InertOpenedObservation(swapped?new object():h,
                identity,(int)buffer.Length,createdNew:true),
                (h,b)=>{Check(object.ReferenceEquals(h,handle));buffer.Write(b,0,b.Length);return fault=="short-write"?b.Length-1:b.Length;},
                h=>{Check(object.ReferenceEquals(h,handle));swapped=fault=="swap";return fault!="flush";},
                (h,n)=>{Check(object.ReferenceEquals(h,handle));if(fault=="grow-on-read")buffer.WriteByte(0);
                    return fault=="short-read"?new byte[0]:buffer.ToArray().Take(n).ToArray();});
            if(fault=="none" || fault=="short-read" || fault=="grow-on-read")
            {
                journal.AppendAndFlush(Bytes("intent\n"));
                if(fault=="none") {Check(journal.Read().SequenceEqual(Bytes("intent\n"))); continue;}
                RejectIo(()=>journal.Read());
            }
            else RejectIo(()=>journal.AppendAndFlush(Bytes("intent\n")));
            RejectIo(()=>journal.AppendAndFlush(Bytes("retry\n")));
        }

        byte[] intent=Bytes("intent\n"), confirmation=Bytes("confirmation\n"), stop=Bytes("stop\n");
        Check(InertJournalEvidence.Classify(null,intent,confirmation,stop)=="no_confirmed_evidence");
        Check(InertJournalEvidence.Classify(intent.Concat(confirmation).ToArray(),intent,confirmation,stop)=="confirmed_as_recorded");
        Check(InertJournalEvidence.Classify(intent.Concat(stop).ToArray(),intent,confirmation,stop)=="pre_effect_stop_as_recorded");
        foreach(var raw in new[]{intent,Bytes("inten"),Bytes("intent\nconfirm"),Bytes("intent\nconfirmation\nextra\n"),Bytes("stale\nstop\n")})
            Check(InertJournalEvidence.Classify(raw,intent,confirmation,stop)=="unknown_or_invalid");
    }

    static void WorkerCases()
    {
        var identity=new InertOpenedIdentity("parent","volume","worker-file","descriptor");
        var wrong=new InertOpenedIdentity("parent","volume","replacement","descriptor");
        var process=new object(); var pipe=new object(); var handle=new object();
        var steps=new[]{InertWorkerStep.FinishSent,InertWorkerStep.WriterClosed,InertWorkerStep.SealRead,
            InertWorkerStep.CleanEof,InertWorkerStep.NaturalExit};
        var prefix=Prefix();
        foreach(string fault in new[]{"none","process","pipe","order","extra-frame","budget","forced","exit","stderr",
            "writer","opened","swap","short-read","digest","prior"})
        {
            var f=new Fixture(protectedJournal:true); int inspections=0;
            var handoff=new InertWorkerHandoff(process,pipe,identity);
            var seal=Bytes(Json(new Dictionary<string,object>{{"v",1},{"type","model_output_evidence_sealed"},{"attempt",Attempt},
                {"request_id",Finish},{"channel",Channel},{"delivery_id",Delivery},{"audit_sha256",fault=="digest"?Hash(Output):Hash(prefix)}}));
            var ordered=(InertWorkerStep[])steps.Clone();
            if(fault=="order") {ordered[1]=InertWorkerStep.SealRead;ordered[2]=InertWorkerStep.WriterClosed;}
            if(fault=="extra-frame") ordered=ordered.Where(s=>s!=InertWorkerStep.CleanEof).ToArray();
            Func<bool> admit=()=>handoff.Admit(f.Owner,fault=="process"?new object():process,fault=="pipe"?new object():pipe,
                ordered,fault!="budget",fault=="forced",fault=="exit"?1:0,fault=="stderr"?1:0,
                fault=="writer"?wrong:identity,handle,
                h=>new InertOpenedObservation(h,fault=="opened" || ++inspections==2 && fault=="swap"?wrong:identity,prefix.Length),
                (h,n)=>fault=="short-read"?new byte[0]:(byte[])prefix.Clone(),seal,Output,fault!="prior");
            Check(admit()==(fault=="none"));Check(!admit());
            if(fault=="none") {Check(f.Permit());Check(f.Owner.Release()=="confirmed" && f.Owner.FakeEffects==1);}
            else {Check(!f.Permit());Check(f.Owner.FakeEffects==0 && f.Appends==0);}
        }
    }

    static void Main()
    {
        var good=new Fixture();good.Tick=7;Check(good.Admit() && good.Permit());good.Tick=9;
        Parallel.Invoke(()=>good.Owner.Release(),()=>good.Owner.Release());
        Check(good.Owner.Release()=="confirmed" && good.Owner.FakeEffects==1 && good.Appends==2);
        var rows=Encoding.UTF8.GetString(good.Journal.ToArray()).Split('\n');
        Check(rows.Length==3 && rows[2]=="");
        var intent=StrictJson.Parse(Bytes(rows[0]));var confirmation=StrictJson.Parse(Bytes(rows[1]));
        Check(intent.Count==14 && (string)intent["event"]=="release_intent" && (string)confirmation["event"]=="delivery_confirmed");
        Check(intent.Where(x=>x.Key!="event").All(x=>object.Equals(x.Value,confirmation[x.Key])));
        Check((string)intent["delivery_id"]==Delivery && (string)intent["output_sha256"]==Hash(Output));

        foreach(string key in new[]{"v","type","attempt","request_id","channel","delivery_id","audit_sha256","extra"})
        {var f=new Fixture();Check(!f.Admit(altered:key));Block(f);}
        var stale=new Fixture(attempt:new string('0',32));Check(!stale.Admit());Block(stale);
        var badExit=new Fixture();Check(!badExit.Admit(exit:false));Block(badExit);
        var badPrior=new Fixture();Check(!badPrior.Admit(prior:false));Block(badPrior);
        var badText=new Fixture();Check(!badText.Admit(candidate:Bytes("mutated")));Block(badText);
        string raw=Encoding.UTF8.GetString(Prefix());
        foreach(string bad in new[]{raw.TrimEnd('\n'),raw+"{}\n",raw.Replace(Delivery,Finish),raw.Replace(Actor,"wrong"),
            raw.Replace("egress_intent","runtime_delivery"),raw.Replace("\"decision\":\"allow\"","\"decision\":\"allow\",\"decision\":\"allow\""),
            raw.Replace("2026-11-09T00:00:00Z","invalid")})
        {var f=new Fixture();Check(!f.Admit(Bytes(bad)));Block(f);}

        foreach(long tick in new long[]{9,10,11})
        {var f=new Fixture();f.Tick=tick;Check(f.Admit()==(tick==9));}
        foreach(long tick in new long[]{2,3,4})
        {var f=new Fixture();Check(f.Admit() && f.Permit());f.Tick=tick;Check((f.Owner.Release()=="confirmed")== (tick==2));}
        var wrongDestination=new Fixture();Check(wrongDestination.Admit() && !wrongDestination.Permit(destination:"other"));Block(wrongDestination);
        var wrongDigest=new Fixture();Check(wrongDigest.Admit() && !wrongDigest.Permit(digest:new string('0',64)));Block(wrongDigest);
        var policy=new Fixture();Check(policy.Admit());policy.Owner.SetPolicy(false);Check(!policy.Permit());Block(policy);
        var duplicate=new Fixture();Check(duplicate.Admit() && duplicate.Permit() && !duplicate.Admit());Block(duplicate);

        var revoked=new Fixture();Check(revoked.Admit() && revoked.Permit());revoked.OnAppend=n=>{if(n==1)revoked.Owner.CancelOrWithdraw();};
        Block(revoked);Check(revoked.Appends==2 && Encoding.UTF8.GetString(revoked.Journal.ToArray()).Contains("pre_effect_stop"));
        var changed=new Fixture();Check(changed.Admit() && changed.Permit());changed.OnRead=n=>{if(n==2)changed.Owner.SetPolicy(true);};Block(changed);
        var expired=new Fixture();Check(expired.Admit() && expired.Permit(1));expired.OnAppend=n=>expired.Tick=1;Block(expired);
        var backwards=new Fixture();backwards.Tick=1;Check(backwards.Admit() && backwards.Permit());backwards.Tick=0;Block(backwards);
        var io=new Fixture();Check(io.Admit() && io.Permit());io.OnAppend=n=>{throw new IOException();};Block(io);
        var torn=new Fixture(protectedJournal:true);Check(torn.Admit() && torn.Permit());torn.OnRead=n=>{if(n==2)torn.Journal.SetLength(4);};Block(torn);
        var old=new Fixture();Check(old.Admit() && old.Permit());old.Journal.WriteByte(1);Block(old);Check(old.Appends==0);
        foreach(bool lose in new[]{false,true})
        {
            var f=new Fixture(lose,protectedJournal:true);Check(f.Admit() && f.Permit());
            f.OnRead=n=>{if(n==3)f.Journal.SetLength(4);};
            Check(f.Owner.Release()=="terminal_delivery_unknown" && f.Owner.Release()=="terminal_delivery_unknown" && f.Owner.FakeEffects==1);
        }
        HandleCases(); WorkerCases();
        Console.WriteLine("Final output inert adapter and handles: "+checks+" assertions passed");
    }
}
