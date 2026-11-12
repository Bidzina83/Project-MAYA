using System;
using System.Linq;
using System.Security.AccessControl;
using System.Security.Principal;
using ProjectMaya.WindowsRuntime;

internal static class DeleteChildControlDescriptorFixtures
{
    static int checks;
    static readonly SecurityIdentifier User=new SecurityIdentifier("S-1-5-21-100-200-300-1001"),
        Package=new SecurityIdentifier("S-1-15-2-100-200-300-400-500-600-700");
    static void Check(bool ok) {checks++;if(!ok)throw new Exception("assertion "+checks);}
    static void Reject(Action action)
    {
        try {action();}catch(ArgumentException){checks++;return;}
        throw new Exception("expected rejection");
    }
    static void RejectDescriptor(Action action,string expected)
    {
        try {action();}
        catch(ArgumentException error)
        {
            Check(expected.Equals(error.Data["delete_child_descriptor_check"]));
            return;
        }
        throw new Exception("expected descriptor rejection");
    }
    static byte[] Bytes(RawSecurityDescriptor descriptor)
    {
        var data=new byte[descriptor.BinaryLength];descriptor.GetBinaryForm(data,0);return data;
    }
    static byte[] Baseline(int packageMask,AceFlags packageFlags,int userMask)
    {
        var raw=new RawSecurityDescriptor("O:BAG:BAD:AI");
        raw.DiscretionaryAcl.InsertAce(0,new CommonAce(AceFlags.Inherited|AceFlags.ContainerInherit,
            AceQualifier.AccessAllowed,userMask,User,false,null));
        raw.DiscretionaryAcl.InsertAce(1,new CommonAce(packageFlags,AceQualifier.AccessAllowed,packageMask,Package,false,null));
        return Bytes(raw);
    }
    static void Main()
    {
        var baseline=Baseline(64,AceFlags.Inherited|AceFlags.ContainerInherit,197055);
        var plan=new DeleteChildControlDescriptor(baseline,User,Package);
        var applied=plan.Proposed;
        var descriptor=new RawSecurityDescriptor(applied,0);
        var entry=(CommonAce)descriptor.DiscretionaryAcl[0];
        Check(entry.AceFlags==AceFlags.None && entry.AceQualifier==AceQualifier.AccessAllowed);
        Check(entry.AccessMask==64 && entry.SecurityIdentifier.Equals(User));
        descriptor.DiscretionaryAcl.RemoveAce(0);
        Check(Bytes(descriptor).SequenceEqual(baseline));
        Check(plan.MatchesApplied(applied) && !plan.MatchesApplied(baseline));
        Check(plan.MatchesRestored(plan.Restore(applied,true,true)));
        Reject(()=>plan.Restore(applied,false,true));
        Reject(()=>plan.Restore(applied,true,false));
        Reject(()=>plan.Restore(baseline,true,true));
        RejectDescriptor(()=>new DeleteChildControlDescriptor(Baseline(0,AceFlags.Inherited,197055),User,Package),"package_right_missing");
        RejectDescriptor(()=>new DeleteChildControlDescriptor(Baseline(64,AceFlags.Inherited|AceFlags.InheritOnly,197055),User,Package),"package_right_missing");
        RejectDescriptor(()=>new DeleteChildControlDescriptor(Baseline(64,AceFlags.None,197055),User,Package),"unexpected_ace");
        try
        {
            new DeleteChildControlDescriptor(Baseline(64,AceFlags.None,197055),User,Package);
            throw new Exception("expected non-inherited entry rejection");
        }
        catch(ArgumentException error)
        {
            Check(2.Equals(error.Data["delete_child_ace_ordinal"]));
            Check(0.Equals(error.Data["delete_child_ace_type"]));
            Check(0.Equals(error.Data["delete_child_ace_flags"]));
            Check("not_inherited".Equals(error.Data["delete_child_ace_failed_predicate"]));
            Check(error.Data.Count==5);
        }
        RejectDescriptor(()=>new DeleteChildControlDescriptor(Baseline(64,AceFlags.Inherited,197055|64),User,Package),"operator_already_granted");
        RejectDescriptor(()=>new DeleteChildControlDescriptor(Bytes(new RawSecurityDescriptor("O:BAG:BAD:P")),User,Package),"dacl_protected");
        applied[0]=0;
        Check(!plan.MatchesApplied(applied) && plan.MatchesApplied(plan.Proposed));
        Lease(baseline);
        Owner(baseline);
        Probe();
        Reply();
#if HERMES_JOURNAL_DELETE_CHILD_SOURCE
        Check(DeleteChildControlCreate.Created(0,2,true));
        Check(!DeleteChildControlCreate.Created(unchecked((int)0xc0000035),2,true));
        Check(!DeleteChildControlCreate.Created(0,1,true));
        Check(!DeleteChildControlCreate.Created(0,2,false));
        string volume=new string('a',8), target=volume+new string('b',16);
        var file=new CoordinatorNativeFile("control",volume,new string('c',16),0,1,true,true,false,false);
        Check(DeleteChildControlCreate.Matches(file,"control",target));
        Check(!DeleteChildControlCreate.Matches(file,"replacement",target));
        Check(!DeleteChildControlCreate.Matches(file,"control",volume+file.Id));
        var reparse=new CoordinatorNativeFile("control",volume,file.Id,0,1,true,true,true,false);
        Check(!DeleteChildControlCreate.Matches(reparse,"control",target));
        Check(ProtectedPython.Scope=="offline-journal-delete-child-control-v1");
        Check(ProductFiles.PayloadPath("journal_delete_child_entry.py")=="journal_delete_child_entry.py");
        Check(ProductFiles.PayloadPath("journal_access_role.py")=="journal_access_role.py");
        foreach(string root in new[]{"journal_access_child_entry.py","journal_access_worker_entry.py","Journal_Delete_Child_Entry.py"})
        {
            try {ProductFiles.PayloadPath(root);throw new Exception("unexpected payload root");}
            catch(StartupFailure) {checks++;}
        }
#endif
        Console.WriteLine("Delete-child descriptor fixture: "+checks+" assertions passed.");
    }

    static System.Collections.Generic.Dictionary<string,object> Message(string attempt,string request)
    {
        return new System.Collections.Generic.Dictionary<string,object>{
            {"v",1},{"type","delete_child_result"},{"attempt",attempt},{"request_id",request},{"pid",10},
            {"control",new System.Collections.Generic.Dictionary<string,object>{
                {"opened",true},{"closed",true},{"identity",new string('c',24)},{"open_error",0},{"identity_error",0}}},
            {"target",new System.Collections.Generic.Dictionary<string,object>{
                {"opened",false},{"closed",false},{"identity",null},{"open_error",5},{"identity_error",0}}}};
    }

    static void Reply()
    {
        string attempt=new string('a',32),request=new string('b',32);
        var reader=new DeleteChildReply(attempt,request,10);
        var row=reader.Admit(Message(attempt,request));
        Check(row[0].Opened && row[0].Closed && row[1].Error==5);
        Reject(()=>reader.Admit(Message(attempt,request)));
        foreach(string key in new[]{"v","type","attempt","request_id","pid","control","target"})
        {
            var bad=Message(attempt,request);bad[key]=null;
            var single=new DeleteChildReply(attempt,request,10);
            Reject(()=>single.Admit(bad));
            Reject(()=>single.Admit(Message(attempt,request)));
        }
        var extra=Message(attempt,request);extra["path"]="unbound";
        Reject(()=>new DeleteChildReply(attempt,request,10).Admit(extra));
        var partial=Message(attempt,request);
        var target=(System.Collections.Generic.Dictionary<string,object>)partial["target"];
        target["opened"]=true;target["open_error"]=0;target["identity_error"]=5;
        Check(new DeleteChildReply(attempt,request,10).Admit(partial)[1].Opened);
        target["identity_error"]=0;
        Reject(()=>new DeleteChildReply(attempt,request,10).Admit(partial));
    }

    static void Probe()
    {
        var allowed=new DeleteChildProbe.OpenResult(true,true,"control",0);
        var denied=new DeleteChildProbe.OpenResult(false,false,null,5);
        var wrongError=new DeleteChildProbe.OpenResult(false,false,null,32);
        var unknownOpen=new DeleteChildProbe.OpenResult(true,false,null,0);
        var calls=new System.Collections.Generic.List<string>();
        var results=DeleteChildProbe.Observe(@"C:\synthetic\attempt",(path,mask,share,disposition,flags)=>{
            Check(mask==64 && share==7 && disposition==3 && flags==0x02200000);
            calls.Add(path);
            return calls.Count==1?allowed:denied;
        });
        Check(calls.SequenceEqual(new[]{@"C:\synthetic\attempt\state\delete-child-control",@"C:\synthetic\attempt"}));
        Check(results[0]==allowed && results[1]==denied);
        Check(DeleteChildProbe.Classify(allowed,denied,"control","target",true,true,true,true)=="target_specific_denial");
        foreach(var control in new[]{denied,unknownOpen,new DeleteChildProbe.OpenResult(true,true,"wrong",0)})
            Check(DeleteChildProbe.Classify(control,denied,"control","target",true,true,true,true)=="inconclusive");
        Check(DeleteChildProbe.Classify(allowed,wrongError,"control","target",true,true,true,true)=="inconclusive");
        Check(DeleteChildProbe.Classify(allowed,denied,"control","control",true,true,true,true)=="inconclusive");
        Check(DeleteChildProbe.Classify(allowed,denied,"control","target",false,true,true,true)=="inconclusive");
        Check(DeleteChildProbe.Classify(allowed,denied,"control","target",true,false,true,true)=="inconclusive");
        Check(DeleteChildProbe.Classify(allowed,denied,"control","target",true,true,false,true)=="inconclusive");
        Check(DeleteChildProbe.Classify(allowed,denied,"control","target",true,true,true,false)=="inconclusive");
        Check(DeleteChildProbe.Classify(denied,unknownOpen,"control","target",true,true,true,false)=="forbidden_open");
        Check(DeleteChildProbe.Classify(denied,unknownOpen,"control","target",true,false,true,true)=="provisional_forbidden_open");
        Check(DeleteChildProbe.Classify(allowed,unknownOpen,"control","target",false,true,true,true)=="inconclusive");
    }

    sealed class Handle : IDeleteChildControlHandle, IDisposable
    {
        internal string Id="control";
        internal byte[] Data;
        internal int Writes;
        internal bool ThrowAfterWrite, IgnoreWrite;
        internal bool Disposed;
        public void Dispose() {Disposed=true;}
        public string Identity() {return Id;}
        public byte[] ReadDescriptor() {return (byte[])Data.Clone();}
        public void WriteDescriptor(byte[] descriptor)
        {
            Writes++;
            if(!IgnoreWrite)Data=(byte[])descriptor.Clone();
            if(ThrowAfterWrite)throw new InvalidOperationException("injected write");
        }
    }

    static void Owner(byte[] baseline)
    {
        var handle=new Handle{Data=baseline,ThrowAfterWrite=true};
        var owner=new DeleteChildControlOwner(handle,handle,"control","target",User,Package);
        Check(!owner.WriteAttempted && !owner.RestorationVerified);
        Block(owner.Apply);
        Check(owner.WriteAttempted && !owner.RestorationVerified);
        Check(owner.CleanupPending && !handle.Disposed);
        Block(()=>owner.StopAndRestore(()=>{throw new InvalidOperationException("stop uncertain");}));
        Check(owner.CleanupPending && handle.Writes==1 && !handle.Disposed);
        handle.ThrowAfterWrite=false;
        handle.IgnoreWrite=true;
        Block(()=>owner.StopAndRestore(()=>{}));
        Check(owner.CleanupPending && !handle.Disposed);
        handle.IgnoreWrite=false;
        owner.StopAndRestore(()=>Check(!handle.Disposed && !handle.Data.SequenceEqual(baseline)));
        Check(!owner.CleanupPending && handle.Disposed && handle.Data.SequenceEqual(baseline));
        Check(owner.WriteAttempted && owner.RestorationVerified);
        Block(owner.Apply);

        var unused=new Handle{Data=baseline};
        var early=new DeleteChildControlOwner(unused,unused,"control","target",User,Package);
        early.StopAndRestore(()=>{});
        Check(!early.CleanupPending && unused.Disposed && unused.Writes==0);
        Check(!early.WriteAttempted && !early.RestorationVerified);
    }

    static void Block(Action action)
    {
        try {action();}catch(InvalidOperationException){checks++;return;}
        throw new Exception("expected blocked operation");
    }

    static void Lease(byte[] baseline)
    {
        var handle=new Handle{Data=baseline};
        Block(()=>new DeleteChildControlLease(handle,"control","control",User,Package));
        Block(()=>new DeleteChildControlLease(handle,"other","target",User,Package));
        var lease=new DeleteChildControlLease(handle,"control","target",User,Package);
        handle.ThrowAfterWrite=true;
        Block(lease.Apply);
        Check(lease.CleanupPending && handle.Writes==1);
        Block(()=>lease.Restore(false));
        handle.Id="replacement";
        Block(()=>lease.Restore(true));
        Check(lease.CleanupPending && handle.Writes==1);
        handle.Id="control";
        handle.ThrowAfterWrite=false;
        handle.IgnoreWrite=true;
        Block(()=>lease.Restore(true));
        Check(lease.CleanupPending && handle.Writes==2);
        handle.IgnoreWrite=false;
        lease.Restore(true);
        Check(!lease.CleanupPending && handle.Writes==3 && handle.Data.SequenceEqual(baseline));
        lease.Restore(true);
        Check(handle.Writes==3);
        Block(lease.Apply);
        var noChange=new Handle{Data=baseline,IgnoreWrite=true};
        var noChangeLease=new DeleteChildControlLease(noChange,"control","target",User,Package);
        Block(noChangeLease.Apply);
        noChangeLease.Restore(true);
        Check(!noChangeLease.CleanupPending && noChange.Writes==1);
    }
}
