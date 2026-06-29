import unittest
from pathlib import Path


class TestPhase2Scope(unittest.TestCase):
    def test_phase2_scope_gate_records_required_boundaries(self):
        root = Path(__file__).resolve().parents[1]
        scope = (root / "docs" / "architecture" / "phase2_scope.md").read_text(
            encoding="utf-8"
        )

        required_phrases = [
            "Enterprise operates without Maya cloud services.",
            "`broker.mode=disabled`",
            "Customer-owned model credentials",
            "Google, Slack, and Telegram",
            "local state reset from",
            "provider-token revocation",
            "Clean package verification",
            "shared Maya-managed Telegram bots",
            "Broker-disabled mode must not silently fall back to Maya cloud.",
            "Unsupported provider operations must report unavailable",
        ]
        missing = [phrase for phrase in required_phrases if phrase not in scope]

        self.assertEqual(missing, [])

    def test_phase2_starts_after_phase1_closure(self):
        root = Path(__file__).resolve().parents[1]

        self.assertTrue((root / "docs" / "architecture" / "phase1_closure.md").is_file())
        self.assertTrue((root / "docs" / "architecture" / "phase2_scope.md").is_file())


if __name__ == "__main__":
    unittest.main()
