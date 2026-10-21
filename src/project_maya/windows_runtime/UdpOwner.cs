using System;
using System.Runtime.InteropServices;

namespace ProjectMaya.WindowsRuntime
{
    internal static class UdpOwner
    {
        [DllImport("iphlpapi.dll")] static extern uint GetExtendedUdpTable(IntPtr table, ref int size,
            bool order, uint family, uint tableClass, uint reserved);
        internal static bool Contains(byte[] table, int family, int port, int pid)
        {
            if (table == null || table.Length < 4 || pid <= 0 || port < 1024 || port > 65535 ||
                (family != 4 && family != 6)) return false;
            uint count = BitConverter.ToUInt32(table, 0); int width = family == 4 ? 12 : 28;
            if (count > (table.Length - 4) / width) return false;
            for (int i = 0; i < count; i++)
            {
                int at = 4 + i * width, offset = at + (family == 4 ? 4 : 20);
                bool loopback = true;
                for (int j = 0; j < (family == 4 ? 4 : 16); j++)
                    if (table[at + j] != (family == 4 ? (j == 0 ? 127 : j == 3 ? 1 : 0) : (j == 15 ? 1 : 0))) loopback = false;
                if (family == 6 && BitConverter.ToUInt32(table, at + 16) != 0) loopback = false;
                int found = table[offset] * 256 + table[offset + 1];
                if (loopback && found == port && BitConverter.ToUInt32(table, offset + 4) == (uint)pid) return true;
            }
            return false;
        }
        internal static bool Verified(int family, int port, int pid)
        {
            int size = 0; uint af = family == 4 ? 2u : 23u;
            uint code = GetExtendedUdpTable(IntPtr.Zero, ref size, false, af, 1, 0);
            if (code != 122 || size < 4 || size > 1024 * 1024) return false;
            int capacity = size; IntPtr memory = Marshal.AllocHGlobal(capacity);
            try
            {
                if (GetExtendedUdpTable(memory, ref size, false, af, 1, 0) != 0 || size < 4 || size > capacity) return false;
                var bytes = new byte[size]; Marshal.Copy(memory, bytes, 0, size);
                return Contains(bytes, family, port, pid);
            }
            finally { Marshal.FreeHGlobal(memory); }
        }
    }
}
