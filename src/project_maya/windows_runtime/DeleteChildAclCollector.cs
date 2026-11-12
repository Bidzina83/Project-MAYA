#if MAYA_DELETE_CHILD_ACL_COMPARISON_INERT
using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.AccessControl;
using System.Security.Principal;

namespace ProjectMaya.WindowsRuntime
{
    internal static class DeleteChildAclCollector
    {
        internal sealed class Snapshot
        {
            internal readonly string Identity;
            internal readonly byte[] Descriptor;
            internal Snapshot(string identity,byte[] descriptor)
            {Identity=identity;Descriptor=descriptor==null?null:(byte[])descriptor.Clone();}
        }

        internal static Dictionary<string,object> Collect(string parentId,string childId,
            Func<Snapshot> readParent,Func<Snapshot> readChild,RawSecurityDescriptor expectedParent,
            RawSecurityDescriptor expectedChild,IDictionary<SecurityIdentifier,string> roles)
        {
            if(String.IsNullOrEmpty(parentId) || String.IsNullOrEmpty(childId) || parentId==childId)
                throw new ArgumentException("acl_comparison_identity_binding");
            var before=readParent();
            var child=readChild();
            var childAfter=readChild();
            var after=readParent();
            var p=Parse(before,parentId);
            var c=Parse(child,childId);
            Parse(after,parentId);
            Parse(childAfter,childId);
            if(!Equal(before.Descriptor,after.Descriptor))
                throw new InvalidOperationException("acl_comparison_parent_changed");
            if(!Equal(child.Descriptor,childAfter.Descriptor))
                throw new InvalidOperationException("acl_comparison_child_changed");
            bool parentMatches=DeleteChildAclComparison.Compare(expectedParent,p,roles)=="marker_difference_not_reproduced";
            string parentDacl=DeleteChildAclComparison.CompareDacl(expectedParent.DiscretionaryAcl,p.DiscretionaryAcl,roles);
            return new Dictionary<string,object>{
                {"parent_matches",parentMatches},{"parent",Summary(p,roles)},{"child",Summary(c,roles)},
                {"parent_policy_comparison",CompareFields(expectedParent,p,roles)},
                {"child_policy_comparison",CompareFields(expectedChild,c,roles)},
                {"child_vs_parent_dacl",parentDacl=="marker_difference_not_reproduced" ?
                    DeleteChildAclComparison.CompareDacl(p.DiscretionaryAcl,c.DiscretionaryAcl,roles) : "inconclusive"},
                {"child_owner_matches_parent_owner",Same(p.Owner,c.Owner)},
                {"child_group_matches_parent_group",Same(p.Group,c.Group)},
                {"child_group_matches_child_owner",Same(c.Group,c.Owner)},
                {"outcome",parentMatches?DeleteChildAclComparison.Compare(expectedChild,c,roles):"inconclusive"}
            };
        }

        static bool Same(SecurityIdentifier expected,SecurityIdentifier observed)
        {return expected!=null && expected.Equals(observed);}

        static Dictionary<string,object> CompareFields(RawSecurityDescriptor expected,RawSecurityDescriptor observed,
            IDictionary<SecurityIdentifier,string> roles)
        {
            return new Dictionary<string,object>{
                {"ordered_dacl",DeleteChildAclComparison.CompareDacl(expected.DiscretionaryAcl,observed.DiscretionaryAcl,roles)},
                {"owner_matches",Same(expected.Owner,observed.Owner)},
                {"group_matches",Same(expected.Group,observed.Group)},
                {"group_role_known",Role(observed.Group,roles)!="unknown"},
                {"label_acl_matches",expected.SystemAcl!=null && observed.SystemAcl!=null &&
                    DeleteChildAclComparison.Bytes(expected.SystemAcl).SequenceEqual(DeleteChildAclComparison.Bytes(observed.SystemAcl))},
                {"expected_control_flags",(int)expected.ControlFlags},{"observed_control_flags",(int)observed.ControlFlags},
                {"control_flags_match",expected.ControlFlags==observed.ControlFlags}};
        }

        static RawSecurityDescriptor Parse(Snapshot snapshot,string expected)
        {
            if(snapshot==null || snapshot.Identity!=expected || snapshot.Descriptor==null ||
                snapshot.Descriptor.Length<20 || snapshot.Descriptor.Length>16384)
                throw new ArgumentException("acl_comparison_snapshot");
            return new RawSecurityDescriptor(snapshot.Descriptor,0);
        }

        static bool Equal(byte[] a,byte[] b)
        {
            if(a.Length!=b.Length)return false;
            for(int i=0;i<a.Length;i++)if(a[i]!=b[i])return false;
            return true;
        }

        static string Role(SecurityIdentifier sid,IDictionary<SecurityIdentifier,string> roles)
        {
            string role;
            if(sid==null || roles==null || !roles.TryGetValue(sid,out role))return "unknown";
            switch(role)
            {
                case "system": case "administrators": case "operator": case "synthetic_package": return role;
                default:return "unknown";
            }
        }

        static Dictionary<string,object> Summary(RawSecurityDescriptor value,IDictionary<SecurityIdentifier,string> roles)
        {
            var rows=new List<Dictionary<string,object>>();
            var acl=value.DiscretionaryAcl;
            if(acl!=null && acl.Count<=16)
                foreach(GenericAce ace in acl)
                {
                    var known=ace as KnownAce;
                    rows.Add(new Dictionary<string,object>{{"type",(int)ace.AceType},{"flags",(int)ace.AceFlags},
                        {"mask",known==null?null:(object)known.AccessMask},
                        {"role",Role(known==null?null:known.SecurityIdentifier,roles)}});
                }
            string label="unknown";
            int? labelFlags=null, labelMask=null;
            var sacl=value.SystemAcl;
            if(sacl!=null && sacl.Count==1)
            {
                var ace=sacl[0];
                if((int)ace.AceType==17 && ace.BinaryLength>=16 && ace.BinaryLength<=76)
                {
                    var bytes=new byte[ace.BinaryLength];ace.GetBinaryForm(bytes,0);
                    var sid=new SecurityIdentifier(bytes,8).Value;
                    if(sid=="S-1-16-4096")label="low";
                    else if(sid=="S-1-16-8192")label="medium";
                    labelFlags=(int)ace.AceFlags;labelMask=BitConverter.ToInt32(bytes,4);
                }
            }
            return new Dictionary<string,object>{{"owner_role",Role(value.Owner,roles)},
                {"group_role",Role(value.Group,roles)},{"control_flags",(int)value.ControlFlags},
                {"integrity",label},{"integrity_flags",labelFlags},{"integrity_mask",labelMask},
                {"ace_count",acl==null?null:(object)acl.Count},{"aces",rows}};
        }
    }
}
#endif
