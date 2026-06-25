# Local API Boundary

## Decision

Phase 1 introduces a minimal authenticated local API handler:
`project_maya.local_api.LocalAPI`.

The handler is versioned under `/v1/` and requires bearer authentication for
all handled routes, including health checks. The bearer token is resolved
through the configured secret store using:

```text
secret://local-api/token
```

The initial routes are:

- `GET /v1/health`
- `POST /v1/run`

`POST /v1/run` delegates to the public Maya `Agent`. It does not call Hermes,
plugins, connectors, or tools directly. This preserves the mandatory path:

```text
local API -> Agent facade -> governed runtime -> authorization gateway -> Hermes
```

## Limits

This is not yet a network server. A future HTTP listener must bind to loopback
by default and delegate to this handler rather than implementing a parallel
execution path.

The handler intentionally returns secret-safe error messages and does not
include tokens, secret references, prompts from failed requests, or raw
exception details in responses.
