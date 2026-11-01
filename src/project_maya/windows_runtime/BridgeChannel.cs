using System;
using System.Collections.Generic;
using System.Collections.Concurrent;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using Microsoft.Win32.SafeHandles;

namespace ProjectMaya.WindowsRuntime
{
    internal sealed class BridgeChannel : IDisposable
    {
        readonly Stream input, output;
        readonly ConcurrentBag<Task> pending = new ConcurrentBag<Task>();
        int readBytes, writtenBytes;
        volatile bool failed;
        readonly object progressGate = new object();
        readonly AutoResetEvent readWake = new AutoResetEvent(false);
        int readActive, readSequence;
        ReadObservation lastRead;
        sealed class ReadObservation
        {
            internal readonly Stopwatch Clock = Stopwatch.StartNew();
            internal int Sequence, OverallMilliseconds, HeaderBytes, PayloadBytes;
            internal int? ExpectedPayloadBytes;
            internal long FirstTicks=-1, FinishedTicks=-1;
            internal bool Started, Parsed, Accepted;
            internal string Stage="queued";
            internal Dictionary<string,object> Failure;
        }
        internal string FailureCategory { get; private set; }
        internal static string Category(Exception error)
        {
            for(int i=0;i<8 && error is AggregateException;i++)
            {
                var aggregate=(AggregateException)error;
                if(aggregate.InnerExceptions.Count!=1)return "multiple_failures";
                error=aggregate.InnerExceptions[0];
            }
            var failure=error as StartupFailure;
            if(failure!=null)
                foreach(string code in new[]{"bridge_channel_timeout","bridge_incomplete_frame_timeout","bridge_frame_size",
                    "bridge_json_size","bridge_json_invalid","bridge_json_depth","bridge_json_duplicate","bridge_json_integer"})
                    if(failure.Message==code)return code;
            if(error is EndOfStreamException)return "eof";
            if(error is DecoderFallbackException)return "invalid_utf8";
            if(error is ObjectDisposedException)return "stream_closed";
            if(error is IOException)return "io_error";
            return "operation_failed";
        }
        internal BridgeChannel(IntPtr read, IntPtr write)
        {
            input = new FileStream(new SafeFileHandle(read, false), FileAccess.Read);
            output = new FileStream(new SafeFileHandle(write, false), FileAccess.Write);
        }
        internal BridgeChannel(Stream read, Stream write) { input = read; output = write; }
        internal static byte[] Encode(Dictionary<string, object> message)
        {
            string json = new JavaScriptSerializer().Serialize(message);
            byte[] raw = new UTF8Encoding(false, true).GetBytes(json);
            if (raw.Length < 1 || raw.Length > 8192) throw new StartupFailure("bridge_frame_size");
            StrictJson.Parse(raw);
            byte[] framed = new byte[raw.Length + 4]; Array.Copy(BitConverter.GetBytes(raw.Length), framed, 4); Array.Copy(raw, 0, framed, 4, raw.Length);
            return framed;
        }
        T Bound<T>(Func<T> operation, int milliseconds)
        {
            if (failed || milliseconds <= 0) throw new StartupFailure("bridge_channel_closed");
            Task<T> task = Task.Factory.StartNew(operation); pending.Add(task);
            try
            {
                if (!task.Wait(milliseconds)) throw new StartupFailure("bridge_channel_timeout");
                return task.Result;
            }
            catch(Exception error) { FailureCategory=Category(error); failed = true; throw new StartupFailure("bridge_channel_failed"); }
        }
        internal Dictionary<string, object> Read(int waitMilliseconds)
        {
            if(failed || waitMilliseconds<=0)throw new StartupFailure("bridge_channel_closed");
            if(Interlocked.CompareExchange(ref readActive,1,0)!=0)throw new StartupFailure("bridge_channel_closed");
            var observation=new ReadObservation{Sequence=Interlocked.Increment(ref readSequence),OverallMilliseconds=waitMilliseconds};
            lock(progressGate){lastRead=observation;}
            try
            {
                readWake.Reset();
                // One blocking reader, explicitly off the caller/shared task scheduler.
                var read = Task.Factory.StartNew(delegate {
                    try
                    {
                    lock(progressGate){observation.Started=true;observation.Stage="first_byte";}
                    int first=input.ReadByte();if(first<0)throw new EndOfStreamException();
                    long firstAt=observation.Clock.ElapsedTicks;
                    lock(progressGate){observation.FirstTicks=firstAt;observation.HeaderBytes=1;observation.Stage="header";}
                    readWake.Set();
                    byte[] tail = new byte[3]; ExactRead(tail,observation,true);
                    byte[] header = new byte[] { (byte)first, tail[0], tail[1], tail[2] };
                    uint size = BitConverter.ToUInt32(header, 0);
                    if (size < 1 || size > 8192 || readBytes + 4L + size > 131072) throw new StartupFailure("bridge_frame_size");
                    readBytes += checked((int)size + 4);
                    lock(progressGate){observation.ExpectedPayloadBytes=(int)size;observation.Stage="payload";}
                    byte[] raw = new byte[size];ExactRead(raw,observation,false);
                    lock(progressGate){observation.Stage="parse";}
                    var parsed=StrictJson.Parse(raw);
                    lock(progressGate){observation.Parsed=true;observation.Stage="complete";}
                    return parsed;
                    }
                    finally
                    {
                        lock(progressGate){observation.FinishedTicks=observation.Clock.ElapsedTicks;}
                    }
                },CancellationToken.None,TaskCreationOptions.LongRunning,TaskScheduler.Default);
                pending.Add(read);
                // Notify only after Task completion is visible; no second queued reader.
                pending.Add(read.ContinueWith(_=>{readWake.Set();},CancellationToken.None,
                    TaskContinuationOptions.ExecuteSynchronously,TaskScheduler.Default));
                while(true)
                {
                    long deadline,now,finished;bool partial;
                    lock(progressGate)
                    {
                        deadline=ReadDeadline(observation,out partial);
                        now=observation.Clock.ElapsedTicks;finished=observation.FinishedTicks;
                    }
                    if(read.IsCompleted)
                    {
                        // Re-sample after completion: an earlier sample may predate the first byte/finally.
                        lock(progressGate){deadline=ReadDeadline(observation,out partial);finished=observation.FinishedTicks;}
                        // Completion observed late cannot admit a frame completed after its deadline.
                        if(finished<0 || finished>deadline)throw new StartupFailure(partial?"bridge_incomplete_frame_timeout":"bridge_channel_timeout");
                        var parsed=read.Result;
                        if(failed)throw new StartupFailure("bridge_channel_closed");
                        lock(progressGate){observation.Accepted=true;}
                        observation.Clock.Stop();return parsed;
                    }
                    if(now>=deadline)throw new StartupFailure(partial?"bridge_incomplete_frame_timeout":"bridge_channel_timeout");
                    int remaining=(int)Math.Min(Int32.MaxValue,Math.Max(1,Math.Ceiling((deadline-now)*1000.0/Stopwatch.Frequency)));
                    readWake.WaitOne(remaining);
                }
            }
            catch(Exception error)
            {
                FailureCategory=Category(error);failed=true;
                lock(progressGate){observation.Failure=ReadSnapshot(observation,"at_read_failure",FailureCategory);}
                throw new StartupFailure("bridge_channel_failed");
            }
            finally{Interlocked.Exchange(ref readActive,0);}
        }
        static long MillisecondsToTicks(int milliseconds)
        {return checked((long)Math.Ceiling(milliseconds*(double)Stopwatch.Frequency/1000.0));}
        static long ReadDeadline(ReadObservation observation,out bool partial)
        {
            long overall=MillisecondsToTicks(observation.OverallMilliseconds);
            long limit=observation.FirstTicks<0?Int64.MaxValue:observation.FirstTicks+MillisecondsToTicks(1000);
            partial=limit<=overall;return Math.Min(overall,limit);
        }
        void ExactRead(byte[] data,ReadObservation observation,bool header)
        {
            for (int offset = 0; offset < data.Length; )
            {
                int count=input.Read(data,offset,data.Length-offset);if(count<=0)throw new EndOfStreamException();offset+=count;
                lock(progressGate){if(header)observation.HeaderBytes+=count;else observation.PayloadBytes+=count;}
            }
        }
        Dictionary<string,object> ReadSnapshot(ReadObservation value,string phase,string category)
        {
            return new Dictionary<string,object>{{"schema","maya.channel.read_progress.v1"},{"observation",phase},
                {"read_sequence",value.Sequence},{"stage",value.Stage},{"reader_started",value.Started},
                {"first_byte_observed",value.FirstTicks>=0},{"header_bytes",value.HeaderBytes},
                {"first_byte_elapsed_ms",value.FirstTicks>=0?(object)(long)(value.FirstTicks*1000.0/Stopwatch.Frequency):null},
                {"payload_bytes_expected",value.ExpectedPayloadBytes.HasValue?(object)value.ExpectedPayloadBytes.Value:null},
                {"payload_bytes_read",value.PayloadBytes},{"json_parsed",value.Parsed},{"frame_accepted",value.Accepted},
                {"reader_finished",value.FinishedTicks>=0},{"elapsed_ms",value.Clock.ElapsedMilliseconds},
                {"reader_finished_elapsed_ms",value.FinishedTicks>=0?(object)(long)(value.FinishedTicks*1000.0/Stopwatch.Frequency):null},
                {"overall_limit_ms",value.OverallMilliseconds},{"partial_limit_ms",1000},{"failure_category",category}};
        }
        internal Dictionary<string,object> SnapshotReadProgress()
        {
            lock(progressGate)
            {
                if(lastRead==null)return new Dictionary<string,object>{{"schema","maya.channel.read_progress.v1"},{"observation","not_started"}};
                return lastRead.Failure!=null?new Dictionary<string,object>(lastRead.Failure):ReadSnapshot(lastRead,"last_read",null);
            }
        }
        internal void Write(Dictionary<string, object> message, int milliseconds)
        {
            byte[] raw = Encode(message);
            if (writtenBytes + raw.Length > 131072) throw new StartupFailure("bridge_channel_budget");
            writtenBytes += raw.Length;
            Bound(delegate { output.Write(raw, 0, raw.Length); output.Flush(); return true; }, milliseconds);
        }
        internal void Eof(int milliseconds)
        {
            if (!Bound(delegate { return input.ReadByte() == -1; }, milliseconds))
            { failed = true; throw new StartupFailure("bridge_trailing_frame"); }
        }
        public void Dispose()
        {
            failed=true;
            // Jobs must be stopped before this join: no blocked reader is abandoned.
            foreach (Task task in pending.ToArray())
                try { if (!task.Wait(1000)) throw new StartupFailure("bridge_pipe_cleanup_uncertain"); }
                catch (AggregateException) { }
            input.Dispose(); output.Dispose();readWake.Dispose(); failed = true;
        }
    }

    internal sealed class StrictJson
    {
        readonly string text; int offset;
        StrictJson(string value) { text = value; }
        internal static Dictionary<string, object> Parse(byte[] raw)
        {
            if (raw.Length < 1 || raw.Length > 8192) throw new StartupFailure("bridge_json_size");
            var parser = new StrictJson(new UTF8Encoding(false, true).GetString(raw));
            object value = parser.Value(0); parser.Space();
            if (parser.offset != parser.text.Length || !(value is Dictionary<string, object>)) throw new StartupFailure("bridge_json_invalid");
            return (Dictionary<string, object>)value;
        }
        void Space() { while (offset < text.Length && " \r\n\t".IndexOf(text[offset]) >= 0) offset++; }
        bool Take(char c) { Space(); if (offset < text.Length && text[offset] == c) { offset++; return true; } return false; }
        void Need(char c) { if (!Take(c)) throw new StartupFailure("bridge_json_invalid"); }
        string String()
        {
            Space(); int start = offset; Need('"');
            bool ended = false;
            while (offset < text.Length)
            {
                char c = text[offset++];
                if (c == '"') { ended = true; break; }
                if (c < 32) throw new StartupFailure("bridge_json_invalid");
                if (c == '\\')
                {
                    if (offset >= text.Length) throw new StartupFailure("bridge_json_invalid");
                    c = text[offset++];
                    if (c == 'u')
                    {
                        int first = UnicodeUnit();
                        if (first >= 0xD800 && first <= 0xDBFF)
                        {
                            if (offset + 2 > text.Length || text[offset++] != '\\' || text[offset++] != 'u') throw new StartupFailure("bridge_json_invalid");
                            int second = UnicodeUnit();
                            if (second < 0xDC00 || second > 0xDFFF) throw new StartupFailure("bridge_json_invalid");
                        }
                        else if (first >= 0xDC00 && first <= 0xDFFF) throw new StartupFailure("bridge_json_invalid");
                    }
                    else if ("\"\\/bfnrt".IndexOf(c) < 0) throw new StartupFailure("bridge_json_invalid");
                }
            }
            if (!ended) throw new StartupFailure("bridge_json_invalid");
            string result = new JavaScriptSerializer().Deserialize<string>(text.Substring(start, offset - start));
            new UTF8Encoding(false, true).GetBytes(result); return result;
        }
        int UnicodeUnit()
        {
            int start = offset;
            for (int i = 0; i < 4; i++) if (offset >= text.Length || !Uri.IsHexDigit(text[offset++])) throw new StartupFailure("bridge_json_invalid");
            return Convert.ToInt32(text.Substring(start, 4), 16);
        }
        object Value(int depth)
        {
            Space(); if (offset >= text.Length) throw new StartupFailure("bridge_json_invalid");
            if (text[offset] == '{')
            {
                if (depth >= 8) throw new StartupFailure("bridge_json_depth"); offset++;
                var result = new Dictionary<string, object>(StringComparer.Ordinal);
                if (Take('}')) return result;
                do { string key = String(); Need(':'); if (result.ContainsKey(key)) throw new StartupFailure("bridge_json_duplicate"); result.Add(key, Value(depth+1)); } while (Take(','));
                Need('}'); return result;
            }
            if (text[offset] == '[')
            {
                if (depth >= 8) throw new StartupFailure("bridge_json_depth"); offset++;
                var result = new List<object>(); if (Take(']')) return result;
                do { result.Add(Value(depth+1)); } while (Take(',')); Need(']'); return result;
            }
            if (text[offset] == '"') return String();
            foreach (string literal in new[] { "true", "false", "null" })
                if (text.Substring(offset).StartsWith(literal, StringComparison.Ordinal))
                { offset += literal.Length; if (literal == "null") return null; return literal == "true"; }
            int start = offset;
            if (text[offset] == '-') offset++;
            if (offset >= text.Length || text[offset] < '0' || text[offset] > '9') throw new StartupFailure("bridge_json_invalid");
            if (text[offset] == '0') offset++;
            else while (offset < text.Length && text[offset] >= '0' && text[offset] <= '9') offset++;
            int number;
            if (!int.TryParse(text.Substring(start, offset-start), System.Globalization.NumberStyles.AllowLeadingSign,
                System.Globalization.CultureInfo.InvariantCulture, out number)) throw new StartupFailure("bridge_json_integer");
            return number;
        }
    }
}
