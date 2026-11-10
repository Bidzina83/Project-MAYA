#if MAYA_FINAL_OUTPUT_INERT_FIXTURE || HERMES_JOURNAL_ACCESS
using System;
using System.Collections.Generic;
using System.Security.Principal;

// Bounded parser for the self-relative descriptor returned by the opened-handle query.
// This intentionally accepts only the fixed coordinator journal descriptor, not general Windows ACLs.
internal static class CoordinatorJournalDescriptor
{
    const uint FullAccess=0x001f01ff, NoWriteUp=1;
    const int PresentDacl=0x0004, PresentLabel=0x0010, ProtectedDacl=0x1000, SelfRelative=0x8000;
    static readonly SecurityIdentifier Administrator=new SecurityIdentifier("S-1-5-32-544");
    static readonly SecurityIdentifier SystemSid=new SecurityIdentifier("S-1-5-18");
    static readonly SecurityIdentifier MediumSid=new SecurityIdentifier("S-1-16-8192");

    sealed class InvalidDescriptor : Exception { }

    sealed class Reader
    {
        internal readonly byte[] Raw;
        readonly List<KeyValuePair<int,int>> spans=new List<KeyValuePair<int,int>>();
        internal Reader(byte[] raw) {Raw=raw;}
        internal void Bound(int at,int size,int limit)
        {if(at<0 || size<0 || limit>Raw.Length || at>limit-size)throw new InvalidDescriptor();}
        internal int Word(int at) {Bound(at,2,Raw.Length);return Raw[at]|Raw[at+1]<<8;}
        internal uint Dword(int at)
        {Bound(at,4,Raw.Length);return (uint)Raw[at]|(uint)Raw[at+1]<<8|(uint)Raw[at+2]<<16|(uint)Raw[at+3]<<24;}
        internal int Offset(int field)
        {uint value=Dword(field);if(value<20 || value>Raw.Length || (value&3)!=0)throw new InvalidDescriptor();return (int)value;}
        internal void Span(int start,int size)
        {
            Bound(start,size,Raw.Length);
            int end=start+size;
            foreach(var span in spans)
                if(start<span.Value && span.Key<end && !(start==span.Key && end==span.Value)) throw new InvalidDescriptor();
            spans.Add(new KeyValuePair<int,int>(start,end));
        }
        internal SecurityIdentifier Sid(int at,int limit,out int end)
        {
            Bound(at,8,limit);
            if(Raw[at]!=1 || Raw[at+1]>15)throw new InvalidDescriptor();
            int size=8+4*Raw[at+1];Bound(at,size,limit);end=at+size;
            return new SecurityIdentifier(Raw,at);
        }
        internal SecurityIdentifier TopSid(int field)
        {int at=Offset(field),end;var sid=Sid(at,Raw.Length,out end);Span(at,end-at);return sid;}
        internal int Acl(int at,int count)
        {
            Bound(at,8,Raw.Length);
            int size=Word(at+2);
            if((Raw[at]!=2 && Raw[at]!=4) || Raw[at+1]!=0 || Word(at+6)!=0 || size<8 || (size&3)!=0 || Word(at+4)!=count)
                throw new InvalidDescriptor();
            Span(at,size);return at+size;
        }
        internal SecurityIdentifier Ace(ref int at,int end,byte type,uint mask)
        {
            Bound(at,8,end);
            int size=Word(at+2);
            if(Raw[at]!=type || Raw[at+1]!=0 || size<16 || (size&3)!=0 || Dword(at+4)!=mask) throw new InvalidDescriptor();
            Bound(at,size,end);
            int sidEnd;var sid=Sid(at+8,at+size,out sidEnd);
            if(sidEnd!=at+size)throw new InvalidDescriptor();
            at=sidEnd;return sid;
        }
    }

    internal static string Compare(byte[] raw)
    {
        if(raw==null || raw.Length<20 || raw.Length>16384 || raw[0]!=1 || raw[1]!=0)
            return "descriptor_invalid";
        var read=new Reader(raw);
        int control=read.Word(2);
        if((control&SelfRelative)==0)return "descriptor_invalid";
        try {if(!Administrator.Equals(read.TopSid(4)) || !Administrator.Equals(read.TopSid(8)))return "descriptor_owner_group";}
        catch(InvalidDescriptor) {return "descriptor_owner_group";}
        catch(ArgumentException) {return "descriptor_owner_group";}
        if((control&(PresentDacl|ProtectedDacl))!=(PresentDacl|ProtectedDacl))return "descriptor_dacl";
        int at,end;
        try {int start=read.Offset(16);end=read.Acl(start,2);at=start+8;}
        catch(InvalidDescriptor) {return "descriptor_dacl";}
        try
        {
            var first=read.Ace(ref at,end,0,FullAccess);var second=read.Ace(ref at,end,0,FullAccess);
            if(at!=end || !((Administrator.Equals(first) && SystemSid.Equals(second)) || (SystemSid.Equals(first) && Administrator.Equals(second))))
                return "descriptor_allow_entries";
        }
        catch(InvalidDescriptor) {return "descriptor_allow_entries";}
        catch(ArgumentException) {return "descriptor_allow_entries";}
        if((control&PresentLabel)==0)return "descriptor_label";
        try
        {
            int start=read.Offset(12);end=read.Acl(start,1);at=start+8;
            return MediumSid.Equals(read.Ace(ref at,end,17,NoWriteUp)) && at==end ? null : "descriptor_label";
        }
        catch(InvalidDescriptor) {return "descriptor_label";}
        catch(ArgumentException) {return "descriptor_label";}
    }
}
#endif
