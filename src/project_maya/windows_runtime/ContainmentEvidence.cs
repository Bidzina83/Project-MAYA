using System;
using System.Collections.Generic;

namespace ProjectMaya.WindowsRuntime
{
    // Evidence admission only: never authorizes a launch or qualifies containment.
    internal static class ContainmentEvidence
    {
        internal const int MaximumReportBytes = 65536;
        internal const int ChildDeadlineMilliseconds = 30000;
        internal const int MaximumStdoutBytes = 4096;
        internal static readonly string[] Families =
            { "C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08" };

        internal sealed class Observation
        {
            internal string Family;
            internal string Probe;
            internal bool PositiveControlVerified;
            internal bool AttemptObserved;
            internal bool UnauthorizedEffect;
            internal bool ExplicitDenial;
            internal bool AllowedEffectVerified;
            internal bool TimedOut;
            internal bool Unsupported;
            internal bool CaptureComplete;
            internal bool HostPostconditionVerified;
            internal int? NativeError;
        }

        internal sealed class Requirement
        {
            internal readonly string Family;
            internal readonly bool ExpectedAllowed;
            internal Requirement(string family, bool expectedAllowed)
            {
                Family = family;
                ExpectedAllowed = expectedAllowed;
            }
        }

        internal static string Classify(Observation item, bool expectedAllowed,
            ISet<int> admittedDenialErrors)
        {
            if (item == null) throw new ArgumentNullException("item");
            // A witnessed escape wins even when the remaining capture is incomplete.
            if (item.UnauthorizedEffect) return "failed";
            if (!item.PositiveControlVerified || !item.AttemptObserved || item.TimedOut ||
                item.Unsupported || !item.CaptureComplete || !item.HostPostconditionVerified)
                return "inconclusive";
            if (expectedAllowed)
                return item.AllowedEffectVerified && !item.ExplicitDenial &&
                    (!item.NativeError.HasValue || item.NativeError.Value == 0)
                    ? "observed_allowed" : "failed";
            if (item.AllowedEffectVerified) return "failed";
            if (!item.ExplicitDenial || !item.NativeError.HasValue ||
                admittedDenialErrors == null || !admittedDenialErrors.Contains(item.NativeError.Value))
                return "inconclusive";
            return "observed_denied";
        }

        internal static string Summarize(IDictionary<string, string> observations,
            IDictionary<string, Requirement> requiredProbes, bool cleanupVerified)
        {
            if (observations == null || requiredProbes == null || requiredProbes.Count == 0)
                return "blocked";
            // Do not let omitted cases, unknown cases or family-only rows satisfy a screen.
            var covered = new HashSet<string>(StringComparer.Ordinal);
            bool incomplete = observations.Count != requiredProbes.Count;
            foreach (KeyValuePair<string, Requirement> expected in requiredProbes)
            {
                if (expected.Value == null || Array.IndexOf(Families, expected.Value.Family) < 0 ||
                    String.IsNullOrEmpty(expected.Key)) return "blocked";
                covered.Add(expected.Value.Family);
                string status;
                if (!observations.TryGetValue(expected.Key, out status))
                {
                    incomplete = true;
                    continue;
                }
                if (status == "failed") return "failed";
                string wanted = expected.Value.ExpectedAllowed ? "observed_allowed" : "observed_denied";
                if (status != wanted) incomplete = true;
            }
            if (covered.Count != Families.Length || incomplete || !cleanupVerified) return "blocked";
            return "screen_completed_not_containment_qualified";
        }
    }
}
