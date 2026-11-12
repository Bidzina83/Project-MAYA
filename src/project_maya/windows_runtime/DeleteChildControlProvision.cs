#if HERMES_JOURNAL_DELETE_CHILD_SOURCE
using System;
using System.IO;
using System.Linq;
using System.Security.AccessControl;
using System.Security.Principal;

namespace ProjectMaya.WindowsRuntime
{
    internal sealed class DeleteChildControlProvision
    {
        const uint Metadata=0x20080, WriteDacl=0x40000, DirectoryNoFollow=0x02200000;
        readonly CoordinatorJournalWindowsCalls calls=new CoordinatorJournalWindowsCalls();
        readonly string attemptDirectory, controlPath, attempt;
        byte[] targetDescriptor, journalDescriptor, journalBytes;
        string journalId;
        DeleteChildControlOwner owner;

        internal string TargetIdentity {get;private set;}
        internal string ControlIdentity {get;private set;}
        internal bool CleanupPending {get{return owner!=null && owner.CleanupPending;}}
        internal bool WriteAttempted {get{return owner!=null && owner.WriteAttempted;}}
        internal bool RestorationVerified {get{return owner!=null && owner.RestorationVerified;}}
        internal string LastSetupStep {get;private set;}
        internal string DescriptorCheck {get;private set;}
        internal System.Collections.Generic.Dictionary<string,object> RejectedAce {get;private set;}

        internal DeleteChildControlProvision(string directory,string attempt)
        {
            Require(CoordinatorJournalBinding.Hex(attempt,32) && directory==Path.Combine(ProductFiles.Root,attempt));
            attemptDirectory=directory;
            this.attempt=attempt;
            controlPath=Path.Combine(directory,"state","delete-child-control");
            LastSetupStep="initialized";
        }

        static void Require(bool valid)
        {if(!valid)throw new StartupFailure("delete_child_control_provision");}

        byte[] ReadTarget(out string id)
        {
            ProductFiles.NoLinks(attemptDirectory);
            using(var target=calls.Open(attemptDirectory,Metadata,3,3,DirectoryNoFollow,null))
            {
                Require(!target.IsInvalid);
                var observed=calls.Inspect(target);
                Require(observed.Directory && observed.Disk && !observed.Reparse && !observed.Inheritable &&
                    String.Equals(observed.Path,attemptDirectory,StringComparison.OrdinalIgnoreCase));
                id=observed.Volume+observed.Id;
                Require(CoordinatorJournalBinding.Hex(id,24));
                return calls.Descriptor(target);
            }
        }

        internal void Prepare(SecurityIdentifier user,SecurityIdentifier package)
        {
            Require(owner==null && TargetIdentity==null);
            string id;
            targetDescriptor=ReadTarget(out id);
            TargetIdentity=id;
            LastSetupStep="target_bound";
            var bytes=System.Text.Encoding.ASCII.GetBytes("Maya delete-child control");
            var digest=BridgeHostFiles.Hash(bytes);
            var binding=new CoordinatorJournalBinding(attempt,digest,"windows:"+user.Value,attempt,digest,digest,digest,
                bytes.Length,attempt,0,0);
            CoordinatorJournalNativeTransport transport=null;
            string volume=id.Substring(0,8), parent=id.Substring(8);
            using(var candidate=new CoordinatorJournalCandidate(binding,parent,volume,
                (path,sd)=>transport=new CoordinatorJournalNativeTransport(attempt,parent,volume,path,sd,calls)))
            {
                candidate.Intent();candidate.PreEffectStop();
                var observed=transport.Inspect();
                journalId=observed.VolumeId+observed.FileId;
                journalDescriptor=observed.Descriptor;
                journalBytes=transport.ReadPrefix(observed.Length);
            }
            LastSetupStep="journal_verified";
            string state=Path.GetDirectoryName(controlPath);
            ProductFiles.NoLinks(state);
            Require(Directory.GetFileSystemEntries(state).Length==0);
            Microsoft.Win32.SafeHandles.SafeFileHandle handle;
            using(var stateHandle=calls.Open(state,Metadata,3,3,DirectoryNoFollow,null))
            {
                Require(!stateHandle.IsInvalid);
                var observed=calls.Inspect(stateHandle);
                Require(observed.Directory && observed.Disk && !observed.Reparse && !observed.Inheritable &&
                    observed.Volume==TargetIdentity.Substring(0,8) &&
                    String.Equals(observed.Path,state,StringComparison.OrdinalIgnoreCase));
                handle=DeleteChildControlCreate.New(stateHandle,Metadata|WriteDacl);
                LastSetupStep="control_created";
            }
            try
            {
                Require(!handle.IsInvalid);
                var observed=calls.Inspect(handle);
                ControlIdentity=observed.Volume+observed.Id;
                Require(DeleteChildControlCreate.Matches(observed,controlPath,TargetIdentity) &&
                    Directory.GetFileSystemEntries(controlPath).Length==0);
                var control=new DeleteChildControlWindowsHandle(handle,controlPath,ControlIdentity);
                LastSetupStep="control_bound";
                var raw=new RawSecurityDescriptor(control.ReadDescriptor(),0);
                LastSetupStep="control_descriptor_parsed";
                Require(raw.SystemAcl!=null && raw.SystemAcl.Count==1);
                byte[] label=new byte[raw.SystemAcl[0].BinaryLength];
                raw.SystemAcl[0].GetBinaryForm(label,0);
                Require(label.Length>=16 && label[0]==17 && label[1]==19 &&
                    BitConverter.ToInt32(label,4)==1 && new SecurityIdentifier(label,8).Value=="S-1-16-4096");
                LastSetupStep="control_label_verified";
                try {owner=new DeleteChildControlOwner(handle,control,ControlIdentity,TargetIdentity,user,package);}
                catch(ArgumentException error)
                {
                    DescriptorCheck=error.Data["delete_child_descriptor_check"] as string ?? "descriptor_parse_or_serialize";
                    if(DescriptorCheck=="unexpected_ace")
                        RejectedAce=new System.Collections.Generic.Dictionary<string,object>{
                            {"ordinal",error.Data["delete_child_ace_ordinal"]},
                            {"type",error.Data["delete_child_ace_type"]},
                            {"flags",error.Data["delete_child_ace_flags"]},
                            {"failed_predicate",error.Data["delete_child_ace_failed_predicate"]}};
                    throw;
                }
                LastSetupStep="control_baseline_verified";
            }
            finally
            {
                if(owner==null)handle.Dispose();
            }
            owner.Apply();
            LastSetupStep="control_grant_verified";
            VerifyObjects();
            LastSetupStep="objects_verified";
        }

        internal void VerifyObjects()
        {
            VerifyTarget();
            ProductFiles.NoLinks(controlPath);
            Require(Directory.GetFileSystemEntries(controlPath).Length==0);
            owner.VerifyApplied();
            var path=Path.Combine(attemptDirectory,CoordinatorJournalCandidate.Leaf);
            ProductFiles.NoLinks(path);
            using(var journal=calls.Open(path,0x80020080,1,3,0x00200000,null))
            {
                Require(!journal.IsInvalid);
                var actual=calls.Inspect(journal);
                Require(actual.Disk && !actual.Directory && !actual.Reparse && !actual.Inheritable &&
                    actual.Links==1 && actual.Volume+actual.Id==journalId && actual.Length==journalBytes.Length &&
                    String.Equals(actual.Path,path,StringComparison.OrdinalIgnoreCase));
                Require(journalDescriptor.SequenceEqual(calls.Descriptor(journal)) &&
                    journalBytes.SequenceEqual(calls.Read(journal,0,actual.Length)));
            }
        }

        internal void VerifyTarget()
        {
            string id;
            var current=ReadTarget(out id);
            Require(id==TargetIdentity && targetDescriptor.SequenceEqual(current));
        }

        internal void StopAndRestore(Action stopOwnedJobs)
        {
            if(owner==null)stopOwnedJobs();
            else owner.StopAndRestore(stopOwnedJobs);
        }
    }
}
#endif
