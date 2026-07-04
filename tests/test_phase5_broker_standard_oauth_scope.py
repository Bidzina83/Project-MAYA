import unittest
from pathlib import Path


class TestPhase5BrokerStandardOAuthScope(unittest.TestCase):
    def test_phase5_is_reserved_for_broker_and_standard_oauth(self):
        scope = Path("docs/architecture/phase5_broker_standard_oauth_scope.md").read_text(
            encoding="utf-8"
        )

        for expected in (
            "Broker and Standard OAuth",
            "mock broker conformance",
            "cryptographic instance protocol",
            "approved token",
            "production Google and Slack OAuth",
            "Maya-managed model billing",
            "V2 Phase 4 work",
            "credential-lifecycle tests",
        ):
            self.assertIn(expected, scope)


if __name__ == "__main__":
    unittest.main()
