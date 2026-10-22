using System;
using System.Collections.Generic;
using ProjectMaya.WindowsRuntime;

internal static class HermesMemoryFixtures
{
    static int checks;
    static void Check(bool value) { checks++; if (!value) throw new Exception("memory check " + checks); }
    static int Main()
    {
        string nonce = new string('a', 32);
        var versions = new Dictionary<string, object> { {"hermes-agent", "0.17.0"} };
        for (int i = 0; i < 63; i++) versions.Add("dep" + i, "1.0");
        var contract = new Dictionary<string, object> { {"schema", HermesMemory.Schema}, {"source_commit", HermesImport.Commit},
            {"config_sha256", new string('a', 64)}, {"distributions", versions},
            {"fixture_version", HermesMemory.Fixture}, {"storage_limit", HermesMemory.StorageLimit} };
        var report = new Dictionary<string, object> { {"schema", HermesMemory.Schema}, {"nonce", nonce},
            {"source_commit", HermesImport.Commit}, {"status", "memory_completed"}, {"stage", "memory_complete"},
            {"class_verified", true}, {"module_origin", "hermes/run_agent.py"}, {"outside_runtime_modules", 0},
            {"output_overflow", false}, {"reason_type", ""}, {"missing_module", ""}, {"operation_failure_stage", ""},
            {"captured_output_bytes", 0}, {"config_sha256", new string('a', 64)}, {"distributions", new Dictionary<string, object>(versions)},
            {"memory_module_origin", "hermes/tools/memory_tool.py"}, {"memory_dir_relative", "memories"},
            {"fixture_version", HermesMemory.Fixture}, {"memory_peak_bytes", 400}, {"mutations_verified", 8},
            {"lock_probe_count", 2}, {"memory_entry_count", 1}, {"user_entry_count", 1},
            {"memory_char_limit", 2200}, {"user_char_limit", 1375} };
        var operations = new Dictionary<string, object>();
        foreach (string target in new[] { "memory", "user" })
            foreach (string action in new[] { "add_first", "add_second", "replace", "remove" }) operations[target + "." + action] = true;
        report["operation_checks"] = operations;
        var hashes = new Dictionary<string, object> { {"memories/MEMORY.md", HermesMemory.ExpectedHash("memory", nonce)},
            {"memories/USER.md", HermesMemory.ExpectedHash("user", nonce)} };
        report["file_hashes"] = hashes;
        string[] flags = { "config_verified", "config_unchanged", "constructor_completed", "client_created", "empty_tools",
            "memory_enabled", "external_memory_disabled", "db_disabled", "config_consumed", "zero_model_calls",
            "context_shutdown_returned", "close_returned", "client_closed", "fresh_home_verified", "memory_class_verified",
            "store_attached", "memory_paths_verified", "windows_locking_available", "initial_empty", "fresh_reload_matches",
            "snapshot_behavior_matches", "files_unchanged_after_reload", "residue_absent", "lock_probes_passed", "storage_within_limit" };
        foreach (string key in flags) report[key] = true;
        Check(HermesMemory.Admit(report, contract, nonce));
        foreach (string key in new List<string>(report.Keys))
        { object old = report[key]; report.Remove(key); Check(!HermesMemory.Admit(report, contract, nonce)); report[key] = old; }
        foreach (string key in flags)
        { report[key] = false; Check(!HermesMemory.Admit(report, contract, nonce)); report[key] = true; }
        foreach (string key in new List<string>(contract.Keys))
        { object old = contract[key]; contract.Remove(key); Check(!HermesMemory.Admit(report, contract, nonce)); contract[key] = old; }
        foreach (string key in new List<string>(operations.Keys))
        {
            operations[key] = false; Check(!HermesMemory.Admit(report, contract, nonce));
            operations.Remove(key); Check(!HermesMemory.Admit(report, contract, nonce)); operations[key] = true;
        }
        foreach (string key in new List<string>(hashes.Keys))
        { object old = hashes[key]; hashes[key] = new string('0', 64); Check(!HermesMemory.Admit(report, contract, nonce)); hashes[key] = old; }
        foreach (int value in new[] { 0, -1, HermesMemory.StorageLimit + 1 })
        { report["memory_peak_bytes"] = value; Check(!HermesMemory.Admit(report, contract, nonce)); }
        report["memory_peak_bytes"] = HermesMemory.StorageLimit; Check(HermesMemory.Admit(report, contract, nonce));
        report["memory_peak_bytes"] = 400;
        foreach (var pair in new Dictionary<string, object> { {"memory_dir_relative", "../memories"}, {"lock_probe_count", 1},
            {"mutations_verified", 7}, {"memory_entry_count", 0}, {"user_entry_count", 2}, {"memory_char_limit", 3000},
            {"memory_module_origin", "outside/memory_tool.py"}, {"status", "construction_completed"}, {"client_closed", "True"},
            {"operation_failure_stage", "memory_lock_probes"}, {"operation_checks", new object[0]}, {"file_hashes", new object[0]} })
        { object old = report[pair.Key]; report[pair.Key] = pair.Value; Check(!HermesMemory.Admit(report, contract, nonce)); report[pair.Key] = old; }
        Check(!HermesMemory.Admit(report, contract, new string('b', 32)));
        var result = new Dictionary<string, object> { {"python_started", true}, {"hermes_memory_evidence_matches", true} };
        Check(HermesMemory.Result(result, true) == "memory_completed_pending_independent_cleanup");
        Check(HermesMemory.Result(result, false) == "blocked");
        result["python_started"] = false; Check(HermesMemory.Result(result, true) == "blocked");
        foreach (string path in new[] { "hermes_memory_check.py", "hermes-memory-contract.json", "hermes-memory-config.json", "hermes_state_check.py" })
            Check(ProductFiles.PayloadPath(path) == path);
        Check(ProtectedPython.Version == "0.1.4-hermes-memory.1");
        Console.WriteLine(checks + " inert Hermes memory checks passed"); return 0;
    }
}
