using System;
using System.Linq;
using System.Security.Principal;

internal static class FinalOutputProbeDescriptorFixtures
{
    static readonly SecurityIdentifier User=new SecurityIdentifier("S-1-5-21-123-456-789-500");
    static readonly SecurityIdentifier SystemSid=new SecurityIdentifier("S-1-5-18");
    static readonly SecurityIdentifier Medium=new SecurityIdentifier("S-1-16-8192");
    static int count;

    static byte[] Sid(SecurityIdentifier sid)
    {var bytes=new byte[sid.BinaryLength];sid.GetBinaryForm(bytes,0);return bytes;}
    static byte[] Ace(SecurityIdentifier sid,byte type=0,uint mask=0x1f01ff,byte flags=0)
    {
        byte[] principal=Sid(sid);
        return new[]{type,flags}.Concat(BitConverter.GetBytes((ushort)(8+principal.Length)))
            .Concat(BitConverter.GetBytes(mask)).Concat(principal).ToArray();
    }
    static byte[] Acl(params byte[][] aces)
    {
        return new byte[]{2,0}.Concat(BitConverter.GetBytes((ushort)(8+aces.Sum(a=>a.Length))))
            .Concat(BitConverter.GetBytes((ushort)aces.Length)).Concat(new byte[2]).Concat(aces.SelectMany(a=>a)).ToArray();
    }
    static byte[] Make(byte[] owner=null,byte[] group=null,byte[] dacl=null,byte[] label=null,ushort flags=0x9014)
    {
        owner=owner??Sid(User);group=group??Sid(User);dacl=dacl??Acl(Ace(User),Ace(SystemSid));
        label=label??Acl(Ace(Medium,17,1));
        return new byte[]{1,0}.Concat(BitConverter.GetBytes(flags)).Concat(BitConverter.GetBytes(20))
            .Concat(BitConverter.GetBytes(20+owner.Length)).Concat(BitConverter.GetBytes(label.Length==0?0:20+owner.Length+group.Length))
            .Concat(BitConverter.GetBytes(dacl.Length==0?0:20+owner.Length+group.Length+label.Length))
            .Concat(owner).Concat(group).Concat(label).Concat(dacl).ToArray();
    }
    static void Check(byte[] raw,string expected,SecurityIdentifier user=null)
    {
        count++;string result=FinalOutputProbeDescriptor.Compare(raw,user??User);
        if(result!=expected)throw new Exception("Descriptor check "+count+": expected "+expected+", got "+result);
    }
    static void Main()
    {
        byte[] original=Make();Check(original,null);
        Check(Make(dacl:Acl(Ace(SystemSid),Ace(User))),null);
        Check(original,null,new SecurityIdentifier(Sid(User),0));
        Check(Make(owner:Sid(SystemSid)),"descriptor_owner_group");Check(Make(group:Sid(SystemSid)),"descriptor_owner_group");
        Check(Make(flags:0x8014),"descriptor_dacl");Check(Make(flags:0x9010),"descriptor_dacl");
        Check(Make(dacl:new byte[0]),"descriptor_dacl");Check(Make(dacl:Acl()),"descriptor_dacl");
        Check(Make(dacl:Acl(Ace(User))),"descriptor_dacl");
        Check(Make(dacl:Acl(Ace(User),Ace(SystemSid),Ace(User))),"descriptor_dacl");
        Check(Make(dacl:Acl(Ace(User),Ace(User))),"descriptor_allow_entries");
        Check(Make(dacl:Acl(Ace(SystemSid),Ace(SystemSid))),"descriptor_allow_entries");
        Check(Make(dacl:Acl(Ace(User,1),Ace(SystemSid))),"descriptor_allow_entries");
        Check(Make(dacl:Acl(Ace(User,5),Ace(SystemSid))),"descriptor_allow_entries");
        Check(Make(dacl:Acl(Ace(User,9),Ace(SystemSid))),"descriptor_allow_entries");
        Check(Make(dacl:Acl(Ace(User,flags:16),Ace(SystemSid))),"descriptor_allow_entries");
        Check(Make(dacl:Acl(Ace(User,flags:1),Ace(SystemSid))),"descriptor_allow_entries");
        Check(Make(dacl:Acl(Ace(User,mask:0x1f01fe),Ace(SystemSid))),"descriptor_allow_entries");
        Check(Make(dacl:Acl(Ace(User),Ace(Medium))),"descriptor_allow_entries");
        Check(Make(flags:0x9004),"descriptor_label");Check(Make(label:new byte[0]),"descriptor_label");
        Check(Make(label:Acl()),"descriptor_label");Check(Make(label:Acl(Ace(Medium,17,1),Ace(Medium,17,1))),"descriptor_label");
        Check(Make(label:Acl(Ace(new SecurityIdentifier("S-1-16-4096"),17,1))),"descriptor_label");
        Check(Make(label:Acl(Ace(Medium,17,3))),"descriptor_label");Check(Make(label:Acl(Ace(Medium,17,1,16))),"descriptor_label");
        Check(Make(label:Acl(Ace(Medium,0,1))),"descriptor_label");
        Check(null,"descriptor_invalid");Check(new byte[16385],"descriptor_invalid");
        byte[] bad=(byte[])original.Clone();bad[0]=2;Check(bad,"descriptor_invalid");
        bad=(byte[])original.Clone();bad[4]=21;Check(bad,"descriptor_owner_group");
        bad=(byte[])original.Clone();Array.Copy(bad,12,bad,16,4);Check(bad,"descriptor_dacl");
        bad=(byte[])original.Clone();int dacl=BitConverter.ToInt32(bad,16);bad[dacl+10]=0;Check(bad,"descriptor_allow_entries");
        for(int n=0;n<original.Length;n++)
        {
            count++;
            if(FinalOutputProbeDescriptor.Compare(original.Take(n).ToArray(),User)==null)
                throw new Exception("Accepted truncated descriptor length "+n);
        }
        Console.WriteLine("Descriptor fixture: "+count+" assertions passed");
    }
}
