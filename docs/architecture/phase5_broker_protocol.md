# Phase 5 Broker Protocol

Project MAYA implements the Phase 5 broker protocol as a local-first,
cryptographic contract. The local Maya instance remains authoritative for
configuration, governance, audit records, local token metadata, and stored
secret references.

## Protocol Contract

- Protocol version: `maya-broker-v1`.
- Instance proof uses Ed25519 private-key possession.
- Requests bind method, path, canonical body hash, nonce, issue time, expiry,
  instance id, key id, and protocol version into the signed payload.
- Broker responses bind the request nonce, canonical body hash, issue time,
  expiry, broker key id, and protocol version into the signed payload.
- Replay protection rejects reused nonces within the local broker conformance
  cache.
- Expired, future-dated, tampered, wrongly versioned, or incorrectly signed
  messages are invalid.

## Ownership Boundary

The broker may assist with registration, OAuth setup, encrypted credential
handoff, token refresh mediation, update metadata, consented diagnostics, and
optional model proxy readiness. It must not own persistent memory, customer
files, vector stores, governance records, workflow state, task state, business
records, Metabase analytics data, or local audit authority.
