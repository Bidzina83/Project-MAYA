using System;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
using System.Text;

namespace ProjectMaya.WindowsRuntime
{
    internal static class HermesMemory
    {
        internal const string Schema = "maya.protected_hermes.memory.v1";
        internal const int StorageLimit = 65536;
        internal const string Fixture = "native-memory-eight-mutations-v1";
        internal static void Prepare(string directory)
        {
            HermesImport.Prepare(directory);
            string destination = Path.Combine(directory, "state", "config.yaml");
            ProductFiles.NoLinks(destination);
            File.Copy(Path.Combine(directory, "runtime", "hermes-memory-config.json"), destination, false);
        }
        internal static void Collect(string directory, string nonce, Dictionary<string, object> record)
        {
            var report = ProtectedPython.ReadRecord(Path.Combine(directory, "state", "hermes-memory.json"));
            var contract = ProtectedPython.ReadRecord(Path.Combine(directory, "runtime", "hermes-memory-contract.json"));
            record["hermes_memory_report_untrusted"] = report;
            record["hermes_memory_contract"] = contract;
            record["hermes_memory_evidence_matches"] = Admit(report, contract, nonce);
        }
        internal static string ExpectedHash(string target, string nonce)
        {
            using (var hash = SHA256.Create())
                return BitConverter.ToString(hash.ComputeHash(Encoding.UTF8.GetBytes(
                    "MAYA synthetic fixture " + target + " revision " + nonce))).Replace("-", "").ToLowerInvariant();
        }
        internal static bool Admit(Dictionary<string, object> report, Dictionary<string, object> contract, string nonce)
        {
            object value, expected;
            foreach (var pair in new Dictionary<string, object> {
                {"schema", Schema}, {"status", "memory_completed"}, {"stage", "memory_complete"},
                {"memory_module_origin", "hermes/tools/memory_tool.py"}, {"memory_dir_relative", "memories"},
                {"fixture_version", Fixture}, {"mutations_verified", 8}, {"lock_probe_count", 2},
                {"memory_entry_count", 1}, {"user_entry_count", 1}, {"memory_char_limit", 2200},
                {"user_char_limit", 1375}, {"operation_failure_stage", ""} })
                if (!report.TryGetValue(pair.Key, out value) || !pair.Value.Equals(value)) return false;
            if (!contract.TryGetValue("schema", out value) || !Schema.Equals(value) ||
                !contract.TryGetValue("fixture_version", out value) || !Fixture.Equals(value) ||
                !contract.TryGetValue("storage_limit", out value) || !StorageLimit.Equals(value) ||
                !contract.TryGetValue("config_sha256", out expected) || !(expected is string) ||
                ((string)expected).Length != 64 || !report.TryGetValue("config_sha256", out value) || !expected.Equals(value) ||
                !report.TryGetValue("memory_peak_bytes", out value) || !(value is int) ||
                (int)value <= 0 || (int)value > StorageLimit) return false;
            foreach (string key in new[] { "config_verified", "config_unchanged", "constructor_completed", "client_created",
                "empty_tools", "memory_enabled", "external_memory_disabled", "db_disabled", "config_consumed", "zero_model_calls",
                "context_shutdown_returned", "close_returned", "client_closed", "fresh_home_verified", "memory_class_verified",
                "store_attached", "memory_paths_verified", "windows_locking_available", "initial_empty", "fresh_reload_matches",
                "snapshot_behavior_matches", "files_unchanged_after_reload", "residue_absent", "lock_probes_passed", "storage_within_limit" })
                if (!report.TryGetValue(key, out value) || !true.Equals(value)) return false;
            if (!report.TryGetValue("operation_checks", out value)) return false;
            var operations = value as Dictionary<string, object>;
            if (operations == null || operations.Count != 8) return false;
            foreach (string target in new[] { "memory", "user" })
                foreach (string action in new[] { "add_first", "add_second", "replace", "remove" })
                    if (!operations.TryGetValue(target + "." + action, out value) || !true.Equals(value)) return false;
            if (!report.TryGetValue("file_hashes", out value)) return false;
            var hashes = value as Dictionary<string, object>;
            if (hashes == null || hashes.Count != 2 ||
                !hashes.TryGetValue("memories/MEMORY.md", out value) || !ExpectedHash("memory", nonce).Equals(value) ||
                !hashes.TryGetValue("memories/USER.md", out value) || !ExpectedHash("user", nonce).Equals(value)) return false;
            // Memory enablement has its own predicates; only shared identity/output
            // admission is reused, never the construction-only memory-disabled test.
            var importReport = new Dictionary<string, object>(report);
            var importContract = new Dictionary<string, object>(contract);
            importReport["schema"] = importContract["schema"] = HermesImport.Schema;
            importReport["status"] = "import_completed"; importReport["stage"] = "import_complete";
            return HermesImport.Admit(importReport, importContract, nonce);
        }
        internal static string Result(Dictionary<string, object> record, bool cleanup)
        {
            object value;
            return cleanup && record.TryGetValue("python_started", out value) && true.Equals(value) &&
                record.TryGetValue("hermes_memory_evidence_matches", out value) && true.Equals(value)
                ? "memory_completed_pending_independent_cleanup" : "blocked";
        }
    }
}
