using System;
using ProjectMaya.WindowsRuntime;

internal static class ResetTcpEvidenceFixtures
{
    static void Main()
    {
        const uint address=0xc0a80102;
        const ushort port=49160, layer=48;
        var header=new UdpEvidence.Header{Flags=0x53f,Version=0,Protocol=6,
            Remote4=address,RemotePort=port,LocalPort=49161,Time=25};
        var drop=new UdpEvidence.Drop{Layer=layer,Direction=0x3901};
        Func<int,ushort,uint,ushort,bool> eligible=(index,l,a,p)=>
            UdpEvidence.EligibleResetTcp(header,drop,index,l,a,p,20,30);
        if(!eligible(0,layer,address,port) || eligible(1,layer,address,port) ||
            eligible(0,49,address,port) || eligible(0,layer,address+1,port) ||
            eligible(0,layer,address,(ushort)(port+1)))throw new Exception("route admission");
        drop.Loopback=1;
        if(eligible(0,layer,address,port))throw new Exception("loopback admitted");
        drop.Loopback=0;header.Protocol=17;
        if(eligible(0,layer,address,port))throw new Exception("UDP admitted");
        header.Protocol=6;header.Time=30;
        if(eligible(0,layer,address,port))throw new Exception("out-of-window event admitted");
        Console.WriteLine("8 TCP event admission checks passed.");
    }
}
