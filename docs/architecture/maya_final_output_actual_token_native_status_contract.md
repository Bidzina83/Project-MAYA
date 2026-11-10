# Native Token Access Status Contract

Approved native adapter source and injected tests only, 2026-11-10. No native
open, worker/child launch, new permissions, package, or VM run is authorized.
The new path requires both `MAYA_JOURNAL_TOKEN_ACCESS_FIXTURE` and
`MAYA_JOURNAL_TOKEN_ACCESS_NATIVE_FIXTURE`. The earlier v1 schema is unchanged.

The v2 command and reply have the same exact envelope keys, role/attempt/PID/
request bindings, ordering and 8192-byte cap as the inert contract, with `v:2`.
The fixed paths and exact per-case masks are unchanged. The adapter receives a
trusted attempt directory and constructs the fixed targets itself. No arbitrary
path or mask is accepted from wire. OPEN_EXISTING, share 7, leaf no-follow and
directory-handle flag for directory cases only. No generic rights, inheritance,
write, delete, rename, metadata modification, or retry.

Exact v2 status keys: `opened`, `closed`, `open_error`, `identity`,
`identity_error`. Failed open: nonzero bounded open error, null identity,
identity error 0, closed false. Successful open: open error 0, independent
close result, either a valid 24-hex opened volume/file identity with identity
error 0, or null identity and nonzero bounded identity error. Capture error
immediately after its native operation. Invalid or unavailable metadata maps to
a bounded error; never reopen with extra rights. Once opened, attempt close
exactly once and preserve the open result even on identity or close failure.

A well-formed successful target open is forbidden regardless of identity or
close result. A positive control needs matching identity and successful close.
Only that control paired with target access denied proves a denied row under
the existing trusted launch/provenance gates. Neither this adapter nor tests
provide a runnable role or perform actual token verification.
