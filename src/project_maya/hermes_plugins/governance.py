"""Native Hermes enforcement adapters over Maya's existing policy engine."""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
import re
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from threading import get_ident
from time import monotonic
from typing import Any, ClassVar, Iterator, Mapping
from urllib.parse import urlsplit

from ..audit import AuditRecord, AuditSink, LocalJsonlAuditSink
from ..config import MayaConfig, config_from_mapping
from ..governance import ActionDeniedError, ActionRequest, ActionAuthorizationGateway, load_policy_gateway


CONTRACT_VERSION = "project-maya.hermes-governance.v1"
REQUIRED_CAPABILITIES = frozenset({
    "fail_closed_execution", "mandatory_middleware", "auxiliary_sync",
    "auxiliary_async", "trusted_context_propagation", "tool_result_validation",
    "iteration_limit_summary", "single_transport_attempt",
    "model_output_validation",
})
MAX_PAYLOAD_BYTES = 1_048_576
_SECRET = re.compile(
    r"sk-(?:proj-)?[A-Za-z0-9_-]{16,}|"
    r"\b\d{6,12}:[A-Za-z0-9_-]{20,}|"
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|"
    r"\bBearer\s+[A-Za-z0-9._~+/-]{16,}",
    re.IGNORECASE,
)
_SECRET_FIELDS = frozenset({"api_key", "access_token", "refresh_token", "password", "authorization"})
_PUBLIC_REASONS = frozenset({
    "identity_missing", "sensitive_payload", "payload_unsupported", "payload_too_large",
    "payload_invalid", "managed_gateway_unavailable", "model_route_mismatch",
    "model_route_invalid", "action_denied", "authorization_unavailable",
    "audit_unavailable", "model_execution_failed", "tool_execution_failed",
    "tool_unmapped", "file_target_invalid", "file_target_outside_root",
    "model_output_failed",
})


class GovernanceBoundaryError(ActionDeniedError):
    """A secret-safe denial or unavailable enforcement boundary."""


@dataclass(frozen=True)
class RequestIdentity:
    actor_id: str
    data_classification: str = "confidential"


SESSION_WRITE_CONTRACT = "project-maya.hermes-session-write.v1"
REQUEST_LIFECYCLE_CONTRACT = "project-maya.request-lifecycle.v1"
SESSION_OPERATIONS = frozenset({"create", "append", "rewrite", "compact", "delete", "metadata"})


@dataclass
class _SessionWriteLease:
    active: bool = True
    parent: _SessionWriteLease | None = None
    deadline: float | None = None
    termination: str | None = None

    def revoke(self, reason: str) -> None:
        if reason not in {"completed", "cancelled", "timeout", "failed"}:
            raise GovernanceBoundaryError("governance.request_termination_invalid")
        if reason == "completed" and self.deadline is not None and monotonic() >= self.deadline:
            reason = "timeout"
        self.active = False
        if self.termination is None:
            self.termination = reason

    def revoke_request(self, reason: str) -> None:
        """Invalidate siblings as well as this receiver's descendant leases."""
        root = self
        while root.parent is not None:
            root = root.parent
        root.revoke(reason)
        self.revoke(reason)

    @property
    def is_active(self) -> bool:
        if self.deadline is not None and monotonic() >= self.deadline:
            self.revoke("timeout")
        return self.active and (self.parent is None or self.parent.is_active)


@dataclass(frozen=True)
class SessionWriteContext:
    contract: ClassVar[str] = REQUEST_LIFECYCLE_CONTRACT
    identity: RequestIdentity
    request_id: str
    session_id: str
    database: Path
    operations: frozenset[str]
    thread_id: int
    task: Any
    lease: _SessionWriteLease


_session_write: ContextVar[SessionWriteContext | None] = ContextVar("maya_session_write", default=None)


def _current_task() -> Any:
    try:
        return asyncio.current_task()
    except RuntimeError:
        return None


@contextmanager
def bind_session_write(request_id: str, session_id: str, database: Path,
                       operations: frozenset[str], *,
                       timeout_seconds: float | None = None) -> Iterator[SessionWriteContext]:
    """Trusted host binding; never call with model/tool supplied authority."""
    identity = _identity.get()
    if identity is None:
        raise GovernanceBoundaryError("governance.identity_missing")
    for value in (request_id, session_id):
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.:@-]{1,128}", value):
            raise GovernanceBoundaryError("governance.session_context_invalid")
    if not isinstance(operations, frozenset) or not operations or not operations <= SESSION_OPERATIONS:
        raise GovernanceBoundaryError("governance.session_context_invalid")
    if timeout_seconds is not None and (
            isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float))
            or not 0 < timeout_seconds <= 3600 or not math.isfinite(timeout_seconds)):
        raise GovernanceBoundaryError("governance.request_timeout_invalid")
    lease = _SessionWriteLease(deadline=None if timeout_seconds is None else monotonic() + timeout_seconds)
    context = SessionWriteContext(identity, request_id, session_id,
                                  Path(database).resolve(), operations, get_ident(), _current_task(), lease)
    token = _session_write.set(context)
    try:
        yield context
    except asyncio.CancelledError:
        lease.revoke("cancelled")
        raise
    except BaseException:
        lease.revoke("failed")
        raise
    finally:
        lease.revoke("completed")
        _session_write.reset(token)


@contextmanager
def _bind_session_handoff(source: SessionWriteContext, parent: _SessionWriteLease) -> Iterator[None]:
    """Internal trusted-host rebinding; inherit limits, never caller-selected authority."""
    if not source.lease.is_active or not parent.is_active:
        raise GovernanceBoundaryError("governance.session_handoff_expired")
    lease = _SessionWriteLease(parent=parent)
    with bind_request_identity(source.identity.actor_id, source.identity.data_classification):
        token = _session_write.set(SessionWriteContext(
            source.identity, source.request_id, source.session_id, source.database,
            source.operations, get_ident(), _current_task(), lease,
        ))
        try:
            yield
        finally:
            lease.active = False
            _session_write.reset(token)


_identity: ContextVar[RequestIdentity | None] = ContextVar("maya_governance_identity", default=None)


@contextmanager
def bind_request_identity(actor_id: str, classification: str = "confidential") -> Iterator[None]:
    """Bind identity supplied by Maya's authenticated host, not tool arguments."""
    if not actor_id or len(actor_id) > 128 or not re.fullmatch(r"[A-Za-z0-9_.:@-]+", actor_id):
        raise GovernanceBoundaryError("governance.identity_invalid")
    if classification not in {"public", "internal", "confidential", "restricted"}:
        raise GovernanceBoundaryError("governance.classification_invalid")
    token = _identity.set(RequestIdentity(actor_id, classification))
    try:
        yield
    finally:
        _identity.reset(token)


def require_runtime_contract(module: Any | None = None) -> None:
    """Reject the current fail-open pin and unqualified replacement contracts."""
    try:
        module = module if module is not None else import_module("hermes_cli.middleware")
        contract = getattr(module, "MAYA_GOVERNANCE_CONTRACT", {})
        if not isinstance(contract, Mapping) or contract.get("version") != CONTRACT_VERSION:
            raise GovernanceBoundaryError("governance.hermes_contract_unsupported")
        capabilities = contract.get("capabilities", ())
        if not isinstance(capabilities, (list, tuple, set, frozenset)) or not REQUIRED_CAPABILITIES.issubset(capabilities):
            raise GovernanceBoundaryError("governance.hermes_contract_incomplete")
        for name in ("run_llm_execution_middleware", "run_tool_execution_middleware", "run_tool_result_middleware", "run_model_output_middleware", "require_middleware", "validate_mandatory_middleware", "require_single_attempt_client"):
            if not callable(getattr(module, name, None)):
                raise GovernanceBoundaryError("governance.hermes_contract_incomplete")
    except GovernanceBoundaryError:
        raise
    except Exception:
        raise GovernanceBoundaryError("governance.hermes_contract_unavailable") from None


def ensure_governance_registered() -> None:
    """Fail before constructing AIAgent if the mandatory plugin did not load."""
    require_runtime_contract()
    try:
        manager = import_module("hermes_cli.plugins").get_plugin_manager()
        manager.discover_and_load()
        if import_module("hermes_cli.middleware").validate_mandatory_middleware() is not True:
            raise GovernanceBoundaryError("governance.middleware_missing")
    except GovernanceBoundaryError:
        raise
    except Exception:
        raise GovernanceBoundaryError("governance.registration_unavailable") from None


def _checked_payload(payload: Any) -> str:
    def check(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                if not isinstance(key, str) or key.lower() in _SECRET_FIELDS:
                    raise GovernanceBoundaryError("governance.sensitive_payload")
                check(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                check(item)
        elif isinstance(value, str):
            if _SECRET.search(value):
                raise GovernanceBoundaryError("governance.sensitive_payload")
            if value.lstrip().startswith(("{", "[")):
                try:
                    decoded = json.loads(value)
                except ValueError:
                    pass
                else:
                    check(decoded)
        elif value is not None and not isinstance(value, (bool, int, float)):
            raise GovernanceBoundaryError("governance.payload_unsupported")
    try:
        check(payload)
        encoded = json.dumps(payload, allow_nan=False, sort_keys=True)
        if len(encoded.encode("utf-8")) > MAX_PAYLOAD_BYTES:
            raise GovernanceBoundaryError("governance.payload_too_large")
        return encoded
    except GovernanceBoundaryError:
        raise
    except Exception:
        raise GovernanceBoundaryError("governance.payload_invalid") from None


def _target_ref(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


class MayaGovernancePlugin:
    """Authorize native execution callbacks through the existing local gateway."""

    def __init__(self, config: MayaConfig, gateway: ActionAuthorizationGateway, audit: AuditSink) -> None:
        self.config = config
        self.gateway = gateway
        self.audit = audit

    def register(self, ctx: Any, *, runtime_module: Any | None = None) -> None:
        require_runtime_contract(runtime_module)
        module = runtime_module if runtime_module is not None else import_module("hermes_cli.middleware")
        ctx.register_middleware("llm_execution", self.model_execution)
        ctx.register_middleware("tool_execution", self.tool_execution)
        ctx.register_middleware("tool_result", self.tool_result)
        ctx.register_middleware("model_output", self.model_output)
        # The runtime must enforce presence on main AND auxiliary dispatch paths.
        module.require_middleware("llm_execution", self.model_execution)
        module.require_middleware("tool_execution", self.tool_execution)
        module.require_middleware("tool_result", self.tool_result)
        module.require_middleware("model_output", self.model_output)

    def _actor(self) -> RequestIdentity:
        identity = _identity.get()
        if identity is None:
            raise GovernanceBoundaryError("governance.identity_missing")
        bound = _session_write.get()
        if bound is not None and (
                not bound.lease.is_active or identity != bound.identity
                or bound.thread_id != get_ident() or bound.task is not _current_task()):
            raise GovernanceBoundaryError("governance.session_context_missing")
        return identity

    def register_session_write_candidate(self, ctx: Any, module: Any) -> None:
        """Explicit source-candidate extension; does not qualify production."""
        if getattr(module, "SESSION_WRITE_CONTRACT", None) != SESSION_WRITE_CONTRACT:
            raise GovernanceBoundaryError("governance.session_contract_unsupported")
        ctx.register_middleware("session_write", self.session_write)
        module.require_middleware("session_write", self.session_write)

    def session_write(self, *, result: Any, **context: Any) -> Any:
        """Authorize final serialized storage values, independently of model output."""
        try:
            identity = self._actor()
            bound = _session_write.get()
            if (bound is None or not bound.lease.is_active or identity != bound.identity or bound.thread_id != get_ident()
                    or bound.task is not _current_task()):
                raise GovernanceBoundaryError("governance.session_context_missing")
            if (context.get("contract") != SESSION_WRITE_CONTRACT
                    or context.get("session_id") != bound.session_id
                    or context.get("purpose") != "hermes_conversation"
                    or Path(context.get("database", "")).resolve() != bound.database
                    or context.get("operation") not in bound.operations):
                raise GovernanceBoundaryError("governance.session_context_mismatch")
            _checked_payload(result)
            self._authorize(ActionRequest(
                identity.actor_id, "session.write", "session:" + bound.session_id,
                context["operation"], data_classification=identity.data_classification,
            ))
            # This records authorization, not a successful SQLite commit.
            self.audit.write(AuditRecord(
                event_type="validation.hermes_session_write", decision="allow",
                reason_code="governance.session_write_authorized", actor_id=identity.actor_id,
                capability="session.write", target=_target_ref(bound.session_id + ":" + bound.request_id),
                operation=context["operation"], data_classification=identity.data_classification,
            ))
            return result
        except GovernanceBoundaryError:
            self._audit_block("session.write", GovernanceBoundaryError("governance.action_denied"))
            raise GovernanceBoundaryError("governance.action_denied") from None
        except Exception:
            self._audit_block("session.write", GovernanceBoundaryError("governance.authorization_unavailable"))
            raise GovernanceBoundaryError("governance.authorization_unavailable") from None

    def _authorize(self, action: ActionRequest) -> None:
        try:
            result = self.gateway.authorize(action)
            # Do not persist caller-controlled paths, prompts, or policy reason text.
            self.audit.write(AuditRecord(
                event_type="authorization.hermes_boundary",
                decision=result.decision.value,
                reason_code="governance.allowed" if result.allowed else "governance.denied",
                actor_id=action.actor_id,
                capability=action.capability,
                target=_target_ref(action.target),
                operation=action.operation,
                data_classification=action.data_classification,
            ))
            if not result.allowed or result.constraints or result.redactions:
                # Approval/redaction/constraints are not silently treated as allow.
                raise GovernanceBoundaryError("governance.action_denied")
        except GovernanceBoundaryError:
            raise
        except Exception:
            raise GovernanceBoundaryError("governance.authorization_unavailable") from None

    def _audit_block(self, capability: str, error: GovernanceBoundaryError) -> None:
        identity = _identity.get()
        try:
            self.audit.write(AuditRecord(
                event_type="denial.hermes_boundary", decision="deny",
                reason_code="governance.boundary_blocked",
                actor_id=identity.actor_id if identity else "unresolved",
                capability=capability, target="withheld", operation="execute",
                data_classification=identity.data_classification if identity else "restricted",
            ))
        except Exception:
            raise GovernanceBoundaryError("governance.audit_unavailable") from None

    def _result(self, action: ActionRequest, result: Any) -> Any:
        _checked_payload(result)
        self.audit.write(AuditRecord(
            event_type="validation.hermes_tool_result", decision="allow",
            reason_code="governance.result_validated", actor_id=action.actor_id,
            capability=action.capability, target=_target_ref(action.target),
            operation=action.operation, data_classification=action.data_classification,
        ))
        return result

    def model_execution(self, *, request: dict[str, Any], next_call: Any, **context: Any) -> Any:
        try:
            identity = self._actor()
            _checked_payload(request)
            provider = context.get("provider")
            endpoint = context.get("base_url")
            expected = self.config.llm.endpoint
            if expected is None and self.config.llm.mode == "customer_owned" and self.config.llm.provider == "openai":
                expected = "https://api.openai.com/v1"
            if self.config.llm.mode == "maya_managed":
                raise GovernanceBoundaryError("governance.managed_gateway_unavailable")
            if not expected or provider != self.config.llm.provider or endpoint != expected:
                raise GovernanceBoundaryError("governance.model_route_mismatch")
            parsed = urlsplit(expected)
            if parsed.username or parsed.password or parsed.query or parsed.fragment:
                raise GovernanceBoundaryError("governance.model_route_invalid")
            if parsed.scheme != "https" and not (self.config.llm.mode == "local" and parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}):
                raise GovernanceBoundaryError("governance.model_route_invalid")
            if request.get("model") != self.config.llm.model:
                raise GovernanceBoundaryError("governance.model_route_mismatch")
            self._authorize(ActionRequest(
                identity.actor_id, "model.egress", "model:" + provider, "infer",
                data_classification=identity.data_classification,
            ))
        except GovernanceBoundaryError as exc:
            error = self._public_error(exc)
            self._audit_block("model.egress", error)
            raise error from None
        except Exception:
            error = GovernanceBoundaryError("governance.model_execution_failed")
            self._audit_block("model.egress", error)
            raise error from None

        # Transport failures belong to Hermes' retry dispatcher, not policy.
        # The auxiliary boundary redacts exhausted errors; main-loop error
        # handling is still a required qualification gate before activation.
        try:
            return next_call(request)
        except GovernanceBoundaryError as exc:
            error = self._public_error(exc)
            self._audit_block("model.egress", error)
            raise error from None

    def model_output(self, *, result: Any, **context: Any) -> Any:
        """Authorize the assembled disclosure at the native output boundary."""
        try:
            identity = self._actor()
            _checked_payload(result)
            expected = self.config.llm.endpoint
            if expected is None and self.config.llm.mode == "customer_owned" and self.config.llm.provider == "openai":
                expected = "https://api.openai.com/v1"
            if (self.config.llm.mode == "maya_managed" or not expected
                    or context.get("provider") != self.config.llm.provider
                    or context.get("model") != self.config.llm.model
                    or context.get("base_url") != expected):
                raise GovernanceBoundaryError("governance.model_route_mismatch")
            action = ActionRequest(
                identity.actor_id, "model.output", "model:" + self.config.llm.provider,
                "disclose", data_classification=identity.data_classification,
            )
            self._authorize(action)
            self.audit.write(AuditRecord(
                event_type="validation.hermes_model_output", decision="allow",
                reason_code="governance.result_validated", actor_id=action.actor_id,
                capability=action.capability, target=_target_ref(action.target),
                operation=action.operation, data_classification=action.data_classification,
            ))
            return result
        except GovernanceBoundaryError as exc:
            error = self._public_error(exc)
            self._audit_block("model.output", error)
            raise error from None
        except Exception:
            error = GovernanceBoundaryError("governance.model_output_failed")
            self._audit_block("model.output", error)
            raise error from None

    @staticmethod
    def _public_error(error: GovernanceBoundaryError) -> GovernanceBoundaryError:
        reason = str(error).removeprefix("governance.")
        return GovernanceBoundaryError(
            "governance." + reason if reason in _PUBLIC_REASONS else "governance.authorization_unavailable"
        )

    def _tool_action(self, name: str, args: dict[str, Any], identity: RequestIdentity) -> ActionRequest:
        memory = {
            "maya_business_memory_search": ("memory.read", "*", "search"),
            "maya_business_memory_ingest": ("memory.ingest", "", "read_and_ingest"),
            "maya_business_memory_rebuild_embeddings": ("memory.write", "*", "rebuild_embeddings"),
        }
        if name in memory:
            capability, target, operation = memory[name]
            if name == "maya_business_memory_ingest":
                target = self._document_path(args.get("path"))
        elif name in {"read_file", "write_file"}:
            target = self._document_path(args.get("path"))
            capability = "file.read" if name == "read_file" else "file.write"
            operation = "read" if name == "read_file" else "write"
        else:
            # Shell/code, delegation, cron, and unknown connectors need bounded adapters.
            raise GovernanceBoundaryError("governance.tool_unmapped")
        return ActionRequest(identity.actor_id, capability, target, operation, data_classification=identity.data_classification)

    def _document_path(self, value: Any) -> str:
        if not isinstance(value, str) or not value:
            raise GovernanceBoundaryError("governance.file_target_invalid")
        root = (self.config.deployment.data_dir / "documents").resolve()
        path = Path(value)
        resolved = (root / path).resolve() if not path.is_absolute() else path.resolve()
        if root not in resolved.parents:
            raise GovernanceBoundaryError("governance.file_target_outside_root")
        return str(resolved)

    def tool_result(self, *, tool_name: str, args: dict[str, Any], result: Any, **context: Any) -> Any:
        """Validate/audit final content using the effective executed arguments."""
        try:
            identity = self._actor()
            _checked_payload(args)
            action = self._tool_action(tool_name, args, identity)
            return self._result(action, result)
        except GovernanceBoundaryError as exc:
            error = self._public_error(exc)
            self._audit_block("tool.result", error)
            raise error from None
        except Exception:
            error = GovernanceBoundaryError("governance.tool_execution_failed")
            self._audit_block("tool.result", error)
            raise error from None

    def tool_execution(self, *, tool_name: str, args: dict[str, Any], next_call: Any, **context: Any) -> Any:
        try:
            identity = self._actor()
            _checked_payload(args)
            action = self._tool_action(tool_name, args, identity)
            self._authorize(action)
            effective = dict(args)
            if tool_name in {"read_file", "write_file", "maya_business_memory_ingest"}:
                # Hermes file tools quote paths for Bash, including on Windows.
                effective["path"] = Path(action.target).as_posix()
            return self._result(action, next_call(effective))
        except GovernanceBoundaryError as exc:
            error = self._public_error(exc)
            self._audit_block("tool.execute", error)
            raise error from None
        except Exception:
            error = GovernanceBoundaryError("governance.tool_execution_failed")
            self._audit_block("tool.execute", error)
            raise error from None


def register(ctx: Any) -> None:
    """Hermes-native plugin entry point, loaded from the Maya-owned config."""
    import os
    try:
        config_path = os.environ.get("MAYA_CONFIG")
        if not config_path:
            raise GovernanceBoundaryError("governance.config_missing")
        config = config_from_mapping(json.loads(Path(config_path).read_text(encoding="utf-8")))
        plugin = MayaGovernancePlugin(
            config, load_policy_gateway(config.governance.policy_file),
            LocalJsonlAuditSink(config.deployment.data_dir / "governance" / "audit" / "runtime.jsonl"),
        )
        plugin.register(ctx)
    except GovernanceBoundaryError:
        raise
    except Exception:
        raise GovernanceBoundaryError("governance.registration_failed") from None
