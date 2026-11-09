# Final-Output Authorization: Inert Source Review

Approved source preparation completed 2026-11-09. Final3 remains blocked under
its original M08 contract. The reference is not wired into the launcher, model
worker, profile selection, production policy, or any publication route.

## Reference Behavior

`src/project_maya/bridge/final_output_inert.py` owns one synthetic attempt and
accepts only an in-memory fake sink. It holds one immutable bounded candidate
after trusted receipt and positive-child admission. Exact candidate/destination
consent and current local policy are required for a separate one-use permission.
Pending time starts at owner creation; release time is bounded by the minimum
of pending, consent, and output-window deadlines. Exact expiry and bad or
backward clock samples fail closed. There is no dispatch-grant input or renewal.

The owner serializes consume, intent append, final validity check, and synchronous
fake acceptance. Revocation, policy changes, or elapsed time after intent can
still stop disclosure. Once the fake sink is invoked, missing acknowledgement
or confirmation persistence failure yields terminal unknown and never retries.
The intent contains binding metadata, not the candidate bytes.

## Verification And Limits

108 focused Python tests passed: 34 new cases and 74 historical M08 cases.
Coverage includes exact timing boundaries, binding substitutions, duplicate
receipt and release, two competing release calls, post-intent revocation,
policy/clock/audit faults, and lost acknowledgement. The prior pytest cache_dir
warning remains. No native or whole-repository test claim.

The receipt and child postcondition flag model already-verified host inputs;
the reference does not authenticate process/channel provenance itself. Audit
durability is represented by a synchronous callback, not tested on Windows.
The restart test shows a new owner has no permit, not durable stale-receipt
rejection. The fixture's elapsed-dispatch example does not exercise a real
dispatch grant. Process-wide capacity, scheduled expiry cleanup, restart
identity admission, durable audit health, strict wire/audit parsing, and actual
policy/consent/sink integration remain outside this reference. No production
deadline or concurrency values were selected.

Final3 ZIP/EXE, 401 frozen entries and 167 original product paths rehashed
unchanged. No existing product file changed. No assembly, VM execution, real
publication, or qualification. Gate A remains open. A later integration design
must resolve the above boundaries before requesting any package approval.
