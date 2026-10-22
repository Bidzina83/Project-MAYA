using System;
using System.Collections.Generic;
using System.IO;
using ProjectMaya.WindowsRuntime;

internal static class HermesConstructionFixtures
{
    static int checks;
    static void Check(bool value) { checks++; if (!value) throw new Exception("construction check " + checks); }
    static int Main(string[] args)
    {
        var versions = new Dictionary<string, object> { {"hermes-agent", "0.17.0"} };
        for (int i = 0; i < 63; i++) versions.Add("dep" + i, "1.0");
        var contract = new Dictionary<string, object> { {"schema", HermesConstruction.Schema},
            {"source_commit", HermesImport.Commit}, {"config_sha256", new string('a', 64)}, {"distributions", versions} };
        var report = new Dictionary<string, object> { {"schema", HermesConstruction.Schema}, {"nonce", "nonce"},
            {"source_commit", HermesImport.Commit}, {"status", "construction_completed"}, {"stage", "construction_complete"},
            {"class_verified", true}, {"module_origin", "hermes/run_agent.py"}, {"outside_runtime_modules", 0},
            {"output_overflow", false}, {"reason_type", ""}, {"missing_module", ""}, {"operation_failure_stage", ""},
            {"captured_output_bytes", 0}, {"config_sha256", new string('a', 64)},
            {"distributions", new Dictionary<string, object>(versions)} };
        string[] flags = { "config_verified", "config_unchanged", "constructor_completed", "client_created",
            "empty_tools", "memory_disabled", "config_consumed", "zero_model_calls", "context_shutdown_returned", "close_returned", "client_closed" };
        foreach (string key in flags) report[key] = true;
        Check(HermesConstruction.Admit(report, contract, "nonce"));
        foreach (string key in new List<string>(report.Keys))
        { object old = report[key]; report.Remove(key); Check(!HermesConstruction.Admit(report, contract, "nonce")); report[key] = old; }
        foreach (string key in flags)
        { report[key] = false; Check(!HermesConstruction.Admit(report, contract, "nonce")); report[key] = true; }
        report["schema"] = HermesImport.Schema; Check(!HermesConstruction.Admit(report, contract, "nonce")); report["schema"] = HermesConstruction.Schema;
        report["config_sha256"] = new string('b', 64); Check(!HermesConstruction.Admit(report, contract, "nonce")); report["config_sha256"] = new string('a', 64);
        report["outside_runtime_modules"] = 1; Check(!HermesConstruction.Admit(report, contract, "nonce")); report["outside_runtime_modules"] = 0;
        report["captured_output_bytes"] = 65537; Check(!HermesConstruction.Admit(report, contract, "nonce")); report["captured_output_bytes"] = 0;
        var record = new Dictionary<string, object> { {"python_started", true}, {"hermes_construction_evidence_matches", true} };
        Check(HermesConstruction.Result(record, true) == "construction_completed_pending_independent_cleanup");
        Check(HermesConstruction.Result(record, false) == "blocked");
        record["python_started"] = false; Check(HermesConstruction.Result(record, true) == "blocked");
        foreach (string path in new[] { "hermes_construction_check.py", "hermes-construction-contract.json", "hermes-construction-config.json" })
            Check(ProductFiles.PayloadPath(path) == path);
        if (args.Length == 1 && args[0] == "--unpack")
        {
            string target = Path.Combine(Directory.GetCurrentDirectory(), "unpack-check");
            if (Directory.Exists(target)) throw new Exception("unpack target already exists");
            Directory.CreateDirectory(target); ProductFiles.ExtractPayload(target);
            HermesConstruction.Prepare(target);
            Check(File.ReadAllText(Path.Combine(target, "state", "config.yaml")) ==
                File.ReadAllText(Path.Combine(target, "runtime", "hermes-construction-config.json")));
        }
        else if (args.Length != 0) throw new Exception("fixture argument");
        Console.WriteLine(checks + " inert Hermes construction checks passed"); return 0;
    }
}
