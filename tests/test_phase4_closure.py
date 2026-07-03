import unittest
from pathlib import Path


class TestPhase4Closure(unittest.TestCase):
    def test_phase4_closure_links_required_evidence(self):
        closure = Path("docs/architecture/phase4_metabase_documents_closure.md").read_text(
            encoding="utf-8"
        )

        for step in (
            "1. Phase 4 scope gate",
            "2. Document capability core",
            "3. Document governance and audit",
            "4. Document CLI/API surface",
            "5. Skill inclusion boundary for documents",
            "6. Metabase integration contract",
            "7. Metabase client and health",
            "8. Metabase provisioning foundation",
            "9. Metabase CLI surface",
            "10. Doctor, repair, backup, and package verification",
            "11. Documentation and closure",
        ):
            self.assertIn(step, closure)

        for expected in (
            "src/project_maya/documents.py",
            "src/project_maya/metabase.py",
            "docs/architecture/phase4_document_capability.md",
            "docs/architecture/phase4_document_capability_hardening.md",
            "docs/architecture/phase4_document_skill_allowlist.md",
            "docs/architecture/phase4_metabase_capability.md",
            "docs/architecture/phase4_metabase_capability_hardening.md",
            "docs/architecture/phase4_backup_boundary.md",
            "tests/test_phase4_documents.py",
            "tests/test_phase4_metabase.py",
            "tests/test_phase4_backup_boundaries.py",
            "scripts/verify_phase1_package.py",
        ):
            self.assertIn(expected, closure)

    def test_phase4_scope_preserves_non_goals(self):
        scope = Path("docs/architecture/phase4_metabase_documents_scope.md").read_text(
            encoding="utf-8"
        )

        for expected in (
            "silently install",
            "bulk-package trained Maya skills",
            "live Metabase dashboard creation",
            "claim platform support",
        ):
            self.assertIn(expected, scope)

    def test_phase4_closure_records_local_api_deferral(self):
        closure = Path("docs/architecture/phase4_metabase_documents_closure.md").read_text(
            encoding="utf-8"
        )

        for expected in (
            "Local API document and Metabase routes are deferred by design",
            "route versioning",
            "request-size limits",
            "upload/download handling",
            "client authorization",
        ):
            self.assertIn(expected, closure)


if __name__ == "__main__":
    unittest.main()
