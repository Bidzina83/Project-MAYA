# Local Authorization Policy

## Decision

Phase 1 includes a minimal file-backed authorization gateway loaded from
`governance.policy_file`.

The policy is JSON and deny-by-default. It supports explicit allow rules for
the first governed runtime operation:

```json
{
  "allow": [
    {
      "actor_id": "operator",
      "capability": "runtime.execute",
      "target": "hermes-agent",
      "operation": "run",
      "reason_code": "policy.runtime_execute"
    }
  ]
}
```

Missing policy files fall back to `DenyByDefaultGateway`. This keeps local
governance mandatory even before the full policy engine exists.

## Limits

This is not the final governance language. It is a small acceptance-gate
mechanism for Phase 1 so local execution can be explicitly authorized without
requiring Maya Cloud.
