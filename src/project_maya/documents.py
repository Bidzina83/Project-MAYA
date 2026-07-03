"""Governed local document capabilities for Project MAYA."""

from __future__ import annotations

import html
import importlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from .audit import AuditRecord, AuditSink, NullAuditSink
from .config import ComponentProfile, MayaConfig
from .governance import ActionAuthorizationGateway, ActionDeniedError, ActionRequest


class DocumentCapabilityError(RuntimeError):
    """Raised when a governed document operation cannot be completed."""


class DocumentDependencyUnavailable(DocumentCapabilityError):
    """Raised when an optional document dependency is not installed."""


@dataclass(frozen=True)
class DocumentOperationResult:
    operation: str
    status: str
    source_ref: str | None = None
    output_ref: str | None = None
    file_type: str | None = None
    bytes_read: int = 0
    bytes_written: int = 0
    pages: int | None = None
    characters: int | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def redacted_summary(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "operation": self.operation,
            "status": self.status,
            "source_ref": self.source_ref,
            "output_ref": self.output_ref,
            "file_type": self.file_type,
            "bytes_read": self.bytes_read,
            "bytes_written": self.bytes_written,
            "pages": self.pages,
            "characters": self.characters,
            "metadata": dict(self.metadata),
        }
        return {key: value for key, value in payload.items() if value is not None}


def inspect_document(
    config: MayaConfig,
    source: Path,
    *,
    gateway: ActionAuthorizationGateway,
    actor_id: str = "local-user",
    audit_sink: AuditSink | None = None,
    data_classification: str = "internal",
    idempotency_key: str | None = None,
) -> DocumentOperationResult:
    _require_documents_profile(config)
    source_path = _resolve_document_path(config, source)
    _require_supported_source(source_path)
    _authorize_document_action(
        gateway,
        audit_sink or NullAuditSink(),
        actor_id=actor_id,
        operation="inspect",
        source_ref=_redacted_ref(config, source_path),
        output_ref=None,
        file_type=_file_type(source_path),
        data_classification=data_classification,
        idempotency_key=idempotency_key,
        mutation=False,
    )
    stat = source_path.stat()
    return DocumentOperationResult(
        operation="inspect",
        status="available",
        source_ref=_redacted_ref(config, source_path),
        file_type=_file_type(source_path),
        bytes_read=stat.st_size,
        metadata={
            "extension": source_path.suffix.lower().removeprefix(".") or "none",
            "name_hash": str(abs(hash(source_path.name)) % 1000000),
        },
    )


def extract_pdf_text(
    config: MayaConfig,
    source: Path,
    *,
    gateway: ActionAuthorizationGateway,
    actor_id: str = "local-user",
    audit_sink: AuditSink | None = None,
    data_classification: str = "internal",
    idempotency_key: str | None = None,
) -> tuple[DocumentOperationResult, str]:
    _require_documents_profile(config)
    source_path = _resolve_document_path(config, source)
    if source_path.suffix.lower() != ".pdf":
        raise DocumentCapabilityError("extract-text supports PDF sources only")
    _authorize_document_action(
        gateway,
        audit_sink or NullAuditSink(),
        actor_id=actor_id,
        operation="extract-text",
        source_ref=_redacted_ref(config, source_path),
        output_ref=None,
        file_type="pdf",
        data_classification=data_classification,
        idempotency_key=idempotency_key,
        mutation=False,
    )
    try:
        pypdf = importlib.import_module("pypdf")
    except ImportError as exc:
        raise DocumentDependencyUnavailable(
            "pypdf is required for PDF text extraction"
        ) from exc
    reader = pypdf.PdfReader(str(source_path))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(pages)
    result = DocumentOperationResult(
        operation="extract-text",
        status="extracted",
        source_ref=_redacted_ref(config, source_path),
        file_type="pdf",
        bytes_read=source_path.stat().st_size,
        pages=len(reader.pages),
        characters=len(text),
    )
    return result, text


def create_pdf(
    config: MayaConfig,
    *,
    text: str,
    output: Path,
    source_format: str = "plain",
    gateway: ActionAuthorizationGateway,
    actor_id: str = "local-user",
    audit_sink: AuditSink | None = None,
    data_classification: str = "internal",
    idempotency_key: str | None = None,
) -> DocumentOperationResult:
    _require_documents_profile(config)
    if not text.strip():
        raise DocumentCapabilityError("document text is required")
    output_path = _resolve_document_path(config, output, must_exist=False)
    if output_path.suffix.lower() != ".pdf":
        raise DocumentCapabilityError("create-pdf output must end with .pdf")
    _authorize_document_action(
        gateway,
        audit_sink or NullAuditSink(),
        actor_id=actor_id,
        operation="create-pdf",
        source_ref=None,
        output_ref=_redacted_ref(config, output_path),
        file_type="pdf",
        data_classification=data_classification,
        idempotency_key=idempotency_key,
        mutation=True,
    )
    try:
        canvas_module = importlib.import_module("reportlab.pdfgen.canvas")
        pagesizes = importlib.import_module("reportlab.lib.pagesizes")
    except ImportError as exc:
        raise DocumentDependencyUnavailable(
            "reportlab is required for PDF creation"
        ) from exc
    rendered = _render_source_text(text, source_format)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas_module.Canvas(str(output_path), pagesize=pagesizes.letter)
    width, height = pagesizes.letter
    y = height - 72
    for line in _plain_lines(rendered):
        if y < 72:
            pdf.showPage()
            y = height - 72
        pdf.drawString(72, y, line[:1000])
        y -= 14
    pdf.save()
    return DocumentOperationResult(
        operation="create-pdf",
        status="created",
        output_ref=_redacted_ref(config, output_path),
        file_type="pdf",
        bytes_written=output_path.stat().st_size,
        characters=len(text),
        metadata={"source_format": source_format},
    )


def document_capability_checks(config: MayaConfig) -> tuple[DocumentOperationResult, ...]:
    if ComponentProfile.DOCUMENTS not in config.runtime.enabled_profiles:
        return ()
    documents_dir = config.deployment.data_dir / "documents"
    cache_dir = documents_dir / "cache"
    results = []
    for operation, path in (
        ("documents-root", documents_dir),
        ("documents-cache", cache_dir),
    ):
        status = "available" if path.is_dir() else "will_create"
        if path.exists() and not path.is_dir():
            status = "invalid"
        results.append(
            DocumentOperationResult(
                operation=operation,
                status=status,
                output_ref=_redacted_ref(config, path),
                metadata={"profile": ComponentProfile.DOCUMENTS.value},
            )
        )
    return tuple(results)


def _require_documents_profile(config: MayaConfig) -> None:
    if ComponentProfile.DOCUMENTS not in config.runtime.enabled_profiles:
        raise DocumentCapabilityError("maya-documents profile is not enabled")


def _resolve_document_path(
    config: MayaConfig,
    path: Path,
    *,
    must_exist: bool = True,
) -> Path:
    root = (config.deployment.data_dir / "documents").resolve()
    candidate = path if path.is_absolute() else root / path
    resolved = candidate.resolve()
    if resolved != root and root not in resolved.parents:
        raise DocumentCapabilityError("document path is outside maya-data/documents")
    if must_exist and not resolved.is_file():
        raise DocumentCapabilityError("document source does not exist")
    if any(part in {"", ".", ".."} for part in resolved.relative_to(root).parts):
        raise DocumentCapabilityError("document path is unsafe")
    return resolved


def _require_supported_source(path: Path) -> None:
    if _file_type(path) not in {"pdf", "txt", "md", "markdown"}:
        raise DocumentCapabilityError("unsupported document type")


def _file_type(path: Path) -> str:
    suffix = path.suffix.lower().removeprefix(".")
    return suffix or "none"


def _redacted_ref(config: MayaConfig, path: Path) -> str:
    root = config.deployment.data_dir.resolve()
    try:
        relative = path.resolve().relative_to(root).as_posix()
    except ValueError:
        relative = "external"
    return f"maya-data/{relative}"


def _authorize_document_action(
    gateway: ActionAuthorizationGateway,
    audit_sink: AuditSink,
    *,
    actor_id: str,
    operation: str,
    source_ref: str | None,
    output_ref: str | None,
    file_type: str,
    data_classification: str,
    idempotency_key: str | None,
    mutation: bool,
) -> None:
    target = output_ref or source_ref or "maya-data/documents"
    metadata = {
        "source_ref": source_ref or "none",
        "output_ref": output_ref or "none",
        "file_type": file_type,
        "mutation": str(mutation).lower(),
    }
    action = ActionRequest(
        actor_id=actor_id,
        capability=f"documents.{operation}",
        target=target,
        operation=operation,
        data_classification=data_classification,
        idempotency_key=idempotency_key,
        metadata=metadata,
    )
    result = gateway.authorize(action)
    if result.audit_required:
        audit_sink.write(
            AuditRecord(
                event_type="authorization.documents",
                decision=result.decision.value,
                reason_code=result.reason_code,
                actor_id=action.actor_id,
                capability=action.capability,
                target=action.target,
                operation=action.operation,
                data_classification=action.data_classification,
                idempotency_key=action.idempotency_key,
                metadata=action.metadata,
            )
        )
    if not result.allowed:
        raise ActionDeniedError(result.reason_code)


def _render_source_text(text: str, source_format: str) -> str:
    normalized = source_format.lower()
    if normalized in {"plain", "txt", "text"}:
        return text
    if normalized in {"markdown", "md"}:
        try:
            markdown = importlib.import_module("markdown")
        except ImportError as exc:
            raise DocumentDependencyUnavailable(
                "Markdown is required for Markdown PDF creation"
            ) from exc
        return html.unescape(markdown.markdown(text))
    raise DocumentCapabilityError("source_format must be plain or markdown")


def _plain_lines(text: str) -> list[str]:
    cleaned = text.replace("<p>", "").replace("</p>", "\n")
    cleaned = cleaned.replace("<br />", "\n").replace("<br>", "\n")
    lines = [line.strip() for line in cleaned.splitlines()]
    return [line for line in lines if line] or [""]
