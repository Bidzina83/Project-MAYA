using System;
using System.Collections.Generic;
using System.IO;

namespace ProjectMaya.WindowsRuntime
{
    internal static class HermesConstruction
    {
        internal const string Schema = "maya.protected_hermes.construction.v1";
        internal static void Prepare(string directory)
        {
            HermesImport.Prepare(directory);
            string destination = Path.Combine(directory, "state", "config.yaml");
            ProductFiles.NoLinks(destination);
            File.Copy(Path.Combine(directory, "runtime", "hermes-construction-config.json"), destination, false);
        }
        internal static void Collect(string directory, string nonce, Dictionary<string, object> record)
        {
            var report = ProtectedPython.ReadRecord(Path.Combine(directory, "state", "hermes-construction.json"));
            var contract = ProtectedPython.ReadRecord(Path.Combine(directory, "runtime", "hermes-construction-contract.json"));
            record["hermes_construction_report_untrusted"] = report;
            record["hermes_construction_contract"] = contract;
            record["hermes_construction_evidence_matches"] = Admit(report, contract, nonce);
        }
        internal static bool Admit(Dictionary<string, object> report, Dictionary<string, object> contract, string nonce)
        {
            object value, expected;
            if (!contract.TryGetValue("schema", out value) || !Schema.Equals(value) ||
                !report.TryGetValue("schema", out value) || !Schema.Equals(value) ||
                !report.TryGetValue("status", out value) || !"construction_completed".Equals(value) ||
                !report.TryGetValue("stage", out value) || !"construction_complete".Equals(value) ||
                !report.TryGetValue("operation_failure_stage", out value) || !"".Equals(value) ||
                !contract.TryGetValue("config_sha256", out expected) || !(expected is string) ||
                ((string)expected).Length != 64 || !report.TryGetValue("config_sha256", out value) || !expected.Equals(value)) return false;
            foreach (string key in new[] { "config_verified", "config_unchanged", "constructor_completed", "client_created",
                "empty_tools", "memory_disabled", "config_consumed", "zero_model_calls", "context_shutdown_returned", "close_returned", "client_closed" })
                if (!report.TryGetValue(key, out value) || !true.Equals(value)) return false;
            // Reuse exact class/origin/version/output admission, without changing
            // the frozen import-only contract or accepting import as construction.
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
                record.TryGetValue("hermes_construction_evidence_matches", out value) && true.Equals(value)
                ? "construction_completed_pending_independent_cleanup" : "blocked";
        }
    }
}
