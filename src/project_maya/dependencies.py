"""Capability dependency contracts and safe readiness checks."""

from __future__ import annotations

import importlib.util
import os
import platform
import shutil
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse

from .config import ComponentProfile, MayaConfig
from .connectors import validate_configured_connectors
from .model_config import validate_local_model_endpoint


class DependencyCategory(str, Enum):
    PYTHON_PACKAGE = "python_package"
    SYSTEM_COMMAND = "system_command"
    LOCAL_APPLICATION = "local_application"
    SERVICE_RUNTIME = "service_runtime"
    EXTERNAL_SERVICE = "external_service"
    MODEL_ENDPOINT = "model_endpoint"
    CUSTOMER_MANAGED = "customer_managed"


class DependencyRequirement(str, Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    CUSTOMER_MANAGED = "customer_managed"


class DependencyReadinessStatus(str, Enum):
    AVAILABLE = "available"
    MISSING_REQUIRED = "missing_required"
    MISSING_OPTIONAL = "missing_optional"
    UNSUPPORTED_OS = "unsupported_os"
    CUSTOMER_MANAGED = "customer_managed"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DependencyContract:
    dependency_id: str
    profile: ComponentProfile
    category: DependencyCategory
    requirement: DependencyRequirement
    display_name: str
    check_name: str
    python_module: str | None = None
    command_names: tuple[str, ...] = ()
    supported_platforms: tuple[str, ...] = ("Windows", "Darwin", "Linux")
    install_hints: dict[str, str] | None = None
    description: str = ""

    def install_hint(self, system_name: str | None = None) -> str:
        hints = self.install_hints or {}
        platform_name = system_name or platform.system()
        return hints.get(platform_name) or hints.get("default") or "manual setup required"


@dataclass(frozen=True)
class DependencyReadiness:
    contract: DependencyContract
    status: DependencyReadinessStatus
    message: str

    @property
    def check_name(self) -> str:
        return self.contract.check_name

    def redacted_summary(self) -> str:
        return (
            f"{self.contract.dependency_id}:"
            f"status={self.status.value};"
            f"category={self.contract.category.value};"
            f"requirement={self.contract.requirement.value};"
            f"message={self.message}"
        )


@dataclass(frozen=True)
class ProfileReadiness:
    profile: ComponentProfile
    status: DependencyReadinessStatus
    dependencies: tuple[DependencyReadiness, ...]

    def redacted_summary(self) -> str:
        return (
            f"{self.profile.value}:status={self.status.value};"
            f"dependencies={len(self.dependencies)}"
        )


PYTHON_PACKAGE_HINTS = {
    "Windows": "python -m pip install project-maya[documents]",
    "Darwin": "python -m pip install project-maya[documents]",
    "Linux": "python -m pip install project-maya[documents]",
    "default": "python -m pip install project-maya[documents]",
}


DEPENDENCY_CONTRACTS: tuple[DependencyContract, ...] = (
    DependencyContract(
        dependency_id="python.project_maya",
        profile=ComponentProfile.CORE,
        category=DependencyCategory.PYTHON_PACKAGE,
        requirement=DependencyRequirement.REQUIRED,
        display_name="Project Maya package",
        check_name="dependencies.python.project_maya",
        python_module="project_maya",
        install_hints={
            "default": "install the Maya managed runtime package",
        },
        description="Core Maya package import required for the local runtime.",
    ),
    DependencyContract(
        dependency_id="python.reportlab",
        profile=ComponentProfile.DOCUMENTS,
        category=DependencyCategory.PYTHON_PACKAGE,
        requirement=DependencyRequirement.REQUIRED,
        display_name="ReportLab",
        check_name="dependencies.python.reportlab",
        python_module="reportlab",
        install_hints=PYTHON_PACKAGE_HINTS,
        description="PDF generation package used by document/PDF workflows.",
    ),
    DependencyContract(
        dependency_id="python.pypdf",
        profile=ComponentProfile.DOCUMENTS,
        category=DependencyCategory.PYTHON_PACKAGE,
        requirement=DependencyRequirement.REQUIRED,
        display_name="pypdf",
        check_name="dependencies.python.pypdf",
        python_module="pypdf",
        install_hints=PYTHON_PACKAGE_HINTS,
        description="PDF validation and text extraction package.",
    ),
    DependencyContract(
        dependency_id="python.markdown",
        profile=ComponentProfile.DOCUMENTS,
        category=DependencyCategory.PYTHON_PACKAGE,
        requirement=DependencyRequirement.REQUIRED,
        display_name="Markdown",
        check_name="dependencies.python.markdown",
        python_module="markdown",
        install_hints=PYTHON_PACKAGE_HINTS,
        description="Markdown conversion package used by document workflows.",
    ),
    DependencyContract(
        dependency_id="python.pillow",
        profile=ComponentProfile.DOCUMENTS,
        category=DependencyCategory.PYTHON_PACKAGE,
        requirement=DependencyRequirement.REQUIRED,
        display_name="Pillow",
        check_name="dependencies.python.pillow",
        python_module="PIL",
        install_hints=PYTHON_PACKAGE_HINTS,
        description="Image handling package used by document/PDF workflows.",
    ),
    DependencyContract(
        dependency_id="python.pymupdf",
        profile=ComponentProfile.DOCUMENTS,
        category=DependencyCategory.PYTHON_PACKAGE,
        requirement=DependencyRequirement.OPTIONAL,
        display_name="PyMuPDF",
        check_name="dependencies.python.pymupdf",
        python_module="fitz",
        install_hints={
            "Windows": "python -m pip install pymupdf",
            "Darwin": "python -m pip install pymupdf",
            "Linux": "python -m pip install pymupdf",
            "default": "python -m pip install pymupdf",
        },
        description="Optional fallback PDF preview renderer.",
    ),
    DependencyContract(
        dependency_id="command.pdftoppm",
        profile=ComponentProfile.DOCUMENTS,
        category=DependencyCategory.SYSTEM_COMMAND,
        requirement=DependencyRequirement.OPTIONAL,
        display_name="Poppler pdftoppm",
        check_name="dependencies.command.pdftoppm",
        command_names=("pdftoppm",),
        install_hints={
            "Windows": "winget install oschwartz10612.Poppler",
            "Darwin": "brew install poppler",
            "Linux": "sudo apt-get install -y poppler-utils",
            "default": "install Poppler for your OS",
        },
        description="Optional PDF preview rendering command.",
    ),
    DependencyContract(
        dependency_id="command.soffice",
        profile=ComponentProfile.DOCUMENTS,
        category=DependencyCategory.SYSTEM_COMMAND,
        requirement=DependencyRequirement.OPTIONAL,
        display_name="LibreOffice",
        check_name="dependencies.command.soffice",
        command_names=("soffice", "libreoffice"),
        install_hints={
            "Windows": "winget install TheDocumentFoundation.LibreOffice",
            "Darwin": "brew install --cask libreoffice",
            "Linux": "sudo apt-get install -y libreoffice",
            "default": "install LibreOffice for your OS",
        },
        description="Optional Office document conversion backend.",
    ),
    DependencyContract(
        dependency_id="application.ms-office",
        profile=ComponentProfile.DOCUMENTS,
        category=DependencyCategory.LOCAL_APPLICATION,
        requirement=DependencyRequirement.CUSTOMER_MANAGED,
        display_name="Microsoft Office",
        check_name="dependencies.application.ms-office",
        supported_platforms=("Windows", "Darwin"),
        install_hints={
            "Windows": "customer-managed Microsoft Office installation",
            "Darwin": "customer-managed Microsoft Office installation",
            "default": "customer-managed application",
        },
        description="Customer-managed local Office application.",
    ),
    DependencyContract(
        dependency_id="runtime.java",
        profile=ComponentProfile.METABASE,
        category=DependencyCategory.SERVICE_RUNTIME,
        requirement=DependencyRequirement.REQUIRED,
        display_name="Java runtime",
        check_name="dependencies.runtime.java",
        command_names=("java",),
        install_hints={
            "Windows": "winget install EclipseAdoptium.Temurin.21.JRE",
            "Darwin": "brew install openjdk@21",
            "Linux": "sudo apt-get install -y openjdk-21-jre",
            "default": "install a supported Java runtime",
        },
        description="Runtime required for managed local Metabase.",
    ),
    DependencyContract(
        dependency_id="service.metabase",
        profile=ComponentProfile.METABASE,
        category=DependencyCategory.SERVICE_RUNTIME,
        requirement=DependencyRequirement.CUSTOMER_MANAGED,
        display_name="Metabase service",
        check_name="dependencies.service.metabase",
        install_hints={
            "default": "configure managed_local or customer-managed Metabase service",
        },
        description="Metabase service lifecycle readiness placeholder.",
    ),
    DependencyContract(
        dependency_id="database.metabase-application",
        profile=ComponentProfile.METABASE,
        category=DependencyCategory.CUSTOMER_MANAGED,
        requirement=DependencyRequirement.CUSTOMER_MANAGED,
        display_name="Metabase application database",
        check_name="dependencies.database.metabase-application",
        install_hints={
            "default": "configure metabase.application_database with secret references",
        },
        description="Metabase application database readiness placeholder.",
    ),
    DependencyContract(
        dependency_id="database.metabase-analytics-sources",
        profile=ComponentProfile.METABASE,
        category=DependencyCategory.CUSTOMER_MANAGED,
        requirement=DependencyRequirement.OPTIONAL,
        display_name="Metabase analytics sources",
        check_name="dependencies.database.metabase-analytics-sources",
        install_hints={
            "default": "configure approved metabase.analytics_sources with secret references",
        },
        description="Approved analytics data source readiness for Metabase.",
    ),
    DependencyContract(
        dependency_id="browser.executable",
        profile=ComponentProfile.BROWSER,
        category=DependencyCategory.SYSTEM_COMMAND,
        requirement=DependencyRequirement.REQUIRED,
        display_name="Browser executable",
        check_name="dependencies.browser.executable",
        command_names=(
            "chrome",
            "chrome.exe",
            "chromium",
            "chromium-browser",
            "msedge",
            "msedge.exe",
            "google-chrome",
        ),
        install_hints={
            "Windows": "install Chrome, Edge, or a supported browser",
            "Darwin": "install Chrome or a supported browser",
            "Linux": "install chromium or google-chrome",
            "default": "install a supported browser",
        },
        description="Browser executable required when browser automation is enabled.",
    ),
    DependencyContract(
        dependency_id="browser.automation-driver",
        profile=ComponentProfile.BROWSER,
        category=DependencyCategory.CUSTOMER_MANAGED,
        requirement=DependencyRequirement.CUSTOMER_MANAGED,
        display_name="Browser automation driver",
        check_name="dependencies.browser.automation-driver",
        install_hints={
            "default": "configure an approved browser automation driver/runtime",
        },
        description="Customer-managed automation driver/runtime readiness placeholder.",
    ),
    DependencyContract(
        dependency_id="browser.governance-policy",
        profile=ComponentProfile.BROWSER,
        category=DependencyCategory.CUSTOMER_MANAGED,
        requirement=DependencyRequirement.CUSTOMER_MANAGED,
        display_name="Browser governance policy",
        check_name="dependencies.browser.governance-policy",
        install_hints={
            "default": "configure browser automation policy before enabling actions",
        },
        description="Local governance policy readiness for browser automation actions.",
    ),
    DependencyContract(
        dependency_id="service.google",
        profile=ComponentProfile.MESSAGING,
        category=DependencyCategory.EXTERNAL_SERVICE,
        requirement=DependencyRequirement.CUSTOMER_MANAGED,
        display_name="Google Workspace",
        check_name="dependencies.service.google",
        install_hints={"default": "configure Google connector credentials and scopes"},
        description="External Google connector readiness from connector validation.",
    ),
    DependencyContract(
        dependency_id="connector.google-contract",
        profile=ComponentProfile.MESSAGING,
        category=DependencyCategory.CUSTOMER_MANAGED,
        requirement=DependencyRequirement.CUSTOMER_MANAGED,
        display_name="Google connector contract",
        check_name="dependencies.connector.google-contract",
        install_hints={"default": "validate Google connector capability and scope contract"},
        description="Google connector capability, scope, and credential-mode contract readiness.",
    ),
    DependencyContract(
        dependency_id="connector.google-governance",
        profile=ComponentProfile.MESSAGING,
        category=DependencyCategory.CUSTOMER_MANAGED,
        requirement=DependencyRequirement.CUSTOMER_MANAGED,
        display_name="Google connector governance",
        check_name="dependencies.connector.google-governance",
        install_hints={"default": "configure Google users/resources allowlists before broad use"},
        description="Google connector allowlist and local-governance readiness.",
    ),
    DependencyContract(
        dependency_id="service.slack",
        profile=ComponentProfile.MESSAGING,
        category=DependencyCategory.EXTERNAL_SERVICE,
        requirement=DependencyRequirement.CUSTOMER_MANAGED,
        display_name="Slack",
        check_name="dependencies.service.slack",
        install_hints={"default": "configure Slack connector credentials and scopes"},
        description="External Slack connector readiness from connector validation.",
    ),
    DependencyContract(
        dependency_id="connector.slack-contract",
        profile=ComponentProfile.MESSAGING,
        category=DependencyCategory.CUSTOMER_MANAGED,
        requirement=DependencyRequirement.CUSTOMER_MANAGED,
        display_name="Slack connector contract",
        check_name="dependencies.connector.slack-contract",
        install_hints={"default": "validate Slack connector capability and scope contract"},
        description="Slack connector capability, scope, and credential-mode contract readiness.",
    ),
    DependencyContract(
        dependency_id="connector.slack-governance",
        profile=ComponentProfile.MESSAGING,
        category=DependencyCategory.CUSTOMER_MANAGED,
        requirement=DependencyRequirement.CUSTOMER_MANAGED,
        display_name="Slack connector governance",
        check_name="dependencies.connector.slack-governance",
        install_hints={"default": "configure Slack workspace/channel/user allowlists before broad use"},
        description="Slack connector allowlist and local-governance readiness.",
    ),
    DependencyContract(
        dependency_id="service.telegram",
        profile=ComponentProfile.MESSAGING,
        category=DependencyCategory.EXTERNAL_SERVICE,
        requirement=DependencyRequirement.CUSTOMER_MANAGED,
        display_name="Telegram",
        check_name="dependencies.service.telegram",
        install_hints={"default": "configure a customer-owned Telegram bot token"},
        description="External Telegram connector readiness from connector validation.",
    ),
    DependencyContract(
        dependency_id="connector.telegram-contract",
        profile=ComponentProfile.MESSAGING,
        category=DependencyCategory.CUSTOMER_MANAGED,
        requirement=DependencyRequirement.CUSTOMER_MANAGED,
        display_name="Telegram connector contract",
        check_name="dependencies.connector.telegram-contract",
        install_hints={"default": "validate customer-owned Telegram bot credential contract"},
        description="Telegram connector capability, scope, and credential-mode contract readiness.",
    ),
    DependencyContract(
        dependency_id="connector.telegram-governance",
        profile=ComponentProfile.MESSAGING,
        category=DependencyCategory.CUSTOMER_MANAGED,
        requirement=DependencyRequirement.CUSTOMER_MANAGED,
        display_name="Telegram connector governance",
        check_name="dependencies.connector.telegram-governance",
        install_hints={"default": "configure Telegram chat/user allowlists before broad use"},
        description="Telegram connector allowlist and local-governance readiness.",
    ),
    DependencyContract(
        dependency_id="endpoint.local-model",
        profile=ComponentProfile.LOCAL_MODELS,
        category=DependencyCategory.MODEL_ENDPOINT,
        requirement=DependencyRequirement.REQUIRED,
        display_name="Local model endpoint",
        check_name="dependencies.endpoint.local-model",
        install_hints={
            "default": "configure an OpenAI-compatible local endpoint such as Ollama, LM Studio, or vLLM",
        },
        description="Local/customer-hosted OpenAI-compatible model endpoint readiness.",
    ),
    DependencyContract(
        dependency_id="runtime.local-model-family",
        profile=ComponentProfile.LOCAL_MODELS,
        category=DependencyCategory.CUSTOMER_MANAGED,
        requirement=DependencyRequirement.CUSTOMER_MANAGED,
        display_name="Local model runtime family",
        check_name="dependencies.runtime.local-model-family",
        install_hints={
            "default": "install or configure Ollama, LM Studio, vLLM, or another OpenAI-compatible runtime",
        },
        description="Customer-managed local model runtime family readiness.",
    ),
    DependencyContract(
        dependency_id="model.local-model-artifact",
        profile=ComponentProfile.LOCAL_MODELS,
        category=DependencyCategory.CUSTOMER_MANAGED,
        requirement=DependencyRequirement.CUSTOMER_MANAGED,
        display_name="Local model artifact",
        check_name="dependencies.model.local-model-artifact",
        install_hints={
            "default": "pull or configure the requested local model in the selected runtime",
        },
        description="Customer-managed local model artifact readiness placeholder.",
    ),
)


def dependency_contracts() -> tuple[DependencyContract, ...]:
    return DEPENDENCY_CONTRACTS


def contracts_for_profile(
    profile: ComponentProfile,
) -> tuple[DependencyContract, ...]:
    return tuple(
        contract for contract in DEPENDENCY_CONTRACTS if contract.profile is profile
    )


def evaluate_dependency(
    contract: DependencyContract,
    config: MayaConfig,
) -> DependencyReadiness:
    system_name = platform.system()
    if system_name not in contract.supported_platforms:
        return DependencyReadiness(
            contract,
            DependencyReadinessStatus.UNSUPPORTED_OS,
            f"unsupported on {system_name}",
        )
    if contract.category is DependencyCategory.PYTHON_PACKAGE:
        return _evaluate_python_package(contract)
    if contract.category is DependencyCategory.SYSTEM_COMMAND:
        return _evaluate_system_command(contract)
    if contract.category is DependencyCategory.LOCAL_APPLICATION:
        return _evaluate_local_application(contract)
    if contract.category is DependencyCategory.EXTERNAL_SERVICE:
        return _evaluate_external_service(contract, config)
    if contract.category is DependencyCategory.MODEL_ENDPOINT:
        return _evaluate_model_endpoint(contract, config)
    if contract.category in {
        DependencyCategory.SERVICE_RUNTIME,
        DependencyCategory.CUSTOMER_MANAGED,
    }:
        if contract.dependency_id.startswith("service.metabase"):
            return _evaluate_metabase_service(contract, config)
        if contract.dependency_id == "database.metabase-application":
            return _evaluate_metabase_application_database(contract, config)
        if contract.dependency_id == "database.metabase-analytics-sources":
            return _evaluate_metabase_analytics_sources(contract, config)
        if contract.dependency_id == "browser.automation-driver":
            return _evaluate_browser_automation_driver(contract, config)
        if contract.dependency_id == "browser.governance-policy":
            return _evaluate_browser_governance_policy(contract, config)
        if contract.dependency_id == "runtime.local-model-family":
            return _evaluate_local_model_runtime_family(contract, config)
        if contract.dependency_id == "model.local-model-artifact":
            return _evaluate_local_model_artifact(contract, config)
        if contract.dependency_id.startswith("connector."):
            return _evaluate_connector_dependency(contract, config)
        if contract.command_names:
            return _evaluate_system_command(contract)
        return DependencyReadiness(
            contract,
            DependencyReadinessStatus.CUSTOMER_MANAGED,
            f"customer-managed; hint={contract.install_hint(system_name)}",
        )
    return DependencyReadiness(
        contract,
        DependencyReadinessStatus.UNKNOWN,
        "no readiness check is available",
    )


def evaluate_profile_readiness(
    config: MayaConfig,
    profile: ComponentProfile,
) -> ProfileReadiness:
    if profile not in config.runtime.enabled_profiles:
        return ProfileReadiness(
            profile=profile,
            status=DependencyReadinessStatus.DISABLED,
            dependencies=(),
        )
    dependencies = tuple(
        evaluate_dependency(contract, config) for contract in contracts_for_profile(profile)
    )
    if any(
        dependency.status is DependencyReadinessStatus.MISSING_REQUIRED
        for dependency in dependencies
    ):
        status = DependencyReadinessStatus.MISSING_REQUIRED
    elif any(
        dependency.status is DependencyReadinessStatus.MISSING_OPTIONAL
        for dependency in dependencies
    ):
        status = DependencyReadinessStatus.MISSING_OPTIONAL
    elif dependencies:
        status = DependencyReadinessStatus.AVAILABLE
    else:
        status = DependencyReadinessStatus.AVAILABLE
    return ProfileReadiness(
        profile=profile,
        status=status,
        dependencies=dependencies,
    )


def evaluate_enabled_profile_readiness(
    config: MayaConfig,
) -> tuple[ProfileReadiness, ...]:
    return tuple(
        evaluate_profile_readiness(config, profile)
        for profile in config.runtime.enabled_profiles
    )


def _evaluate_python_package(contract: DependencyContract) -> DependencyReadiness:
    assert contract.python_module is not None
    available = importlib.util.find_spec(contract.python_module) is not None
    if available:
        return DependencyReadiness(
            contract,
            DependencyReadinessStatus.AVAILABLE,
            f"{contract.python_module} importable",
        )
    return _missing_dependency(
        contract,
        f"{contract.python_module} is not importable; hint={contract.install_hint()}",
    )


def _evaluate_system_command(contract: DependencyContract) -> DependencyReadiness:
    command = next(
        (name for name in contract.command_names if shutil.which(name) is not None),
        None,
    )
    if command is not None:
        return DependencyReadiness(
            contract,
            DependencyReadinessStatus.AVAILABLE,
            f"{command} available",
        )
    return _missing_dependency(
        contract,
        f"command not found; hint={contract.install_hint()}",
    )


def _evaluate_local_application(contract: DependencyContract) -> DependencyReadiness:
    system_name = platform.system()
    if system_name == "Windows":
        office_root = os.environ.get("ProgramFiles", "")
        office_x86_root = os.environ.get("ProgramFiles(x86)", "")
        office_markers = (
            "Microsoft Office",
            "Microsoft Office\\root\\Office16",
        )
        if any(
            root
            and any(os.path.exists(os.path.join(root, marker)) for marker in office_markers)
            for root in (office_root, office_x86_root)
        ):
            return DependencyReadiness(
                contract,
                DependencyReadinessStatus.CUSTOMER_MANAGED,
                "customer-managed local application; availability requires setup validation",
            )
    return DependencyReadiness(
        contract,
        DependencyReadinessStatus.CUSTOMER_MANAGED,
        f"customer-managed; hint={contract.install_hint(system_name)}",
    )


def _evaluate_external_service(
    contract: DependencyContract,
    config: MayaConfig,
) -> DependencyReadiness:
    service_name = contract.dependency_id.removeprefix("service.")
    validation = _connector_validation_for(service_name, config)
    if validation is None:
        return DependencyReadiness(
            contract,
            DependencyReadinessStatus.DISABLED,
            f"{service_name} connector not configured",
        )
    if not validation.enabled:
        return DependencyReadiness(
            contract,
            DependencyReadinessStatus.DISABLED,
            f"{service_name} connector disabled",
        )
    status = (
        DependencyReadinessStatus.CUSTOMER_MANAGED
        if validation.valid
        else DependencyReadinessStatus.MISSING_REQUIRED
    )
    return DependencyReadiness(
        contract,
        status,
        validation.redacted_summary(),
    )


def _evaluate_connector_dependency(
    contract: DependencyContract,
    config: MayaConfig,
) -> DependencyReadiness:
    dependency_name = contract.dependency_id.removeprefix("connector.")
    connector_name, readiness_kind = dependency_name.rsplit("-", 1)
    validation = _connector_validation_for(connector_name, config)
    if validation is None:
        return DependencyReadiness(
            contract,
            DependencyReadinessStatus.DISABLED,
            f"{connector_name} connector not configured",
        )
    if not validation.enabled:
        return DependencyReadiness(
            contract,
            DependencyReadinessStatus.DISABLED,
            f"{connector_name} connector disabled",
        )
    if not validation.valid:
        return DependencyReadiness(
            contract,
            DependencyReadinessStatus.MISSING_REQUIRED,
            validation.redacted_summary(),
        )
    if readiness_kind == "contract":
        return DependencyReadiness(
            contract,
            DependencyReadinessStatus.CUSTOMER_MANAGED,
            (
                f"{connector_name}:credential_mode={validation.credential_mode.value}; "
                f"capabilities={_join_or_none(validation.capabilities)}; "
                f"scopes={_join_or_none(validation.scopes)}; "
                "network_used=false"
            ),
        )
    if readiness_kind == "governance":
        allowlists = (
            ",".join(
                f"{key}:{value}"
                for key, value in sorted(validation.allowlist_state.items())
            )
            if validation.allowlist_state
            else "none"
        )
        return DependencyReadiness(
            contract,
            DependencyReadinessStatus.CUSTOMER_MANAGED,
            (
                f"{connector_name}:allowlists={allowlists}; "
                f"default_action={config.governance.default_action}; "
                "governance_required=true; "
                "network_used=false"
            ),
        )
    return DependencyReadiness(
        contract,
        DependencyReadinessStatus.UNKNOWN,
        f"unknown connector dependency kind: {readiness_kind}",
    )


def _connector_validation_for(connector_name: str, config: MayaConfig):
    integration = config.integrations.get(connector_name)
    if integration is None:
        return None
    return validate_configured_connectors(
        {connector_name: integration},
        broker_mode=config.broker.mode,
    )[0]


def _join_or_none(values: tuple[str, ...]) -> str:
    return ",".join(values) if values else "none"


def _evaluate_model_endpoint(
    contract: DependencyContract,
    config: MayaConfig,
) -> DependencyReadiness:
    if config.llm.mode != "local":
        return DependencyReadiness(
            contract,
            DependencyReadinessStatus.DISABLED,
            f"llm.mode={config.llm.mode}",
        )
    readiness = validate_local_model_endpoint(config)
    status = (
        DependencyReadinessStatus.CUSTOMER_MANAGED
        if readiness.ready
        else DependencyReadinessStatus.MISSING_REQUIRED
    )
    return DependencyReadiness(
        contract,
        status,
        readiness.redacted_summary(),
    )


def _evaluate_local_model_runtime_family(
    contract: DependencyContract,
    config: MayaConfig,
) -> DependencyReadiness:
    readiness = validate_local_model_endpoint(config)
    if not readiness.ready:
        return DependencyReadiness(
            contract,
            DependencyReadinessStatus.MISSING_REQUIRED,
            readiness.redacted_summary(),
        )
    return DependencyReadiness(
        contract,
        DependencyReadinessStatus.CUSTOMER_MANAGED,
        (
            f"family={readiness.endpoint_family}; "
            "customer_managed=true; "
            "network_used=false; "
            f"hint={contract.install_hint()}"
        ),
    )


def _evaluate_local_model_artifact(
    contract: DependencyContract,
    config: MayaConfig,
) -> DependencyReadiness:
    readiness = validate_local_model_endpoint(config)
    if not readiness.ready:
        return DependencyReadiness(
            contract,
            DependencyReadinessStatus.MISSING_REQUIRED,
            readiness.redacted_summary(),
        )
    return DependencyReadiness(
        contract,
        DependencyReadinessStatus.CUSTOMER_MANAGED,
        (
            f"model={config.llm.model}; "
            f"family={readiness.endpoint_family}; "
            "model_presence=not_probed; "
            "network_used=false; "
            f"hint={contract.install_hint()}"
        ),
    )


def _evaluate_metabase_service(
    contract: DependencyContract,
    config: MayaConfig,
) -> DependencyReadiness:
    metabase = config.metabase
    if not metabase.enabled:
        return DependencyReadiness(
            contract,
            DependencyReadinessStatus.MISSING_REQUIRED,
            "metabase.enabled=false",
        )
    if metabase.deployment == "disabled":
        return DependencyReadiness(
            contract,
            DependencyReadinessStatus.MISSING_REQUIRED,
            "metabase.deployment=disabled",
        )
    endpoint_state = _metabase_endpoint_state(metabase.endpoint)
    if metabase.endpoint is None:
        return DependencyReadiness(
            contract,
            DependencyReadinessStatus.MISSING_REQUIRED,
            (
                f"deployment={metabase.deployment}; "
                f"endpoint={endpoint_state}; "
                f"hint={contract.install_hint()}"
            ),
        )
    return DependencyReadiness(
        contract,
        DependencyReadinessStatus.CUSTOMER_MANAGED,
        (
            f"deployment={metabase.deployment}; "
            f"endpoint={endpoint_state}; "
            "network_used=false"
        ),
    )


def _evaluate_metabase_application_database(
    contract: DependencyContract,
    config: MayaConfig,
) -> DependencyReadiness:
    metabase = config.metabase
    if not metabase.enabled:
        return DependencyReadiness(
            contract,
            DependencyReadinessStatus.DISABLED,
            "metabase.enabled=false",
        )
    if metabase.application_database is None:
        return DependencyReadiness(
            contract,
            DependencyReadinessStatus.MISSING_REQUIRED,
            f"application_database=missing; hint={contract.install_hint()}",
        )
    return DependencyReadiness(
        contract,
        DependencyReadinessStatus.CUSTOMER_MANAGED,
        (
            f"engine={metabase.application_database.engine}; "
            "credential_ref=configured"
        ),
    )


def _evaluate_metabase_analytics_sources(
    contract: DependencyContract,
    config: MayaConfig,
) -> DependencyReadiness:
    metabase = config.metabase
    if not metabase.enabled:
        return DependencyReadiness(
            contract,
            DependencyReadinessStatus.DISABLED,
            "metabase.enabled=false",
        )
    if not metabase.analytics_sources:
        return DependencyReadiness(
            contract,
            DependencyReadinessStatus.MISSING_OPTIONAL,
            f"analytics_sources=0; hint={contract.install_hint()}",
        )
    engines = ",".join(
        sorted({source.engine for source in metabase.analytics_sources})
    )
    return DependencyReadiness(
        contract,
        DependencyReadinessStatus.CUSTOMER_MANAGED,
        (
            f"analytics_sources={len(metabase.analytics_sources)}; "
            f"engines={engines}; "
            "credential_refs=configured"
        ),
    )


def _metabase_endpoint_state(endpoint: str | None) -> str:
    if endpoint is None:
        return "not_configured"
    parsed = urlparse(endpoint)
    host = parsed.hostname or ""
    if host == "localhost" or host == "::1" or host.startswith("127."):
        return "loopback_configured"
    return "customer_hosted_configured"


def _evaluate_browser_automation_driver(
    contract: DependencyContract,
    config: MayaConfig,
) -> DependencyReadiness:
    if ComponentProfile.BROWSER not in config.runtime.enabled_profiles:
        return DependencyReadiness(
            contract,
            DependencyReadinessStatus.DISABLED,
            "maya-browser profile disabled",
        )
    return DependencyReadiness(
        contract,
        DependencyReadinessStatus.CUSTOMER_MANAGED,
        (
            "customer-managed; "
            "network_used=false; "
            f"hint={contract.install_hint()}"
        ),
    )


def _evaluate_browser_governance_policy(
    contract: DependencyContract,
    config: MayaConfig,
) -> DependencyReadiness:
    if ComponentProfile.BROWSER not in config.runtime.enabled_profiles:
        return DependencyReadiness(
            contract,
            DependencyReadinessStatus.DISABLED,
            "maya-browser profile disabled",
        )
    return DependencyReadiness(
        contract,
        DependencyReadinessStatus.CUSTOMER_MANAGED,
        (
            f"policy_file={config.governance.policy_file.name}; "
            f"default_action={config.governance.default_action}; "
            "governance_required=true"
        ),
    )


def _missing_dependency(
    contract: DependencyContract,
    message: str,
) -> DependencyReadiness:
    status = (
        DependencyReadinessStatus.MISSING_REQUIRED
        if contract.requirement is DependencyRequirement.REQUIRED
        else DependencyReadinessStatus.MISSING_OPTIONAL
    )
    return DependencyReadiness(contract, status, message)
