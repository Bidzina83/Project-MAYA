using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using ProjectMaya.WindowsRuntime;

internal static class ChannelReaderFixtures
{
    static int checks;
    static readonly List<Dictionary<string,object>> results=new List<Dictionary<string,object>>();
    static void Check(bool value,string name){checks++;if(!value)throw new Exception("fixture assertion: "+name);}
    static byte[] Frame(){return BridgeChannel.Encode(new Dictionary<string,object>{{"v",1},{"type","fixture_ready"},{"attempt",new string('a',32)}});}

    sealed class ObservedStream:MemoryStream
    {
        internal int TailReads;
        internal bool? FirstReadOnThreadPool;
        public override int ReadByte(){FirstReadOnThreadPool=Thread.CurrentThread.IsThreadPoolThread;return base.ReadByte();}
        internal ObservedStream(byte[] raw):base(raw){}
        public override int Read(byte[] data,int offset,int count){Interlocked.Increment(ref TailReads);return base.Read(data,offset,count);}
    }

    // Private fixture scheduler only. No ThreadPool/global machine setting is changed.
    sealed class TwoWorkerScheduler:TaskScheduler,IDisposable
    {
        readonly BlockingCollection<Task> queue=new BlockingCollection<Task>();
        readonly ConcurrentDictionary<int,int> order=new ConcurrentDictionary<int,int>();
        readonly List<Task> tasks=new List<Task>();
        readonly Thread[] workers=new Thread[2];
        internal readonly ManualResetEvent ReleaseNested=new ManualResetEvent(false);
        internal int Queued,NestedStarted,DrainedWorkers;
        internal TwoWorkerScheduler()
        {
            for(int i=0;i<workers.Length;i++)
            {
                workers[i]=new Thread(delegate(){
                    foreach(Task task in queue.GetConsumingEnumerable())
                    {
                        int number=order[task.Id];
                        if(number==3){ReleaseNested.WaitOne();Interlocked.Exchange(ref NestedStarted,1);}
                        TryExecuteTask(task);
                    }
                });
                workers[i].IsBackground=true;workers[i].Start();
            }
        }
        protected override void QueueTask(Task task)
        {
            int number=Interlocked.Increment(ref Queued);order[task.Id]=number;
            lock(tasks)tasks.Add(task);queue.Add(task);
        }
        protected override bool TryExecuteTaskInline(Task task,bool previouslyQueued){return false;}
        protected override IEnumerable<Task> GetScheduledTasks(){return queue.ToArray();}
        internal bool AllTasksComplete{get{lock(tasks){foreach(Task task in tasks)if(!task.IsCompleted)return false;}return true;}}
        public void Dispose()
        {
            ReleaseNested.Set();queue.CompleteAdding();
            foreach(Thread worker in workers){if(!worker.Join(5000))throw new Exception("fixture scheduler did not drain");DrainedWorkers++;}
            ReleaseNested.Dispose();queue.Dispose();
        }
    }

    // Offers only a prefix until released. The rest is late data, not EOF.
    class DelayedStream:Stream
    {
        readonly byte[] raw;readonly int available;
        int position;
        internal readonly ManualResetEvent Release=new ManualResetEvent(false);
        internal readonly ManualResetEvent Waiting=new ManualResetEvent(false);
        internal int TailReads;
        internal int PositionObserved{get{return Volatile.Read(ref position);}}
        internal DelayedStream(byte[] frame,int prefix){raw=frame;available=prefix;}
        void WaitIfMissing(){if(position>=available && !Release.WaitOne(0)){Waiting.Set();Release.WaitOne();}}
        public override int ReadByte(){WaitIfMissing();return position<raw.Length?raw[position++]:-1;}
        public override int Read(byte[] data,int offset,int count)
        {
            Interlocked.Increment(ref TailReads);WaitIfMissing();
            int cap=Release.WaitOne(0)?raw.Length:available;
            int n=Math.Min(count,cap-position);
            if(n<=0)return 0;
            Array.Copy(raw,position,data,offset,n);position+=n;return n;
        }
        public override bool CanRead{get{return true;}}
        public override bool CanSeek{get{return false;}}
        public override bool CanWrite{get{return false;}}
        public override long Length{get{return raw.Length;}}
        public override long Position{get{return position;}set{throw new NotSupportedException();}}
        public override void Flush(){}
        public override long Seek(long offset,SeekOrigin origin){throw new NotSupportedException();}
        public override void SetLength(long value){throw new NotSupportedException();}
        public override void Write(byte[] data,int offset,int count){throw new NotSupportedException();}
        protected override void Dispose(bool disposing){Release.Set();base.Dispose(disposing);}
        internal void DisposeSignals(){Release.Dispose();Waiting.Dispose();}
    }

    static void Terminal(BridgeChannel channel)
    {
        bool read=false,write=false,eof=false;
        try{channel.Read(5000);}catch(StartupFailure e){read=e.Message=="bridge_channel_closed";}
        try{channel.Write(new Dictionary<string,object>{{"v",1}},5000);}catch(StartupFailure e){write=e.Message=="bridge_channel_closed";}
        try{channel.Eof(5000);}catch(StartupFailure e){eof=e.Message=="bridge_channel_closed";}
        Check(read && write && eof,"failed channel stays terminal");
    }

    static void CompleteFrameDefault()
    {
        byte[] raw=Frame();var stream=new ObservedStream(raw);var channel=new BridgeChannel(stream,new MemoryStream());
        var clock=Stopwatch.StartNew();var reply=channel.Read(5000);clock.Stop();
        Check("fixture_ready".Equals(reply["type"]),"default complete frame");
        Check(stream.Position==raw.Length,"default drained frame");Check(channel.FailureCategory==null,"default no error");
        results.Add(new Dictionary<string,object>{{"case","complete_frame_default_scheduler"},{"accepted",true},{"category",null},
            {"frame_bytes_present_before_read",raw.Length},{"remaining_bytes_at_result",raw.Length-stream.Position},{"elapsed_ms",clock.ElapsedMilliseconds}});
        channel.Dispose();
    }

    static void CompleteFrameDelayedScheduler()
    {
        byte[] raw=Frame();var stream=new ObservedStream(raw);var channel=new BridgeChannel(stream,new MemoryStream());
        var scheduler=new TwoWorkerScheduler();Dictionary<string,object> result=null;
        try
        {
            var caller=Task.Factory.StartNew(delegate(){
                var clock=Stopwatch.StartNew();var reply=channel.Read(5000);clock.Stop();
                Check("fixture_ready".Equals(reply["type"]),"constrained scheduler complete frame accepted");
                Check(scheduler.Queued==1 && scheduler.NestedStarted==0,"reader never queues on private caller scheduler");
                Check(stream.Position==raw.Length,"complete frame drained");
                Check(stream.FirstReadOnThreadPool==false,"I/O reader not on shared ThreadPool");
                var progress=channel.SnapshotReadProgress();
                Check(progress.Count==18,"bounded exact progress shape");
                string diagnostic=new JavaScriptSerializer().Serialize(progress);
                Check(!diagnostic.Contains("fixture_ready") && !diagnostic.Contains(new string('a',32)),"no frame contents in progress");
                Check(true.Equals(progress["frame_accepted"]) && true.Equals(progress["json_parsed"]),"read progress success is not model admission");
                Check(4.Equals(progress["header_bytes"]) && (raw.Length-4).Equals(progress["payload_bytes_read"]),"complete counters");
                result=new Dictionary<string,object>{{"case","complete_frame_constrained_caller_scheduler"},{"accepted",true},
                    {"category",channel.FailureCategory},{"frame_bytes_present_before_read",raw.Length},
                    {"remaining_bytes_at_result",raw.Length-stream.Position},{"queued_tasks_on_private_scheduler",scheduler.Queued},
                    {"elapsed_ms",clock.ElapsedMilliseconds},{"progress",progress}};
            },CancellationToken.None,TaskCreationOptions.None,scheduler);
            Check(caller.Wait(7000),"fixture caller bounded");
            channel.Dispose();Check(scheduler.AllTasksComplete,"scheduler tasks drained");
        }
        finally{scheduler.ReleaseNested.Set();scheduler.Dispose();}
        Check(scheduler.DrainedWorkers==2,"private workers joined");result["fixture_workers_drained"]=true;results.Add(result);
    }

    static void ActualDelay(string name,int prefix,string category)
    {
        byte[] raw=Frame();var stream=new DelayedStream(raw,prefix);var channel=new BridgeChannel(stream,new MemoryStream());
        var clock=Stopwatch.StartNew();bool rejected=false;Dictionary<string,object> frozen=null;
        try
        {
            try{channel.Read(5000);}catch(StartupFailure e){rejected=e.Message=="bridge_channel_failed";}
            clock.Stop();
            Check(rejected,"delayed bytes rejected");Check(channel.FailureCategory==category,"delayed bytes category");
            Check(stream.Waiting.WaitOne(0),"fixture actually waiting for missing bytes");
            Check(stream.PositionObserved==prefix,"exact offered prefix observed");
            frozen=channel.SnapshotReadProgress();
            Check("at_read_failure".Equals(frozen["observation"]) && false.Equals(frozen["frame_accepted"]),"failure snapshot not admission");
            Check((prefix==0?"first_byte":prefix==1?"header":"payload").Equals(frozen["stage"]),"exact blocked stage");
            Check((prefix==0?0:prefix==1?1:4).Equals(frozen["header_bytes"]),"header count at timeout");
            Check((prefix==5?1:0).Equals(frozen["payload_bytes_read"]),"payload count at timeout");
            results.Add(new Dictionary<string,object>{{"case",name},{"accepted",false},{"category",category},
                {"frame_bytes_available_before_release",prefix},{"position_at_failure",stream.PositionObserved},
                {"tail_reads_at_failure",stream.TailReads},{"reader_waiting_for_bytes",true},{"elapsed_ms",clock.ElapsedMilliseconds},{"progress",frozen}});
        }
        finally{stream.Release.Set();channel.Dispose();stream.DisposeSignals();}
        Terminal(channel);
        var after=channel.SnapshotReadProgress();
        foreach(var item in frozen)Check(Object.Equals(item.Value,after[item.Key]),"failure snapshot stable after late bytes and teardown");
        after["stage"]="tampered";Check(!"tampered".Equals(channel.SnapshotReadProgress()["stage"]),"snapshot copy cannot mutate authority");
    }

    static void BadFrame(string name,byte[] raw,string category)
    {
        var channel=new BridgeChannel(new MemoryStream(raw),new MemoryStream());bool rejected=false;
        try{channel.Read(5000);}catch(StartupFailure e){rejected=e.Message=="bridge_channel_failed";}
        Check(rejected,"bad frame rejected");Check(channel.FailureCategory==category,"bad frame category");Terminal(channel);channel.Dispose();
        if(name=="invalid_JSON")
        {
            var progress=channel.SnapshotReadProgress();
            Check("parse".Equals(progress["stage"]) && 4.Equals(progress["header_bytes"]) && 1.Equals(progress["payload_bytes_read"]),"malformed JSON parse progress");
            Check(false.Equals(progress["json_parsed"]) && false.Equals(progress["frame_accepted"]),"parse failure not accepted");
        }
        results.Add(new Dictionary<string,object>{{"case",name},{"accepted",false},{"category",category}});
    }

    sealed class LateFirstStream:DelayedStream
    {
        internal LateFirstStream(byte[] raw):base(raw,1){}
        public override int ReadByte(){Thread.Sleep(1500);return base.ReadByte();}
    }
    static void EarlierOverallDeadline()
    {
        var stream=new LateFirstStream(Frame());var channel=new BridgeChannel(stream,new MemoryStream());
        try
        {
            bool rejected=false;try{channel.Read(2000);}catch(StartupFailure e){rejected=e.Message=="bridge_channel_failed";}
            var progress=channel.SnapshotReadProgress();
            Check(rejected && channel.FailureCategory=="bridge_channel_timeout","overall RPC limit wins over later partial deadline");
            Check(true.Equals(progress["first_byte_observed"]) && "header".Equals(progress["stage"]),"late first byte then partial header");
            Check(2000.Equals(progress["overall_limit_ms"]) && 1000.Equals(progress["partial_limit_ms"]),"unchanged caller and partial budgets");
            results.Add(new Dictionary<string,object>{{"case","earlier_overall_RPC_deadline"},{"accepted",false},{"category",channel.FailureCategory},{"progress",progress}});
        }
        finally{stream.Release.Set();channel.Dispose();stream.DisposeSignals();}
        Terminal(channel);
    }
    static void PendingReaderOwnership()
    {
        var stream=new DelayedStream(Frame(),1);var channel=new BridgeChannel(stream,new MemoryStream());
        try
        {
            try{channel.Read(5000);Check(false,"expected partial timeout");}catch(StartupFailure e){Check(e.Message=="bridge_channel_failed","owned pending read failed");}
            bool uncertain=false;try{channel.Dispose();}catch(StartupFailure e){uncertain=e.Message=="bridge_pipe_cleanup_uncertain";}
            Check(uncertain,"cannot claim disposal while reader still blocked");
        }
        finally{stream.Release.Set();channel.Dispose();stream.DisposeSignals();}
        Check(true,"released pending reader drained by second disposal");
        results.Add(new Dictionary<string,object>{{"case","pending_reader_cleanup_uncertainty"},{"blocked_disposal_rejected",true},{"released_reader_drained",true}});
    }
    static void SuccessiveFramesAndBudget()
    {
        var raw=Frame();var combined=new MemoryStream();for(int i=0;i<20;i++)combined.Write(raw,0,raw.Length);combined.Position=0;
        var channel=new BridgeChannel(combined,new MemoryStream());
        for(int i=0;i<20;i++)Check("fixture_ready".Equals(channel.Read(5000)["type"]),"successive frame");
        Check(20.Equals(channel.SnapshotReadProgress()["read_sequence"]),"successive read sequence");channel.Dispose();
        var big=BridgeChannel.Encode(new Dictionary<string,object>{{"blob",new string('x',8000)}});
        int allowed=131072/big.Length;combined=new MemoryStream();for(int i=0;i<=allowed;i++)combined.Write(big,0,big.Length);combined.Position=0;
        channel=new BridgeChannel(combined,new MemoryStream());
        for(int i=0;i<allowed;i++)Check(channel.Read(5000).ContainsKey("blob"),"bounded channel admitted bytes");
        bool rejected=false;try{channel.Read(5000);}catch(StartupFailure){rejected=channel.FailureCategory=="bridge_frame_size";}
        Check(rejected,"same 128KiB channel budget rejects next frame");Terminal(channel);channel.Dispose();
        results.Add(new Dictionary<string,object>{{"case","successive_frames_and_channel_budget"},{"successive_frames",20},{"byte_limit",131072},{"overspend_rejected",true}});
    }
    static void OverlappingReadOwnership()
    {
        var stream=new DelayedStream(Frame(),0);var channel=new BridgeChannel(stream,new MemoryStream());
        var first=Task.Factory.StartNew(()=>channel.Read(5000));
        try
        {
            Check(stream.Waiting.WaitOne(1000),"owned reader actually blocked");
            bool rejected=false;try{channel.Read(5000);}catch(StartupFailure e){rejected=e.Message=="bridge_channel_closed";}
            Check(rejected,"overlapping read cannot spawn another reader");
        }
        finally{stream.Release.Set();Check(first.Wait(5000),"owned reader drained");channel.Dispose();stream.DisposeSignals();}
        Check("fixture_ready".Equals(first.Result["type"]),"original read retained ownership");
        Check(1.Equals(channel.SnapshotReadProgress()["read_sequence"]),"rejected overlap does not replace observation");
        results.Add(new Dictionary<string,object>{{"case","overlapping_read_ownership"},{"second_read_rejected",true},{"first_read_completed",true}});
    }

    static int Main(string[] args)
    {
        CompleteFrameDefault();CompleteFrameDelayedScheduler();
        ActualDelay("delayed_header",1,"bridge_incomplete_frame_timeout");
        ActualDelay("delayed_payload",5,"bridge_incomplete_frame_timeout");
        ActualDelay("no_first_byte",0,"bridge_channel_timeout");
        BadFrame("early_EOF",new byte[]{1,0},"eof");
        BadFrame("invalid_length",new byte[]{0,0,0,0},"bridge_frame_size");
        BadFrame("invalid_JSON",new byte[]{1,0,0,0,(byte)'x'},"bridge_json_invalid");
        BadFrame("oversize_length",BitConverter.GetBytes((uint)8193),"bridge_frame_size");
        EarlierOverallDeadline();PendingReaderOwnership();SuccessiveFramesAndBudget();
        OverlappingReadOwnership();
        var report=new Dictionary<string,object>{{"schema","maya.channel.reader.correction.inert.v1"},{"assertions",checks},{"cases",results},
            {"ready_limit_ms",5000},{"partial_limit_ms",1000},{"product_source_modified",true},{"native_product_execution",false},
            {"private_scheduler_fixture_only",true},{"guest_root_cause_proven",false}};
        if(File.Exists(args[0]))throw new Exception("Refuse result overwrite");
        File.WriteAllText(args[0],new JavaScriptSerializer().Serialize(report));
        Console.WriteLine(checks+" corrected channel-reader assertions passed across "+results.Count+" inert cases.");return 0;
    }
}
