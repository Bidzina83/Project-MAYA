# Phase 3 Dependency Readiness Scope

## Status

Phase 3 scope gate for Capability Dependency and Readiness Foundation.

## Objective

Phase 3 creates Maya's dependency/readiness contract layer before heavy
capabilities are treated as implemented. Maya must be able to explain what a
profile requires, what is optional, what is customer-managed, what is missing,
and how to remediate it without silently installing system software.

## Dependency Categories

- `python_package`
- `system_command`
- `local_application`
- `service_runtime`
- `external_service`
- `model_endpoint`
- `customer_managed`

## Readiness Statuses

- `available`
- `missing_required`
- `missing_optional`
- `unsupported_os`
- `customer_managed`
- `disabled`
- `unknown`

## Profile Coverage

Phase 3 defines dependency contracts for:

- `maya-core`
- `maya-documents`
- `maya-metabase`
- `maya-browser`
- `maya-messaging`
- `maya-local-models`

`maya-core` remains usable without optional heavy-profile dependencies.

## Acceptance Criteria

1. Dependency contracts are typed, deterministic, and importable from the
   installed package.
2. Contracts distinguish Python packages, system commands, local applications,
   service runtimes, external services, model endpoints, and customer-managed
   dependencies.
3. `maya doctor` reports readiness for enabled profiles without leaking
   secrets or raw credential references.
4. Missing optional dependencies warn rather than failing core runtime.
5. Missing required dependencies fail only when the enabled profile cannot
   operate without them.
6. Disabled profiles do not fail doctor.
7. Install hints are OS-specific and informational only.
8. Clean package verification proves dependency metadata ships in the wheel.

## Non-Goals

This phase does not:

- install Poppler, Java, LibreOffice, browsers, Metabase, Docker, Ollama,
  LM Studio, vLLM, Microsoft Office, or system packages;
- package trained Maya skills;
- implement full Metabase lifecycle;
- implement full document-processing workflows;
- perform live connector OAuth or webhook validation;
- perform live model inference;
- claim Windows, macOS, Linux, server, or container platform support;
- build signed installers or update artifacts.
