#if MAYA_FINAL_OUTPUT_INERT_FIXTURE
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Web.Script.Serialization;

namespace ProjectMaya.WindowsRuntime
{
    // Observations must come from the opened object, never a path-only lookup.
    internal interface ICoordinatorJournalHandle : IDisposable
    {
        CoordinatorJournalObservation Inspect();
        int Append(byte[] bytes);
        bool Flush();
        byte[] ReadPrefix(int length);
    }

    internal sealed class CoordinatorJournalObservation
    {
        internal readonly object Token;
        internal readonly string ParentId, VolumeId, FileId;
        internal readonly byte[] Descriptor;
        internal readonly int Length, Links;
        internal readonly bool ParentPinned, LocalNtfs, Regular, Reparse, Exclusive, Inheritable, CreatedNew;
        internal CoordinatorJournalObservation(object token, string parentId, string volumeId, string fileId,
            byte[] descriptor, int length, int links, bool parentPinned, bool localNtfs, bool regular,
            bool reparse, bool exclusive, bool inheritable, bool createdNew)
        {
            Token=token; ParentId=parentId; VolumeId=volumeId; FileId=fileId; Descriptor=descriptor;
            Length=length; Links=links; ParentPinned=parentPinned; LocalNtfs=localNtfs; Regular=regular;
            Reparse=reparse; Exclusive=exclusive; Inheritable=inheritable; CreatedNew=createdNew;
        }
    }

    internal sealed class CoordinatorJournalBinding
    {
        internal readonly string Attempt, Channel, Actor, Delivery, RequestHash, ResponseHash, OutputHash, Consent;
        internal readonly int OutputBytes;
        internal readonly long Epoch, Deadline;
        internal CoordinatorJournalBinding(string attempt, string channel, string actor, string delivery,
            string requestHash, string responseHash, string outputHash, int outputBytes, string consent, long epoch, long deadline)
        {
            foreach(string id in new[]{attempt,delivery,consent})
                if(!Hex(id,32))throw new ArgumentException("coordinator_journal_binding");
            foreach(string hash in new[]{channel,requestHash,responseHash,outputHash})
                if(!Hex(hash,64))throw new ArgumentException("coordinator_journal_binding");
            if(actor==null || actor.Length>192 || !Regex.IsMatch(actor,"\\Awindows:S-1-5-(?:[0-9]+-)*[0-9]+\\z") ||
                outputBytes<1 || outputBytes>4096 || epoch<0 || deadline<0)
                throw new ArgumentException("coordinator_journal_binding");
            Attempt=attempt; Channel=channel; Actor=actor; Delivery=delivery;
            RequestHash=requestHash; ResponseHash=responseHash; OutputHash=outputHash;
            OutputBytes=outputBytes; Consent=consent; Epoch=epoch; Deadline=deadline;
        }
        internal static bool Hex(string text,int length)
        {return text!=null && text.Length==length && Regex.IsMatch(text,"\\A[0-9a-f]+\\z");}
    }

    internal sealed class CoordinatorJournalCandidate : IDisposable
    {
        internal const string Leaf="final-output-journal.v1.jsonl";
        internal const string CreationDescriptor="O:BAG:BAD:P(A;;FA;;;BA)(A;;FA;;;SY)S:(ML;;NW;;;ME)";
        readonly object gate=new object(), token;
        readonly ICoordinatorJournalHandle handle;
        readonly CoordinatorJournalBinding binding;
        readonly string parent, volume, file;
        byte[] verified=new byte[0];
        int records;
        bool poisoned, disposed;

        // A future native transport must implement CREATE_NEW, share zero and no inheritance.
        // The fixture factory cannot choose the path or the creation descriptor.
        internal CoordinatorJournalCandidate(CoordinatorJournalBinding binding, string parentId, string volumeId,
            Func<string,string,ICoordinatorJournalHandle> createExclusive)
        {
            if(binding==null || createExclusive==null || !CoordinatorJournalBinding.Hex(parentId,16) ||
                !CoordinatorJournalBinding.Hex(volumeId,8)) throw new ArgumentException("coordinator_journal_parent");
            this.binding=binding; parent=parentId; volume=volumeId;
            handle=createExclusive(Path.Combine(ProductFiles.Root,binding.Attempt,Leaf),CreationDescriptor);
            Require(handle!=null,"coordinator_journal_open");
            try
            {
                var opened=handle.Inspect();
                Require(opened!=null && opened.CreatedNew && opened.Token!=null &&
                    CoordinatorJournalBinding.Hex(opened.FileId,16) && opened.FileId!=parent,"coordinator_journal_new");
                token=opened.Token; file=opened.FileId;
                Verify(opened,0);
                var bytes=handle.ReadPrefix(0);
                Require(bytes!=null && bytes.Length==0,"coordinator_journal_empty");
                Verify(handle.Inspect(),0);
            }
            catch {handle.Dispose();throw;}
        }

        static void Require(bool ok,string code) {if(!ok)throw new IOException(code);}
        void Verify(CoordinatorJournalObservation current,int expectedLength)
        {
            Require(current!=null && object.ReferenceEquals(token,current.Token) && current.ParentId==parent &&
                current.VolumeId==volume && current.FileId==file && current.Length==expectedLength &&
                current.ParentPinned && current.LocalNtfs && current.Regular && !current.Reparse &&
                current.Exclusive && !current.Inheritable && current.Links==1,"coordinator_journal_identity");
            Require(CoordinatorJournalDescriptor.Compare(current.Descriptor)==null,"coordinator_journal_descriptor");
        }

        byte[] Encode(string stage)
        {
            var fields=new Dictionary<string,object>{{"v",1},{"event",stage},{"attempt",binding.Attempt},
                {"channel",binding.Channel},{"actor",binding.Actor},{"delivery_id",binding.Delivery},
                {"request_sha256",binding.RequestHash},{"response_sha256",binding.ResponseHash},
                {"output_sha256",binding.OutputHash},{"output_bytes",binding.OutputBytes},
                {"destination",FinalOutputInertAdapter.Destination},{"consent_id",binding.Consent},
                {"epoch",binding.Epoch},{"deadline",binding.Deadline}};
            return new UTF8Encoding(false,true).GetBytes(new JavaScriptSerializer().Serialize(fields)+"\n");
        }

        internal void Intent() {Write("release_intent",0);}
        internal void Confirmed() {Write("delivery_confirmed",1);}
        internal void PreEffectStop() {Write("pre_effect_stop",1);}

        void Write(string stage,int expectedRecords)
        {
            lock(gate)
            {
                Require(!disposed && !poisoned,"coordinator_journal_unavailable");
                try
                {
                    Require(records==expectedRecords,"coordinator_journal_order");
                    byte[] next=Encode(stage);
                    Require(next.Length<=8192 && next.Length<=16384-verified.Length,"coordinator_journal_size");
                    Verify(handle.Inspect(),verified.Length);
                    // Detect same-length corruption of a previously verified prefix before append.
                    var previous=handle.ReadPrefix(verified.Length);
                    Require(previous!=null && verified.SequenceEqual(previous),"coordinator_journal_prefix");
                    Verify(handle.Inspect(),verified.Length);
                    Require(handle.Append((byte[])next.Clone())==next.Length,"coordinator_journal_short_write");
                    int length=verified.Length+next.Length;
                    Verify(handle.Inspect(),length);
                    Require(handle.Flush(),"coordinator_journal_flush");
                    Verify(handle.Inspect(),length);
                    byte[] expected=verified.Concat(next).ToArray();
                    byte[] actual=handle.ReadPrefix(length);
                    Require(actual!=null && expected.SequenceEqual(actual),"coordinator_journal_readback");
                    Verify(handle.Inspect(),length);
                    verified=expected;records++;
                }
                catch {poisoned=true;throw;}
            }
        }

        public void Dispose()
        {
            lock(gate)
            {
                if(disposed)return;
                disposed=true;handle.Dispose();
            }
        }
    }
}
#endif
