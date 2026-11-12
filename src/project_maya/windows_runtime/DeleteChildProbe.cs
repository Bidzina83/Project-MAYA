#if MAYA_DELETE_CHILD_CONTROL_INERT || HERMES_JOURNAL_DELETE_CHILD_SOURCE
using System;

namespace ProjectMaya.WindowsRuntime
{
    internal static class DeleteChildProbe
    {
        const int DeleteChild=64, ShareAll=7, OpenExisting=3, DirectoryNoFollow=0x02200000;

        internal sealed class OpenResult
        {
            internal readonly bool Opened, Closed;
            internal readonly string Identity;
            internal readonly int Error;

            internal OpenResult(bool opened,bool closed,string identity,int error)
            {Opened=opened;Closed=closed;Identity=identity;Error=error;}

            internal bool Valid
            {
                get{return Opened?Error==0:!Closed && Identity==null && Error>0 && Error<=65535;}
            }
        }

        internal delegate OpenResult OpenClose(string path,int mask,int share,int disposition,int flags);

        internal static OpenResult[] Observe(string attemptDirectory,OpenClose open)
        {
            if(String.IsNullOrEmpty(attemptDirectory) || open==null)throw new ArgumentException("delete_child_probe_binding");
            return new[]{
                open(System.IO.Path.Combine(attemptDirectory,"state","delete-child-control"),DeleteChild,ShareAll,OpenExisting,DirectoryNoFollow),
                open(attemptDirectory,DeleteChild,ShareAll,OpenExisting,DirectoryNoFollow)
            };
        }

        internal static string Classify(OpenResult control,OpenResult target,string controlId,string targetId,
            bool replyBound,bool lifecycleVerified,bool objectsUnchanged,bool cleanupVerified)
        {
            if(!replyBound || target==null || !target.Valid)return "inconclusive";
            if(target.Opened)
                return lifecycleVerified && objectsUnchanged?"forbidden_open":"provisional_forbidden_open";
            if(String.IsNullOrEmpty(controlId) || String.IsNullOrEmpty(targetId) || controlId==targetId ||
                control==null || !control.Valid || !lifecycleVerified || !objectsUnchanged || !cleanupVerified)
                return "inconclusive";
            return control.Opened && control.Closed && control.Identity==controlId && target.Error==5
                ? "target_specific_denial":"inconclusive";
        }
    }
}
#endif
