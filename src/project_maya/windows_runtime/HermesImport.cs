using System;
using System.Collections.Generic;
using System.IO;

namespace ProjectMaya.WindowsRuntime
{
    internal static class HermesImport
    {
        internal const string Schema = "maya.protected_hermes.import.v1";
        internal const string Commit = "b13e2fd6948a59eeb59fe618914147d97a2ee90a";
        internal static void Prepare(string directory)
        {
            // HERMES_HOME, USERPROFILE, TEMP and LOCALAPPDATA already bind to state.
            string state = Path.Combine(directory, "state"); ProductFiles.NoLinks(state);
            foreach (string name in new[] { "cache", "logs" })
            {
                string path = Path.Combine(state, name); ProductFiles.NoLinks(path);
                Directory.CreateDirectory(path);
            }
        }
        internal static void Collect(string directory, string nonce, Dictionary<string, object> record)
        {
            var report = ProtectedPython.ReadRecord(Path.Combine(directory, "state", "hermes-import.json"));
            var contract = ProtectedPython.ReadRecord(Path.Combine(directory, "runtime", "hermes-import-contract.json"));
            record["hermes_import_report_untrusted"] = report;
            record["hermes_import_contract"] = contract;
            record["hermes_import_evidence_matches"] = Admit(report, contract, nonce);
        }
        internal static bool Admit(Dictionary<string, object> report, Dictionary<string, object> contract, string nonce)
        {
            object value;
            foreach (var pair in new Dictionary<string, object> {
                {"schema", Schema}, {"nonce", nonce}, {"source_commit", Commit},
                {"status", "import_completed"}, {"stage", "import_complete"},
                {"class_verified", true}, {"module_origin", "hermes/run_agent.py"},
                {"outside_runtime_modules", 0}, {"output_overflow", false}, {"reason_type", ""}, {"missing_module", ""} })
                if (!report.TryGetValue(pair.Key, out value) || !pair.Value.Equals(value)) return false;
            if (!report.TryGetValue("captured_output_bytes", out value) || !(value is int) || (int)value < 0 || (int)value > 65536) return false;
            if (!contract.TryGetValue("schema", out value) || !Schema.Equals(value) ||
                !contract.TryGetValue("source_commit", out value) || !Commit.Equals(value)) return false;
            object actual, expected;
            if (!report.TryGetValue("distributions", out actual) || !contract.TryGetValue("distributions", out expected)) return false;
            var left = actual as Dictionary<string, object>; var right = expected as Dictionary<string, object>;
            if (left == null || right == null || right.Count != 64 || left.Count != right.Count) return false;
            foreach (var pair in right)
                if (!(pair.Value is string) || !left.TryGetValue(pair.Key, out value) || !pair.Value.Equals(value)) return false;
            return true;
        }
        internal static string Result(Dictionary<string, object> record, bool cleanup)
        {
            object value;
            return cleanup && record.TryGetValue("python_started", out value) && true.Equals(value) &&
                record.TryGetValue("hermes_import_evidence_matches", out value) && true.Equals(value)
                ? "import_completed_pending_independent_cleanup" : "blocked";
        }
    }
}
