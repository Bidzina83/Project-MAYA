"""Phase 5 broker protocol and Standard OAuth contracts."""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

try:  # pragma: no cover - absence is exercised by installed package smoke.
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )
    from cryptography.hazmat.primitives.serialization import (
        Encoding,
        NoEncryption,
        PrivateFormat,
        PublicFormat,
    )
except ImportError:  # pragma: no cover
    InvalidSignature = Exception
    Ed25519PrivateKey = None
    Ed25519PublicKey = None
    Encoding = None
    NoEncryption = None
    PrivateFormat = None
    PublicFormat = None

from .config import BrokerMode, CredentialMode, Edition, MayaConfig
from .connectors import build_connector_manifest
from .secrets import SecretRef, SecretStore, SecretStoreError


BROKER_PROTOCOL_VERSION = "maya-broker-v1"
INSTANCE_PRIVATE_KEY_REF = SecretRef("broker/instance-private-key")
INSTANCE_PUBLIC_KEY_REF = SecretRef("broker/instance-public-key")
SUPPORTED_BROKER_PROVIDERS = frozenset({"google", "slack"})
TOKEN_SECRET_PREFIX = "integrations"


class BrokerProtocolError(ValueError):
    """Raised when a broker protocol message is invalid."""


class BrokerOperationError(RuntimeError):
    """Raised when a broker operation cannot be completed safely."""


class BrokerReadinessStatus(str, Enum):
    READY = "ready"
    BLOCKED = "blocked"
    PENDING = "pending"
    DISABLED = "disabled"
    NOT_CONFIGURED = "not_configured"


class TokenLifecycleState(str, Enum):
    NOT_CONFIGURED = "not_configured"
    ACTIVE = "active"
    REFRESH_REQUIRED = "refresh_required"
    REVOKED = "revoked"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class BrokerInstanceIdentity:
    instance_id: str
    key_id: str
    public_key: str
    private_key_ref: SecretRef = INSTANCE_PRIVATE_KEY_REF

    def redacted_summary(self) -> dict[str, object]:
        return {
            "instance_id": self.instance_id,
            "key_id": self.key_id,
            "public_key_state": "configured",
            "private_key_ref": str(self.private_key_ref),
        }


@dataclass(frozen=True)
class SignedBrokerRequest:
    protocol_version: str
    instance_id: str
    key_id: str
    method: str
    path: str
    body_hash: str
    nonce: str
    issued_at: str
    expires_at: str
    signature: str

    def signing_payload(self) -> bytes:
        return _canonical_json(
            {
                "protocol_version": self.protocol_version,
                "instance_id": self.instance_id,
                "key_id": self.key_id,
                "method": self.method,
                "path": self.path,
                "body_hash": self.body_hash,
                "nonce": self.nonce,
                "issued_at": self.issued_at,
                "expires_at": self.expires_at,
            }
        )

    def redacted_summary(self) -> dict[str, object]:
        return {
            "protocol_version": self.protocol_version,
            "instance_id": self.instance_id,
            "key_id": self.key_id,
            "method": self.method,
            "path": self.path,
            "body_hash": self.body_hash,
            "nonce_state": "configured",
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "signature_state": "configured",
        }


@dataclass(frozen=True)
class SignedBrokerResponse:
    protocol_version: str
    broker_key_id: str
    request_nonce: str
    body_hash: str
    issued_at: str
    expires_at: str
    signature: str

    def signing_payload(self) -> bytes:
        return _canonical_json(
            {
                "protocol_version": self.protocol_version,
                "broker_key_id": self.broker_key_id,
                "request_nonce": self.request_nonce,
                "body_hash": self.body_hash,
                "issued_at": self.issued_at,
                "expires_at": self.expires_at,
            }
        )


@dataclass(frozen=True)
class OAuthSession:
    session_id: str
    provider: str
    state: str
    nonce: str
    code_challenge: str
    code_challenge_method: str
    redirect_uri: str
    authorization_url: str
    scopes: tuple[str, ...]
    expires_at: str
    mutation: str

    def redacted_summary(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "provider": self.provider,
            "state": "configured",
            "nonce": "configured",
            "code_challenge_method": self.code_challenge_method,
            "redirect_uri": self.redirect_uri,
            "authorization_url": self.authorization_url,
            "scopes": list(self.scopes),
            "expires_at": self.expires_at,
            "mutation": self.mutation,
        }


@dataclass(frozen=True)
class BrokerOperationResult:
    operation: str
    status: BrokerReadinessStatus
    provider: str | None
    mutation: str
    network_used: bool
    message: str
    details: dict[str, object] = field(default_factory=dict)

    @property
    def successful(self) -> bool:
        return self.status in {
            BrokerReadinessStatus.READY,
            BrokerReadinessStatus.PENDING,
        }

    def redacted_summary(self) -> dict[str, object]:
        return {
            "operation": self.operation,
            "status": self.status.value,
            "provider": self.provider,
            "mutation": self.mutation,
            "network_used": self.network_used,
            "message": self.message,
            **self.details,
        }


@dataclass(frozen=True)
class TokenLifecycleStatus:
    provider: str
    state: TokenLifecycleState
    credential_ref: SecretRef
    refresh_owner: str
    scopes: tuple[str, ...]
    expires_at: str | None
    rotation_count: int
    revoked_at: str | None
    network_used: bool
    message: str

    def redacted_summary(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "state": self.state.value,
            "credential_ref": str(self.credential_ref),
            "refresh_owner": self.refresh_owner,
            "scopes": list(self.scopes),
            "expires_at": self.expires_at,
            "rotation_count": self.rotation_count,
            "revoked_at": self.revoked_at,
            "network_used": self.network_used,
            "message": self.message,
        }


@dataclass(frozen=True)
class BrokerConformanceReport:
    status: BrokerReadinessStatus
    checks: tuple[dict[str, object], ...]
    network_used: bool = False

    @property
    def passed(self) -> bool:
        return self.status is BrokerReadinessStatus.READY

    def redacted_summary(self) -> dict[str, object]:
        return {
            "operation": "broker.conformance",
            "status": self.status.value,
            "checks": list(self.checks),
            "network_used": self.network_used,
            "message": (
                "mock broker conformance passed"
                if self.passed
                else "mock broker conformance failed"
            ),
        }


@dataclass(frozen=True)
class ModelProxyReadiness:
    status: BrokerReadinessStatus
    mode: str
    broker_mode: BrokerMode
    protocol_ready: bool
    governance_required: bool
    billing_state: str
    network_used: bool
    message: str

    def redacted_summary(self) -> dict[str, object]:
        return {
            "operation": "broker.model-proxy-status",
            "status": self.status.value,
            "mode": self.mode,
            "broker_mode": self.broker_mode.value,
            "protocol_ready": self.protocol_ready,
            "governance_required": self.governance_required,
            "billing_state": self.billing_state,
            "network_used": self.network_used,
            "message": self.message,
        }


class ReplayCache:
    """Small local replay cache used by tests and mock broker conformance."""

    def __init__(self) -> None:
        self._seen: set[str] = set()

    def remember(self, nonce: str) -> None:
        if nonce in self._seen:
            raise BrokerProtocolError("broker request nonce was replayed")
        self._seen.add(nonce)


def generate_instance_identity(config: MayaConfig) -> tuple[BrokerInstanceIdentity, str]:
    _require_crypto()
    private_key = Ed25519PrivateKey.generate()
    private_raw = private_key.private_bytes(
        encoding=Encoding.Raw,
        format=PrivateFormat.Raw,
        encryption_algorithm=NoEncryption(),
    )
    public_raw = private_key.public_key().public_bytes(
        encoding=Encoding.Raw,
        format=PublicFormat.Raw,
    )
    key_id = _digest(f"{config.product.instance_id}:{_b64(public_raw)}".encode())[:16]
    return (
        BrokerInstanceIdentity(
            instance_id=config.product.instance_id,
            key_id=key_id,
            public_key=_b64(public_raw),
        ),
        _b64(private_raw),
    )


def sign_broker_request(
    *,
    identity: BrokerInstanceIdentity,
    private_key: str,
    method: str,
    path: str,
    body: dict[str, object],
    ttl_seconds: int = 300,
    now: datetime | None = None,
) -> SignedBrokerRequest:
    issued = now or datetime.now(UTC)
    request = SignedBrokerRequest(
        protocol_version=BROKER_PROTOCOL_VERSION,
        instance_id=identity.instance_id,
        key_id=identity.key_id,
        method=method.upper(),
        path=path,
        body_hash=_hash_body(body),
        nonce=secrets.token_urlsafe(32),
        issued_at=_format_time(issued),
        expires_at=_format_time(issued + timedelta(seconds=ttl_seconds)),
        signature="",
    )
    signature = _load_private_key(private_key).sign(request.signing_payload())
    return SignedBrokerRequest(
        **{**request.__dict__, "signature": _b64(signature)}
    )


def verify_broker_request(
    request: SignedBrokerRequest,
    *,
    public_key: str,
    body: dict[str, object],
    replay_cache: ReplayCache | None = None,
    now: datetime | None = None,
) -> None:
    _require_protocol(request.protocol_version)
    _require_hash(request.body_hash, body)
    _require_fresh(request.issued_at, request.expires_at, now=now)
    try:
        _load_public_key(public_key).verify(
            _unb64(request.signature),
            request.signing_payload(),
        )
    except InvalidSignature as exc:
        raise BrokerProtocolError("broker request signature is invalid") from exc
    if replay_cache is not None:
        replay_cache.remember(request.nonce)


def sign_broker_response(
    *,
    broker_key_id: str,
    broker_private_key: str,
    request_nonce: str,
    body: dict[str, object],
    ttl_seconds: int = 300,
    now: datetime | None = None,
) -> SignedBrokerResponse:
    issued = now or datetime.now(UTC)
    response = SignedBrokerResponse(
        protocol_version=BROKER_PROTOCOL_VERSION,
        broker_key_id=broker_key_id,
        request_nonce=request_nonce,
        body_hash=_hash_body(body),
        issued_at=_format_time(issued),
        expires_at=_format_time(issued + timedelta(seconds=ttl_seconds)),
        signature="",
    )
    signature = _load_private_key(broker_private_key).sign(response.signing_payload())
    return SignedBrokerResponse(**{**response.__dict__, "signature": _b64(signature)})


def verify_broker_response(
    response: SignedBrokerResponse,
    *,
    broker_public_key: str,
    request_nonce: str,
    body: dict[str, object],
    now: datetime | None = None,
) -> None:
    _require_protocol(response.protocol_version)
    if response.request_nonce != request_nonce:
        raise BrokerProtocolError("broker response nonce does not match request")
    _require_hash(response.body_hash, body)
    _require_fresh(response.issued_at, response.expires_at, now=now)
    try:
        _load_public_key(broker_public_key).verify(
            _unb64(response.signature),
            response.signing_payload(),
        )
    except InvalidSignature as exc:
        raise BrokerProtocolError("broker response signature is invalid") from exc


def broker_status(config: MayaConfig, secret_store: SecretStore) -> BrokerOperationResult:
    if config.broker.mode is BrokerMode.DISABLED:
        return BrokerOperationResult(
            operation="broker.status",
            status=BrokerReadinessStatus.DISABLED,
            provider=None,
            mutation="none",
            network_used=False,
            message="broker disabled by configuration",
        )
    endpoint_state = "configured" if config.broker.endpoint else "not_configured"
    key_state = "configured" if secret_store.contains(INSTANCE_PRIVATE_KEY_REF) else "missing"
    status = (
        BrokerReadinessStatus.READY
        if endpoint_state == "configured" and key_state == "configured"
        else BrokerReadinessStatus.PENDING
    )
    return BrokerOperationResult(
        operation="broker.status",
        status=status,
        provider=None,
        mutation="none",
        network_used=False,
        message="broker status is redacted and local",
        details={
            "broker_mode": config.broker.mode.value,
            "endpoint": endpoint_state,
            "instance_private_key": key_state,
        },
    )


def register_broker_instance(
    config: MayaConfig,
    secret_store: SecretStore,
    *,
    apply: bool,
) -> BrokerOperationResult:
    _require_broker_not_disabled(config, runtime_required=False)
    identity, private_key = generate_instance_identity(config)
    if apply:
        secret_store.write(INSTANCE_PRIVATE_KEY_REF, private_key)
        secret_store.write(INSTANCE_PUBLIC_KEY_REF, identity.public_key)
        mutation = "stored_instance_identity"
        status = BrokerReadinessStatus.READY
        message = "broker instance identity stored locally"
    else:
        mutation = "dry_run"
        status = BrokerReadinessStatus.PENDING
        message = "broker instance identity would be generated and stored"
    return BrokerOperationResult(
        operation="broker.register",
        status=status,
        provider=None,
        mutation=mutation,
        network_used=False,
        message=message,
        details={"identity": identity.redacted_summary()},
    )


def start_oauth_session(
    config: MayaConfig,
    provider: str,
    *,
    apply: bool,
) -> OAuthSession:
    _require_broker_runtime(config)
    provider = _require_supported_provider(provider)
    _require_broker_connector(config, provider)
    verifier = secrets.token_urlsafe(64)[:96]
    challenge = _b64(hashlib.sha256(verifier.encode("ascii")).digest())
    session = OAuthSession(
        session_id=secrets.token_urlsafe(24),
        provider=provider,
        state=secrets.token_urlsafe(32),
        nonce=secrets.token_urlsafe(32),
        code_challenge=challenge,
        code_challenge_method="S256",
        redirect_uri="http://127.0.0.1/oauth/maya/callback",
        authorization_url=_authorization_url(provider, challenge),
        scopes=_connector_scopes(config, provider),
        expires_at=_format_time(datetime.now(UTC) + timedelta(minutes=10)),
        mutation="stored_oauth_session" if apply else "dry_run",
    )
    if apply:
        _write_session(config, session, verifier)
    return session


def complete_oauth_session(
    config: MayaConfig,
    secret_store: SecretStore,
    *,
    provider: str,
    session_id: str,
    callback_url: str,
    apply: bool,
) -> BrokerOperationResult:
    _require_broker_runtime(config)
    provider = _require_supported_provider(provider)
    if not apply:
        raise BrokerOperationError("oauth completion requires --apply")
    session_doc = _read_session(config, session_id)
    if session_doc["provider"] != provider:
        raise BrokerOperationError("oauth session provider mismatch")
    _require_fresh(session_doc["created_at"], str(session_doc["expires_at"]))
    parsed = urlparse(callback_url)
    params = parse_qs(parsed.query)
    state = params.get("state", [""])[0]
    code = params.get("code", [""])[0]
    if not state or state != session_doc["state"]:
        raise BrokerOperationError("oauth callback state mismatch")
    if not code:
        raise BrokerOperationError("oauth callback code is required")
    token_ref = _token_secret_ref(provider)
    token_payload = {
        "provider": provider,
        "access_token": secrets.token_urlsafe(48),
        "refresh_token": secrets.token_urlsafe(48),
        "token_type": "Bearer",
        "scope": " ".join(session_doc["scopes"]),
        "expires_at": _format_time(datetime.now(UTC) + timedelta(hours=12)),
        "refresh_owner": _refresh_owner(provider),
        "rotation_count": 0,
    }
    secret_store.write(token_ref, json.dumps(token_payload, sort_keys=True))
    metadata = _token_metadata_from_payload(token_ref, token_payload)
    _write_token_metadata(config, provider, metadata)
    return BrokerOperationResult(
        operation="broker.oauth-complete",
        status=BrokerReadinessStatus.READY,
        provider=provider,
        mutation="stored_token_envelope",
        network_used=False,
        message="broker-assisted OAuth token envelope stored locally",
        details={"token": metadata.redacted_summary()},
    )


def token_status(config: MayaConfig, provider: str) -> TokenLifecycleStatus:
    provider = _require_supported_provider(provider)
    path = _token_metadata_path(config, provider)
    token_ref = _token_secret_ref(provider)
    if not path.is_file():
        return TokenLifecycleStatus(
            provider=provider,
            state=TokenLifecycleState.NOT_CONFIGURED,
            credential_ref=token_ref,
            refresh_owner=_refresh_owner(provider),
            scopes=(),
            expires_at=None,
            rotation_count=0,
            revoked_at=None,
            network_used=False,
            message="token metadata not configured",
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    return TokenLifecycleStatus(
        provider=provider,
        state=TokenLifecycleState(raw["state"]),
        credential_ref=token_ref,
        refresh_owner=raw["refresh_owner"],
        scopes=tuple(raw["scopes"]),
        expires_at=raw.get("expires_at"),
        rotation_count=int(raw.get("rotation_count", 0)),
        revoked_at=raw.get("revoked_at"),
        network_used=False,
        message=raw["message"],
    )


def refresh_token(
    config: MayaConfig,
    secret_store: SecretStore,
    provider: str,
    *,
    apply: bool,
) -> BrokerOperationResult:
    _require_broker_runtime(config)
    provider = _require_supported_provider(provider)
    if not apply:
        raise BrokerOperationError("token refresh requires --apply")
    token_ref = _token_secret_ref(provider)
    try:
        payload = json.loads(secret_store.read(token_ref))
    except (SecretStoreError, json.JSONDecodeError) as exc:
        raise BrokerOperationError("token envelope is unavailable") from exc
    payload["access_token"] = secrets.token_urlsafe(48)
    payload["expires_at"] = _format_time(datetime.now(UTC) + timedelta(hours=12))
    if provider == "slack":
        payload["refresh_token"] = secrets.token_urlsafe(48)
    payload["rotation_count"] = int(payload.get("rotation_count", 0)) + 1
    secret_store.write(token_ref, json.dumps(payload, sort_keys=True))
    metadata = _token_metadata_from_payload(token_ref, payload)
    _write_token_metadata(config, provider, metadata)
    return BrokerOperationResult(
        operation="broker.token-refresh",
        status=BrokerReadinessStatus.READY,
        provider=provider,
        mutation="rotated_token_envelope",
        network_used=False,
        message="token envelope refreshed through broker lifecycle",
        details={"token": metadata.redacted_summary()},
    )


def revoke_token(
    config: MayaConfig,
    secret_store: SecretStore,
    provider: str,
    *,
    apply: bool,
) -> BrokerOperationResult:
    _require_broker_runtime(config)
    provider = _require_supported_provider(provider)
    if not apply:
        raise BrokerOperationError("token revocation requires --apply")
    token_ref = _token_secret_ref(provider)
    secret_store.delete(token_ref)
    metadata = TokenLifecycleStatus(
        provider=provider,
        state=TokenLifecycleState.REVOKED,
        credential_ref=token_ref,
        refresh_owner=_refresh_owner(provider),
        scopes=(),
        expires_at=None,
        rotation_count=0,
        revoked_at=_format_time(datetime.now(UTC)),
        network_used=False,
        message="local token envelope revoked; provider revocation is broker-mediated",
    )
    _write_token_metadata(config, provider, metadata)
    return BrokerOperationResult(
        operation="broker.token-revoke",
        status=BrokerReadinessStatus.READY,
        provider=provider,
        mutation="deleted_token_envelope",
        network_used=False,
        message="local token envelope deleted",
        details={"token": metadata.redacted_summary()},
    )


def model_proxy_readiness(config: MayaConfig, secret_store: SecretStore) -> ModelProxyReadiness:
    if config.llm.mode != "maya_managed":
        return ModelProxyReadiness(
            status=BrokerReadinessStatus.NOT_CONFIGURED,
            mode=config.llm.mode,
            broker_mode=config.broker.mode,
            protocol_ready=False,
            governance_required=True,
            billing_state="not_configured",
            network_used=False,
            message="llm.mode is not maya_managed",
        )
    if config.broker.mode is not BrokerMode.RUNTIME:
        return ModelProxyReadiness(
            status=BrokerReadinessStatus.BLOCKED,
            mode=config.llm.mode,
            broker_mode=config.broker.mode,
            protocol_ready=False,
            governance_required=True,
            billing_state="blocked",
            network_used=False,
            message="maya_managed model billing requires broker runtime mode",
        )
    protocol_ready = secret_store.contains(INSTANCE_PRIVATE_KEY_REF)
    return ModelProxyReadiness(
        status=BrokerReadinessStatus.READY if protocol_ready else BrokerReadinessStatus.PENDING,
        mode=config.llm.mode,
        broker_mode=config.broker.mode,
        protocol_ready=protocol_ready,
        governance_required=True,
        billing_state="ready" if protocol_ready else "pending_instance_registration",
        network_used=False,
        message=(
            "model proxy billing readiness verified without inference"
            if protocol_ready
            else "register broker instance before model proxy billing"
        ),
    )


def run_mock_broker_conformance() -> BrokerConformanceReport:
    _require_crypto()
    checks: list[dict[str, object]] = []
    cache = ReplayCache()
    private = Ed25519PrivateKey.generate()
    private_raw = _b64(
        private.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    )
    public_raw = _b64(private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw))
    broker_private = Ed25519PrivateKey.generate()
    broker_private_raw = _b64(
        broker_private.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    )
    broker_public_raw = _b64(
        broker_private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    )
    identity = BrokerInstanceIdentity(
        instance_id="mock-instance",
        key_id="mock-key",
        public_key=public_raw,
    )
    body = {"provider": "google", "state": "redacted"}
    request = sign_broker_request(
        identity=identity,
        private_key=private_raw,
        method="POST",
        path="/oauth/start",
        body=body,
    )
    _record_check(
        checks,
        "signed_request_valid",
        lambda: verify_broker_request(
            request, public_key=public_raw, body=body, replay_cache=cache
        ),
    )
    _record_expected_failure(
        checks,
        "replay_rejected",
        lambda: verify_broker_request(
            request, public_key=public_raw, body=body, replay_cache=cache
        ),
    )
    _record_expected_failure(
        checks,
        "tampered_body_rejected",
        lambda: verify_broker_request(
            request, public_key=public_raw, body={"provider": "slack"}
        ),
    )
    response_body = {"session": "created", "token": "redacted"}
    response = sign_broker_response(
        broker_key_id="broker-key",
        broker_private_key=broker_private_raw,
        request_nonce=request.nonce,
        body=response_body,
    )
    _record_check(
        checks,
        "signed_response_valid",
        lambda: verify_broker_response(
            response,
            broker_public_key=broker_public_raw,
            request_nonce=request.nonce,
            body=response_body,
        ),
    )
    _record_expected_failure(
        checks,
        "wrong_response_nonce_rejected",
        lambda: verify_broker_response(
            response,
            broker_public_key=broker_public_raw,
            request_nonce="wrong",
            body=response_body,
        ),
    )
    expired = sign_broker_request(
        identity=identity,
        private_key=private_raw,
        method="POST",
        path="/oauth/start",
        body=body,
        ttl_seconds=1,
        now=datetime.now(UTC) - timedelta(minutes=10),
    )
    _record_expected_failure(
        checks,
        "expired_request_rejected",
        lambda: verify_broker_request(expired, public_key=public_raw, body=body),
    )
    status = (
        BrokerReadinessStatus.READY
        if all(check["status"] == "passed" for check in checks)
        else BrokerReadinessStatus.BLOCKED
    )
    return BrokerConformanceReport(status=status, checks=tuple(checks))


def _record_check(
    checks: list[dict[str, object]], name: str, operation
) -> None:
    try:
        operation()
    except Exception as exc:  # pragma: no cover - failure payload tested by caller
        checks.append({"name": name, "status": "failed", "message": type(exc).__name__})
    else:
        checks.append({"name": name, "status": "passed", "message": "ok"})


def _record_expected_failure(
    checks: list[dict[str, object]], name: str, operation
) -> None:
    try:
        operation()
    except BrokerProtocolError:
        checks.append({"name": name, "status": "passed", "message": "rejected"})
    else:
        checks.append({"name": name, "status": "failed", "message": "accepted"})


def _authorization_url(provider: str, challenge: str) -> str:
    base = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        if provider == "google"
        else "https://slack.com/oauth/v2/authorize"
    )
    return base + "?" + urlencode(
        {
            "response_type": "code",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": "redacted",
        }
    )


def _connector_scopes(config: MayaConfig, provider: str) -> tuple[str, ...]:
    integration = config.integrations[provider]
    manifest = build_connector_manifest(
        provider,
        integration,
        broker_mode=config.broker.mode,
    )
    return tuple(
        dict.fromkeys(
            scope
            for capability in manifest.capabilities
            for scope in capability.scopes
        )
    )


def _require_broker_not_disabled(config: MayaConfig, *, runtime_required: bool) -> None:
    if config.broker.mode is BrokerMode.DISABLED:
        raise BrokerOperationError("broker mode is disabled")
    if runtime_required and config.broker.mode is not BrokerMode.RUNTIME:
        raise BrokerOperationError("broker runtime mode is required")


def _require_broker_runtime(config: MayaConfig) -> None:
    _require_broker_not_disabled(config, runtime_required=True)
    if not config.broker.endpoint:
        raise BrokerOperationError("broker endpoint is required")


def _require_broker_connector(config: MayaConfig, provider: str) -> None:
    integration = config.integrations.get(provider)
    if integration is None or not integration.enabled:
        raise BrokerOperationError(f"{provider} integration is not enabled")
    if integration.credential_mode is not CredentialMode.BROKER:
        raise BrokerOperationError(f"{provider} integration is not broker-assisted")
    if config.product.edition is Edition.ENTERPRISE:
        raise BrokerOperationError("Enterprise must use customer-owned OAuth clients")


def _require_supported_provider(provider: str) -> str:
    normalized = provider.lower().strip()
    if normalized not in SUPPORTED_BROKER_PROVIDERS:
        raise BrokerOperationError("broker OAuth supports google and slack only")
    return normalized


def _write_session(config: MayaConfig, session: OAuthSession, verifier: str) -> None:
    path = _session_path(config, session.session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                **session.redacted_summary(),
                "provider": session.provider,
                "state": session.state,
                "nonce": session.nonce,
                "code_verifier_ref": "secret://broker/oauth-session-verifier",
                "code_verifier_hash": _digest(verifier.encode()),
                "created_at": _format_time(datetime.now(UTC)),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _read_session(config: MayaConfig, session_id: str) -> dict[str, Any]:
    path = _session_path(config, session_id)
    if not path.is_file():
        raise BrokerOperationError("oauth session not found")
    return json.loads(path.read_text(encoding="utf-8"))


def _session_path(config: MayaConfig, session_id: str) -> Path:
    safe = "".join(ch for ch in session_id if ch.isalnum() or ch in "-_")
    if safe != session_id or not safe:
        raise BrokerOperationError("invalid oauth session id")
    return config.deployment.data_dir / "broker" / "oauth-sessions" / f"{safe}.json"


def _token_secret_ref(provider: str) -> SecretRef:
    return SecretRef(f"{TOKEN_SECRET_PREFIX}/{provider}/broker-token-envelope")


def _token_metadata_path(config: MayaConfig, provider: str) -> Path:
    return config.deployment.data_dir / "integrations" / provider / "token-status.json"


def _write_token_metadata(
    config: MayaConfig,
    provider: str,
    metadata: TokenLifecycleStatus,
) -> None:
    path = _token_metadata_path(config, provider)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(metadata.redacted_summary(), indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _token_metadata_from_payload(
    token_ref: SecretRef,
    payload: dict[str, object],
) -> TokenLifecycleStatus:
    provider = str(payload["provider"])
    return TokenLifecycleStatus(
        provider=provider,
        state=TokenLifecycleState.ACTIVE,
        credential_ref=token_ref,
        refresh_owner=str(payload["refresh_owner"]),
        scopes=tuple(str(payload.get("scope", "")).split()),
        expires_at=str(payload["expires_at"]),
        rotation_count=int(payload.get("rotation_count", 0)),
        revoked_at=None,
        network_used=False,
        message="token envelope active; raw values stored only in SecretStore",
    )


def _refresh_owner(provider: str) -> str:
    return "local" if provider == "google" else "broker_assisted"


def _hash_body(body: dict[str, object]) -> str:
    return _digest(_canonical_json(body))


def _require_hash(expected: str, body: dict[str, object]) -> None:
    if expected != _hash_body(body):
        raise BrokerProtocolError("broker message body hash mismatch")


def _require_protocol(version: str) -> None:
    if version != BROKER_PROTOCOL_VERSION:
        raise BrokerProtocolError("unsupported broker protocol version")


def _require_fresh(
    issued_at: str,
    expires_at: str,
    *,
    now: datetime | None = None,
) -> None:
    current = now or datetime.now(UTC)
    issued = datetime.fromisoformat(issued_at)
    expires = datetime.fromisoformat(expires_at)
    if issued > current + timedelta(minutes=1):
        raise BrokerProtocolError("broker message issued_at is in the future")
    if expires <= current:
        raise BrokerProtocolError("broker message expired")


def _canonical_json(value: dict[str, object]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _format_time(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def _digest(value: bytes) -> str:
    return _b64(hashlib.sha256(value).digest())


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _unb64(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def _load_private_key(value: str) -> Ed25519PrivateKey:
    _require_crypto()
    return Ed25519PrivateKey.from_private_bytes(_unb64(value))


def _load_public_key(value: str) -> Ed25519PublicKey:
    _require_crypto()
    return Ed25519PublicKey.from_public_bytes(_unb64(value))


def _require_crypto() -> None:
    if Ed25519PrivateKey is None:
        raise BrokerOperationError(
            "cryptography>=42 is required for broker protocol operations"
        )
