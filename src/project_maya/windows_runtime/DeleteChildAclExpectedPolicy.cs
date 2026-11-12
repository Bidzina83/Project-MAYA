#if MAYA_DELETE_CHILD_ACL_COMPARISON_INERT
using System;
using System.Security.AccessControl;
using System.Security.Principal;

namespace ProjectMaya.WindowsRuntime
{
    internal static class DeleteChildAclExpectedPolicy
    {
        static readonly SecurityIdentifier Admin=new SecurityIdentifier("S-1-5-32-544"),
            SystemSid=new SecurityIdentifier("S-1-5-18");
        const AceFlags Both=AceFlags.ContainerInherit|AceFlags.ObjectInherit;

        internal static RawSecurityDescriptor Build(SecurityIdentifier user,SecurityIdentifier package,bool child)
        {
            if(user==null || package==null || user.Equals(package) || user.Equals(Admin) ||
                user.Equals(SystemSid) || package.Equals(Admin) || package.Equals(SystemSid))
                throw new ArgumentException("acl_comparison_principals");
            var result=new RawSecurityDescriptor(child?"O:BAG:BAD:AI S:(ML;OICIID;NW;;;LW)".Replace(" ",""):
                "O:BAG:BAD:PS:(ML;OICI;NW;;;LW)");
            var acl=result.DiscretionaryAcl;
            var inherited=child?AceFlags.Inherited:AceFlags.None;
            const FileSystemRights packageRights=FileSystemRights.Read|FileSystemRights.Write|FileSystemRights.Delete|
                FileSystemRights.DeleteSubdirectoriesAndFiles|FileSystemRights.Synchronize;
            Add(acl,SystemSid,FileSystemRights.FullControl,Both|inherited);
            Add(acl,Admin,FileSystemRights.FullControl,Both|inherited);
            Add(acl,user,FileSystemRights.Modify|FileSystemRights.Synchronize,Both|inherited);
            Add(acl,package,packageRights|FileSystemRights.Traverse,AceFlags.ContainerInherit|inherited);
            Add(acl,package,packageRights,AceFlags.ObjectInherit|AceFlags.InheritOnly|inherited);
            return result;
        }

        static void Add(RawAcl acl,SecurityIdentifier sid,FileSystemRights rights,AceFlags flags)
        {acl.InsertAce(acl.Count,new CommonAce(flags,AceQualifier.AccessAllowed,(int)rights,sid,false,null));}
    }
}
#endif
