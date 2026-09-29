"""Native Hermes enforcement adapters over Maya's existing policy engine."""

from __future__ import annotations

import hashlib
import json
import re
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, Iterator, Mapping
from urllib.parse import urlsplit

from ..audit import AuditRecord, AuditSink, LocalJsonlAuditSink
from ..config import MayaConfig, config_from_mapping
from ..governance import ActionDeniedError, ActionRequest, ActionAuthorizationGateway, load_policy_gateway


CONTRACT_VERSION = "project-maya.hermes-governance.v1"
REQUIRED_CAPABILITIES = frozenset({
    "fail_closed_execution", "mandatory_middleware", "auxiliary_sync",
    "auxiliary_async", "trusted_context_propagation",
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
})


class GovernanceBoundaryError(ActionDeniedError):
    """A secret-safe denial or unavailable enforcement boundary."""


@dataclass(frozen=True)
class RequestIdentity:
    actor_id: str
    data_classification: str = "confidential"


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
        for name in ("run_llm_execution_middleware", "run_tool_execution_middleware", "require_middleware", "validate_mandatory_middleware"):
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
        # The runtime must enforce presence on main AND auxiliary dispatch paths.
        module.require_middleware("llm_execution", self.model_execution)
        module.require_middleware("tool_execution", self.tool_execution)

    def _actor(self) -> RequestIdentity:
        identity = _identity.get()
        if identity is None:
            raise GovernanceBoundaryError("governance.identity_missing")
        return identity

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
            return next_call(request)
        except GovernanceBoundaryError as exc:
            error = self._public_error(exc)
            self._audit_block("model.egress", error)
            raise error from None
        except Exception:
            error = GovernanceBoundaryError("governance.model_execution_failed")
            self._audit_block("model.egress", error)
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

    def tool_execution(self, *, tool_name: str, args: dict[str, Any], next_call: Any, **context: Any) -> Any:
        try:
            identity = self._actor()
            _checked_payload(args)
            action = self._tool_action(tool_name, args, identity)
            self._authorize(action)
            effective = dict(args)
            if tool_name in {"read_file", "write_file", "maya_business_memory_ingest"}:
                effective["path"] = action.target
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
