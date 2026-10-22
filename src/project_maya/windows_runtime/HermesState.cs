using System;
using System.Collections.Generic;
using System.IO;

namespace ProjectMaya.WindowsRuntime
{
    internal static class HermesState
    {
        internal const string Schema = "maya.protected_hermes.state.v1";
        internal const int StorageLimit = 32 * 1024 * 1024;
        internal static void Collect(string directory, string nonce, Dictionary<string, object> record)
        {
            var report = ProtectedPython.ReadRecord(Path.Combine(directory, "state", "hermes-state.json"));
            var contract = ProtectedPython.ReadRecord(Path.Combine(directory, "runtime", "hermes-state-contract.json"));
            record["hermes_state_report_untrusted"] = report;
            record["hermes_state_contract"] = contract;
            record["hermes_state_evidence_matches"] = Admit(report, contract, nonce);
        }
        internal static bool Admit(Dictionary<string, object> report, Dictionary<string, object> contract, string nonce)
        {
            object value;
            foreach (var pair in new Dictionary<string, object> {
                {"schema", Schema}, {"status", "state_completed"}, {"stage", "state_complete"},
                {"db_module_origin", "hermes/hermes_state.py"}, {"db_relative_path", "state.db"},
                {"fixture_version", "session-two-records-v1"}, {"session_id", "maya-state-" + nonce},
                {"journal_mode", "wal"}, {"session_count", 1}, {"message_count", 2}, {"db_cleanup_reason_type", ""} })
                if (!report.TryGetValue(pair.Key, out value) || !pair.Value.Equals(value)) return false;
            if (!contract.TryGetValue("schema", out value) || !Schema.Equals(value) ||
                !contract.TryGetValue("fixture_version", out value) || !"session-two-records-v1".Equals(value) ||
                !contract.TryGetValue("storage_limit", out value) || !StorageLimit.Equals(value) ||
                !report.TryGetValue("db_peak_bytes", out value) || !(value is int) || (int)value <= 0 || (int)value > StorageLimit) return false;
            foreach (string key in new[] { "db_class_verified", "fresh_db_verified", "db_path_verified", "session_created", "agent_db_bound",
                "write_readback", "session_end_verified", "writer_closed", "read_only_reopened", "reopen_readback", "reader_closed", "storage_within_limit" })
                if (!report.TryGetValue(key, out value) || !true.Equals(value)) return false;
            var constructionReport = new Dictionary<string, object>(report);
            var constructionContract = new Dictionary<string, object>(contract);
            constructionReport["schema"] = constructionContract["schema"] = HermesConstruction.Schema;
            constructionReport["status"] = "construction_completed"; constructionReport["stage"] = "construction_complete";
            return HermesConstruction.Admit(constructionReport, constructionContract, nonce);
        }
        internal static string Result(Dictionary<string, object> record, bool cleanup)
        {
            object value;
            return cleanup && record.TryGetValue("python_started", out value) && true.Equals(value) &&
                record.TryGetValue("hermes_state_evidence_matches", out value) && true.Equals(value)
                ? "state_completed_pending_independent_cleanup" : "blocked";
        }
    }
}
