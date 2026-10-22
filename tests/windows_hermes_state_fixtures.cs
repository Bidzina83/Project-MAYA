using System;
using System.Collections.Generic;
using ProjectMaya.WindowsRuntime;

internal static class HermesStateFixtures
{
    static int checks;
    static void Check(bool value) { checks++; if (!value) throw new Exception("state check " + checks); }
    static int Main()
    {
        var versions = new Dictionary<string, object> { {"hermes-agent", "0.17.0"} };
        for (int i = 0; i < 63; i++) versions.Add("dep" + i, "1.0");
        var contract = new Dictionary<string, object> { {"schema", HermesState.Schema}, {"source_commit", HermesImport.Commit},
            {"config_sha256", new string('a', 64)}, {"distributions", versions},
            {"fixture_version", "session-two-records-v1"}, {"storage_limit", HermesState.StorageLimit} };
        var report = new Dictionary<string, object> { {"schema", HermesState.Schema}, {"nonce", "nonce"},
            {"source_commit", HermesImport.Commit}, {"status", "state_completed"}, {"stage", "state_complete"},
            {"class_verified", true}, {"module_origin", "hermes/run_agent.py"}, {"outside_runtime_modules", 0},
            {"output_overflow", false}, {"reason_type", ""}, {"missing_module", ""}, {"operation_failure_stage", ""},
            {"captured_output_bytes", 0}, {"config_sha256", new string('a', 64)}, {"distributions", new Dictionary<string, object>(versions)},
            {"db_module_origin", "hermes/hermes_state.py"}, {"db_relative_path", "state.db"}, {"fixture_version", "session-two-records-v1"},
            {"session_id", "maya-state-nonce"}, {"journal_mode", "wal"}, {"session_count", 1}, {"message_count", 2},
            {"db_cleanup_reason_type", ""}, {"db_peak_bytes", 4096} };
        string[] flags = { "config_verified", "config_unchanged", "constructor_completed", "client_created", "empty_tools",
            "memory_disabled", "config_consumed", "zero_model_calls", "context_shutdown_returned", "close_returned", "client_closed",
            "db_class_verified", "fresh_db_verified", "db_path_verified", "session_created", "agent_db_bound", "write_readback",
            "session_end_verified", "writer_closed", "read_only_reopened", "reopen_readback", "reader_closed", "storage_within_limit" };
        foreach (string key in flags) report[key] = true;
        Check(HermesState.Admit(report, contract, "nonce"));
        foreach (string key in new List<string>(report.Keys))
        { object old = report[key]; report.Remove(key); Check(!HermesState.Admit(report, contract, "nonce")); report[key] = old; }
        foreach (string key in flags)
        { report[key] = false; Check(!HermesState.Admit(report, contract, "nonce")); report[key] = true; }
        foreach (string key in new List<string>(contract.Keys))
        { object old = contract[key]; contract.Remove(key); Check(!HermesState.Admit(report, contract, "nonce")); contract[key] = old; }
        foreach (int value in new[] { 0, -1, HermesState.StorageLimit + 1 })
        { report["db_peak_bytes"] = value; Check(!HermesState.Admit(report, contract, "nonce")); }
        report["db_peak_bytes"] = HermesState.StorageLimit; Check(HermesState.Admit(report, contract, "nonce"));
        report["db_peak_bytes"] = 4096;
        foreach (var pair in new Dictionary<string, object> { {"db_relative_path", "../state.db"}, {"journal_mode", "delete"},
            {"session_id", "wrong"}, {"message_count", 3}, {"session_count", 2}, {"db_cleanup_reason_type", "OSError"},
            {"db_module_origin", "outside/hermes_state.py"}, {"status", "construction_completed"}, {"writer_closed", "True"} })
        { object old = report[pair.Key]; report[pair.Key] = pair.Value; Check(!HermesState.Admit(report, contract, "nonce")); report[pair.Key] = old; }
        Check(!HermesState.Admit(report, contract, "another-nonce"));
        var result = new Dictionary<string, object> { {"python_started", true}, {"hermes_state_evidence_matches", true} };
        Check(HermesState.Result(result, true) == "state_completed_pending_independent_cleanup");
        Check(HermesState.Result(result, false) == "blocked");
        result["python_started"] = false; Check(HermesState.Result(result, true) == "blocked");
        Check(ProductFiles.PayloadPath("hermes_state_check.py") == "hermes_state_check.py");
        Check(ProductFiles.PayloadPath("hermes-state-contract.json") == "hermes-state-contract.json");
        Console.WriteLine(checks + " inert Hermes state checks passed"); return 0;
    }
}
