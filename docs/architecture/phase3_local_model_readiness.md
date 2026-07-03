# Phase 3 Local Model Readiness

## Status

Local model readiness hardening slice for Phase 3 Capability Dependency and
Readiness Foundation.

## Decision

Maya reports local-model readiness through deterministic configuration checks
before local model execution is treated as product-complete.

The `maya-local-models` profile now reports:

- OpenAI-compatible endpoint configuration readiness.
- Customer-managed runtime family readiness.
- Customer-managed model artifact readiness.

The readiness layer reuses `validate_local_model_endpoint()` and remains
network-free. It recognizes common OpenAI-compatible endpoint families:

- `ollama` for port `11434`;
- `lm_studio` for port `1234`;
- `vllm` for port `8000`;
- generic local OpenAI-compatible endpoints;
- customer-hosted OpenAI-compatible endpoints.

## Doctor Behavior

`maya doctor` emits stable checks such as:

- `dependencies.profile.maya-local-models`
- `dependencies.endpoint.local-model`
- `dependencies.runtime.local-model-family`
- `dependencies.model.local-model-artifact`

When `maya-local-models` is enabled, invalid or non-local model configuration
is a required readiness failure. Runtime family and model artifact checks are
customer-managed in Phase 3 because Maya does not install local model servers,
pull model weights, or perform live inference.

Messages are redacted. They include endpoint family, model name, credential
reference state, and `network_used=false`, but do not print endpoint hostnames,
ports, secret references, prompts, or model responses.

## Non-Goals

This slice does not:

- install Ollama, LM Studio, vLLM, or model runtimes;
- pull or verify model weights;
- probe `/v1/models`, `/health`, or any live endpoint;
- perform local inference;
- claim local model support for any platform.

Those capabilities belong to later installer, setup, and runtime integration
work.
