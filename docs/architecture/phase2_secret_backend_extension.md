# Phase 2 Secret Backend Extension Point

## Status

Step 9 defines the Enterprise secret backend extension point. Phase 2 still
ships only the platform backend used by the local product plus a local test
implementation for contract coverage.

## Contract

All secret backends implement the existing `SecretStore` operations:

- `read(ref)`
- `write(ref, value)`
- `delete(ref)`
- `contains(ref)`
- `health()`

Enterprise-capable backends also expose a redacted
`SecretBackendDescriptor` through the `EnterpriseSecretBackend` protocol. The
descriptor identifies backend kind and configuration state without exposing
secret values:

- `platform`
- `master_key`
- `tpm_hsm`
- `external_vault`
- `test`

The descriptor may include a backend location and a `secret://...` key
reference, but health and summaries report only whether those fields are
configured.

## Phase 2 Implementation

`InMemoryEnterpriseSecretBackend` is a local test implementation for contract
tests only. It proves the Enterprise backend interface can be used by Maya
without changing configuration semantics or storing raw credentials in config.

Phase 2 does not implement a production master-key file backend, TPM/HSM
backend, HashiCorp Vault backend, cloud KMS backend, or provider-specific
credential lifecycle. Those integrations must be added later behind this
contract with their own threat models, audit behavior, rotation semantics, and
platform qualification.

## Boundaries

- Configuration stores secret references, never raw credentials.
- Backend health is redacted.
- An encrypted file with its key stored beside it is not an acceptable vault.
- `build_platform_secret_store()` remains the default local backend selector.
- Enterprise backends are extension points until a production backend is
  explicitly implemented and tested.
