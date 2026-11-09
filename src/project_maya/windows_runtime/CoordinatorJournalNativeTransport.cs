#if MAYA_FINAL_OUTPUT_INERT_FIXTURE
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32.SafeHandles;

namespace ProjectMaya.WindowsRuntime
{
    internal interface ICoordinatorJournalNativeCalls
    {
        bool LocalNtfs(string root);
        SafeFileHandle Open(string path,uint access,uint share,uint disposition,uint flags,string descriptor);
        CoordinatorNativeFile Inspect(SafeFileHandle handle);
        byte[] Descriptor(SafeFileHandle handle);
        int Write(SafeFileHandle handle,int offset,byte[] bytes);
        byte[] Read(SafeFileHandle handle,int offset,int count);
        bool Flush(SafeFileHandle handle);
        void Close(SafeFileHandle handle);
    }

    internal sealed class CoordinatorNativeFile
    {
        internal readonly string Path, Volume, Id;
        internal readonly int Length, Links;
        internal readonly bool Disk, Directory, Reparse, Inheritable;
        internal CoordinatorNativeFile(string path,string volume,string id,int length,int links,bool disk,
            bool directory,bool reparse,bool inheritable)
        {
            Path=path;Volume=volume;Id=id;Length=length;Links=links;Disk=disk;
            Directory=directory;Reparse=reparse;Inheritable=inheritable;
        }
    }

    // Source candidate only; no launcher constructs this transport.
    internal sealed class CoordinatorJournalNativeTransport : ICoordinatorJournalHandle
    {
        const int Limit=16384;
        const uint MetadataAccess=0x20080, JournalAccess=0xc0020080, NoFollow=0x00200000, DirectoryHandle=0x02000000;
        readonly object gate=new object();
        readonly ICoordinatorJournalNativeCalls calls;
        readonly List<SafeFileHandle> owned=new List<SafeFileHandle>();
        readonly List<CoordinatorNativeFile> ancestors=new List<CoordinatorNativeFile>();
        readonly string path, parentId, volumeId, fileId;
        readonly SafeFileHandle file;
        bool failed, disposed;

        internal CoordinatorJournalNativeTransport(string attempt,string parentId,string volumeId,string path,
            string descriptor,ICoordinatorJournalNativeCalls calls)
        {
            if(!CoordinatorJournalBinding.Hex(attempt,32) || !CoordinatorJournalBinding.Hex(parentId,16) ||
                !CoordinatorJournalBinding.Hex(volumeId,8) || calls==null)throw new ArgumentException("journal_native_binding");
            string directory=Path.Combine(ProductFiles.Root,attempt);
            Require(string.Equals(path,Path.Combine(directory,CoordinatorJournalCandidate.Leaf),StringComparison.Ordinal) &&
                descriptor==CoordinatorJournalCandidate.CreationDescriptor,"journal_native_path");
            this.path=path;this.parentId=parentId;this.volumeId=volumeId;this.calls=calls;
            string root=Path.GetPathRoot(directory);
            Require(root!=null && root.Length==3 && root[1]==':' && root[2]=='\\' && calls.LocalNtfs(root),"journal_native_volume");
            try
            {
                var chain=new Stack<string>();
                for(string part=directory;part!=null;part=Path.GetDirectoryName(part))chain.Push(part);
                foreach(string part in chain)
                {
                    var handle=Open(part,MetadataAccess,3,3,NoFollow|DirectoryHandle,null);
                    ancestors.Add(CheckObject(handle,part,true));
                }
                Require(ancestors[ancestors.Count-1].Id==parentId,"journal_native_parent");
                file=Open(path,JournalAccess,0,1,NoFollow,descriptor);
                var opened=CheckObject(file,path,false);
                Require(opened.Length==0 && opened.Id!=parentId,"journal_native_new");
                fileId=opened.Id;
                Inspect();
            }
            catch {Dispose();throw;}
        }

        static void Require(bool ok,string code) {if(!ok)throw new IOException(code);}
        SafeFileHandle Open(string name,uint access,uint share,uint disposition,uint flags,string descriptor)
        {
            var handle=calls.Open(name,access,share,disposition,flags,descriptor);
            if(handle!=null)owned.Add(handle);
            Require(handle!=null && !handle.IsInvalid && !handle.IsClosed,"journal_native_open");
            return handle;
        }
        static string Normalize(string name) {return name==null?null:name.TrimEnd('\\');}
        CoordinatorNativeFile CheckObject(SafeFileHandle handle,string expected,bool directory)
        {
            Require(handle!=null && !handle.IsClosed && !handle.IsInvalid,"journal_native_handle");
            var current=calls.Inspect(handle);
            Require(current!=null && current.Disk && current.Directory==directory && !current.Reparse && !current.Inheritable &&
                current.Volume==volumeId && CoordinatorJournalBinding.Hex(current.Id,16) &&
                string.Equals(Normalize(current.Path),Normalize(expected),StringComparison.OrdinalIgnoreCase) &&
                (directory || current.Links==1 && current.Length>=0 && current.Length<=Limit),"journal_native_identity");
            return current;
        }
        CoordinatorJournalObservation InspectOwned()
        {
            Require(!disposed && !failed,"journal_native_unavailable");
            for(int i=0;i<ancestors.Count;i++)
                Require(CheckObject(owned[i],ancestors[i].Path,true).Id==ancestors[i].Id,"journal_native_ancestor_changed");
            var current=CheckObject(file,path,false);
            Require(current.Id==fileId,"journal_native_file_changed");
            byte[] descriptor=calls.Descriptor(file);
            Require(CoordinatorJournalDescriptor.Compare(descriptor)==null,"journal_native_descriptor");
            return new CoordinatorJournalObservation(file,parentId,volumeId,fileId,descriptor,current.Length,current.Links,
                true,true,true,false,true,false,true);
        }
        T Guard<T>(Func<T> work)
        {
            lock(gate)
            {
                try {return work();}
                catch {failed=true;throw;}
            }
        }
        public CoordinatorJournalObservation Inspect() {return Guard(InspectOwned);}
        public int Append(byte[] bytes)
        {
            return Guard(()=>{
                int length=InspectOwned().Length;
                Require(bytes!=null && bytes.Length>0 && bytes.Length<=Limit-length,"journal_native_write_bounds");
                int n=calls.Write(file,length,(byte[])bytes.Clone());
                Require(n==bytes.Length && InspectOwned().Length==length+n,"journal_native_short_write");
                return n;
            });
        }
        public bool Flush()
        {
            return Guard(()=>{
                int length=InspectOwned().Length;
                Require(calls.Flush(file) && InspectOwned().Length==length,"journal_native_flush");
                return true;
            });
        }
        public byte[] ReadPrefix(int length)
        {
            return Guard(()=>{
                Require(length>=0 && length<=Limit && InspectOwned().Length==length,"journal_native_read_bounds");
                byte[] data=calls.Read(file,0,length);
                Require(data!=null && data.Length==length && InspectOwned().Length==length,"journal_native_short_read");
                return (byte[])data.Clone();
            });
        }
        public void Dispose()
        {
            lock(gate)
            {
                if(disposed)return;
                disposed=true;
                Exception failure=null;
                for(int i=owned.Count-1;i>=0;i--)
                    try {calls.Close(owned[i]);} catch(Exception error) {if(failure==null)failure=error;}
                if(failure!=null)throw new IOException("journal_native_close",failure);
            }
        }
    }

    // Native calls are compiled, never invoked by the injected fixture.
    internal sealed class CoordinatorJournalWindowsCalls : ICoordinatorJournalNativeCalls
    {
        const uint DescriptorFields=0x17;
        [StructLayout(LayoutKind.Sequential)] struct Attributes {internal uint Size;internal IntPtr Descriptor;internal int Inherit;}
        [StructLayout(LayoutKind.Sequential)] struct FileInfo
        {
            internal uint Attributes;
            internal System.Runtime.InteropServices.ComTypes.FILETIME Creation,Access,Write;
            internal uint Volume,SizeHigh,SizeLow,Links,IdHigh,IdLow;
        }
        [DllImport("kernel32.dll",CharSet=CharSet.Unicode,ExactSpelling=true,SetLastError=true)] static extern SafeFileHandle CreateFileW(
            string path,uint access,uint share,IntPtr attributes,uint disposition,uint flags,IntPtr template);
        [DllImport("kernel32.dll",CharSet=CharSet.Unicode,ExactSpelling=true)] static extern uint GetDriveTypeW(string root);
        [DllImport("kernel32.dll")] static extern uint GetFileType(SafeFileHandle handle);
        [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetHandleInformation(SafeFileHandle handle,out uint flags);
        [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetFileInformationByHandle(SafeFileHandle handle,out FileInfo info);
        [DllImport("kernel32.dll",CharSet=CharSet.Unicode,ExactSpelling=true,SetLastError=true)] static extern uint GetFinalPathNameByHandleW(
            SafeFileHandle handle,StringBuilder path,uint length,uint flags);
        [DllImport("kernel32.dll",SetLastError=true)] static extern bool SetFilePointerEx(SafeFileHandle handle,long offset,out long position,uint method);
        [DllImport("kernel32.dll",SetLastError=true)] static extern bool WriteFile(SafeFileHandle handle,byte[] data,int size,out int written,IntPtr overlap);
        [DllImport("kernel32.dll",SetLastError=true)] static extern bool ReadFile(SafeFileHandle handle,[Out] byte[] data,int size,out int read,IntPtr overlap);
        [DllImport("kernel32.dll",SetLastError=true)] static extern bool FlushFileBuffers(SafeFileHandle handle);
        [DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr value);
        [DllImport("advapi32.dll",CharSet=CharSet.Unicode,ExactSpelling=true,SetLastError=true)] static extern bool ConvertStringSecurityDescriptorToSecurityDescriptorW(
            string text,uint revision,out IntPtr descriptor,out uint size);
        [DllImport("advapi32.dll")] static extern uint GetSecurityInfo(SafeFileHandle handle,int kind,uint fields,
            out IntPtr owner,out IntPtr group,out IntPtr dacl,out IntPtr sacl,out IntPtr descriptor);
        [DllImport("advapi32.dll")] static extern bool IsValidSecurityDescriptor(IntPtr descriptor);
        [DllImport("advapi32.dll")] static extern uint GetSecurityDescriptorLength(IntPtr descriptor);

        static void Require(bool ok,string code) {if(!ok)throw new IOException(code);}
        static string Hex(uint value) {return value.ToString("x8",CultureInfo.InvariantCulture);}
        public bool LocalNtfs(string root) {return GetDriveTypeW(root)==3 && new DriveInfo(root).DriveFormat=="NTFS";}
        public SafeFileHandle Open(string path,uint access,uint share,uint disposition,uint flags,string descriptor)
        {
            IntPtr security=IntPtr.Zero, attributes=IntPtr.Zero;
            try
            {
                if(descriptor!=null)
                {
                    uint size;Require(ConvertStringSecurityDescriptorToSecurityDescriptorW(descriptor,1,out security,out size),"journal_native_sddl");
                    int length=Marshal.SizeOf(typeof(Attributes));attributes=Marshal.AllocHGlobal(length);
                    Marshal.StructureToPtr(new Attributes{Size=(uint)length,Descriptor=security,Inherit=0},attributes,false);
                }
                return CreateFileW(path,access,share,attributes,disposition,flags,IntPtr.Zero);
            }
            finally {if(attributes!=IntPtr.Zero)Marshal.FreeHGlobal(attributes);if(security!=IntPtr.Zero)LocalFree(security);}
        }
        public CoordinatorNativeFile Inspect(SafeFileHandle handle)
        {
            FileInfo info;uint flags;
            Require(GetFileInformationByHandle(handle,out info),"journal_native_file_info");
            Require(GetHandleInformation(handle,out flags),"journal_native_handle_info");
            var path=new StringBuilder(32768);uint n=GetFinalPathNameByHandleW(handle,path,(uint)path.Capacity,0);
            string name=path.ToString();
            Require(n>0 && n<path.Capacity && name.StartsWith("\\\\?\\",StringComparison.Ordinal) &&
                !name.StartsWith("\\\\?\\UNC\\",StringComparison.OrdinalIgnoreCase),"journal_native_final_path");
            int length=info.SizeHigh==0 && info.SizeLow<=int.MaxValue?(int)info.SizeLow:-1;
            return new CoordinatorNativeFile(name.Substring(4),Hex(info.Volume),Hex(info.IdHigh)+Hex(info.IdLow),length,
                checked((int)info.Links),GetFileType(handle)==1,(info.Attributes&16)!=0,(info.Attributes&1024)!=0,(flags&1)!=0);
        }
        public byte[] Descriptor(SafeFileHandle handle)
        {
            IntPtr owner,group,dacl,sacl,raw;
            Require(GetSecurityInfo(handle,1,DescriptorFields,out owner,out group,out dacl,out sacl,out raw)==0,"journal_native_security_info");
            try
            {
                Require(raw!=IntPtr.Zero && IsValidSecurityDescriptor(raw),"journal_native_security_invalid");
                uint size=GetSecurityDescriptorLength(raw);Require(size>=20 && size<=16384,"journal_native_security_bounds");
                byte[] data=new byte[(int)size];Marshal.Copy(raw,data,0,data.Length);return data;
            }
            finally {if(raw!=IntPtr.Zero)LocalFree(raw);}
        }
        static void Seek(SafeFileHandle handle,int offset)
        {long actual;Require(SetFilePointerEx(handle,offset,out actual,0) && actual==offset,"journal_native_seek");}
        public int Write(SafeFileHandle handle,int offset,byte[] bytes)
        {Seek(handle,offset);int n;Require(WriteFile(handle,bytes,bytes.Length,out n,IntPtr.Zero),"journal_native_write");return n;}
        public byte[] Read(SafeFileHandle handle,int offset,int count)
        {
            Seek(handle,offset);byte[] bytes=new byte[count];int n;
            if(count!=0)Require(ReadFile(handle,bytes,count,out n,IntPtr.Zero) && n==count,"journal_native_read");
            return bytes;
        }
        public bool Flush(SafeFileHandle handle) {return FlushFileBuffers(handle);}
        public void Close(SafeFileHandle handle) {handle.Dispose();}
    }
}
#endif
