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

    def test_source_strategy_records_selected_runtime_and_skill_sources(self):
        doc = Path("docs/architecture/hermes_source_strategy.md").read_text(
            encoding="utf-8"
        )
        normalized = " ".join(doc.split()).lower()

        for expected in (
            "Bidzina83/hermes-agent",
            "selected integration source",
            "NousResearch/hermes-agent",
            "upstream compatibility reference",
            "Bidzina83/Hermes-Agent-Maya-Skills",
            "trained Maya skill artifact source",
            "default Maya-relevant skills",
            "HermesRuntimeAdapter",
            "must not depend on a local repo checkout",
            "Do not copy arbitrary Hermes runtime folders",
            "personal account details",
            "path shims",
        ):
            self.assertIn(expected.lower(), normalized)

    def test_plan_links_step_2_evidence(self):
        doc = Path("docs/architecture/hermes_runtime_inclusion_plan.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("docs/architecture/hermes_source_strategy.md", doc)

    def test_runtime_contract_inventory_records_selected_hermes_surface(self):
        doc = Path("docs/architecture/hermes_runtime_contract_inventory.md").read_text(
            encoding="utf-8"
        )
        normalized = " ".join(doc.split()).lower()

        for expected in (
            "b13e2fd6948a59eeb59fe618914147d97a2ee90a",
            "885e80df74f017d5e897d39928f49b0212e9bedb",
            "run_agent:AIAgent",
            "AIAgent.__init__",
            "chat(message",
            "run_conversation",
            "close()",
            "does not expose `attach_memory()`",
            "MemoryProvider",
            "MemoryManager",
            "skills.external_dirs",
            "`72` default",
            "`101` optional",
            "`46` `skills/**/SKILL.md`",
            "Python support: `>=3.11,<3.14`",
            "fork-specific behavior must be documented",
        ):
            self.assertIn(expected.lower(), normalized)

    def test_plan_links_step_3_evidence(self):
        doc = Path("docs/architecture/hermes_runtime_inclusion_plan.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("docs/architecture/hermes_runtime_contract_inventory.md", doc)

    def test_adapter_contract_update_records_memory_bridge_boundary(self):
        doc = Path("docs/architecture/hermes_adapter_contract_update.md").read_text(
            encoding="utf-8"
        )
        normalized = " ".join(doc.split()).lower()

        for expected in (
            "run_agent:AIAgent",
            "chat-oriented",
            "AIAgent._memory_manager.add_provider()",
            "Hermes-shaped provider named `maya`",
            "does not create a second memory store",
            "arbitrary plugin loading remains unavailable",
            "does not package Hermes into Maya",
        ):
            self.assertIn(expected.lower(), normalized)

    def test_plan_links_step_4_evidence(self):
        doc = Path("docs/architecture/hermes_runtime_inclusion_plan.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("docs/architecture/hermes_adapter_contract_update.md", doc)

    def test_package_inclusion_records_pinned_runtime_dependency(self):
        doc = Path("docs/architecture/hermes_package_inclusion.md").read_text(
            encoding="utf-8"
        )
        setup = Path("setup.py").read_text(encoding="utf-8")
        verifier = Path("scripts/verify_phase1_package.py").read_text(
            encoding="utf-8"
        )
        normalized = " ".join(doc.split()).lower()

        for expected in (
            "hermes-agent @ git+https://github.com/Bidzina83/hermes-agent.git",
            "b13e2fd6948a59eeb59fe618914147d97a2ee90a",
            "Requires-Python: >=3.11,<3.14",
            "local checkout",
            "`PYTHONPATH`",
            "`/opt/hermes`",
            "Python 3.14",
            "Installed Package Verification",
        ):
            self.assertIn(expected.lower(), normalized)
        for expected in (
            "HERMES_RUNTIME_REQUIREMENT",
            "git+https://github.com/Bidzina83/hermes-agent.git",
            "b13e2fd6948a59eeb59fe618914147d97a2ee90a",
            "python_requires='>=3.11,<3.14'",
            "install_requires",
        ):
            self.assertIn(expected, setup)
        for expected in (
            "HERMES_RUNTIME_COMMIT",
            "HERMES_RUNTIME_REQUIREMENT_PREFIX",
            "MAYA_PYTHON_REQUIRES",
            "Requires-Dist",
            "Requires-Python",
            "pinned Hermes runtime dependency",
        ):
            self.assertIn(expected, verifier)

    def test_plan_links_step_5_evidence(self):
        doc = Path("docs/architecture/hermes_runtime_inclusion_plan.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("docs/architecture/hermes_package_inclusion.md", doc)


if __name__ == "__main__":
    unittest.main()
