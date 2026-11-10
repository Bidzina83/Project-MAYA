using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Microsoft.Win32.SafeHandles;
using ProjectMaya.WindowsRuntime;

internal static class CoordinatorJournalNativeBaselineFixtures
{
    static readonly string Root=CoordinatorJournalScratchTarget.Root, Attempt=new string('a',32);
    static int checks;
    static void Check(bool ok) {checks++;if(!ok)throw new Exception("Assertion "+checks);}
    static void Reject(Action action)
    {try {action();}catch(IOException){Check(true);return;}Check(false);}

    sealed class Api : ICoordinatorJournalNativeCalls
    {
        readonly Dictionary<SafeFileHandle,string> paths=new Dictionary<SafeFileHandle,string>();
        internal readonly List<byte> Data=new List<byte>();
        internal readonly List<string> Report=new List<string>();
        internal string Fault;
        internal int Creates,Writes,Flushes,Reopens,Closes;
        readonly string directory=Path.Combine(Root,Attempt);
        string Leaf {get{return Path.Combine(directory,CoordinatorJournalCandidate.Leaf);}}
        SafeFileHandle writer;
        internal int Opens {get{return paths.Count;}}
        internal bool AllClosed {get{return paths.Keys.All(x=>x.IsClosed);}}
        public bool LocalNtfs(string path) {Check(path==@"C:\");return Fault!="remote";}
        internal bool Create(string path,string sddl)
        {
            Check(path==directory && sddl==CoordinatorJournalCandidate.CreationDescriptor);
            Check(paths.Any(x=>x.Value==Root && !x.Key.IsClosed));
            Creates++;return Fault!="collision";
        }
        public SafeFileHandle Open(string path,uint access,uint share,uint disposition,uint flags,string descriptor)
        {
            bool leaf=path==Leaf;
            if(leaf && disposition==1)
                Check(access==0xc0020080 && share==0 && flags==0x00200000 && descriptor==CoordinatorJournalCandidate.CreationDescriptor);
            else if(leaf)
            {
                Check(access==0x80020080 && share==0 && disposition==3 && flags==0x00200000 && descriptor==null && writer.IsClosed);
                Check(paths.Any(x=>x.Value==directory && !x.Key.IsClosed));Reopens++;
            }
            else
                Check((path==directory || Root.StartsWith(path.TrimEnd('\\')+"\\",StringComparison.OrdinalIgnoreCase) || path==Root) &&
                    access==0x20080 && share==3 && disposition==3 && flags==0x02200000 && descriptor==null);
            var handle=new SafeFileHandle(new IntPtr(paths.Count+1),false);paths.Add(handle,path);
            if(leaf && disposition==1)writer=handle;
            return handle;
        }
        public CoordinatorNativeFile Inspect(SafeFileHandle handle)
        {
            Check(paths.ContainsKey(handle) && !handle.IsClosed);
            string path=paths[handle];bool leaf=path==Leaf;
            string id=leaf?"000000000000000a":path==directory?"000000000000000b":"000000000000000c";
            if(leaf && Reopens>0 && Fault=="reopen-id")id="000000000000000d";
            return new CoordinatorNativeFile(path,"00000001",id,leaf?Data.Count:0,1,true,!leaf,
                Fault=="root-reparse" && path==Root,false);
        }
        public byte[] Descriptor(SafeFileHandle handle)
        {return CoordinatorJournalCandidateFixtures.Descriptor(Fault=="parent-acl" && paths[handle]==directory?"worker-ace":null);}
        public int Write(SafeFileHandle handle,int offset,byte[] bytes)
        {Check(handle==writer && !handle.IsClosed && offset==Data.Count);Writes++;Data.AddRange(bytes);return bytes.Length;}
        public byte[] Read(SafeFileHandle handle,int offset,int count)
        {
            Check(paths[handle]==Leaf && offset==0 && count==Data.Count && !handle.IsClosed);
            byte[] bytes=Data.ToArray();if(Reopens>0 && Fault=="reopen-bytes")bytes[0]^=1;return bytes;
        }
        public bool Flush(SafeFileHandle handle) {Check(handle==writer && !handle.IsClosed);Flushes++;return Fault!="flush";}
        public void Close(SafeFileHandle handle) {Check(!handle.IsClosed);Closes++;handle.Dispose();}
        internal string Run(string root=null)
        {return CoordinatorJournalNativeBaseline.Run(root??Root,Attempt,this,Create,Report.Add);}
    }

    static void Main()
    {
        var good=new Api();
        Check(good.Run().StartsWith("classification=pre_effect_stop_as_recorded volume=00000001 file=000000000000000a bytes="));
        Check(good.Creates==1 && good.Writes==2 && good.Flushes==2 && good.Reopens==1 && good.Closes==good.Opens && good.AllClosed);
        Check(good.Report.SequenceEqual(new[]{"stage=scratch_setup","attempt_target="+Path.Combine(Root,Attempt),"scratch="+Path.Combine(Root,Attempt),"stage=journal_create",
            "stage=journal_intent","stage=journal_pre_effect_stop","stage=writer_close","stage=read_only_reopen"}));
        foreach(string root in new[]{ProductFiles.Root,Path.Combine(Root,"other"),@"D:\MayaJournalProbeScratch"})
        {var api=new Api();Reject(()=>api.Run(root));Check(api.Opens==0 && api.Creates==0 && api.Writes==0);}
        foreach(string fault in new[]{"remote","root-reparse","collision","parent-acl","flush","reopen-id","reopen-bytes"})
        {
            var api=new Api{Fault=fault};Reject(()=>api.Run());Check(api.AllClosed && api.Closes==api.Opens);
            if(fault=="remote" || fault=="root-reparse")Check(api.Creates==0 && api.Writes==0);
            if(fault=="collision" || fault=="parent-acl")Check(api.Creates==1 && api.Writes==0);
            if(fault=="flush")Check(api.Writes==1 && api.Reopens==0);
            if(fault.StartsWith("reopen-"))Check(api.Writes==2 && api.Reopens==1);
        }
        var normal=new Api();Reject(()=>new CoordinatorJournalNativeTransport(Attempt,new string('b',16),"00000001",
            Path.Combine(Root,Attempt,CoordinatorJournalCandidate.Leaf),CoordinatorJournalCandidate.CreationDescriptor,normal));
        Check(normal.Opens==0 && normal.Creates==0 && normal.Writes==0);
        Console.WriteLine("Native baseline injected fixture: "+checks+" assertions passed");
    }
}
