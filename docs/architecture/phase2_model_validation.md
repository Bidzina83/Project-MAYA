# Phase 2 Model Configuration Validation

Phase 2 introduces explicit model configuration validation for Enterprise BYO
and broker-disabled operation. The validation surface lives at
`project_maya.model_config.validate_model_config()`.

The validator is intentionally local and redacted. It checks model mode,
provider, model name, endpoint shape, and secret-reference presence without
contacting model providers or exposing secret reference values.

Supported model modes are:

- `customer_owned`: provider credentials are customer-owned and represented by
  `llm.credential_ref`.
- `local`: inference uses a local or customer-hosted endpoint represented by
  `llm.endpoint`; credentials are optional but must be secret references when
  present.
- `maya_managed`: Maya-managed model proxy or billing, which is not valid for
  Enterprise configurations when `broker.mode=disabled`.

`maya doctor` reports the redacted validation result through `model.config`.
`build_local_product()` requires the same validation before assembling the
Hermes-compatible runtime adapter. This keeps validation, diagnostics, and
runtime assembly aligned.

The validation does not prove provider reachability, token freshness, quota,
or model availability. Those checks belong behind the versioned model adapter
and must remain governed model egress when they contact external services.
