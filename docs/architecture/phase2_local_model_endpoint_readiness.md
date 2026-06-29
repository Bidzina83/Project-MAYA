# Phase 2 Local Model Endpoint Readiness

## Status

Step 8 adds a local, redacted readiness contract for OpenAI-compatible local
model endpoints such as Ollama, LM Studio, and vLLM.

## Contract

Local model mode is represented as:

```json
{
  "llm": {
    "mode": "local",
    "provider": "openai-compatible",
    "model": "<local model name>",
    "endpoint": "http://127.0.0.1:<port>/v1",
    "credential_ref": null
  }
}
```

`project_maya.validate_local_model_endpoint()` validates this configuration
without contacting the endpoint. It reports:

- whether local mode is configured;
- whether the provider is `openai-compatible`;
- whether the endpoint is local or customer-hosted;
- a best-effort endpoint family label for common defaults:
  `ollama` for port `11434`, `lm_studio` for port `1234`, and `vllm`
  for port `8000`;
- whether a credential reference is configured;
- `network_used=false`.

The readiness check is a configuration and adapter-boundary check only. It
does not prove that a local model server is running, that a model is pulled,
or that the endpoint accepts inference requests. Those probes belong behind a
future governed model adapter health check.

## Runtime Boundary

When `llm.mode=local`, `build_local_product()` still constructs the Hermes
adapter with the configured model and `base_url`, but does not install a
non-local `ModelEgressPolicy`. This keeps local inference inside the local or
customer-controlled trust boundary while preserving runtime adapter
portability.
