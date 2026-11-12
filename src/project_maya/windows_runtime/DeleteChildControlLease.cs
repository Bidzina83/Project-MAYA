#if MAYA_DELETE_CHILD_CONTROL_INERT || HERMES_JOURNAL_DELETE_CHILD_SOURCE
using System;
using System.Security.Principal;

namespace ProjectMaya.WindowsRuntime
{
    internal interface IDeleteChildControlHandle
    {
        // The implementation must observe and update the retained handle, never reopen by name.
        string Identity();
        byte[] ReadDescriptor();
        void WriteDescriptor(byte[] descriptor);
    }

    internal sealed class DeleteChildControlLease
    {
        readonly IDeleteChildControlHandle handle;
        readonly string identity;
        readonly DeleteChildControlDescriptor descriptor;
        bool attempted, restored;

        internal DeleteChildControlLease(IDeleteChildControlHandle handle,string expectedIdentity,
            string targetIdentity,SecurityIdentifier user,SecurityIdentifier package)
        {
            Require(handle!=null && !String.IsNullOrEmpty(expectedIdentity) &&
                !String.IsNullOrEmpty(targetIdentity) && expectedIdentity!=targetIdentity);
            this.handle=handle;
            identity=expectedIdentity;
            descriptor=new DeleteChildControlDescriptor(ReadBound(),user,package);
        }

        internal bool CleanupPending {get{return attempted && !restored;}}
        internal bool WriteAttempted {get{return attempted;}}
        internal bool RestorationVerified {get{return restored;}}

        static void Require(bool valid)
        {if(!valid)throw new InvalidOperationException("delete_child_control_binding");}

        byte[] ReadBound()
        {
            Require(handle.Identity()==identity);
            var value=handle.ReadDescriptor();
            Require(handle.Identity()==identity);
            return value;
        }

        internal void Apply()
        {
            Require(!attempted && descriptor.MatchesRestored(ReadBound()));
            // A failed write may already have taken effect.
            attempted=true;
            handle.WriteDescriptor(descriptor.Proposed);
            Require(descriptor.MatchesApplied(ReadBound()));
        }

        internal void VerifyApplied()
        {Require(CleanupPending && descriptor.MatchesApplied(ReadBound()));}

        internal void Restore(bool jobsStopped)
        {
            if(!CleanupPending)return;
            Require(jobsStopped);
            var observed=ReadBound();
            if(!descriptor.MatchesRestored(observed))
            {
                handle.WriteDescriptor(descriptor.Restore(observed,true,true));
                Require(descriptor.MatchesRestored(ReadBound()));
            }
            restored=true;
        }
    }
}
#endif
