"""Minimal governed runtime composition for Maya."""

from __future__ import annotations

from typing import Any

from .agent.contracts import AgentRuntime, RuntimeCompatibility, RuntimeHealth
from .audit import AuditRecord, AuditSink, NullAuditSink
from .governance import ActionAuthorizationGateway, ActionDeniedError, ActionRequest


class GovernedAgentRuntime:
    """AgentRuntime wrapper that enforces Maya authorization before execution."""

    def __init__(
        self,
        runtime: AgentRuntime,
        gateway: ActionAuthorizationGateway,
        *,
        actor_id: str,
        audit_sink: AuditSink | None = None,
    ) -> None:
        if not isinstance(runtime, AgentRuntime):
            raise TypeError("runtime does not implement the AgentRuntime contract")
        if not isinstance(gateway, ActionAuthorizationGateway):
            raise TypeError("gateway does not implement ActionAuthorizationGateway")
        if audit_sink is not None and not isinstance(audit_sink, AuditSink):
            raise TypeError("audit_sink does not implement the AuditSink contract")
        self._runtime = runtime
        self._gateway = gateway
        self._actor_id = actor_id
        self._audit_sink = audit_sink or NullAuditSink()

    def compatibility(self) -> RuntimeCompatibility:
        return self._runtime.compatibility()

    def attach_memory(self, memory_provider: Any) -> None:
        self._runtime.attach_memory(memory_provider)

    def load_plugin(self, name: str, plugin: Any | None = None) -> None:
        self._runtime.load_plugin(name, plugin)

    def start(self, *, agent_name: str) -> None:
        self._runtime.start(agent_name=agent_name)

    def run(self, request: str, **kwargs: Any) -> Any:
        action = ActionRequest(
            actor_id=self._actor_id,
            capability="runtime.execute",
            target="hermes-agent",
            operation="run",
            data_classification=kwargs.pop("data_classification", "internal"),
            idempotency_key=kwargs.pop("idempotency_key", None),
            metadata={"request_type": "agent_request"},
        )
        result = self._gateway.authorize(action)
        if result.audit_required:
            self._audit_sink.write(
                AuditRecord(
                    event_type="authorization.runtime",
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
        return self._runtime.run(request, **kwargs)

    def health(self) -> RuntimeHealth:
        return self._runtime.health()

    def stop(self) -> None:
        self._runtime.stop()
