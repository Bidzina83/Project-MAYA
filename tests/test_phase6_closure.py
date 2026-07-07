import unittest
from pathlib import Path


class TestPhase6Closure(unittest.TestCase):
    def test_phase6_distribution_docs_record_scope_and_boundaries(self):
        scope = Path("docs/architecture/phase6_production_distribution.md").read_text(
            encoding="utf-8"
        )

        for expected in (
            "Windows desktop",
            "signed production distribution contract",
            "trusted public keys only",
            "Unsigned, tampered, wrong-key, wrong-platform",
            "scripts/build_phase6_release.py",
            "scripts/verify_phase6_release.py",
            "does not add automatic background updates",
        ):
            self.assertIn(expected, scope)

    def test_phase6_closure_maps_implementation_evidence(self):
        closure = Path(
            "docs/architecture/phase6_production_distribution_closure.md"
        ).read_text(encoding="utf-8")

        for expected in (
            "Implementation complete",
            "src/project_maya/release.py",
            "src/project_maya/update.py",
            "scripts/build_phase6_release.py",
            "scripts/verify_phase6_release.py",
            "scripts/verify_phase1_package.py",
            "Windows desktop is the only advertised",
            "external independent security review gate",
        ):
            self.assertIn(expected, closure)

    def test_phase6_docs_do_not_claim_forbidden_support(self):
        docs = "\n".join(
            Path(path).read_text(encoding="utf-8")
            for path in (
                "docs/architecture/phase6_production_distribution.md",
                "docs/architecture/phase6_production_distribution_closure.md",
            )
        )

        for forbidden in (
            "macOS is supported",
            "Linux is supported",
            "server is supported",
            "container is supported",
            "automatic background updates are enabled",
            "silently installs system dependencies",
            "creates customer tenant resources",
        ):
            self.assertNotIn(forbidden, docs)


if __name__ == "__main__":
    unittest.main()
