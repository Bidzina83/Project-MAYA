# Phase 2 Enterprise Config Profiles

## Status

Step 7 adds documented Enterprise configuration profiles that can be loaded,
materialized, normalized, and validated through the same V2 configuration
contracts used by runtime assembly.

## Profiles

The initial profiles live under `docs/config/`:

- `enterprise-byo-broker-disabled.json` configures Maya Enterprise with
  customer-owned model, Google, Slack, and Telegram credentials,
  `broker.mode=disabled`, governed local memory, and authenticated loopback
  local API.
- `enterprise-local-model-broker-disabled.json` configures Maya Enterprise
  with broker disabled, a local OpenAI-compatible model endpoint, disabled
  connectors, governed local memory, and authenticated loopback local API.

The profiles intentionally use placeholders instead of hardcoded machine
paths:

- `${MAYA_DATA_DIR}`
- `${MAYA_INSTANCE_ID}`

`project_maya.load_config_profile()` resolves those placeholders from
explicit caller input and then validates the result with `config_from_mapping()`.
The loader does not read environment variables, infer cloud endpoints, or
insert secret values.

## Boundaries

Enterprise config profiles must:

- keep raw credentials out of configuration;
- use `secret://...` references for credential-bearing modes;
- keep `broker.endpoint` absent when broker mode is disabled;
- preserve local governance and audit defaults;
- keep memory local and governed;
- avoid claiming live provider health or reachability;
- remain examples of supported contracts, not setup-time credential material.

Profile loading is not yet the final guided setup UX. Later setup work may
write a selected profile to disk through `maya import-config`, after resolving
operator-approved paths and secret references.
