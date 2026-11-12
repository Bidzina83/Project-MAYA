#if MAYA_DELETE_CHILD_ACL_COMPARISON_INERT
using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.AccessControl;
using System.Security.Principal;

namespace ProjectMaya.WindowsRuntime
{
    // Expected is an independently specified policy, not a copy of the observed child.
    internal static class DeleteChildAclComparison
    {
        internal static string Compare(RawSecurityDescriptor expected,RawSecurityDescriptor observed,
            IDictionary<SecurityIdentifier,string> roles)
        {
            if(expected==null || observed==null || roles==null || expected.DiscretionaryAcl==null ||
                observed.DiscretionaryAcl==null || expected.Owner==null || expected.Group==null ||
                observed.Owner==null || observed.Group==null || expected.SystemAcl==null || observed.SystemAcl==null)
                return "inconclusive";
            if(!roles.ContainsKey(expected.Owner) || !roles.ContainsKey(expected.Group) ||
                !roles.ContainsKey(observed.Owner) || !roles.ContainsKey(observed.Group))
                return "policy_difference";
            if(!expected.Owner.Equals(observed.Owner) || !expected.Group.Equals(observed.Group) ||
                expected.ControlFlags!=observed.ControlFlags || !Bytes(expected.SystemAcl).SequenceEqual(Bytes(observed.SystemAcl)))
                return "policy_difference";
            return CompareDacl(expected.DiscretionaryAcl,observed.DiscretionaryAcl,roles);
        }

        internal static string CompareDacl(RawAcl want,RawAcl actual,IDictionary<SecurityIdentifier,string> roles)
        {
            if(want==null || actual==null || roles==null)return "inconclusive";
            if(want.Count==0 || want.Count>16 || actual.Count>16)return "inconclusive";
            if(want.Count!=actual.Count || want.Revision!=actual.Revision)return "policy_difference";
            bool missing=false;
            for(int i=0;i<want.Count;i++)
            {
                var a=want[i] as CommonAce;
                var b=actual[i] as CommonAce;
                if(a==null || b==null || a.IsCallback || b.IsCallback ||
                    a.AceQualifier!=AceQualifier.AccessAllowed || b.AceQualifier!=AceQualifier.AccessAllowed ||
                    a.AceType!=b.AceType || a.AccessMask!=b.AccessMask ||
                    !a.SecurityIdentifier.Equals(b.SecurityIdentifier) || !roles.ContainsKey(b.SecurityIdentifier) ||
                    (a.AceFlags&~AceFlags.Inherited)!=(b.AceFlags&~AceFlags.Inherited) ||
                    (!a.IsInherited && b.IsInherited))
                    return "policy_difference";
                missing|=a.IsInherited && !b.IsInherited;
            }
            return missing?"inheritance_marker_only":"marker_difference_not_reproduced";
        }

        internal static byte[] Bytes(RawAcl acl)
        {
            var bytes=new byte[acl.BinaryLength];
            acl.GetBinaryForm(bytes,0);
            return bytes;
        }
    }
}
#endif
