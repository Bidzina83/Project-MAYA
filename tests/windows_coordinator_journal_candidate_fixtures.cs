using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Text;
using Microsoft.Win32.SafeHandles;
using ProjectMaya.WindowsRuntime;

internal static class CoordinatorJournalCandidateFixtures
{
    static readonly SecurityIdentifier Admin=new SecurityIdentifier("S-1-5-32-544"), SystemSid=new SecurityIdentifier("S-1-5-18"),
        Medium=new SecurityIdentifier("S-1-16-8192"), Other=new SecurityIdentifier("S-1-5-21-500");
    static readonly string Parent=new string('1',16), Volume=new string('2',8), FileId=new string('3',16);
    static readonly CoordinatorJournalBinding Binding=new CoordinatorJournalBinding(new string('a',32),new string('b',64),
        "windows:S-1-5-21-500",new string('c',32),new string('d',64),new string('e',64),new string('f',64),
        42,new string('0',32),1,100);
    static int checks;
    static void Check(bool ok) {checks++;if(!ok)throw new Exception("Assertion "+checks);}
    static void Rejected(Action action)
    {
        try {action();}
        catch(IOException) {Check(true);return;}
        Check(false);
    }

    static byte[] Descriptor(string fault=null)
    {
        var dacl=new RawAcl(2,2);
        var first=new CommonAce(fault=="inherit-ace"?AceFlags.Inherited:AceFlags.None,
            fault=="deny-ace"?AceQualifier.AccessDenied:AceQualifier.AccessAllowed,
            fault=="mask"?0x1f01fe:0x1f01ff,fault=="worker-ace"?Other:Admin,false,null);
        var second=new CommonAce(AceFlags.None,AceQualifier.AccessAllowed,0x1f01ff,fault=="duplicate"?Admin:SystemSid,false,null);
        dacl.InsertAce(0,fault=="reverse"?second:first);dacl.InsertAce(1,fault=="reverse"?first:second);
        if(fault=="extra")dacl.InsertAce(2,new CommonAce(AceFlags.None,AceQualifier.AccessAllowed,0x1f01ff,Other,false,null));
        var label=new RawAcl(2,1);var sid=fault=="low"?new SecurityIdentifier("S-1-16-4096"):Medium;
        byte[] labelBytes=new byte[4+sid.BinaryLength];labelBytes[0]=(byte)(fault=="label-mask"?3:1);sid.GetBinaryForm(labelBytes,4);
        label.InsertAce(0,new CustomAce((AceType)17,AceFlags.None,labelBytes));
        var flags=ControlFlags.DiscretionaryAclPresent|ControlFlags.SystemAclPresent|ControlFlags.SelfRelative;
        if(fault!="unprotected")flags|=ControlFlags.DiscretionaryAclProtected;
        var descriptor=new RawSecurityDescriptor(flags,fault=="owner"?Other:Admin,fault=="group"?Other:Admin,
            fault=="no-label"?null:label,fault=="null-dacl"?null:dacl);
        byte[] bytes=new byte[descriptor.BinaryLength];descriptor.GetBinaryForm(bytes,0);return bytes;
    }

    sealed class FakeHandle : ICoordinatorJournalHandle
    {
        internal readonly List<byte> Bytes=new List<byte>();
        internal readonly object Token=new object();
        internal string Fault;
        internal int Writes, Flushes, Reads, Closes;
        public CoordinatorJournalObservation Inspect()
        {
            return new CoordinatorJournalObservation(Fault=="token" || Fault=="swap" && Writes>0?new object():Token,
                Fault=="parent"?FileId:Parent,Fault=="volume"?"11111111":Volume,
                Fault=="id-after-write" && Writes>0?"4444444444444444":FileId,
                Descriptor(Fault=="descriptor-after-flush" && Flushes>0?"worker-ace":Fault),
                Bytes.Count,Fault=="link"?2:1,Fault!="unpinned",Fault!="remote",Fault!="directory",
                Fault=="reparse",Fault!="shared",Fault=="inherited",Fault!="existing");
        }
        public int Append(byte[] bytes)
        {Writes++;Bytes.AddRange(bytes);return Fault=="short-write"?bytes.Length-1:bytes.Length;}
        public bool Flush() {Flushes++;return Fault!="flush";}
        public byte[] ReadPrefix(int length)
        {
            Reads++;
            if(Fault=="short-read" && Writes>0)return new byte[0];
            if(Fault=="mutate-after-read" && Writes>0)Bytes.Add(0);
            byte[] result=Bytes.Take(length).ToArray();
            if(Fault=="wrong-bytes" && result.Length>0)result[0]^=1;
            return result;
        }
        public void Dispose() {Closes++;}
    }

    static CoordinatorJournalCandidate Create(FakeHandle handle)
    {
        return new CoordinatorJournalCandidate(Binding,Parent,Volume,(path,sddl)=>
        {
            Check(path==Path.Combine(ProductFiles.Root,Binding.Attempt,CoordinatorJournalCandidate.Leaf));
            Check(sddl==CoordinatorJournalCandidate.CreationDescriptor);return handle;
        });
    }

    sealed class FakeNative : ICoordinatorJournalNativeCalls
    {
        internal string Fault;
        internal readonly List<SafeFileHandle> Opens=new List<SafeFileHandle>(), Closes=new List<SafeFileHandle>();
        internal readonly List<string> Paths=new List<string>();
        internal readonly List<byte> Bytes=new List<byte>();
        internal int Writes, Flushes;
        internal readonly string Directory=Path.Combine(ProductFiles.Root,Binding.Attempt);
        internal string Leaf {get{return Path.Combine(Directory,CoordinatorJournalCandidate.Leaf);}}
        public bool LocalNtfs(string root) {Check(root==Path.GetPathRoot(Directory));return Fault!="volume-kind";}
        public SafeFileHandle Open(string path,uint access,uint share,uint disposition,uint flags,string descriptor)
        {
            bool file=path==Leaf;
            if(file)
                Check(access==0xc0020080 && share==0 && disposition==1 && flags==0x00200000 &&
                    descriptor==CoordinatorJournalCandidate.CreationDescriptor && Paths.Last()==Directory);
            else
                Check(access==0x20080 && share==3 && disposition==3 && flags==0x02200000 && descriptor==null &&
                    (Paths.Count==0?path==Path.GetPathRoot(Directory):Path.GetDirectoryName(path)==Paths.Last()));
            var handle=new SafeFileHandle(new IntPtr(file && Fault=="create-failed"?-1:Opens.Count+1),false);
            Opens.Add(handle);Paths.Add(path);return handle;
        }
        public CoordinatorNativeFile Inspect(SafeFileHandle handle)
        {
            int index=Opens.IndexOf(handle);Check(index>=0 && !handle.IsClosed);
            string name=Paths[index];bool file=name==Leaf;
            string id=file?FileId:name==Directory?Parent:(index+100).ToString("x16");
            if(Fault=="parent-id" && name==Directory || Fault=="ancestor-change" && !file && Writes>0 ||
                Fault=="file-id" && file && Writes>0)id="ffffffffffffffff";
            return new CoordinatorNativeFile(Fault=="path"?name+".other":name,Fault=="volume"?"ffffffff":Volume,id,
                file?Bytes.Count:0,Fault=="link" && file?2:1,Fault!="nondisk",!file,Fault=="reparse",Fault=="inherit");
        }
        void CheckLeaf(SafeFileHandle handle) {Check(Opens.Last()==handle && Paths.Last()==Leaf && !handle.IsClosed);}
        public byte[] Descriptor(SafeFileHandle handle) {CheckLeaf(handle);return CoordinatorJournalCandidateFixtures.Descriptor(Fault=="acl"?"worker-ace":null);}
        public int Write(SafeFileHandle handle,int offset,byte[] bytes)
        {CheckLeaf(handle);Check(offset==Bytes.Count);Writes++;Bytes.AddRange(bytes);return Fault=="short-write"?bytes.Length-1:bytes.Length;}
        public byte[] Read(SafeFileHandle handle,int offset,int count)
        {CheckLeaf(handle);Check(offset==0 && count==Bytes.Count);return Bytes.Take(Fault=="short-read"?Math.Max(0,count-1):count).ToArray();}
        public bool Flush(SafeFileHandle handle) {CheckLeaf(handle);Flushes++;return Fault!="flush";}
        public void Close(SafeFileHandle handle) {Closes.Add(handle);handle.Dispose();}
    }

    static CoordinatorJournalNativeTransport Open(FakeNative api)
    {return new CoordinatorJournalNativeTransport(Binding.Attempt,Parent,Volume,api.Leaf,CoordinatorJournalCandidate.CreationDescriptor,api);}

    static void NativeCases()
    {
        var good=new FakeNative();
        using(var journal=new CoordinatorJournalCandidate(Binding,Parent,Volume,(p,d)=>
            new CoordinatorJournalNativeTransport(Binding.Attempt,Parent,Volume,p,d,good)))
        {journal.Intent();journal.Confirmed();Check(good.Writes==2 && good.Flushes==2 && good.Closes.Count==0);}
        Check(good.Closes.SequenceEqual(good.Opens.AsEnumerable().Reverse()));
        Check(good.Opens.All(h=>h.IsClosed));

        var badPath=new FakeNative();
        Rejected(()=>new CoordinatorJournalNativeTransport(Binding.Attempt,Parent,Volume,badPath.Leaf+".other",
            CoordinatorJournalCandidate.CreationDescriptor,badPath));Check(badPath.Opens.Count==0);
        Rejected(()=>new CoordinatorJournalNativeTransport(Binding.Attempt,Parent,Volume,badPath.Leaf,"invalid",badPath));
        Check(badPath.Opens.Count==0);
        foreach(string fault in new[]{"volume-kind","parent-id","volume","reparse","inherit","path","nondisk","create-failed","link","acl","nonempty"})
        {
            var api=new FakeNative{Fault=fault};if(fault=="nonempty")api.Bytes.Add(1);
            Rejected(()=>Open(api));Check(api.Closes.SequenceEqual(api.Opens.AsEnumerable().Reverse()) && api.Writes==0);
        }
        foreach(string fault in new[]{"short-write","flush","short-read","ancestor-change","file-id"})
        {
            var api=new FakeNative();using(var transport=Open(api))
            {
                api.Fault=fault;
                Rejected(()=>{transport.Append(new byte[]{1});transport.Flush();transport.ReadPrefix(1);});
                int writes=api.Writes;api.Fault=null;Rejected(()=>transport.Append(new byte[]{2}));Check(api.Writes==writes);
            }
            Check(api.Closes.SequenceEqual(api.Opens.AsEnumerable().Reverse()));
        }
        var oversize=new FakeNative();using(var transport=Open(oversize))
        {Rejected(()=>transport.Append(new byte[16385]));Check(oversize.Writes==0);}
        var wrongLength=new FakeNative();using(var transport=Open(wrongLength))
        {Rejected(()=>transport.ReadPrefix(1));Check(wrongLength.Writes==0);}
    }

    static void Main()
    {
        Check(CoordinatorJournalDescriptor.Compare(Descriptor())==null);
        Check(CoordinatorJournalDescriptor.Compare(Descriptor("reverse"))==null);
        foreach(string fault in new[]{"owner","group","unprotected","null-dacl","worker-ace","duplicate","mask","extra",
            "inherit-ace","deny-ace","low","no-label","label-mask"})
            Check(CoordinatorJournalDescriptor.Compare(Descriptor(fault))!=null);
        byte[] valid=Descriptor();
        for(int i=0;i<valid.Length;i++)Check(CoordinatorJournalDescriptor.Compare(valid.Take(i).ToArray())!=null);

        foreach(string fault in new[]{"existing","parent","volume","link","unpinned","remote","directory","reparse","shared","inherited","worker-ace","nonempty"})
        {
            var h=new FakeHandle{Fault=fault};if(fault=="nonempty")h.Bytes.Add(1);
            Rejected(()=>Create(h));Check(h.Closes==1 && h.Writes==0);
        }
        foreach(string fault in new[]{"token","short-write","flush","swap","id-after-write","descriptor-after-flush","short-read","wrong-bytes","mutate-after-read"})
        {
            var h=new FakeHandle();using(var journal=Create(h))
            {
                h.Fault=fault;Rejected(journal.Intent);
                int before=h.Writes;h.Fault=null;Rejected(journal.Intent);Check(h.Writes==before);
            }
            Check(h.Closes==1);
        }
        foreach(bool stop in new[]{false,true})
        {
            var h=new FakeHandle{Fault="reverse"};var journal=Create(h);
            journal.Intent();if(stop)journal.PreEffectStop();else journal.Confirmed();
            var rows=Encoding.UTF8.GetString(h.Bytes.ToArray()).Split('\n');
            Check(rows.Length==3 && rows[2]=="");
            var first=StrictJson.Parse(Encoding.UTF8.GetBytes(rows[0]));var second=StrictJson.Parse(Encoding.UTF8.GetBytes(rows[1]));
            Check(first.Count==14 && second.Count==14 && (string)first["event"]=="release_intent" &&
                (string)second["event"]==(stop?"pre_effect_stop":"delivery_confirmed"));
            Check(first.Where(x=>x.Key!="event").All(x=>object.Equals(x.Value,second[x.Key])));
            Check((string)first["attempt"]==Binding.Attempt && (string)first["output_sha256"]==Binding.OutputHash);
            Rejected(journal.Confirmed);journal.Dispose();journal.Dispose();Rejected(journal.Intent);
            Check(h.Closes==1 && h.Writes==2 && h.Flushes==2);
        }
        var corrupt=new FakeHandle();using(var journal=Create(corrupt))
        {journal.Intent();corrupt.Bytes[0]^=1;Rejected(journal.Confirmed);Check(corrupt.Writes==1);}
        var noIntent=new FakeHandle();using(var journal=Create(noIntent))
        {Rejected(journal.Confirmed);Rejected(journal.Intent);Check(noIntent.Writes==0);}
        NativeCases();
        Console.WriteLine("Coordinator journal candidate and injected transport: "+checks+" assertions passed");
    }
}
