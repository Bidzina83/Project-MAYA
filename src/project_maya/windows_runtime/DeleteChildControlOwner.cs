#if MAYA_DELETE_CHILD_CONTROL_INERT || HERMES_JOURNAL_DELETE_CHILD_SOURCE
using System;
using System.Security.Principal;

namespace ProjectMaya.WindowsRuntime
{
    internal sealed class DeleteChildControlOwner
    {
        readonly IDisposable retainedHandle;
        readonly DeleteChildControlLease lease;
        bool released;

        // Ownership transfers only when construction succeeds. No write occurs here.
        internal DeleteChildControlOwner(IDisposable retainedHandle,IDeleteChildControlHandle control,
            string controlId,string targetId,SecurityIdentifier user,SecurityIdentifier package)
        {
            if(retainedHandle==null)throw new ArgumentNullException("retainedHandle");
            lease=new DeleteChildControlLease(control,controlId,targetId,user,package);
            this.retainedHandle=retainedHandle;
        }

        internal bool CleanupPending {get{return !released;}}
        internal bool WriteAttempted {get{return lease.WriteAttempted;}}
        internal bool RestorationVerified {get{return lease.RestorationVerified;}}

        internal void Apply()
        {
            if(released)throw new InvalidOperationException("delete_child_control_released");
            lease.Apply();
        }

        internal void VerifyApplied()
        {
            if(released)throw new InvalidOperationException("delete_child_control_released");
            lease.VerifyApplied();
        }

        internal void StopAndRestore(Action stopOwnedJobs)
        {
            if(released)return;
            if(stopOwnedJobs==null)throw new ArgumentNullException("stopOwnedJobs");
            stopOwnedJobs();
            lease.Restore(true);
            retainedHandle.Dispose();
            released=true;
        }
    }
}
#endif
