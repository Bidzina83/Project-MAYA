# Local Secret Store

## Decision

Phase 1 includes a first approved local secret backend for Windows:
`WindowsDPAPISecretStore`.

The store writes encrypted blobs under:

```text
<MAYA_DATA_DIR>/secrets/
```

The encryption keys are protected by Windows DPAPI for the current user
profile. Maya configuration continues to store only `secret://...`
references, never raw credential values.

On platforms where no approved backend is implemented yet, Maya assembles an
`UnavailableSecretStore` and `maya doctor` reports the backend as unavailable
without claiming secret support.

## Limits

This is not a cross-platform secret strategy. macOS Keychain, Linux Secret
Service, supplied master-key, TPM/HSM, and external-vault backends remain
future work.

Do not replace this with plaintext files or an encrypted file whose key is
stored beside it.
