"""Explicit, loopback-only startup for the unqualified governance candidate.

This entry point never changes the production compatibility contract. Run it in
a separate process: native mandatory mode and its bindings cannot be reset.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import zipfile
from dataclasses import replace
from importlib import import_module
from importlib.util import find_spec
from ipaddress import ip_address
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit

from ..adapters.hermes import HermesRuntimeAdapter
from ..agent.contracts import RuntimeHealth
from ..bootstrap import LocalMayaProduct, _assemble_local_product, _build_audit_sink, _build_gateway
from ..config import BrokerMode, ComponentProfile, ConfigError, MayaConfig
from ..model_config import require_valid_model_config
from ..secrets import build_platform_secret_store
from .governance import GovernanceBoundaryError, MayaGovernancePlugin, bind_request_identity


ACKNOWLEDGEMENT = "unqualified-governance-candidate"
CANDIDATE_VERSION = "0.17.0+maya.gov12.candidate.20261002"
CANDIDATE_SHA256 = "af979f8445e56e0379c7ad5252a228be5e7cf924c86f37c3c76a85ade867a323"
_MARKER = ".maya-governance-candidate.json"


def initialize_test_only_home(data_dir: Path, *, acknowledgement: str) -> Path:
    """Create a new, separately owned data root; never reuse customer state."""
    if acknowledgement != ACKNOWLEDGEMENT:
        raise GovernanceBoundaryError("governance.candidate_acknowledgement_required")
    data_dir = Path(data_dir).resolve()
    try:
        data_dir.mkdir(parents=True, exist_ok=False)
        home = data_dir / "hermes"
        home.mkdir()
        (data_dir / _MARKER).write_text(
            json.dumps({"qualification": "test_only_unqualified", "wheel_sha256": CANDIDATE_SHA256}),
            encoding="utf-8",
        )
        return home
    except Exception:
        raise GovernanceBoundaryError("governance.candidate_home_creation_failed") from None


def _validate_test_scope(config: MayaConfig, acknowledgement: str) -> None:
    if acknowledgement != ACKNOWLEDGEMENT:
        raise GovernanceBoundaryError("governance.candidate_acknowledgement_required")
    try:
        config.validate()
        require_valid_model_config(config)
    except ConfigError:
        raise GovernanceBoundaryError("governance.candidate_scope_invalid") from None
    endpoint = urlsplit(config.llm.endpoint or "")
    try:
        loopback = endpoint.hostname == "localhost" or ip_address(endpoint.hostname).is_loopback
    except (ValueError, TypeError):
        loopback = False
    if (config.runtime.hermes_factory != "run_agent:AIAgent" or config.llm.mode != "local"
            or config.llm.provider != "openai-compatible" or config.llm.credential_ref
            or endpoint.scheme not in {"http", "https"} or not loopback
            or endpoint.username or endpoint.password or endpoint.query or endpoint.fragment
            or config.broker.mode is not BrokerMode.DISABLED or config.metabase.enabled
            or any(item.enabled for item in config.integrations.values())
            or config.runtime.enabled_profiles != (ComponentProfile.CORE,)):
        raise GovernanceBoundaryError("governance.candidate_scope_invalid")
    root = config.deployment.data_dir.resolve()
    try:
        if root not in config.governance.policy_file.resolve().parents:
            raise ValueError("policy outside candidate state")
        marker = json.loads((root / _MARKER).read_text(encoding="utf-8"))
        if marker != {"qualification": "test_only_unqualified", "wheel_sha256": CANDIDATE_SHA256}:
            raise ValueError("invalid marker")
        if Path(os.environ.get("HERMES_HOME", "")).resolve() != root / "hermes":
            raise ValueError("wrong Hermes home")
        # Refuse ambient credentials or user-installed plugins in this isolated host.
        if any(value and (name.endswith(("API_KEY", "TOKEN", "PASSWORD")) or name == "MAYA_CONFIG")
               for name, value in os.environ.items()):
            raise ValueError("ambient credential")
        home = root / "hermes"
        if any((home / name).exists() for name in (".env", "config.yaml", "plugins")):
            raise ValueError("external Hermes configuration")
    except Exception:
        raise GovernanceBoundaryError("governance.candidate_home_invalid") from None


def _verify_loaded_artifact(wheel_path: Path) -> None:
    """Bind candidate permission to the exact wheel and its installed Python files."""
    try:
        wheel_path = Path(wheel_path)
        if hashlib.sha256(wheel_path.read_bytes()).hexdigest() != CANDIDATE_SHA256:
            raise ValueError("wrong artifact")
        spec = find_spec("run_agent")
        if spec is None or not spec.origin:
            raise ValueError("missing runtime")
        root = Path(spec.origin).resolve().parent
        for name, loaded in tuple(sys.modules.items()):
            if name.split(".", 1)[0] in {"run_agent", "model_tools", "agent", "tools", "hermes_cli", "plugins", "gateway"}:
                file = getattr(loaded, "__file__", None)
                if file and root not in Path(file).resolve().parents:
                    raise ValueError("mixed imported runtime")
        with zipfile.ZipFile(wheel_path) as wheel:
            for name in wheel.namelist():
                if name.endswith(".py") and ".data/" not in name:
                    if (root / name).read_bytes() != wheel.read(name):
                        raise ValueError("installed artifact mismatch")
        module = import_module("hermes_cli.middleware")
        if Path(module.__file__).resolve() != root / "hermes_cli" / "middleware.py":
            raise ValueError("mixed runtime")
        if hasattr(module, "MAYA_GOVERNANCE_CONTRACT"):
            raise ValueError("unexpected qualified contract")
        for name in ("enable_mandatory_middleware", "require_middleware", "validate_mandatory_middleware",
                     "run_llm_execution_middleware", "run_tool_execution_middleware",
                     "run_tool_result_middleware", "run_model_output_middleware", "require_single_attempt_client"):
            if not callable(getattr(module, name, None)):
                raise ValueError("missing candidate interface")
    except Exception:
        raise GovernanceBoundaryError("governance.candidate_artifact_invalid") from None


class _CandidateStartup:
    def __init__(self, plugin: MayaGovernancePlugin, wheel_path: Path, scope_check: Callable[[], None]) -> None:
        self.plugin = plugin
        self.wheel_path = wheel_path
        self.bound = False
        self.scope_check = scope_check

    def __call__(self) -> None:
        try:
            self.scope_check()
            _verify_loaded_artifact(self.wheel_path)
            module = import_module("hermes_cli.middleware")
            if not self.bound:
                module.enable_mandatory_middleware()
                native = import_module("hermes_cli.plugins")
                ctx = native.PluginContext(native.PluginManifest(name="maya-governance-candidate"), native.get_plugin_manager())
                for kind, callback in (
                    ("llm_execution", self.plugin.model_execution),
                    ("tool_execution", self.plugin.tool_execution),
                    ("tool_result", self.plugin.tool_result),
                    ("model_output", self.plugin.model_output),
                ):
                    ctx.register_middleware(kind, callback)
                    module.require_middleware(kind, callback)
                self.bound = True
            if module.validate_mandatory_middleware() is not True:
                raise ValueError("missing mandatory bindings")
        except GovernanceBoundaryError:
            raise
        except Exception:
            raise GovernanceBoundaryError("governance.candidate_registration_failed") from None


class _CandidateAdapter(HermesRuntimeAdapter):
    def health(self) -> RuntimeHealth:
        health = super().health()
        return replace(health, details=dict(health.details, qualification="test_only_unqualified",
                                            production_qualified="false"))


def build_test_only_product(
    config: MayaConfig, *, wheel_path: Path, acknowledgement: str, actor_id: str,
    iteration_limit: int = 1,
) -> LocalMayaProduct:
    """Assemble the real local product with an explicit unqualified startup host.

Only synthetic/local testing is supported. No default launcher, config field or
environment switch selects this route. Supply the wheel retained by the release.
"""
    if type(iteration_limit) is not int or not 1 <= iteration_limit <= 3:
        raise GovernanceBoundaryError("governance.candidate_iteration_limit_invalid")
    _validate_test_scope(config, acknowledgement)
    with bind_request_identity(actor_id):
        pass
    _verify_loaded_artifact(wheel_path)
    gateway = _build_gateway(config)
    audit = _build_audit_sink(config)
    startup = _CandidateStartup(MayaGovernancePlugin(config, gateway, audit), wheel_path,
                                lambda: _validate_test_scope(config, acknowledgement))

    def construct(**kwargs):
        startup()
        kwargs.pop("agent_name", None)
        agent = import_module("run_agent").AIAgent(**kwargs)
        startup()
        # Hermes creates this manager only when an external provider is selected.
        # The isolated host attaches Maya via the existing lifecycle adapter;
        # built-in MEMORY.md/USER.md and session storage remain Hermes-owned.
        if agent._memory_manager is None:
            agent._memory_manager = import_module("agent.memory_manager").MemoryManager()
        return agent

    adapter = _CandidateAdapter(
        factory=construct, runtime_version=CANDIDATE_VERSION,
        supported_contract="project-maya.candidate-test-only.v1",
        startup_guard=startup,
        factory_kwargs={"model": config.llm.model, "provider": config.llm.provider,
                        "base_url": config.llm.endpoint, "api_key": "local-test-only",
                        "api_mode": "chat_completions", "quiet_mode": True,
                        "skip_context_files": True,
                        "enabled_toolsets": [], "max_iterations": iteration_limit},
    )
    secret_store = build_platform_secret_store(config.deployment.data_dir)
    return _assemble_local_product(config, secret_store, adapter, actor_id=actor_id, gateway=gateway)


def main(argv: list[str] | None = None) -> int:
    """Dedicated candidate launcher, never selected by production shortcuts."""
    import argparse
    from ..config import config_from_mapping

    parser = argparse.ArgumentParser(description="Isolated, unqualified Maya governance candidate")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--acknowledge", choices=[ACKNOWLEDGEMENT], required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--initialize-test-home", action="store_true")
    args = parser.parse_args(argv)
    product = None
    started = False
    try:
        config = config_from_mapping(json.loads(args.config.read_text(encoding="utf-8")))
        if args.initialize_test_home:
            initialize_test_only_home(config.deployment.data_dir, acknowledgement=args.acknowledge)
        os.environ["HERMES_HOME"] = str(config.deployment.data_dir.resolve() / "hermes")
        product = build_test_only_product(config, wheel_path=args.wheel,
                                         acknowledgement=args.acknowledge, actor_id=args.actor)
        product.start()
        started = True
        print(json.dumps({"qualification": "test_only_unqualified", "production_qualified": False,
                          "lifecycle": product.health().state.value}))
        return 0
    except Exception:
        print(json.dumps({"qualification": "test_only_unqualified", "production_qualified": False,
                          "status": "blocked", "reason_code": "governance.candidate_startup_failed"}))
        return 1
    finally:
        if product is not None:
            try:
                if started:
                    product.stop()
                else:
                    close = getattr(product.retriever, "close", None)
                    if callable(close):
                        close()
            except Exception:
                print(json.dumps({"qualification": "test_only_unqualified", "status": "blocked",
                                  "reason_code": "governance.candidate_shutdown_failed"}))
                return 1


if __name__ == "__main__":
    raise SystemExit(main())
