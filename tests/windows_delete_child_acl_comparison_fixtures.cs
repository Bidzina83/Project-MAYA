using System;
using System.Collections.Generic;
using System.Security.AccessControl;
using System.Security.Principal;
using ProjectMaya.WindowsRuntime;

internal static class DeleteChildAclComparisonFixtures
{
    static readonly SecurityIdentifier Admin=new SecurityIdentifier("S-1-5-32-544"),
        SystemSid=new SecurityIdentifier("S-1-5-18"), Other=new SecurityIdentifier("S-1-5-19");
    static readonly Dictionary<SecurityIdentifier,string> Roles=new Dictionary<SecurityIdentifier,string>{
        {Admin,"administrators"},{SystemSid,"system"}};
    static int checks;

    static RawSecurityDescriptor Policy(bool inherited,int mask=64,SecurityIdentifier principal=null,
        AceFlags extra=AceFlags.None,AceQualifier qualifier=AceQualifier.AccessAllowed,string header="O:BAG:BAD:AI")
    {
        var d=new RawSecurityDescriptor(header+"S:(ML;OICIID;NW;;;LW)");
        d.DiscretionaryAcl.InsertAce(0,new CommonAce(
            AceFlags.ContainerInherit|AceFlags.ObjectInherit|extra|(inherited?AceFlags.Inherited:AceFlags.None),
            qualifier,mask,principal??SystemSid,false,null));
        return d;
    }

    static void Expect(RawSecurityDescriptor a,RawSecurityDescriptor b,string want)
    {
        checks++;
        if(DeleteChildAclComparison.Compare(a,b,Roles)!=want)throw new Exception("assertion "+checks);
    }

    static void Main()
    {
        var expected=Policy(true);
        Expect(expected,Policy(false),"inheritance_marker_only");
        Expect(expected,Policy(true),"marker_difference_not_reproduced");
        Expect(expected,Policy(false,65),"policy_difference");
        Expect(expected,Policy(false,64,Other),"policy_difference");
        Expect(expected,Policy(false,64,Admin),"policy_difference");
        Expect(expected,Policy(false,extra:AceFlags.InheritOnly),"policy_difference");
        Expect(expected,Policy(false,qualifier:AceQualifier.AccessDenied),"policy_difference");
        Expect(expected,Policy(false,header:"O:SYG:BAD:AI"),"policy_difference");
        Expect(expected,Policy(false,header:"O:BAG:BAD:P"),"policy_difference");
        Expect(Policy(false),Policy(true),"policy_difference");
        Expect(expected,null,"inconclusive");
        var extra=Policy(false);
        extra.DiscretionaryAcl.InsertAce(1,new CommonAce(AceFlags.None,AceQualifier.AccessAllowed,1,Admin,false,null));
        Expect(expected,extra,"policy_difference");
        Collect(expected);
        StatePolicy();
        Console.WriteLine("ACL comparison fixture: "+checks+" assertions passed.");
    }

    static void StatePolicy()
    {
        var user=new SecurityIdentifier("S-1-5-21-100-200-300-1001");
        var package=new SecurityIdentifier("S-1-15-2-100-200-300-400-500-600-700");
        var parent=DeleteChildAclExpectedPolicy.Build(user,package,false);
        var child=DeleteChildAclExpectedPolicy.Build(user,package,true);
        if(parent.DiscretionaryAcl.Count!=5 || child.DiscretionaryAcl.Count!=5)
            throw new Exception("policy entry count");
        checks++;
        if(!((CommonAce)parent.DiscretionaryAcl[0]).SecurityIdentifier.Equals(SystemSid) ||
            !((CommonAce)parent.DiscretionaryAcl[1]).SecurityIdentifier.Equals(Admin))
            throw new Exception("expected state ACL order");
        checks++;
        for(int i=0;i<5;i++)
        {
            var a=(CommonAce)parent.DiscretionaryAcl[i];
            var b=(CommonAce)child.DiscretionaryAcl[i];
            if(a.AccessMask!=b.AccessMask || !a.SecurityIdentifier.Equals(b.SecurityIdentifier) ||
                a.IsInherited || b.AceFlags!=(a.AceFlags|AceFlags.Inherited))
                throw new Exception("policy inheritance projection");
            checks++;
        }
        var effective=(CommonAce)child.DiscretionaryAcl[3];
        var inheritOnly=(CommonAce)child.DiscretionaryAcl[4];
        if((effective.AccessMask&64)==0 || (effective.AceFlags&AceFlags.InheritOnly)!=0 ||
            (inheritOnly.AceFlags&AceFlags.InheritOnly)==0)
            throw new Exception("package entry purpose");
        checks++;
    }

    static DeleteChildAclCollector.Snapshot Snapshot(string id,RawSecurityDescriptor descriptor)
    {
        var bytes=new byte[descriptor.BinaryLength];
        descriptor.GetBinaryForm(bytes,0);
        return new DeleteChildAclCollector.Snapshot(id,bytes);
    }

    static void Collect(RawSecurityDescriptor expected)
    {
        var parent=Snapshot("parent",expected);
        var child=Snapshot("child",Policy(false));
        var observed=DeleteChildAclCollector.Collect("parent","child",()=>parent,()=>child,expected,expected,Roles);
        if(!true.Equals(observed["parent_matches"]) || !"inheritance_marker_only".Equals(observed["outcome"]))
            throw new Exception("collector verdict");
        checks++;
        var details=(Dictionary<string,object>)observed["child"];
        var rows=(List<Dictionary<string,object>>)details["aces"];
        if(rows[0].Count!=4 || !"system".Equals(rows[0]["role"]) || !3.Equals(rows[0]["flags"]) ||
            !"low".Equals(details["integrity"]))throw new Exception("bounded child summary");
        checks++;
        var otherGroup=Policy(false);
        otherGroup.Group=Other;
        var separate=DeleteChildAclCollector.Collect("parent","child",()=>parent,()=>Snapshot("child",otherGroup),
            expected,expected,Roles);
        var fields=(Dictionary<string,object>)separate["child_policy_comparison"];
        if(!"inheritance_marker_only".Equals(fields["ordered_dacl"]) || !false.Equals(fields["group_matches"]) ||
            !false.Equals(fields["group_role_known"]) || !false.Equals(separate["child_group_matches_parent_group"]) ||
            !"policy_difference".Equals(separate["outcome"]))throw new Exception("group difference masked");
        checks++;
        if(!"marker_difference_not_reproduced".Equals(observed["parent_policy_comparison"] is Dictionary<string,object>
            ? ((Dictionary<string,object>)observed["parent_policy_comparison"])["ordered_dacl"] : null))
            throw new Exception("parent DACL not independently checked");
        checks++;
        var mismatch=DeleteChildAclCollector.Collect("parent","child",()=>parent,()=>child,Policy(false),expected,Roles);
        if(!false.Equals(mismatch["parent_matches"]) || !"inconclusive".Equals(mismatch["outcome"]))
            throw new Exception("parent mismatch accepted");
        checks++;
        try
        {
            DeleteChildAclCollector.Collect("parent","child",()=>parent,()=>parent,expected,expected,Roles);
            throw new Exception("wrong identity accepted");
        }
        catch(ArgumentException) {checks++;}
        int reads=0;
        try
        {
            DeleteChildAclCollector.Collect("parent","child",()=>parent,
                ()=>++reads==1?child:Snapshot("child",Policy(false,65)),expected,expected,Roles);
            throw new Exception("drift accepted");
        }
        catch(InvalidOperationException) {checks++;}
    }
}
