#if (MAYA_DELETE_CHILD_CONTROL_INERT && MAYA_FINAL_OUTPUT_INERT_FIXTURE) || HERMES_JOURNAL_DELETE_CHILD_SOURCE
using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using Microsoft.Win32.SafeHandles;

namespace ProjectMaya.WindowsRuntime
{
    // The caller owns a verified, non-inheritable directory handle with READ_CONTROL and WRITE_DAC.
    // No path is reopened and no security descriptor field other than the DACL is submitted.
    internal sealed class DeleteChildControlWindowsHandle : IDeleteChildControlHandle
    {
        readonly SafeFileHandle handle;
        readonly string path, identity;
        readonly CoordinatorJournalWindowsCalls calls=new CoordinatorJournalWindowsCalls();

        [DllImport("advapi32.dll",ExactSpelling=true)]
        static extern uint SetSecurityInfo(SafeFileHandle file,uint objectType,uint information,
            IntPtr owner,IntPtr group,IntPtr dacl,IntPtr sacl);

        internal DeleteChildControlWindowsHandle(SafeFileHandle handle,string path,string identity)
        {
            this.handle=handle;
            this.path=path;
            this.identity=identity;
            Require(CoordinatorJournalBinding.Hex(identity,24) && Identity()==identity);
        }

        static void Require(bool ok)
        {if(!ok)throw new IOException("delete_child_control_handle");}

        public string Identity()
        {
            Require(handle!=null && !handle.IsInvalid && !handle.IsClosed);
            var file=calls.Inspect(handle);
            Require(file.Disk && file.Directory && !file.Reparse && !file.Inheritable &&
                String.Equals(file.Path,path,StringComparison.OrdinalIgnoreCase));
            return file.Volume+file.Id;
        }

        public byte[] ReadDescriptor()
        {
            Require(Identity()==identity);
            return calls.Descriptor(handle);
        }

        public void WriteDescriptor(byte[] descriptor)
        {
            Require(Identity()==identity);
            ProductFiles.NoLinks(path);
            Require(Directory.GetFileSystemEntries(path).Length==0);
            var current=new RawSecurityDescriptor(calls.Descriptor(handle),0);
            var desired=new RawSecurityDescriptor(descriptor,0);
            Require(current.DiscretionaryAcl!=null && desired.DiscretionaryAcl!=null &&
                current.Owner.Equals(desired.Owner) && current.Group.Equals(desired.Group) &&
                current.ControlFlags==desired.ControlFlags && SameAcl(current.SystemAcl,desired.SystemAcl));
            var bytes=new byte[desired.DiscretionaryAcl.BinaryLength];
            desired.DiscretionaryAcl.GetBinaryForm(bytes,0);
            var pinned=GCHandle.Alloc(bytes,GCHandleType.Pinned);
            try
            {
                Require(Identity()==identity);
                if(SetSecurityInfo(handle,1,4,IntPtr.Zero,IntPtr.Zero,pinned.AddrOfPinnedObject(),IntPtr.Zero)!=0)
                    throw new IOException("delete_child_control_dacl_write");
            }
            finally {pinned.Free();}
        }

        static bool SameAcl(RawAcl left,RawAcl right)
        {
            if(left==null || right==null)return left==right;
            if(left.BinaryLength!=right.BinaryLength)return false;
            var a=new byte[left.BinaryLength];
            var b=new byte[right.BinaryLength];
            left.GetBinaryForm(a,0);
            right.GetBinaryForm(b,0);
            for(int i=0;i<a.Length;i++)if(a[i]!=b[i])return false;
            return true;
        }
    }
}
#endif
