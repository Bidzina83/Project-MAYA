# Windows Final-Output Inert Evidence Contract

Fixture-only source preparation, 2026-11-09. No runnable profile or worker
command is enabled. Compile the adapter only with `MAYA_FINAL_OUTPUT_INERT_FIXTURE`.

- Prospective command: `model_output_evidence_finish`, exact keys `v`, `type`,
  `attempt`, `request_id`. It must not be added to the legacy worker.
- Inert seal reply: exact keys `v`, `type`, `attempt`, `request_id`, `channel`,
  `delivery_id`, `audit_sha256`. Version 1, type `model_output_evidence_sealed`.
  Verify against coordinator-owned identities and a four-record sealed legacy
  delivery prefix. Natural completion is a trusted external observation, not a
  worker assertion in the reply. The fixture does not run or terminate a worker.
- Release journal: bounded LF-delimited strict UTF-8 JSON; maximum 16 KiB and
  two records. Exact keys `v`, `event`, `attempt`, `channel`, `actor`,
  `delivery_id`, `request_sha256`, `response_sha256`, `output_sha256`,
  `output_bytes`, `destination`, `consent_id`, `epoch`, `deadline`.
  Destination is `synthetic:fake-operator`. Attempt ID is the one-use identity
  because this owner admits only one release. Epoch combines local policy,
  revocation and consent withdrawal. Events are `release_intent`, followed by
  `delivery_confirmed` or `pre_effect_stop`, with identical bindings.
- No rehydration API. An intent without a valid terminal record, an invalid
  journal, or readback failure is never permission. Inert journal calls model
  persistence and readback; actual file handle semantics remain unverified.
- Exact deadline is expired. All ticks and limits are fixture parameters; no
  production values, real consent UI, or real publisher. An owner is bound to
  a fresh attempt and channel supplied by trusted admission. No legacy parser,
  launcher, isolation, or dispatch lease changes.
