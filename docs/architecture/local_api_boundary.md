# Local API Boundary

## Decision

Phase 1 introduces a minimal authenticated local API handler:
`project_maya.local_api.LocalAPI`.

The handler is versioned under `/v1/` and requires bearer authentication for
all handled routes, including health checks. A small standard-library HTTP
server adapter, `build_local_api_http_server()`, can expose the handler on
loopback for local clients. The bearer token is resolved through the
configured secret store using:

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

The request body accepts:

- `input`: required input text;
- `idempotency_key`: optional replay/idempotency label;
- `data_classification`: optional governance label, defaulting to `internal`.

The data-classification label is passed to the governed runtime so runtime
authorization, model-egress authorization, and audit records classify the
request without logging prompt contents.

## Limits

The Phase 1 HTTP adapter only permits loopback binding. Non-loopback and
remote access require later TLS, CORS/CSRF, privilege separation, and explicit
policy work before they can be enabled. Phase 1 configuration therefore
rejects `local_api.remote_access: true` and non-loopback `local_api.bind`
values instead of accepting settings the runtime will not honor.

The handler intentionally returns secret-safe error messages and does not
include tokens, secret references, prompts from failed requests, or raw
exception details in responses.
