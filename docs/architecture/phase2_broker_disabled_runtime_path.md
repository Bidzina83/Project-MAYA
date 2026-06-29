# Phase 2 Broker-Disabled Runtime Path

## Status

This document records the Phase 2 runtime-path requirement for Maya
Enterprise with `broker.mode=disabled`.

## Requirement

Broker-disabled Enterprise operation means Maya can validate, assemble, start,
run, use governed local memory, audit decisions, and expose the authenticated
local API without depending on Maya cloud services.

This path must use the same local product runtime as Standard:

```text
Enterprise config
  -> build_local_product()
  -> governed Agent facade
  -> HermesRuntimeAdapter
  -> local authorization gateway
  -> audit sink
  -> governed memory provider
  -> authenticated local API
```

The broker-disabled path must not:

- require a broker endpoint;
- fall back to Maya-managed model mode;
- bypass local model-egress authorization;
- bypass memory authorization;
- expose raw secret values through API responses, health, audit, or errors;
- report a connector or runtime capability as healthy when it is unavailable.

## Acceptance Evidence

`tests/test_phase2_broker_disabled_runtime.py` proves that an Enterprise
configuration with `broker.mode=disabled` can:

- validate and assemble through `build_local_product()`;
- construct the Hermes adapter with customer-owned model settings;
- start, run, and stop through the public Maya Agent lifecycle facade;
- authorize and audit `runtime.execute` and external `model.egress`;
- use the Hermes memory provider over governed local persistent memory;
- expose `/v1/health` and `/v1/run` through the authenticated local API;
- complete with no broker endpoint or Maya cloud dependency in configuration.
