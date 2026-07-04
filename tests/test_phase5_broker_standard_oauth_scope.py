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

    def test_phase5_closure_records_review_ready_boundary(self):
        closure = Path(
            "docs/architecture/phase5_broker_standard_oauth_closure.md"
        ).read_text(encoding="utf-8")

        for expected in (
            "Implementation complete; independent security review pending",
            "src/project_maya/broker.py",
            "maya broker conformance",
            "Maya-managed model billing readiness",
            "Final Phase 5 completion requires an independent security review",
        ):
            self.assertIn(expected, closure)

    def test_phase5_docs_do_not_claim_forbidden_broker_ownership(self):
        docs = "\n".join(
            Path(path).read_text(encoding="utf-8")
            for path in (
                "docs/architecture/phase5_broker_protocol.md",
                "docs/architecture/phase5_standard_oauth_lifecycle.md",
                "docs/architecture/phase5_token_lifecycle.md",
                "docs/architecture/phase5_broker_standard_oauth_closure.md",
            )
        )

        for forbidden in (
            "broker owns persistent memory",
            "broker owns customer files",
            "broker owns governance records",
            "broker owns workflows",
            "broker owns business records",
            "broker owns Metabase data",
            "Telegram is broker-assisted",
            "production installers are complete",
            "automatic updates are complete",
            "platform support is complete",
        ):
            self.assertNotIn(forbidden, docs)


if __name__ == "__main__":
    unittest.main()
