using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using ProjectMaya.WindowsRuntime;

internal static class ChannelSchedulingFixtures
{
    static int checks;
    static readonly List<Dictionary<string,object>> results=new List<Dictionary<string,object>>();
    static void Check(bool value,string name){checks++;if(!value)throw new Exception("fixture assertion: "+name);}
    static byte[] Frame(){return BridgeChannel.Encode(new Dictionary<string,object>{{"v",1},{"type","fixture_ready"},{"attempt",new string('a',32)}});}

    sealed class ObservedStream:MemoryStream
    {
        internal int TailReads;
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
    sealed class DelayedStream:Stream
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
                var clock=Stopwatch.StartNew();bool rejected=false;
                try{channel.Read(5000);}catch(StartupFailure e){rejected=e.Message=="bridge_channel_failed";}
                clock.Stop();
                result=new Dictionary<string,object>{{"case","complete_frame_delayed_nested_reader"},{"accepted",false},
                    {"category",channel.FailureCategory},{"frame_bytes_present_before_read",raw.Length},
                    {"remaining_bytes_at_failure",raw.Length-stream.Position},{"tail_reads_at_failure",stream.TailReads},
                    {"nested_started_at_failure",scheduler.NestedStarted!=0},{"queued_tasks_at_failure",scheduler.Queued},
                    {"elapsed_ms",clock.ElapsedMilliseconds}};
                Check(rejected,"delayed scheduler rejects");Check(channel.FailureCategory=="bridge_incomplete_frame_timeout","delayed scheduler category");
                Check(stream.Position==1 && stream.TailReads==0,"complete frame unread remainder");
                Check(scheduler.Queued==3 && scheduler.NestedStarted==0,"nested queued but not started");
                scheduler.ReleaseNested.Set();Terminal(channel);
            },CancellationToken.None,TaskCreationOptions.None,scheduler);
            try{Check(caller.Wait(7000),"fixture caller bounded");}
            finally{scheduler.ReleaseNested.Set();}
            channel.Dispose();Check(scheduler.AllTasksComplete,"scheduler tasks drained");
        }
        finally{scheduler.ReleaseNested.Set();scheduler.Dispose();}
        Check(scheduler.DrainedWorkers==2,"private workers joined");result["fixture_workers_drained"]=true;results.Add(result);
    }

    static void ActualDelay(string name,int prefix,string category)
    {
        byte[] raw=Frame();var stream=new DelayedStream(raw,prefix);var channel=new BridgeChannel(stream,new MemoryStream());
        var clock=Stopwatch.StartNew();bool rejected=false;
        try
        {
            try{channel.Read(5000);}catch(StartupFailure e){rejected=e.Message=="bridge_channel_failed";}
            clock.Stop();
            Check(rejected,"delayed bytes rejected");Check(channel.FailureCategory==category,"delayed bytes category");
            Check(stream.Waiting.WaitOne(0),"fixture actually waiting for missing bytes");
            Check(stream.PositionObserved==prefix,"exact offered prefix observed");
            results.Add(new Dictionary<string,object>{{"case",name},{"accepted",false},{"category",category},
                {"frame_bytes_available_before_release",prefix},{"position_at_failure",stream.PositionObserved},
                {"tail_reads_at_failure",stream.TailReads},{"reader_waiting_for_bytes",true},{"elapsed_ms",clock.ElapsedMilliseconds}});
        }
        finally{stream.Release.Set();channel.Dispose();stream.DisposeSignals();}
        Terminal(channel);
    }

    static void BadFrame(string name,byte[] raw,string category)
    {
        var channel=new BridgeChannel(new MemoryStream(raw),new MemoryStream());bool rejected=false;
        try{channel.Read(5000);}catch(StartupFailure e){rejected=e.Message=="bridge_channel_failed";}
        Check(rejected,"bad frame rejected");Check(channel.FailureCategory==category,"bad frame category");Terminal(channel);channel.Dispose();
        results.Add(new Dictionary<string,object>{{"case",name},{"accepted",false},{"category",category}});
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
        var report=new Dictionary<string,object>{{"schema","maya.channel.scheduling.inert.v1"},{"assertions",checks},{"cases",results},
            {"ready_limit_ms",5000},{"partial_limit_ms",1000},{"product_source_modified",false},{"native_product_execution",false},
            {"private_scheduler_fixture_only",true},{"guest_root_cause_proven",false}};
        if(File.Exists(args[0]))throw new Exception("Refuse result overwrite");
        File.WriteAllText(args[0],new JavaScriptSerializer().Serialize(report));
        Console.WriteLine(checks+" channel scheduling assertions passed across "+results.Count+" inert cases.");return 0;
    }
}
