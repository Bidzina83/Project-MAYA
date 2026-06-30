from pathlib import Path
import unittest


class TestHermesRuntimeInclusionScope(unittest.TestCase):
    def test_plan_records_approved_step_order(self):
        doc = Path("docs/architecture/hermes_runtime_inclusion_plan.md").read_text(
            encoding="utf-8"
        )

        for step in range(1, 12):
            self.assertIn(f"{step}. **", doc)

        for expected in (
            "Scope Gate",
            "Hermes Source Strategy",
            "Runtime Contract Inventory",
            "Adapter Contract Update",
            "Package Inclusion",
            "Skills Inclusion Boundary",
            "Memory Hook Wiring",
            "Governed Execution Smoke Path",
            "Installed Package Verification",
            "Windows Manual Smoke Test",
            "Closure Audit",
        ):
            self.assertIn(expected, doc)

    def test_scope_gate_defines_acceptance_and_non_goals(self):
        doc = Path("docs/architecture/hermes_runtime_inclusion_scope.md").read_text(
            encoding="utf-8"
        )

        for expected in (
            "clean installed Maya package",
            "compatible Hermes runtime",
            "without `PYTHONPATH` shims",
            "maya doctor",
            "maya run --config",
            "GovernedAgentRuntime",
            "HermesRuntimeAdapter",
            "authorization and audit records",
            "HermesMemoryProvider",
            "Broker-disabled Enterprise configuration",
            "Metabase service packaging",
            "Maya OAuth Broker",
            "signed production installers",
        ):
            self.assertIn(expected, doc)

    def test_phase2_closure_points_to_runtime_completion_phase(self):
        doc = Path("docs/architecture/phase2_closure.md").read_text(
            encoding="utf-8"
        )
        normalized = " ".join(doc.split())

        self.assertIn("Hermes Runtime Inclusion and Adapter Wiring", normalized)
        self.assertIn("installed-package gap", normalized)


if __name__ == "__main__":
    unittest.main()
