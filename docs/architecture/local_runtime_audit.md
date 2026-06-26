# Local Runtime Audit

## Decision

Phase 1 records runtime authorization decisions to a local JSON Lines audit
sink:

```text
<MAYA_DATA_DIR>/governance/audit/runtime.jsonl
```

The first audited event types are:

```text
authorization.runtime
authorization.model_egress
```

The record includes decision metadata such as actor, capability, target,
operation, data classification, idempotency key, decision, reason code, and
timestamp.

`authorization.model_egress` records provider and endpoint-classification
facts before external inference is delegated to Hermes. It records whether an
endpoint is configured, not the endpoint secret or model request body.

## Privacy

Runtime audit records must not include prompt text, completion text, secret
values, connector payloads, raw files, memory record bodies, or model request
bodies. Those may be governed elsewhere, but the Phase 1 runtime audit only
records authorization facts.

## Limits

This is not the final audit subsystem. Future work should add retention
policy, tamper evidence, rotation, export, and richer event families while
preserving the redaction rule.
