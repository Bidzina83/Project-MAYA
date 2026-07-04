import unittest
from pathlib import Path


class TestPhase3MetabaseDocumentsClosure(unittest.TestCase):
    def test_phase3_metabase_documents_closure_links_required_evidence(self):
        closure = Path("docs/architecture/phase3_metabase_documents_closure.md").read_text(
            encoding="utf-8"
        )

        for step in (
            "1. Phase 3 scope gate",
            "2. Document capability core",
            "3. Document governance and audit",
            "4. Document CLI/API surface",
            "5. Packaged trained document skill",
            "6. Metabase integration contract",
            "7. Metabase client and health",
            "8. Governed Metabase dashboard provisioning",
            "9. Metabase CLI surface",
            "10. Doctor, repair, backup, and package verification",
            "11. Documentation and closure",
        ):
            self.assertIn(step, closure)

        for expected in (
            "src/project_maya/documents.py",
            "src/project_maya/metabase.py",
            "src/project_maya/packaged_skills/pdf/SKILL.md",
            "docs/architecture/phase3_document_capability.md",
            "docs/architecture/phase3_document_capability_hardening.md",
            "docs/architecture/phase3_document_skill_allowlist.md",
            "docs/architecture/phase3_metabase_capability.md",
            "docs/architecture/phase3_metabase_capability_hardening.md",
            "docs/architecture/phase3_backup_boundary.md",
            "tests/test_phase3_documents.py",
            "tests/test_phase3_metabase.py",
            "tests/test_phase3_backup_boundaries.py",
            "scripts/verify_phase1_package.py",
        ):
            self.assertIn(expected, closure)

    def test_phase3_metabase_documents_scope_preserves_v2_core_capabilities(self):
        scope = Path("docs/architecture/phase3_metabase_documents_scope.md").read_text(
            encoding="utf-8"
        )
        closure = Path("docs/architecture/phase3_metabase_documents_closure.md").read_text(
            encoding="utf-8"
        )

        for expected in (
            "governed views",
            "dashboards",
            "LibreOffice",
            "trained document skill",
            "claim platform support",
        ):
            self.assertIn(expected, scope + closure)
        for forbidden in (
            "package trained Maya skills;",
            "automate Microsoft Office or LibreOffice conversion",
            "perform live Metabase dashboard creation by default",
        ):
            self.assertNotIn(forbidden, scope + closure)

    def test_phase3_metabase_documents_closure_records_local_api_deferral(self):
        closure = Path("docs/architecture/phase3_metabase_documents_closure.md").read_text(
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
