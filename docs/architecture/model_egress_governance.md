# Model Egress Governance

## Decision

Phase 1 authorizes model-bound runtime requests separately from generic
runtime execution. `GovernedAgentRuntime` first authorizes:

```text
runtime.execute -> hermes-agent -> run
```

When the configured model mode is not local, it then authorizes:

```text
model.egress -> model:<provider> -> infer
```

The runtime call is not delegated to Hermes until both decisions allow the
operation.

## Redacted Metadata

The model-egress authorization record includes:

- model mode;
- provider;
- whether an endpoint is configured;
- data classification;
- redaction decision label;
- consent source label;
- idempotency key when supplied.

It does not include prompt text, completions, credential references, raw
secrets, connector payloads, local files, memory record bodies, or model
request bodies.

## Assembly

`build_local_product()` derives the egress policy from the existing `llm`
configuration and passes it into `GovernedAgentRuntime`. The Phase 1 contract
does not yet implement provider-specific redaction, residency enforcement,
model fallback, or customer consent UX. Those belong to later model-adapter and
setup work, but must preserve this local authorization point.

Callers can provide the request data classification through both `/v1/run` and
`maya run --data-classification`. If omitted, Phase 1 treats the request as
`internal`. The label is used for authorization and audit metadata only; prompt
contents remain excluded from local API errors and audit records.

