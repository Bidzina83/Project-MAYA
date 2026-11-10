#if MAYA_FINAL_OUTPUT_INERT_FIXTURE && MAYA_JOURNAL_NATIVE_BASELINE
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Microsoft.Win32.SafeHandles;

namespace ProjectMaya.WindowsRuntime
{
    internal sealed class CoordinatorJournalScratchTarget : IDisposable
    {
        internal const string Root=@"C:\Users\Bidzina\AppData\Local\MayaJournalProbeScratch";
        internal const string OperatorSid="S-1-5-21-748951685-2862888470-2464618232-500";
        const uint Metadata=0x20080, NoFollow=0x00200000, DirectoryHandle=0x02000000;
        readonly ICoordinatorJournalNativeCalls calls;
        readonly List<SafeFileHandle> pins=new List<SafeFileHandle>();
        readonly List<CoordinatorNativeFile> identities=new List<CoordinatorNativeFile>();
        internal readonly string Attempt, Directory, ParentId, Volume;
        bool disposed;

        internal CoordinatorJournalScratchTarget(string root,string attempt,ICoordinatorJournalNativeCalls calls,
            Func<string,string,bool> createDirectory)
        {
            Require(root==Root && CoordinatorJournalBinding.Hex(attempt,32) && calls!=null && createDirectory!=null,
                "scratch_target");
            Require(!root.Equals(ProductFiles.Root,StringComparison.OrdinalIgnoreCase) &&
                !root.StartsWith(ProductFiles.Root+"\\",StringComparison.OrdinalIgnoreCase),"scratch_product_root");
            this.calls=calls; Attempt=attempt; Directory=Path.Combine(root,attempt);
            Require(calls.LocalNtfs(Path.GetPathRoot(root)),"scratch_volume");
            try
            {
                var chain=new Stack<string>();
                for(string part=root;part!=null;part=Path.GetDirectoryName(part))chain.Push(part);
                foreach(string part in chain)Pin(part);
                Volume=identities.Last().Volume;
                VerifyPins();
                Require(createDirectory(Directory,CoordinatorJournalCandidate.CreationDescriptor),"scratch_create_new");
                Pin(Directory);ParentId=identities.Last().Id;
                VerifyPins();
                Require(CoordinatorJournalDescriptor.Compare(calls.Descriptor(pins.Last()))==null,"scratch_parent_descriptor");
            }
            catch {Dispose();throw;}
        }

        internal string DirectoryFor(CoordinatorJournalBinding binding)
        {
            Require(binding!=null && binding.Attempt==Attempt,"scratch_attempt_binding");
            VerifyPins();return Directory;
        }
        static void Require(bool ok,string code) {if(!ok)throw new IOException(code);}
        static bool SamePath(string a,string b)
        {return a!=null && b!=null && a.TrimEnd('\\').Equals(b.TrimEnd('\\'),StringComparison.OrdinalIgnoreCase);}
        CoordinatorNativeFile CheckObject(SafeFileHandle handle,string path,bool directory)
        {
            Require(handle!=null && !handle.IsClosed && !handle.IsInvalid,"scratch_open");
            var info=calls.Inspect(handle);
            Require(info!=null && info.Disk && info.Directory==directory && !info.Reparse && !info.Inheritable &&
                SamePath(info.Path,path) && CoordinatorJournalBinding.Hex(info.Volume,8) &&
                CoordinatorJournalBinding.Hex(info.Id,16) && (directory || info.Links==1),"scratch_object");
            return info;
        }
        void Pin(string path)
        {
            var handle=calls.Open(path,Metadata,3,3,NoFollow|DirectoryHandle,null);
            if(handle!=null)pins.Add(handle);
            identities.Add(CheckObject(handle,path,true));
        }
        void VerifyPins()
        {
            Require(!disposed,"scratch_closed");
            for(int i=0;i<pins.Count;i++)
            {
                var original=identities[i];var now=CheckObject(pins[i],original.Path,true);
                Require(now.Id==original.Id && now.Volume==Volume,"scratch_ancestor_identity");
            }
        }

        internal byte[] ReadClosedJournal(string id,byte[] expected)
        {
            Require(CoordinatorJournalBinding.Hex(id,16) && expected!=null && expected.Length>0 && expected.Length<=16384,
                "scratch_reopen_binding");
            VerifyPins();
            string path=Path.Combine(Directory,CoordinatorJournalCandidate.Leaf);
            var handle=calls.Open(path,0x80020080,0,3,NoFollow,null);
            try
            {
                VerifyClosed(handle,path,id,expected.Length);
                byte[] actual=calls.Read(handle,0,expected.Length);
                Require(actual!=null && expected.SequenceEqual(actual),"scratch_reopen_bytes");
                VerifyClosed(handle,path,id,expected.Length);VerifyPins();
                return actual;
            }
            finally {if(handle!=null)calls.Close(handle);}
        }
        void VerifyClosed(SafeFileHandle handle,string path,string id,int length)
        {
            var info=CheckObject(handle,path,false);
            Require(info.Id==id && info.Volume==Volume && info.Length==length,"scratch_reopen_identity");
            Require(CoordinatorJournalDescriptor.Compare(calls.Descriptor(handle))==null,"scratch_reopen_descriptor");
        }

        public void Dispose()
        {
            if(disposed)return;
            disposed=true;
            Exception failure=null;
            for(int i=pins.Count-1;i>=0;i--)
                try {calls.Close(pins[i]);} catch(Exception error) {if(failure==null)failure=error;}
            if(failure!=null)throw new IOException("scratch_close",failure);
        }
    }
}
#endif
