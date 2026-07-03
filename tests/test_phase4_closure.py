import unittest
from pathlib import Path


class TestPhase4Closure(unittest.TestCase):
    def test_phase4_closure_links_required_evidence(self):
        closure = Path("docs/architecture/phase4_metabase_documents_closure.md").read_text(
            encoding="utf-8"
        )

        for expected in (
            "src/project_maya/documents.py",
            "src/project_maya/metabase.py",
            "tests/test_phase4_documents.py",
            "tests/test_phase4_metabase.py",
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


if __name__ == "__main__":
    unittest.main()
