# Phase 5 Mock Broker Conformance

The mock broker conformance suite is network-free and validates the protocol
without live Google, Slack, or Maya cloud credentials.

Required checks include:

- valid signed request acceptance;
- replayed nonce rejection;
- tampered body rejection;
- valid signed response acceptance;
- wrong response nonce rejection;
- expired request rejection;
- broker-disabled and setup-only mutation boundaries through CLI and unit
  tests;
- token lifecycle redaction for Google and Slack.

Conformance proves the local protocol boundary and credential lifecycle shape.
It does not replace the independent security review required before Phase 5 is
closed as complete.
