import unittest
from pathlib import Path


class TestPhase3MetabaseDocumentsPackageVerification(unittest.TestCase):
    def test_clean_package_verifier_covers_phase3_metabase_document_surfaces(self):
        verifier = Path("scripts/verify_phase1_package.py").read_text(
            encoding="utf-8"
        )

        for expected in (
            "_verify_installed_phase3_metabase_document_surfaces",
            "phase3-metabase-documents-importable",
            "documents",
            "metabase",
            "documents.documents-root",
            "documents.documents-outputs",
            "documents.pdf-extraction",
            "documents.pdf-creation",
            "metabase.lifecycle",
            "last-applied-plan.json",
            "metabase.provisioning",
        ):
            self.assertIn(expected, verifier)


if __name__ == "__main__":
    unittest.main()
