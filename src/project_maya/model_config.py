"""Model configuration validation for Maya runtime assembly."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse

from .config import BrokerMode, ConfigError, Edition, MayaConfig, ModelConfig
from .secrets import SecretRef, SecretReferenceError


class ModelConfigStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"


class LocalModelEndpointStatus(str, Enum):
    READY = "ready"
    NOT_CONFIGURED = "not_configured"
    INVALID = "invalid"


@dataclass(frozen=True)
class ModelConfigValidation:
    """Redacted model configuration validation result."""

    status: ModelConfigStatus
    mode: str
    provider: str
    model: str
    endpoint_state: str
    credential_ref_state: str
    network_used: bool
    message: str

    @property
    def valid(self) -> bool:
        return self.status is ModelConfigStatus.VALID

    def redacted_summary(self) -> str:
        return (
            f"mode={self.mode}; "
            f"provider={self.provider}; "
            f"model={self.model}; "
            f"endpoint={self.endpoint_state}; "
            f"credential_ref={self.credential_ref_state}; "
            f"network_used={str(self.network_used).lower()}; "
            f"{self.message}"
        )


@dataclass(frozen=True)
class LocalModelEndpointReadiness:
    """Redacted readiness report for OpenAI-compatible local endpoints."""

    status: LocalModelEndpointStatus
    provider: str
    endpoint_state: str
    endpoint_family: str
    openai_compatible: bool
    credential_ref_state: str
    network_used: bool
    message: str

    @property
    def ready(self) -> bool:
        return self.status is LocalModelEndpointStatus.READY

    def redacted_summary(self) -> str:
        return (
            f"provider={self.provider}; "
            f"endpoint={self.endpoint_state}; "
            f"family={self.endpoint_family}; "
            f"openai_compatible={str(self.openai_compatible).lower()}; "
            f"credential_ref={self.credential_ref_state}; "
            f"network_used={str(self.network_used).lower()}; "
            f"{self.message}"
        )


SUPPORTED_MODEL_MODES = frozenset({"customer_owned", "local", "maya_managed"})
LOCAL_MODEL_PROVIDER = "openai-compatible"


def validate_model_config(config: MayaConfig) -> ModelConfigValidation:
    """Validate model configuration without provider network calls."""

    llm = config.llm
    endpoint_state = _endpoint_state(llm)
    credential_state = _credential_ref_state(llm)

    invalid_reason = _first_invalid_reason(config)
    if invalid_reason is not None:
        return ModelConfigValidation(
            status=ModelConfigStatus.INVALID,
            mode=llm.mode,
            provider=llm.provider,
            model=llm.model,
            endpoint_state=endpoint_state,
            credential_ref_state=credential_state,
            network_used=False,
            message=invalid_reason,
        )
    return ModelConfigValidation(
        status=ModelConfigStatus.VALID,
        mode=llm.mode,
        provider=llm.provider,
        model=llm.model,
        endpoint_state=endpoint_state,
        credential_ref_state=credential_state,
        network_used=False,
        message="model configuration valid",
    )


def require_valid_model_config(config: MayaConfig) -> ModelConfigValidation:
    """Return validation or raise ConfigError for invalid model configuration."""

    validation = validate_model_config(config)
    if not validation.valid:
        raise ConfigError(validation.message)
    return validation


def validate_local_model_endpoint(config: MayaConfig) -> LocalModelEndpointReadiness:
    """Validate local model endpoint readiness without network calls."""

    llm = config.llm
    endpoint_state = _endpoint_state(llm)
    credential_state = _credential_ref_state(llm)
    endpoint_family = _endpoint_family(llm.endpoint)
    if llm.mode != "local":
        return LocalModelEndpointReadiness(
            status=LocalModelEndpointStatus.NOT_CONFIGURED,
            provider=llm.provider,
            endpoint_state=endpoint_state,
            endpoint_family=endpoint_family,
            openai_compatible=False,
            credential_ref_state=credential_state,
            network_used=False,
            message="llm.mode is not local",
        )
    invalid_reason = _first_invalid_reason(config)
    if invalid_reason is not None:
        return LocalModelEndpointReadiness(
            status=LocalModelEndpointStatus.INVALID,
            provider=llm.provider,
            endpoint_state=endpoint_state,
            endpoint_family=endpoint_family,
            openai_compatible=False,
            credential_ref_state=credential_state,
            network_used=False,
            message=invalid_reason,
        )
    return LocalModelEndpointReadiness(
        status=LocalModelEndpointStatus.READY,
        provider=llm.provider,
        endpoint_state=endpoint_state,
        endpoint_family=endpoint_family,
        openai_compatible=True,
        credential_ref_state=credential_state,
        network_used=False,
        message="local OpenAI-compatible endpoint configured",
    )


def _first_invalid_reason(config: MayaConfig) -> str | None:
    llm = config.llm
    if llm.mode not in SUPPORTED_MODEL_MODES:
        return f"llm.mode is unsupported: {llm.mode}"
    if not llm.provider.strip():
        return "llm.provider is required"
    if not llm.model.strip():
        return "llm.model is required"
    if llm.credential_ref is not None:
        try:
            SecretRef.parse(llm.credential_ref)
        except SecretReferenceError:
            return "llm.credential_ref must be a secret:// reference"
    if llm.endpoint is not None and not _valid_endpoint(llm.endpoint):
        return "llm.endpoint must be an http or https URL"
    if llm.mode == "customer_owned" and llm.credential_ref is None:
        return "customer_owned model mode requires llm.credential_ref"
    if llm.mode == "local" and llm.endpoint is None:
        return "local model mode requires llm.endpoint"
    if llm.mode == "local" and llm.provider != LOCAL_MODEL_PROVIDER:
        return "local model mode requires llm.provider=openai-compatible"
    if (
        llm.mode == "maya_managed"
        and config.product.edition is Edition.ENTERPRISE
        and config.broker.mode is BrokerMode.DISABLED
    ):
        return "maya_managed model mode requires Maya cloud services"
    return None


def _endpoint_state(llm: ModelConfig) -> str:
    if llm.endpoint is None:
        return "provider_default"
    parsed = urlparse(llm.endpoint)
    host = parsed.hostname or ""
    if host == "localhost" or host == "::1" or host.startswith("127."):
        return "local_configured"
    return "customer_hosted_configured"


def _endpoint_family(endpoint: str | None) -> str:
    if endpoint is None:
        return "not_configured"
    parsed = urlparse(endpoint)
    host = parsed.hostname or ""
    port = parsed.port
    if port == 11434:
        return "ollama"
    if port == 1234:
        return "lm_studio"
    if port == 8000:
        return "vllm"
    if host == "localhost" or host == "::1" or host.startswith("127."):
        return "openai_compatible_local"
    return "openai_compatible_customer_hosted"


def _credential_ref_state(llm: ModelConfig) -> str:
    if llm.credential_ref is None:
        return "not_configured"
    try:
        SecretRef.parse(llm.credential_ref)
    except SecretReferenceError:
        return "invalid"
    return "configured"


def _valid_endpoint(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
