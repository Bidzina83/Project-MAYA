using System;
using System.Collections;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using ProjectMaya.WindowsRuntime;

internal static class UdpEvidenceFixtures
{
    static int checks;
    static void Check(bool value) { checks++; if (!value) throw new Exception("UDP inert check " + checks); }
    static UdpEvidence.Header Header()
    {
        return new UdpEvidence.Header { Flags = 0x53f, Protocol = 17, Time = 150, Version = 0,
            Local4 = 0x7f000001, Remote4 = 0x7f000001, LocalPort = 45000, RemotePort = 46000 };
    }
    static int Main()
    {
        Check(IntPtr.Size == 8);
        Check(Marshal.SizeOf(typeof(UdpEvidence.Header)) == 136);
        Check(Marshal.SizeOf(typeof(UdpEvidence.Event)) == 152);
        Check(Marshal.OffsetOf(typeof(UdpEvidence.Event), "Data").ToInt32() == 144);
        Check(Marshal.OffsetOf(typeof(UdpEvidence.Header), "Package").ToInt32() == 96);
        Check(Marshal.OffsetOf(typeof(UdpEvidence.Drop), "Direction").ToInt32() == 24);
        Check(Marshal.OffsetOf(typeof(UdpEvidence.Drop), "Switch").ToInt32() == 32);
        Check(UdpEvidence.EqualBytes(new byte[] { 1, 2 }, new byte[] { 1, 2 }));
        Check(!UdpEvidence.EqualBytes(new byte[] { 1 }, new byte[] { 1, 0 }));
        Check(!UdpEvidence.EqualBytes(null, new byte[] { 1 }));
        var drop = new UdpEvidence.Drop { Layer = 42, Loopback = 1, Direction = 0x3901 };
        Check(UdpEvidence.Eligible(Header(), drop, 0, 42, 100, 200));
        foreach (uint flag in new uint[] { 1, 2, 4, 8, 16, 32, 256, 1024 })
        { var h = Header(); h.Flags &= ~flag; Check(!UdpEvidence.Eligible(h, drop, 0, 42, 100, 200)); }
        var wrong = Header(); wrong.Protocol = 6; Check(!UdpEvidence.Eligible(wrong, drop, 0, 42, 100, 200));
        wrong = Header(); wrong.Time = 99; Check(!UdpEvidence.Eligible(wrong, drop, 0, 42, 100, 200));
        wrong = Header(); wrong.Time = 201; Check(!UdpEvidence.Eligible(wrong, drop, 0, 42, 100, 200));
        wrong = Header(); wrong.Remote4++; Check(!UdpEvidence.Eligible(wrong, drop, 0, 42, 100, 200));
        Check(!UdpEvidence.Eligible(Header(), drop, 0, 43, 100, 200));
        Check(!UdpEvidence.Eligible(Header(), drop, 1, 42, 100, 200));
        Check(!UdpEvidence.Eligible(Header(), drop, 2, 42, 100, 200));
        drop.Direction = 0; Check(!UdpEvidence.Eligible(Header(), drop, 0, 42, 100, 200));
        drop.Direction = 0x3900; Check(UdpEvidence.Eligible(Header(), drop, 4, 42, 100, 200));
        var v6 = Header(); v6.Version = 1; v6.Local6Low = v6.Remote6Low = 0;
        v6.Local6High = v6.Remote6High = 0x0100000000000000;
        Check(UdpEvidence.Eligible(v6, drop, 5, 42, 100, 200));
        v6.Remote6High = 0; Check(!UdpEvidence.Eligible(v6, drop, 5, 42, 100, 200));
        var matches = new List<UdpEvidence.Match> { new UdpEvidence.Match {
            Family = 4, LayerIndex = 0, LocalPort = 45000, RemotePort = 46000 } };
        Check(UdpEvidence.MatchTuple(matches, true, null, 4, false, 45000, 46000));
        Check(!UdpEvidence.MatchTuple(matches, false, null, 4, false, 45000, 46000));
        Check(!UdpEvidence.MatchTuple(matches, true, "lost", 4, false, 45000, 46000));
        Check(!UdpEvidence.MatchTuple(matches, true, null, 6, false, 45000, 46000));
        Check(!UdpEvidence.MatchTuple(matches, true, null, 4, true, 45000, 46000));
        Check(!UdpEvidence.MatchTuple(matches, true, null, 4, false, 45001, 46000));
        Check(!UdpEvidence.MatchTuple(matches, true, null, 4, false, 45000, 46001));
        Check(!UdpEvidence.MatchTuple(new UdpEvidence.Match[0], true, null, 4, false, 45000, 46000));
        byte[] table = new byte[16]; table[0] = 1; table[4] = 127; table[7] = 1;
        table[8] = 0xaf; table[9] = 0xc8; table[12] = 123;
        Check(UdpOwner.Contains(table, 4, 45000, 123));
        Check(!UdpOwner.Contains(table, 4, 45000, 124));
        Check(!UdpOwner.Contains(table, 4, 45001, 123));
        Check(!UdpOwner.Contains(table, 4, 45000, 0));
        table[7] = 2; Check(!UdpOwner.Contains(table, 4, 45000, 123));
        table[0] = 2; Check(!UdpOwner.Contains(table, 4, 45000, 123));
        Check(!UdpOwner.Contains(null, 4, 45000, 123));
        byte[] six = new byte[32]; six[0] = 1; six[19] = 1; six[24] = 0xaf; six[25] = 0xc8; six[28] = 123;
        Check(UdpOwner.Contains(six, 6, 45000, 123));
        six[20] = 1; Check(!UdpOwner.Contains(six, 6, 45000, 123));
        var details = new ArrayList();
        Check(ContainmentScreen.ReadUdpDetails(details).Count == 0);
        details.Add(new Dictionary<string, object> { {"id", "C05.4udp.send"}, {"local_port", 45000},
            {"remote_port", 46000}, {"sent_bytes", 38}, {"received_bytes", 0}, {"bind_error", 0} });
        Check(ContainmentScreen.ReadUdpDetails(details).Count == 1);
        var detail = (Dictionary<string, object>)details[0];
        Check(ContainmentScreen.UdpCaseStatus(false, "inconclusive", 38, detail, true, true, true) == "observed_denied");
        Check(ContainmentScreen.UdpCaseStatus(false, "inconclusive", 38, detail, true, true, false) == "inconclusive");
        Check(ContainmentScreen.UdpCaseStatus(false, "denied", 38, detail, false, true, true) == "inconclusive");
        Check(ContainmentScreen.UdpCaseStatus(false, "denied", 38, detail, true, false, true) == "inconclusive");
        Check(ContainmentScreen.UdpCaseStatus(false, "allowed", 38, detail, true, true, true) == "inconclusive");
        Check(ContainmentScreen.UdpCaseStatus(false, "effect", 0, detail, false, false, false) == "failed");
        Check(ContainmentScreen.UdpCaseStatus(false, "inconclusive", 0, detail, true, true, true) == "inconclusive");
        detail["bind_error"] = 10013;
        Check(ContainmentScreen.UdpCaseStatus(false, "denied", 38, detail, true, true, true) == "inconclusive");
        detail["bind_error"] = 0; detail["sent_bytes"] = 37;
        Check(ContainmentScreen.UdpCaseStatus(false, "inconclusive", 37, detail, true, true, true) == "inconclusive");
        detail["sent_bytes"] = 0;
        Check(ContainmentScreen.UdpCaseStatus(true, "inconclusive", 0, detail, true, true, true) == "observed_denied");
        Check(ContainmentScreen.UdpCaseStatus(true, "denied", 0, detail, false, true, true) == "inconclusive");
        detail["received_bytes"] = 1;
        Check(ContainmentScreen.UdpCaseStatus(true, "inconclusive", 0, detail, false, false, false) == "failed");
        details.Add(details[0]);
        try { ContainmentScreen.ReadUdpDetails(details); Check(false); } catch (StartupFailure) { Check(true); }
        Console.WriteLine(checks + " inert UDP evidence checks passed");
        return 0;
    }
}
