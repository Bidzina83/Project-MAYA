import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from project_maya import (
    ActionRequest,
    AuthorizationResult,
    DocumentCapabilityError,
    DocumentDependencyUnavailable,
    GovernanceDecision,
    LocalJsonlAuditSink,
    config_from_mapping,
    create_pdf,
    extract_pdf_text,
    inspect_document,
)
from tests.test_phase0_contracts import valid_config_mapping


class Gateway:
    def __init__(self, decision=GovernanceDecision.ALLOW):
        self.decision = decision
        self.requests = []

    def authorize(self, request: ActionRequest):
        self.requests.append(request)
        return AuthorizationResult(
            decision=self.decision,
            reason_code=f"test.{self.decision.value}",
        )


def _config(data_dir: Path):
    data = valid_config_mapping()
    data["runtime"]["enabled_profiles"] = ["maya-core", "maya-documents"]
    data["deployment"]["data_dir"] = str(data_dir)
    data["governance"]["policy_file"] = str(data_dir / "governance" / "policy.json")
    data["metabase"] = {
        "enabled": False,
        "deployment": "disabled",
        "endpoint": None,
        "application_database": None,
        "analytics_sources": [],
    }
    return config_from_mapping(data)


class TestPhase4Documents(unittest.TestCase):
    def test_inspect_rejects_paths_outside_documents_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            outside = Path(tmp) / "outside.txt"
            outside.write_text("outside", encoding="utf-8")

            with self.assertRaises(DocumentCapabilityError):
                inspect_document(
                    _config(data_dir),
                    outside,
                    gateway=Gateway(),
                )

    def test_inspect_governs_and_audits_without_full_path_or_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            docs = data_dir / "documents"
            docs.mkdir(parents=True)
            source = docs / "sample.txt"
            source.write_text("confidential text", encoding="utf-8")
            audit_path = data_dir / "governance" / "audit" / "runtime.jsonl"
            gateway = Gateway()

            result = inspect_document(
                _config(data_dir),
                source,
                gateway=gateway,
                audit_sink=LocalJsonlAuditSink(audit_path),
            )

            audit_text = audit_path.read_text(encoding="utf-8")
            record = json.loads(audit_text.splitlines()[0])

        self.assertEqual(result.status, "available")
        self.assertEqual(gateway.requests[0].capability, "documents.inspect")
        self.assertEqual(record["event_type"], "authorization.documents")
        self.assertNotIn("confidential text", audit_text)
        self.assertNotIn(str(source), audit_text)
        self.assertIn("maya-data/documents/sample.txt", audit_text)

    def test_extract_pdf_text_reports_missing_pypdf_without_leaking_source_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            docs = data_dir / "documents"
            docs.mkdir(parents=True)
            source = docs / "sample.pdf"
            source.write_bytes(b"%PDF-1.4\n%empty\n")

            with mock.patch("project_maya.documents.importlib.import_module") as import_module:
                import_module.side_effect = ImportError("missing")
                with self.assertRaises(DocumentDependencyUnavailable):
                    extract_pdf_text(
                        _config(data_dir),
                        source,
                        gateway=Gateway(),
                    )

    def test_create_pdf_requires_output_under_documents_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            outside = Path(tmp) / "out.pdf"

            with self.assertRaises(DocumentCapabilityError):
                create_pdf(
                    _config(data_dir),
                    text="hello",
                    output=outside,
                    gateway=Gateway(),
                )

    def test_create_pdf_denied_before_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            output = data_dir / "documents" / "out.pdf"

            with self.assertRaises(PermissionError):
                create_pdf(
                    _config(data_dir),
                    text="hello",
                    output=output,
                    gateway=Gateway(GovernanceDecision.DENY),
                )

            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
