#if HERMES_JOURNAL_DELETE_CHILD_SOURCE
using System;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;

namespace ProjectMaya.WindowsRuntime
{
    internal static class DeleteChildControlCreate
    {
        const string Leaf="delete-child-control";
        [StructLayout(LayoutKind.Sequential)] struct UnicodeString
        {internal ushort Length, MaximumLength;internal IntPtr Buffer;}
        [StructLayout(LayoutKind.Sequential)] struct ObjectAttributes
        {internal int Length;internal IntPtr RootDirectory, ObjectName;internal uint Attributes;
         internal IntPtr SecurityDescriptor, SecurityQualityOfService;}
        [StructLayout(LayoutKind.Sequential)] struct IoStatus
        {internal IntPtr Status;internal UIntPtr Information;}

        [DllImport("ntdll.dll",ExactSpelling=true)]
        static extern int NtCreateFile(out SafeFileHandle file,uint access,ref ObjectAttributes attributes,
            out IoStatus io,IntPtr size,uint fileAttributes,uint share,uint disposition,uint options,IntPtr ea,uint eaLength);

        internal static bool Created(int status,ulong information,bool validHandle)
        {return status==0 && information==2 && validHandle;}

        internal static bool Matches(CoordinatorNativeFile file,string path,string target)
        {
            return file!=null && CoordinatorJournalBinding.Hex(target,24) && file.Disk && file.Directory &&
                !file.Reparse && !file.Inheritable && file.Volume==target.Substring(0,8) &&
                CoordinatorJournalBinding.Hex(file.Id,16) && file.Volume+file.Id!=target &&
                String.Equals(file.Path,path,StringComparison.OrdinalIgnoreCase);
        }

        internal static SafeFileHandle New(SafeFileHandle parent,uint access)
        {return Create(parent,access,Leaf,IntPtr.Zero);}

#if MAYA_DELETE_CHILD_ACL_COMPARISON_INERT
        internal static SafeFileHandle NewScratchParent(SafeFileHandle root,string nonce,byte[] security)
        {
            if(!CoordinatorJournalBinding.Hex(nonce,32) || security==null || security.Length<20 || security.Length>16384)
                throw new ArgumentException("acl_comparison_scratch_policy");
            var pinned=GCHandle.Alloc(security,GCHandleType.Pinned);
            try {return Create(root,0x20080,"acl-comparison-"+nonce,pinned.AddrOfPinnedObject());}
            finally {pinned.Free();}
        }
#endif

        static SafeFileHandle Create(SafeFileHandle parent,uint access,string leaf,IntPtr security)
        {
            IntPtr name=IntPtr.Zero, descriptor=IntPtr.Zero;
            bool retained=false;
            try
            {
                parent.DangerousAddRef(ref retained);
                name=Marshal.StringToHGlobalUni(leaf);
                descriptor=Marshal.AllocHGlobal(Marshal.SizeOf(typeof(UnicodeString)));
                Marshal.StructureToPtr(new UnicodeString {Length=(ushort)(leaf.Length*2),
                    MaximumLength=(ushort)((leaf.Length+1)*2),Buffer=name},descriptor,false);
                var attributes=new ObjectAttributes{Length=Marshal.SizeOf(typeof(ObjectAttributes)),
                    RootDirectory=parent.DangerousGetHandle(),ObjectName=descriptor,Attributes=0x40,SecurityDescriptor=security};
                SafeFileHandle handle;
                IoStatus io;
                // FILE_CREATE | FILE_DIRECTORY_FILE; use the returned handle, never reopen by path.
                int status=NtCreateFile(out handle,access,ref attributes,out io,IntPtr.Zero,0,3,2,1,IntPtr.Zero,0);
                if(Created(status,io.Information.ToUInt64(),handle!=null && !handle.IsInvalid && !handle.IsClosed))
                    return handle;
                if(handle!=null)handle.Dispose();
                throw new StartupFailure("delete_child_control_exclusive_create");
            }
            finally
            {
                if(descriptor!=IntPtr.Zero)Marshal.FreeHGlobal(descriptor);
                if(name!=IntPtr.Zero)Marshal.FreeHGlobal(name);
                if(retained)parent.DangerousRelease();
            }
        }
    }
}
#endif
