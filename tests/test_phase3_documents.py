import importlib.util
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
    convert_document,
    create_pdf,
    extract_pdf_text,
    inspect_document,
    run_doctor,
)
from project_maya.adapters import HermesRuntimeAdapter
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

    def test_convert_document_rejects_paths_outside_documents_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            outside = Path(tmp) / "outside.docx"
            outside.write_text("outside", encoding="utf-8")

            with self.assertRaises(DocumentCapabilityError):
                convert_document(
                    _config(data_dir),
                    outside,
                    output=Path("out.pdf"),
                    output_format="pdf",
                    gateway=Gateway(),
                )

    def test_convert_document_denied_before_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            source = data_dir / "documents" / "input.docx"
            source.parent.mkdir(parents=True)
            source.write_text("content", encoding="utf-8")
            output = data_dir / "documents" / "outputs" / "out.pdf"

            with self.assertRaises(PermissionError):
                convert_document(
                    _config(data_dir),
                    source,
                    output=Path("out.pdf"),
                    output_format="pdf",
                    gateway=Gateway(GovernanceDecision.DENY),
                )

            self.assertFalse(output.exists())

    def test_convert_document_uses_libreoffice_and_writes_outputs_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            source = data_dir / "documents" / "input.docx"
            source.parent.mkdir(parents=True)
            source.write_text("content", encoding="utf-8")

            def fake_run(command, **kwargs):
                output_dir = Path(command[command.index("--outdir") + 1])
                (output_dir / "input.pdf").write_bytes(b"%PDF-1.4\n")
                return mock.Mock(returncode=0)

            with mock.patch("project_maya.documents.shutil.which", return_value="soffice"):
                with mock.patch("project_maya.documents.subprocess.run", side_effect=fake_run):
                    result = convert_document(
                        _config(data_dir),
                        source,
                        output=Path("converted.pdf"),
                        output_format="pdf",
                        gateway=Gateway(),
                    )

        self.assertEqual(result.status, "converted")
        self.assertIn("documents/outputs/converted.pdf", result.output_ref)
        self.assertEqual(result.metadata["backend"], "libreoffice")

    @unittest.skipUnless(
        importlib.util.find_spec("pypdf") is not None
        and importlib.util.find_spec("reportlab") is not None,
        "pypdf and reportlab are required for real PDF round-trip coverage",
    )
    def test_create_pdf_and_extract_text_round_trip_to_outputs_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            config = _config(data_dir)
            gateway = Gateway()

            created = create_pdf(
                config,
                text="Maya document round trip",
                output=Path("round-trip.pdf"),
                gateway=gateway,
            )
            extracted, text = extract_pdf_text(
                config,
                data_dir / "documents" / "outputs" / "round-trip.pdf",
                output=Path("round-trip.txt"),
                gateway=gateway,
            )

            output_text = (
                data_dir / "documents" / "outputs" / "round-trip.txt"
            ).read_text(encoding="utf-8")

        self.assertEqual(created.status, "created")
        self.assertEqual(extracted.status, "extracted")
        self.assertIn("documents/outputs/round-trip.pdf", created.output_ref)
        self.assertIn("Maya document round trip", text)
        self.assertIn("Maya document round trip", output_text)
        self.assertEqual(
            [request.capability for request in gateway.requests],
            ["documents.create-pdf", "documents.extract-text"],
        )

    def test_markdown_pdf_creation_reports_missing_markdown_without_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            output = data_dir / "documents" / "outputs" / "markdown.pdf"
            real_import = __import__("importlib").import_module

            def import_or_missing_markdown(name):
                if name == "markdown":
                    raise ImportError("missing markdown")
                return real_import(name)

            with mock.patch(
                "project_maya.documents.importlib.import_module",
                side_effect=import_or_missing_markdown,
            ):
                with self.assertRaises(DocumentDependencyUnavailable):
                    create_pdf(
                        _config(data_dir),
                        text="# Heading",
                        output=Path("markdown.pdf"),
                        source_format="markdown",
                        gateway=Gateway(),
                    )

            self.assertFalse(output.exists())

    def test_doctor_reports_document_output_and_operation_readiness(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            report = run_doctor(
                _config(data_dir),
                HermesRuntimeAdapter(factory_path="missing.hermes:factory"),
            )

        checks = {check.name: check for check in report.checks}
        self.assertIn("documents.documents-root", checks)
        self.assertIn("documents.documents-cache", checks)
        self.assertIn("documents.documents-outputs", checks)
        self.assertIn("documents.pdf-extraction", checks)
        self.assertIn("documents.pdf-creation", checks)
        self.assertIn("documents.libreoffice-conversion", checks)
        self.assertNotIn("secret://", checks["documents.pdf-extraction"].message)


if __name__ == "__main__":
    unittest.main()
