using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Security.Principal;

namespace ProjectMaya.WindowsRuntime
{
    // Read-only, bounded retained-event snapshot. Never changes event collection.
    internal sealed class UdpEvidence : IDisposable
    {
        [StructLayout(LayoutKind.Sequential)] internal struct Blob { internal uint Size; internal IntPtr Data; }
        [StructLayout(LayoutKind.Explicit, Size = 136)] internal struct Header
        {
            [FieldOffset(0)] internal long Time;
            [FieldOffset(8)] internal uint Flags;
            [FieldOffset(12)] internal uint Version;
            [FieldOffset(16)] internal byte Protocol;
            [FieldOffset(20)] internal uint Local4;
            [FieldOffset(20)] internal ulong Local6Low;
            [FieldOffset(28)] internal ulong Local6High;
            [FieldOffset(36)] internal uint Remote4;
            [FieldOffset(36)] internal ulong Remote6Low;
            [FieldOffset(44)] internal ulong Remote6High;
            [FieldOffset(52)] internal ushort LocalPort;
            [FieldOffset(54)] internal ushort RemotePort;
            [FieldOffset(64)] internal Blob App;
            [FieldOffset(96)] internal IntPtr Package;
        }
        [StructLayout(LayoutKind.Sequential)] internal struct Event
        { internal Header Header; internal uint Type; internal IntPtr Data; }
        [StructLayout(LayoutKind.Sequential)] internal struct Drop
        {
            internal ulong Filter; internal ushort Layer;
            internal uint Reauth, Original, Current, Direction; internal int Loopback;
            internal Blob Switch; internal uint SourcePort, DestinationPort;
        }
        [StructLayout(LayoutKind.Sequential)] struct Template
        { internal long Start, End; internal uint Count; internal IntPtr Conditions; }
        [StructLayout(LayoutKind.Sequential)] struct Layer
        {
            internal Guid Key; internal IntPtr Name, Description; internal uint Flags, Count;
            internal IntPtr Fields; internal Guid Default; internal ushort Id;
        }
        [DllImport("fwpuclnt.dll")] static extern uint FwpmEngineOpen0(IntPtr server, uint auth, IntPtr identity, IntPtr session, out IntPtr engine);
        [DllImport("fwpuclnt.dll")] static extern uint FwpmEngineClose0(IntPtr engine);
        [DllImport("fwpuclnt.dll")] static extern uint FwpmEngineGetOption0(IntPtr engine, uint option, out IntPtr value);
        [DllImport("fwpuclnt.dll", CharSet = CharSet.Unicode)] static extern uint FwpmGetAppIdFromFileName0(string path, out IntPtr app);
        [DllImport("fwpuclnt.dll")] static extern uint FwpmLayerGetByKey0(IntPtr engine, ref Guid key, out IntPtr layer);
        [DllImport("fwpuclnt.dll")] static extern uint FwpmNetEventCreateEnumHandle0(IntPtr engine, ref Template template, out IntPtr enumeration);
        [DllImport("fwpuclnt.dll")] static extern uint FwpmNetEventEnum5(IntPtr engine, IntPtr enumeration, uint count, out IntPtr entries, out uint returned);
        [DllImport("fwpuclnt.dll")] static extern uint FwpmNetEventDestroyEnumHandle0(IntPtr engine, IntPtr enumeration);
        [DllImport("fwpuclnt.dll")] static extern void FwpmFreeMemory0(ref IntPtr memory);
        internal sealed class Match
        {
            internal int Family, LocalPort, RemotePort, LayerIndex;
            internal ulong Filter;
            internal long Time;
        }
        readonly List<Match> matches = new List<Match>();
        readonly List<Dictionary<string, object>> otherDrops = new List<Dictionary<string, object>>();
        readonly Dictionary<ulong, int> ids;
        readonly ushort[] layers = new ushort[6];
        readonly SecurityIdentifier package;
        readonly byte[] application;
        readonly long start;
        IntPtr engine;
        internal bool SnapshotExhausted { get; private set; }
        internal string Failure { get; private set; }
        internal UdpEvidence(string python, SecurityIdentifier package, Dictionary<ulong, int> ids)
        {
            this.package = package; this.ids = ids;
            if (IntPtr.Size != 8) throw new StartupFailure("udp_event_x64_required");
            try
            {
                Native.Check(FwpmEngineOpen0(IntPtr.Zero, 10, IntPtr.Zero, IntPtr.Zero, out engine), "udp_event_engine");
                VerifyEnabled();
                IntPtr memory;
                Native.Check(FwpmGetAppIdFromFileName0(python, out memory), "udp_event_appid");
                try { application = CopyBlob((Blob)Marshal.PtrToStructure(memory, typeof(Blob))); }
                finally { FwpmFreeMemory0(ref memory); }
                for (int i = 0; i < layers.Length; i++)
                {
                    Guid key = WindowsIsolation.NetworkLayer(i);
                    Native.Check(FwpmLayerGetByKey0(engine, ref key, out memory), "udp_event_layer");
                    try
                    {
                        var layer = (Layer)Marshal.PtrToStructure(memory, typeof(Layer));
                        if (layer.Key != key || layer.Id == 0) throw new StartupFailure("udp_event_layer_identity");
                        layers[i] = layer.Id;
                    }
                    finally { FwpmFreeMemory0(ref memory); }
                }
                start = DateTime.UtcNow.ToFileTimeUtc();
            }
            catch { Dispose(); throw; }
        }
        void VerifyEnabled()
        {
            IntPtr memory;
            Native.Check(FwpmEngineGetOption0(engine, 0, out memory), "udp_event_option");
            try
            {
                if (memory == IntPtr.Zero || Marshal.ReadInt32(memory) != 3 || Marshal.ReadInt32(memory, 8) != 1)
                    throw new StartupFailure("udp_event_collection_unavailable");
            }
            finally { FwpmFreeMemory0(ref memory); }
        }
        static byte[] CopyBlob(Blob blob)
        {
            if (blob.Size == 0 || blob.Size > 32768 || blob.Data == IntPtr.Zero) throw new StartupFailure("udp_event_blob");
            var bytes = new byte[blob.Size]; Marshal.Copy(blob.Data, bytes, 0, bytes.Length); return bytes;
        }
        internal static bool EqualBytes(byte[] left, byte[] right)
        {
            if (left == null || right == null || left.Length != right.Length) return false;
            for (int i = 0; i < left.Length; i++) if (left[i] != right[i]) return false;
            return true;
        }
        internal static bool Loopback(Header header)
        {
            if (header.Version == 0) return header.Local4 == 0x7f000001 && header.Remote4 == 0x7f000001;
            return header.Version == 1 && header.Local6Low == 0 && header.Remote6Low == 0 &&
                header.Local6High == 0x0100000000000000 && header.Remote6High == 0x0100000000000000;
        }
        internal static bool Eligible(Header header, Drop drop, int index, ushort layer, long start, long end)
        {
            return (header.Flags & 0x53f) == 0x53f && header.Protocol == 17 &&
                header.Time >= start && header.Time <= end && header.LocalPort != 0 && header.RemotePort != 0 &&
                Loopback(header) && drop.Loopback != 0 && drop.Layer == layer &&
                ((index < 2 && drop.Direction == 0x3901) || (index >= 4 && drop.Direction == 0x3900)) &&
                (header.Version == 0 ? index % 2 == 0 : index % 2 == 1);
        }
        internal void Collect(Dictionary<string, object> record)
        {
            IntPtr enumeration = IntPtr.Zero;
            long end = DateTime.UtcNow.ToFileTimeUtc();
            try
            {
                VerifyEnabled();
                var template = new Template { Start = start, End = end };
                Native.Check(FwpmNetEventCreateEnumHandle0(engine, ref template, out enumeration), "udp_event_enum_create");
                for (int page = 0; page < 4; page++)
                {
                    IntPtr entries = IntPtr.Zero; uint returned;
                    Native.Check(FwpmNetEventEnum5(engine, enumeration, 256, out entries, out returned), "udp_event_enum");
                    try
                    {
                        if (returned > 256 || (returned != 0 && entries == IntPtr.Zero)) throw new StartupFailure("udp_event_page");
                        for (int i = 0; i < returned; i++)
                        {
                            IntPtr pointer = Marshal.ReadIntPtr(entries, i * IntPtr.Size);
                            if (pointer == IntPtr.Zero) throw new StartupFailure("udp_event_null");
                            var item = (Event)Marshal.PtrToStructure(pointer, typeof(Event));
                            if (item.Type != 3 || item.Data == IntPtr.Zero) continue;
                            var drop = (Drop)Marshal.PtrToStructure(item.Data, typeof(Drop)); int index;
                            if ((item.Header.Flags & 0x53f) != 0x53f || item.Header.Protocol != 17 ||
                                item.Header.Time < start || item.Header.Time > end || !Loopback(item.Header)) continue;
                            if (item.Header.Package == IntPtr.Zero || !new SecurityIdentifier(item.Header.Package).Equals(package) ||
                                !EqualBytes(application, CopyBlob(item.Header.App))) continue;
                            if (matches.Count + otherDrops.Count == 64) throw new StartupFailure("udp_event_match_limit");
                            if (!ids.TryGetValue(drop.Filter, out index))
                            {
                                otherDrops.Add(new Dictionary<string, object> {
                                    {"family", item.Header.Version == 0 ? 4 : 6}, {"local_port", item.Header.LocalPort},
                                    {"remote_port", item.Header.RemotePort}, {"filter_id", drop.Filter.ToString()},
                                    {"layer_id", drop.Layer}, {"direction", drop.Direction}, {"maya_owned", false} });
                                continue;
                            }
                            if (!Eligible(item.Header, drop, index, layers[index], start, end)) continue;
                            matches.Add(new Match { Family = item.Header.Version == 0 ? 4 : 6, LocalPort = item.Header.LocalPort,
                                RemotePort = item.Header.RemotePort, Filter = drop.Filter, LayerIndex = index, Time = item.Header.Time });
                        }
                        if (returned < 256) { SnapshotExhausted = true; break; }
                    }
                    finally { if (entries != IntPtr.Zero) FwpmFreeMemory0(ref entries); }
                }
                if (!SnapshotExhausted) Failure = "udp_event_page_limit";
            }
            catch (Exception error) { Failure = ProtectedPython.FailureCode(error); SnapshotExhausted = false; }
            finally
            {
                if (enumeration != IntPtr.Zero && FwpmNetEventDestroyEnumHandle0(engine, enumeration) != 0)
                { Failure = "udp_event_enum_close"; SnapshotExhausted = false; }
            }
            var rows = new List<Dictionary<string, object>>();
            foreach (Match match in matches) rows.Add(new Dictionary<string, object> {
                {"family", match.Family}, {"local_port", match.LocalPort}, {"remote_port", match.RemotePort},
                {"filter_id", match.Filter.ToString()}, {"layer_guid", WindowsIsolation.NetworkLayer(match.LayerIndex).ToString()},
                {"timestamp_filetime", match.Time.ToString()} });
            record["screen_udp_drop_events"] = rows;
            record["screen_udp_other_filter_drops_diagnostic_only"] = otherDrops;
            record["screen_udp_snapshot_exhausted"] = SnapshotExhausted;
            record["screen_udp_event_reason"] = Failure;
            record["screen_udp_event_retention_loss_known"] = false;
        }
        internal bool Denied(int family, bool receive, int local, int remote)
        {
            return MatchTuple(matches, SnapshotExhausted, Failure, family, receive, local, remote);
        }
        internal static bool MatchTuple(IEnumerable<Match> matches, bool exhausted, string failure, int family, bool receive, int local, int remote)
        {
            if (!exhausted || failure != null || local < 1024 || remote < 1 || remote > 65535 ||
                local > 65535 || (family != 4 && family != 6)) return false;
            int layer = (receive ? 4 : 0) + (family == 6 ? 1 : 0);
            foreach (Match match in matches)
                if (match.Family == family && match.LayerIndex == layer && match.LocalPort == local && match.RemotePort == remote) return true;
            return false;
        }
        public void Dispose()
        {
            if (engine != IntPtr.Zero) { uint code = FwpmEngineClose0(engine); engine = IntPtr.Zero; Native.Check(code, "udp_event_engine_close"); }
        }
    }
}
