using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Web.Script.Serialization;
using ProjectMaya.WindowsRuntime;

internal static class HermesImportFixtures
{
    static int checks;
    static void Check(bool value) { checks++; if (!value) throw new Exception("import check " + checks); }
    static void Reject(Action action)
    {
        bool failed = false; try { action(); } catch (Exception) { failed = true; } Check(failed);
    }
    static List<PayloadFile> Files(int count)
    {
        var result = new List<PayloadFile>();
        for (int i = 0; i < count; i++) result.Add(new PayloadFile { path = i == 0 ? "python/python.exe" :
            i == 1 ? "python/python313.dll" : i == 2 ? "startup_check.py" : "python/f" + i, size = 0, sha256 = new string('a', 64) });
        return result;
    }
    static string Json(List<PayloadFile> files)
    { return new JavaScriptSerializer { MaxJsonLength = 8 * 1024 * 1024 }.Serialize(new PayloadIndex { files = files, python_version = "3.13.14", zip_sha256 = new string('b', 64) }); }
    static PayloadIndex Read(string text, bool import)
    { using (var input = new MemoryStream(Encoding.UTF8.GetBytes(text))) return ProductFiles.ReadIndex(input, import); }
    static int Main(string[] args)
    {
        Check(Read(Json(Files(2000)), false).files.Count == 2000);
        Reject(() => Read(Json(Files(2001)), false));
        Check(Read(Json(Files(8192)), true).files.Count == 8192);
        Reject(() => Read(Json(Files(8193)), true));
        string padded = new string(' ', 1024 * 1024 + 1) + Json(Files(3));
        Reject(() => Read(padded, false));
        Check(Read(padded, true).files.Count == 3);
        Reject(() => Read(new string(' ', 4 * 1024 * 1024 + 1) + Json(Files(3)), true));
        var big = Files(3); big[0].size = 32 * 1024 * 1024 + 1;
        Reject(() => Read(Json(big), true));
        big = Files(9); foreach (var file in big) file.size = 32 * 1024 * 1024;
        Reject(() => Read(Json(big), true));
        var versions = new Dictionary<string, object> { {"hermes-agent", "0.17.0"} };
        for (int i = 0; i < 63; i++) versions.Add("dep" + i, "1.0");
        var contract = new Dictionary<string, object> { {"schema", HermesImport.Schema}, {"source_commit", HermesImport.Commit}, {"distributions", versions} };
        var report = new Dictionary<string, object> { {"schema", HermesImport.Schema}, {"nonce", "nonce"},
            {"source_commit", HermesImport.Commit}, {"status", "import_completed"}, {"stage", "import_complete"},
            {"class_verified", true}, {"module_origin", "hermes/run_agent.py"}, {"outside_runtime_modules", 0},
            {"output_overflow", false}, {"reason_type", ""}, {"missing_module", ""},
            {"captured_output_bytes", 0}, {"distributions", new Dictionary<string, object>(versions)} };
        Check(HermesImport.Admit(report, contract, "nonce"));
        foreach (string key in new[] { "schema", "nonce", "source_commit", "status", "stage", "class_verified", "module_origin", "outside_runtime_modules", "output_overflow", "reason_type", "missing_module", "captured_output_bytes", "distributions" })
        { object old = report[key]; report.Remove(key); Check(!HermesImport.Admit(report, contract, "nonce")); report.Add(key, old); }
        report["outside_runtime_modules"] = 1; Check(!HermesImport.Admit(report, contract, "nonce")); report["outside_runtime_modules"] = 0;
        report["module_origin"] = "outside/run_agent.py"; Check(!HermesImport.Admit(report, contract, "nonce"));
        var actual = (Dictionary<string, object>)report["distributions"]; actual["dep0"] = "2";
        report["module_origin"] = "hermes/run_agent.py"; Check(!HermesImport.Admit(report, contract, "nonce"));
        var result = new Dictionary<string, object> { {"python_started", true}, {"hermes_import_evidence_matches", true} };
        Check(HermesImport.Result(result, true) == "import_completed_pending_independent_cleanup");
        Check(HermesImport.Result(result, false) == "blocked");
        result["python_started"] = false; Check(HermesImport.Result(result, true) == "blocked");
        if (args.Length == 1 && args[0] == "--unpack")
        {
            string target = Path.Combine(Directory.GetCurrentDirectory(), ".codex-build", "maya-protected-hermes-import-20261021-1", "unpack-check");
            Directory.CreateDirectory(target); ProductFiles.ExtractPayload(target);
        }
        else if (args.Length != 0) throw new Exception("fixture argument");
        Console.WriteLine(checks + " inert Hermes import checks passed"); return 0;
    }
}
