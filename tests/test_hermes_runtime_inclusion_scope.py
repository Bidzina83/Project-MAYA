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

    def test_skills_inclusion_boundary_records_artifact_contract(self):
        doc = Path("docs/architecture/hermes_skills_inclusion_boundary.md").read_text(
            encoding="utf-8"
        )
        skills = Path("src/project_maya/skills.py").read_text(encoding="utf-8")
        normalized = " ".join(doc.split()).lower()

        for expected in (
            "Bidzina83/hermes-agent",
            "Bidzina83/Hermes-Agent-Maya-Skills",
            "explicit allowlisting",
            "versioning",
            "sanitization",
            "hermes_default",
            "maya_trained",
            "skills.external_dirs",
            "local action authorization",
            "connector credential contracts",
            "model-egress governance",
            "governed memory",
            "does not",
            "package trained Maya skills",
            "claim that any skill is loaded or healthy",
        ):
            self.assertIn(expected.lower(), normalized)
        for expected in (
            "SkillOrigin",
            "HERMES_DEFAULT",
            "MAYA_TRAINED",
            "MayaSkillArtifact",
            "validate_skill_artifacts",
            "validate_skill_text_is_sanitized",
            "_FORBIDDEN_TEXT_MARKERS",
        ):
            self.assertIn(expected, skills)

    def test_plan_links_step_6_evidence(self):
        doc = Path("docs/architecture/hermes_runtime_inclusion_plan.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("docs/architecture/hermes_skills_inclusion_boundary.md", doc)

    def test_memory_hook_wiring_records_governed_tool_boundary(self):
        doc = Path("docs/architecture/hermes_memory_hook_wiring.md").read_text(
            encoding="utf-8"
        )
        adapter = Path("src/project_maya/adapters/hermes.py").read_text(
            encoding="utf-8"
        )
        normalized = " ".join(doc.split()).lower()

        for expected in (
            "AIAgent._memory_manager.add_provider()",
            "HermesMemoryProvider.begin_session",
            "HermesMemoryProvider.prefetch",
            "HermesMemoryProvider.synchronize_turn",
            "HermesMemoryProvider.end_session",
            "maya_memory_search",
            "maya_memory_recall",
            "maya_memory_remember",
            "GovernedMemoryRetriever",
            "does not create a second memory database",
            "does not persist Hermes-only state",
        ):
            self.assertIn(expected.lower(), normalized)
        for expected in (
            "maya_memory_search",
            "maya_memory_recall",
            "maya_memory_remember",
            "handle_tool_call",
            "get_tool_schemas",
            "_prefetch_records",
        ):
            self.assertIn(expected, adapter)

    def test_plan_links_step_7_evidence(self):
        doc = Path("docs/architecture/hermes_runtime_inclusion_plan.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("docs/architecture/hermes_memory_hook_wiring.md", doc)

    def test_governed_execution_smoke_records_runtime_and_cli_boundary(self):
        doc = Path("docs/architecture/hermes_governed_execution_smoke.md").read_text(
            encoding="utf-8"
        )
        test_source = Path(
            "tests/test_hermes_governed_execution_smoke.py"
        ).read_text(encoding="utf-8")
        normalized = " ".join(doc.split()).lower()

        for expected in (
            "build_local_product(config)",
            "maya run --config",
            "public Agent facade",
            "GovernedAgentRuntime",
            "HermesRuntimeAdapter",
            "runtime.execute",
            "model.egress",
            "idempotency key",
            "data classification",
            "prompt text",
            "secret://",
            "Step 9",
        ):
            self.assertIn(expected.lower(), normalized)
        for expected in (
            "test_build_local_product_run_emits_runtime_and_model_egress_audit",
            "test_maya_run_cli_emits_runtime_and_model_egress_audit",
            "authorization.runtime",
            "authorization.model_egress",
            'f"{__name__}:SmokeAIAgent"',
        ):
            self.assertIn(expected, test_source)

    def test_plan_links_step_8_evidence(self):
        doc = Path("docs/architecture/hermes_runtime_inclusion_plan.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("docs/architecture/hermes_governed_execution_smoke.md", doc)

    def test_installed_package_verification_records_hermes_runtime_mode(self):
        doc = Path(
            "docs/architecture/hermes_installed_package_verification.md"
        ).read_text(encoding="utf-8")
        script = Path("scripts/verify_phase1_package.py").read_text(
            encoding="utf-8"
        )
        normalized = " ".join(doc.split()).lower()

        for expected in (
            "--with-hermes-runtime",
            "--no-deps",
            "run_agent:AIAgent",
            "direct-url metadata",
            "--no-cache-dir",
            "stale local wheel cache",
            "hermes_cli.config",
            "load_env",
            "get_hermes_home",
            "_expand_env_vars",
            "b13e2fd6948a59eeb59fe618914147d97a2ee90a",
            "HermesRuntimeAdapter().compatibility()",
            "without editable installs",
            "PYTHONPATH",
            "/opt/hermes",
            "local checkout paths",
        ):
            self.assertIn(expected.lower(), normalized)
        for expected in (
            "with_hermes_runtime",
            "_install_wheel",
            "_verify_installed_hermes_runtime_dependency",
            "metadata.distribution('hermes-agent')",
            "from run_agent import AIAgent",
            "--no-cache-dir",
            "import hermes_cli.config as hermes_config",
            "required_config_attrs",
            "load_env",
            "get_hermes_home",
            "_expand_env_vars",
            "direct_url.json",
            "HermesRuntimeAdapter",
        ):
            self.assertIn(expected, script)

    def test_plan_links_step_9_evidence(self):
        doc = Path("docs/architecture/hermes_runtime_inclusion_plan.md").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "docs/architecture/hermes_installed_package_verification.md",
            doc,
        )

    def test_windows_manual_smoke_records_installed_runtime_result(self):
        doc = Path("docs/architecture/hermes_windows_manual_smoke.md").read_text(
            encoding="utf-8"
        )
        normalized = " ".join(doc.split()).lower()

        for expected in (
            "Step 10",
            "Windows installed-package smoke path",
            "--with-hermes-runtime",
            "neutral working directory",
            "from run_agent import AIAgent",
            "project_maya True",
            "stale local `hermes-agent` wheel cache",
            "--no-cache-dir",
            "hermes_cli.config",
            "load_config",
            "load_env",
            "get_hermes_home",
            "_expand_env_vars",
            "zero exit code",
            "does not claim full Windows product support",
        ):
            self.assertIn(expected.lower(), normalized)

    def test_plan_links_step_10_evidence(self):
        doc = Path("docs/architecture/hermes_runtime_inclusion_plan.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("docs/architecture/hermes_windows_manual_smoke.md", doc)

    def test_closure_audit_maps_phase_evidence_and_limits(self):
        doc = Path("docs/architecture/hermes_runtime_inclusion_closure.md").read_text(
            encoding="utf-8"
        )
        normalized = " ".join(doc.split()).lower()

        for expected in (
            "Step 11",
            "Hermes Runtime Inclusion phase is complete for its approved scope",
            "Acceptance Criteria Audit",
            "docs/architecture/hermes_runtime_inclusion_scope.md",
            "docs/architecture/hermes_source_strategy.md",
            "docs/architecture/hermes_runtime_contract_inventory.md",
            "docs/architecture/hermes_adapter_contract_update.md",
            "docs/architecture/hermes_package_inclusion.md",
            "docs/architecture/hermes_skills_inclusion_boundary.md",
            "docs/architecture/hermes_memory_hook_wiring.md",
            "docs/architecture/hermes_governed_execution_smoke.md",
            "docs/architecture/hermes_installed_package_verification.md",
            "docs/architecture/hermes_windows_manual_smoke.md",
            "scripts/verify_phase1_package.py --with-hermes-runtime",
            "tests/test_hermes_governed_execution_smoke.py",
            "known limits",
            "does not claim",
            "live model inference",
            "packaged trained Maya skills",
            "Metabase runtime packaging",
            "signed production installers",
        ):
            self.assertIn(expected.lower(), normalized)

    def test_plan_links_step_11_evidence(self):
        doc = Path("docs/architecture/hermes_runtime_inclusion_plan.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("docs/architecture/hermes_runtime_inclusion_closure.md", doc)


if __name__ == "__main__":
    unittest.main()
