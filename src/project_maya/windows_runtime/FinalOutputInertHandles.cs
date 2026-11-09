#if MAYA_FINAL_OUTPUT_INERT_FIXTURE
using System;
using System.IO;
using System.Linq;

namespace ProjectMaya.WindowsRuntime
{
    // These types carry injected observations only. No method opens a Windows handle.
    internal sealed class InertOpenedIdentity
    {
        internal readonly string Parent, Volume, File, Descriptor;
        internal InertOpenedIdentity(string parent, string volume, string file, string descriptor)
        {
            if(new[]{parent,volume,file,descriptor}.Any(string.IsNullOrEmpty)) throw new ArgumentException();
            Parent=parent; Volume=volume; File=file; Descriptor=descriptor;
        }
        internal bool Matches(InertOpenedIdentity other)
        {
            return other!=null && Parent==other.Parent && Volume==other.Volume && File==other.File && Descriptor==other.Descriptor;
        }
    }

    internal sealed class InertOpenedObservation
    {
        internal readonly object Handle;
        internal readonly InertOpenedIdentity Identity;
        internal readonly int Length, Links;
        internal readonly bool Regular, Local, Reparse, ParentPinned, Exclusive, Inheritable, CreatedNew;
        internal InertOpenedObservation(object handle, InertOpenedIdentity identity, int length, int links=1,
            bool regular=true, bool local=true, bool reparse=false, bool parentPinned=true,
            bool exclusive=true, bool inheritable=false, bool createdNew=false)
        {
            Handle=handle; Identity=identity; Length=length; Links=links; Regular=regular; Local=local; Reparse=reparse;
            ParentPinned=parentPinned; Exclusive=exclusive; Inheritable=inheritable; CreatedNew=createdNew;
        }
        internal bool Matches(object handle, InertOpenedIdentity identity, int length)
        {
            return handle!=null && object.ReferenceEquals(Handle,handle) && identity.Matches(Identity) && Length==length &&
                Links==1 && Regular && Local && !Reparse && ParentPinned && Exclusive && !Inheritable;
        }
    }

    internal sealed class InertProtectedJournal
    {
        readonly object gate=new object(), handle;
        readonly InertOpenedIdentity identity;
        readonly Func<object,InertOpenedObservation> inspect;
        readonly Func<object,byte[],int> write;
        readonly Func<object,bool> flush;
        readonly Func<object,int,byte[]> read;
        int length;
        bool failed;

        internal InertProtectedJournal(object handle, InertOpenedIdentity identity, Func<object,InertOpenedObservation> inspect,
            Func<object,byte[],int> write, Func<object,bool> flush, Func<object,int,byte[]> read)
        {
            if(identity==null || inspect==null || write==null || flush==null || read==null) throw new ArgumentNullException();
            this.handle=handle; this.identity=identity; this.inspect=inspect; this.write=write; this.flush=flush; this.read=read;
            var opened=Inspect(0);
            if(!opened.CreatedNew) throw new IOException("inert_journal_not_new");
        }
        InertOpenedObservation Inspect(int size)
        {
            if(failed) throw new IOException("inert_journal_poisoned");
            var observation=inspect(handle);
            if(observation==null || !observation.Matches(handle,identity,size)) throw new IOException("inert_journal_identity");
            return observation;
        }
        internal void AppendAndFlush(byte[] bytes)
        {
            lock(gate)
            {
                try
                {
                    if(bytes==null || bytes.Length==0 || bytes.Length>16384-length) throw new IOException("inert_journal_bounds");
                    Inspect(length);
                    int next=length+bytes.Length;
                    if(write(handle,(byte[])bytes.Clone())!=bytes.Length) throw new IOException("inert_journal_short_write");
                    Inspect(next);
                    if(!flush(handle)) throw new IOException("inert_journal_flush");
                    Inspect(next);
                    length=next;
                }
                catch { failed=true; throw; }
            }
        }
        internal byte[] Read()
        {
            lock(gate)
            {
                try
                {
                    Inspect(length);
                    byte[] bytes=read(handle,length);
                    if(bytes==null || bytes.Length!=length) throw new IOException("inert_journal_short_read");
                    Inspect(length);
                    return (byte[])bytes.Clone();
                }
                catch { failed=true; throw; }
            }
        }
    }

    internal enum InertWorkerStep { FinishSent, WriterClosed, SealRead, CleanEof, NaturalExit }

    internal sealed class InertWorkerHandoff
    {
        static readonly InertWorkerStep[] Ordered = {InertWorkerStep.FinishSent, InertWorkerStep.WriterClosed,
            InertWorkerStep.SealRead, InertWorkerStep.CleanEof, InertWorkerStep.NaturalExit};
        readonly object process, pipe;
        readonly InertOpenedIdentity writer;
        readonly object gate=new object();
        bool used;

        internal InertWorkerHandoff(object process, object pipe, InertOpenedIdentity writer)
        {
            if(process==null || pipe==null || writer==null) throw new ArgumentNullException();
            this.process=process; this.pipe=pipe; this.writer=writer;
        }

        internal bool Admit(FinalOutputInertAdapter owner, object observedProcess, object observedPipe,
            InertWorkerStep[] steps, bool withinBudget, bool forcedStop, int exitCode, int stderrBytes,
            InertOpenedIdentity sealedWriter, object auditHandle, Func<object,InertOpenedObservation> inspect,
            Func<object,int,byte[]> read, byte[] seal, byte[] candidate, bool verifiedDeliveryAndChild)
        {
            lock(gate)
            {
                if(used) return false;
                used=true;
                try
                {
                    if(!object.ReferenceEquals(process,observedProcess) || !object.ReferenceEquals(pipe,observedPipe) ||
                        steps==null || !Ordered.SequenceEqual(steps) || !withinBudget || forcedStop || exitCode!=0 || stderrBytes!=0 ||
                        !writer.Matches(sealedWriter)) return false;
                    var before=inspect(auditHandle);
                    if(before==null || before.Length<=0 || before.Length>131072 || !before.Matches(auditHandle,writer,before.Length)) return false;
                    var bytes=read(auditHandle,before.Length);
                    var after=inspect(auditHandle);
                    if(bytes==null || bytes.Length!=before.Length || after==null || !after.Matches(auditHandle,writer,before.Length)) return false;
                    return owner.Admit(seal,bytes,candidate,true,verifiedDeliveryAndChild);
                }
                catch(Exception) { return false; }
            }
        }
    }

    internal static class InertJournalEvidence
    {
        // Expected records are canonical bytes from independently trusted binding, not recovered from raw.
        internal static string Classify(byte[] raw, byte[] intent, byte[] confirmation, byte[] stop)
        {
            if(raw==null || raw.Length==0) return "no_confirmed_evidence";
            if(raw.Length>16384 || new[]{intent,confirmation,stop}.Any(x=>x==null || x.Length==0 || x.Length>8192) ||
                confirmation.SequenceEqual(stop)) return "unknown_or_invalid";
            if(raw.SequenceEqual(intent.Concat(confirmation))) return "confirmed_as_recorded";
            if(raw.SequenceEqual(intent.Concat(stop))) return "pre_effect_stop_as_recorded";
            return "unknown_or_invalid";
        }
    }
}
#endif
