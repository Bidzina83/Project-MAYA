using System;
using System.Collections.Generic;
using System.Collections.Concurrent;
using System.Diagnostics;
using System.IO;
using System.Text;
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
        bool failed;
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
            catch { failed = true; throw new StartupFailure("bridge_channel_failed"); }
        }
        internal Dictionary<string, object> Read(int waitMilliseconds)
        {
            return Bound(delegate {
                int first = input.ReadByte(); if (first < 0) throw new EndOfStreamException();
                var read = Task.Factory.StartNew(delegate {
                    byte[] tail = new byte[3]; Exact(input, tail);
                    byte[] header = new byte[] { (byte)first, tail[0], tail[1], tail[2] };
                    uint size = BitConverter.ToUInt32(header, 0);
                    if (size < 1 || size > 8192 || readBytes + 4L + size > 131072) throw new StartupFailure("bridge_frame_size");
                    readBytes += checked((int)size + 4); byte[] raw = new byte[size]; Exact(input, raw);
                    return StrictJson.Parse(raw);
                });
                pending.Add(read);
                if (!read.Wait(1000)) throw new StartupFailure("bridge_incomplete_frame_timeout");
                return read.Result;
            }, waitMilliseconds);
        }
        static void Exact(Stream stream, byte[] data)
        {
            for (int offset = 0; offset < data.Length; )
            { int count = stream.Read(data, offset, data.Length - offset); if (count <= 0) throw new EndOfStreamException(); offset += count; }
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
            // Jobs must be stopped before this join: no blocked reader is abandoned.
            foreach (Task task in pending.ToArray())
                try { if (!task.Wait(1000)) throw new StartupFailure("bridge_pipe_cleanup_uncertain"); }
                catch (AggregateException) { }
            input.Dispose(); output.Dispose(); failed = true;
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
