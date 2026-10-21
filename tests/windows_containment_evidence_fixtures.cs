using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using ProjectMaya.WindowsRuntime;

internal static class ContainmentEvidenceFixtures
{
    private static int checks;
    private static void Equal(string actual, string expected)
    {
        checks++;
        if (actual != expected) throw new Exception(actual + " != " + expected);
    }
    private static void Reject(string text)
    {
        checks++;
        try { ScreenJson.Read(text); }
        catch (StartupFailure) { return; }
        throw new Exception("accepted invalid report");
    }
    private static ContainmentEvidence.Observation Complete()
    {
        return new ContainmentEvidence.Observation {
            Family = "C02", Probe = "protected_document_read",
            PositiveControlVerified = true, AttemptObserved = true,
            CaptureComplete = true, HostPostconditionVerified = true,
            ExplicitDenial = true, NativeError = 5,
            UnauthorizedEffect = false, AllowedEffectVerified = false,
            TimedOut = false, Unsupported = false
        };
    }
    private sealed class OneByteReadStream : Stream
    {
        readonly MemoryStream data;
        internal OneByteReadStream(byte[] bytes) { data = new MemoryStream(bytes); }
        public override bool CanRead { get { return true; } }
        public override bool CanSeek { get { return false; } }
        public override bool CanWrite { get { return false; } }
        public override long Length { get { throw new NotSupportedException(); } }
        public override long Position { get { throw new NotSupportedException(); } set { throw new NotSupportedException(); } }
        public override void Flush() { }
        public override int Read(byte[] buffer, int offset, int count) { return data.Read(buffer, offset, Math.Min(count, 1)); }
        public override long Seek(long offset, SeekOrigin origin) { throw new NotSupportedException(); }
        public override void SetLength(long value) { throw new NotSupportedException(); }
        public override void Write(byte[] buffer, int offset, int count) { throw new NotSupportedException(); }
        protected override void Dispose(bool disposing) { if (disposing) data.Dispose(); base.Dispose(disposing); }
    }
    private static void AdsChecks()
    {
        var write = new ContainmentScreen.AdsRequest(@"C:\MayaAdsFixture", true);
        var read = new ContainmentScreen.AdsRequest(@"C:\MayaAdsFixture", false);
        Equal(write.BasePath, @"C:\MayaAdsFixture\screen-fixtures\document\canary.txt");
        Equal(write.Path, write.BasePath + ":maya-screen"); Equal(read.Path, write.Path);
        Equal(write.Access.ToString("X"), "40000000"); Equal(read.Access.ToString("X"), "80000000");
        Equal(write.Disposition.ToString(), "1"); Equal(read.Disposition.ToString(), "3");
        Equal(ContainmentScreen.AdsRequest.Share.ToString(), "1"); Equal(ContainmentScreen.AdsRequest.Flags.ToString("X"), "80");
        string nonce = new string('a', 32);
        using (var data = new MemoryStream())
        {
            ContainmentScreen.WriteAdsContents(data, nonce);
            Equal(System.Text.Encoding.ASCII.GetString(data.ToArray()), nonce);
            data.Position = 0; Equal(ContainmentScreen.AdsContentsMatch(data, nonce).ToString(), "True");
        }
        foreach (string contents in new[] { "", new string('a', 31), new string('b', 32), new string('a', 33) })
            using (var data = new MemoryStream(System.Text.Encoding.ASCII.GetBytes(contents)))
                Equal(ContainmentScreen.AdsContentsMatch(data, nonce).ToString(), "False");
        using (var data = new MemoryStream(new byte[65536]))
        {
            Equal(ContainmentScreen.AdsContentsMatch(data, nonce).ToString(), "False");
            Equal(data.Position.ToString(), "33");
        }
        using (var data = new OneByteReadStream(System.Text.Encoding.ASCII.GetBytes(nonce)))
            Equal(ContainmentScreen.AdsContentsMatch(data, nonce).ToString(), "True");
        var failure = new NotSupportedException(); var record = new Dictionary<string, object>();
        ProtectedPython.RecordStageFailure(record, "screen_failure", "ads_create", failure);
        ProtectedPython.RecordStageFailure(record, "screen_cleanup_failure", "alias_symbolic_cleanup", failure);
        Equal((string)record["screen_failure_stage"], "ads_create");
        Equal((string)record["screen_cleanup_failure_stage"], "alias_symbolic_cleanup");
        Equal((string)record["screen_failure_hresult"], "0x" + failure.HResult.ToString("X8"));
    }
    private static void VerifyProduct(string path)
    {
        byte[] exe = File.ReadAllBytes(path);
        int pe = BitConverter.ToInt32(exe, 0x3c);
        Equal(BitConverter.ToUInt32(exe, pe).ToString("X"), "4550");
        Equal(BitConverter.ToUInt16(exe, pe + 4).ToString("X"), "8664");
        Equal(BitConverter.ToUInt16(exe, pe + 24).ToString("X"), "20B");
        Equal(BitConverter.ToUInt16(exe, pe + 24 + 68).ToString(), "2");
        foreach (string name in new[] { "MayaPython.payload.zip", "MayaPython.payload-index.json" })
        {
            using (var stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(name))
            using (var copy = new MemoryStream())
            {
                stream.CopyTo(copy); byte[] resource = copy.ToArray(); int matches = 0;
                for (int at = 4; at <= exe.Length - resource.Length; at++)
                {
                    if (exe[at] != resource[0] || BitConverter.ToInt32(exe, at - 4) != resource.Length) continue;
                    int i = 0; while (i < resource.Length && exe[at + i] == resource[i]) i++;
                    if (i == resource.Length) matches++;
                }
                Equal(matches.ToString(), "1");
            }
        }
        Console.WriteLine("Product x64 GUI headers and exact length-prefixed resources verified without loading product assembly");
    }
    public static int Main(string[] args)
    {
        if (args.Length == 2 && args[0] == "--verify-product") { VerifyProduct(args[1]); return 0; }
        if (args.Length == 1 && args[0] == "--contract")
        {
            var cases = new List<object>();
            foreach (var pair in ContainmentScreen.Requirements())
                cases.Add(new { id = pair.Key, family = pair.Value.Family, expected_allowed = pair.Value.ExpectedAllowed,
                    admitted_denial_errors = pair.Value.ExpectedAllowed ? new HashSet<int>() : ContainmentScreen.DeniedErrors(pair.Key) });
            Console.WriteLine(new System.Web.Script.Serialization.JavaScriptSerializer().Serialize(new {
                schema = ContainmentScreen.Schema, child_deadline_ms = ContainmentEvidence.ChildDeadlineMilliseconds,
                stdout_max_bytes = ContainmentEvidence.MaximumStdoutBytes, report_max_bytes = ContainmentEvidence.MaximumReportBytes,
                cases = cases }));
            return 0;
        }
        if (args.Length != 0) throw new Exception("fixture_argument");
        AdsChecks();
        var errors = new HashSet<int> { 5 };
        Equal(ContainmentEvidence.Classify(Complete(), false, errors), "observed_denied");
        var item = Complete(); item.TimedOut = true;
        Equal(ContainmentEvidence.Classify(item, false, errors), "inconclusive");
        item.UnauthorizedEffect = true;
        Equal(ContainmentEvidence.Classify(item, false, errors), "failed");
        item = Complete(); item.Unsupported = true;
        Equal(ContainmentEvidence.Classify(item, false, errors), "inconclusive");
        item = Complete(); item.PositiveControlVerified = false;
        Equal(ContainmentEvidence.Classify(item, false, errors), "inconclusive");
        item = Complete(); item.AttemptObserved = false;
        Equal(ContainmentEvidence.Classify(item, false, errors), "inconclusive");
        item = Complete(); item.CaptureComplete = false;
        Equal(ContainmentEvidence.Classify(item, false, errors), "inconclusive");
        item = Complete(); item.HostPostconditionVerified = false;
        Equal(ContainmentEvidence.Classify(item, false, errors), "inconclusive");
        item = Complete(); item.NativeError = 2;
        Equal(ContainmentEvidence.Classify(item, false, errors), "inconclusive");
        item = Complete(); item.NativeError = null;
        Equal(ContainmentEvidence.Classify(item, false, errors), "inconclusive");
        item = Complete(); item.ExplicitDenial = false;
        Equal(ContainmentEvidence.Classify(item, false, errors), "inconclusive");
        item = Complete(); item.AllowedEffectVerified = true;
        Equal(ContainmentEvidence.Classify(item, false, errors), "failed");
        item = Complete(); item.ExplicitDenial = false; item.NativeError = 0;
        item.AllowedEffectVerified = true;
        Equal(ContainmentEvidence.Classify(item, true, errors), "observed_allowed");
        item.AllowedEffectVerified = false;
        Equal(ContainmentEvidence.Classify(item, true, errors), "failed");
        var required = new Dictionary<string, ContainmentEvidence.Requirement>();
        var observed = new Dictionary<string, string>();
        foreach (string family in ContainmentEvidence.Families)
        {
            required.Add(family + "_case", new ContainmentEvidence.Requirement(family, false));
            observed.Add(family + "_case", "observed_denied");
        }
        Equal(ContainmentEvidence.Summarize(observed, required, true),
            "screen_completed_not_containment_qualified");
        Equal(ContainmentEvidence.Summarize(observed, required, false), "blocked");
        observed.Remove("C05_case");
        Equal(ContainmentEvidence.Summarize(observed, required, true), "blocked");
        observed.Add("C05_case", "inconclusive");
        Equal(ContainmentEvidence.Summarize(observed, required, true), "blocked");
        observed["C05_case"] = "failed";
        Equal(ContainmentEvidence.Summarize(observed, required, true), "failed");
        observed["C05_case"] = "observed_denied";
        observed.Add("unknown", "observed_denied");
        Equal(ContainmentEvidence.Summarize(observed, required, true), "blocked");
        observed.Remove("unknown");
        required["C01_case"] = new ContainmentEvidence.Requirement("C01", true);
        Equal(ContainmentEvidence.Summarize(observed, required, true), "blocked");
        observed["C01_case"] = "observed_allowed";
        Equal(ContainmentEvidence.Summarize(observed, required, true),
            "screen_completed_not_containment_qualified");
        required["C08_case"] = new ContainmentEvidence.Requirement("C01", false);
        Equal(ContainmentEvidence.Summarize(observed, required, true), "blocked");
        required["C08_case"] = new ContainmentEvidence.Requirement("C99", false);
        Equal(ContainmentEvidence.Summarize(observed, required, true), "blocked");
        Equal(ContainmentScreen.Requirements().Count.ToString(), "48");
        foreach (var pair in ContainmentScreen.Requirements())
        {
            var expectedErrors = new HashSet<int> { pair.Key.StartsWith("C05.", StringComparison.Ordinal) ? 10013 : 5 };
            if (pair.Key == "C06.spawn") expectedErrors.Add(367);
            Equal(ContainmentScreen.DeniedErrors(pair.Key).SetEquals(expectedErrors).ToString(), "True");
        }
        item = Complete(); item.NativeError = 367;
        Equal(ContainmentEvidence.Classify(item, false, ContainmentScreen.DeniedErrors("C06.spawn")), "observed_denied");
        Equal(ContainmentEvidence.Classify(item, false, ContainmentScreen.DeniedErrors("C06.process_access")), "inconclusive");
        item.NativeError = 9999;
        Equal(ContainmentEvidence.Classify(item, false, ContainmentScreen.DeniedErrors("C06.spawn")), "inconclusive");
        item.NativeError = 0; item.ExplicitDenial = false;
        Equal(ContainmentEvidence.Classify(item, false, ContainmentScreen.DeniedErrors("C05.4udp.connect")), "inconclusive");
        item.UnauthorizedEffect = true; item.NativeError = 367;
        Equal(ContainmentEvidence.Classify(item, false, ContainmentScreen.DeniedErrors("C06.spawn")), "failed");
        var parsed = ScreenJson.Read("{\"schema\":\"test\",\"rows\":[{\"error\":5}]}");
        Equal((string)parsed["schema"], "test");
        Reject("{\"nonce\":\"a\",\"nonce\":\"b\"}");
        Reject("{\"rows\":[{\"id\":\"a\",\"id\":\"b\"}]}");
        Reject("{\"error\":-1}"); Reject("{\"error\":01}"); Reject("{\"error\":2147483648}");
        Reject("{\"error\":null}"); Reject("{\"error\":1.5}"); Reject("{} trailing");
        Reject("{\"id\":\"\\u0061\"}"); Reject("{\"id\":\"line\n\"}");
        Reject("{\"rows\":[1,]}"); Reject("{\"rows\":[],}");
        Reject("{\"rows\":[[[[[[0]]]]]]}");
        Reject(new string(' ', ContainmentEvidence.MaximumReportBytes + 1));
        var complete = new Dictionary<string, string>();
        foreach (var pair in ContainmentScreen.Requirements())
            if (pair.Key != "C08.cleanup") complete.Add(pair.Key, pair.Value.ExpectedAllowed ? "observed_allowed" : "observed_denied");
        Equal(ContainmentScreen.Finish(complete, true), "screen_completed_not_containment_qualified");
        complete["host.effect"] = "failed";
        Equal(ContainmentScreen.Finish(complete, false), "failed");
        Equal(ProtectedPython.SerializeRecord(new Dictionary<string, object> { {"value", 1} }), "{\"value\":1}");
        checks++;
        try { ProtectedPython.SerializeRecord(new Dictionary<string, object> { {"value", new String('a', 65536)} }); throw new Exception("oversized record accepted"); }
        catch (StartupFailure) { }
        Console.WriteLine(checks + " inert containment evidence checks passed");
        return 0;
    }
}
