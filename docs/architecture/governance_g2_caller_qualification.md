# G2 Caller Qualification Evidence

## Scope And Reviewed Inputs

Caller-refinement Step 3 within G2 work package 3/create Step 4. This increment
qualifies the bounded native host preparation/receipt/reader failure matrix,
not the complete create-to-AIAgent loop, live frontend, production runtime or
Windows product. Step 2 sources, Patch 29 and its parent inputs are unchanged.

`prepare_governance_g2_caller_qualification.py` reconstructs the reviewed caller
overlay and binds the new diagnostic file and its fresh-host restart helper in
`governance-g2-caller-qualification.json`. Generated metadata cannot override
reviewed parent, test or helper hashes. Native and staged Maya inventories retain
the parent verification. Final qualification manifest SHA256:
`8530d3272480e98b0c62367ebac857056c5b0257ec76a82a8ab6b21bed9315a0`.

Twenty cases pass together: eight frozen Step 2 probes and twelve additional
qualification cases. One known pytest cache_dir warning occurs, with no skips.
The ordinary-mode parity remains the Step 2 evidence; native/host implementation
bytes did not change. No additional ordinary-mode behavior is claimed here.

## Required-Case Mapping

Names below refer to functions in `hermes_g2_caller_native.py` (base) or
`hermes_g2_caller_qualification_native.py` (matrix). Parameter variants count
separately in the native run; they are not fabricated agent dispatches.

| Contract case | Native evidence |
| --- | --- |
| successful_exit | Base normal-exit acknowledgement and separate reader selection. |
| caller_exception | Base failed-caller exception identity preserved; quarantined. |
| cancellation | Matrix normal-exit authority loss: actual Task.cancel(), native acknowledgement denial, queued CancelledError delivery. |
| expiry | Matrix normal-exit authority loss: deterministic deadline clock, no acknowledgement. |
| revocation | Matrix normal-exit authority loss: revoke before acknowledgement, quarantine only. |
| process_exit_before_ack | Matrix actual child os._exit; pending receipt retained; separate fresh native host denies read/scope/blind create. |
| ack_policy_denial | Base acknowledgement permission removed after allocation; no implicit reuse of create permission. |
| ack_audit_failure | Matrix audit throws before acknowledgement CAS; fixed error, quarantined. |
| ack_sql_failure | Matrix actual native SQLite trigger rejects acknowledgement update; rollback and quarantine. |
| unknown_ack_commit | Matrix failures before and after actual commit: no reported scope success, no replay, actual durable outcome retained. |
| quarantine_failure | Base actual SQLite trigger rejects quarantine; original caller exception preserved and pending stays blocked. |
| duplicate_ack | Matrix old authority after scope exit cannot acknowledge again or mutate state. |
| foreign_receipt | Matrix controlled correlation/principal descriptor mutation cannot acknowledge original row; exact original cleanup only. |
| stale_route | Matrix fixture injects newer route/generation/hash; neither acknowledgement nor cleanup overwrites it. |
| legacy_published | Base legacy published row is not adopted by the reader. |
| reader_before_ack | Base pending receipt read denied; direct native create stays pending. |
| reader_after_ack | Base acknowledged result is independently read-authorized, then an append-only G1 scope enters/exits. |

## Outcomes And Limitations

Denied cases check durable state, no active transaction, empty caches/inactive
caller/reader state, SQLite integrity/foreign keys, exclusion release, no blind
create replay and secret-safe fixed diagnostic/audit output where applicable.
Expired or revoked create authority never becomes acknowledgement authority;
cleanup uses only the exact host-created reducing descriptor.

If acknowledgement commit actually occurred but its return was lost, the scope
still reports failure and no continuation executes. The row remains acknowledged:
rollback is not falsely claimed, and cleanup cannot downgrade that outcome. A
new, separately authorized reader may confirm this durable state without replay.
This is not cross-store audit reconciliation or automatic maintenance.

The process worker initializes only synthetic fixture state, exits before scope
acknowledgement, and is bounded/reaped by subprocess timeout handling. Restart
uses the actual native store and installed callbacks/reader; its caller-body
counter is zero. It does not construct AIAgent or measure SDK/provider transport.

Foreign/stale cases are explicit fixture state/descriptor injection, not enabled
reset/switch or user-provided selectors. Expiry uses a controlled clock; this
does not qualify every timed/thread revocation interleaving. Cancellation has no
async suspension inside the synchronous preparation body. General workers and
untrusted executable preparation bodies remain excluded.

## Next In The Approved Sequence

Validation passed: 20 native caller cases, 12 provenance/design tests and 47
product regression tests. The product-context validator, Python syntax checks
and whitespace checks also passed. These results do not extend the bounded
qualification scope described above.

The bounded required-case matrix has evidence, but Step 3 is not accepted as
complete. Next is complete caller composition evidence: preparation completion
through the acknowledged native reader and G1 lease into the actual native agent
loop, with failure/denial stopping before unauthorized execution. Do not infer
that G1's earlier resumed-session profile already qualifies this create path.
Then perform the Step 4/create acceptance review, including filesystem, platform,
frontend and other unresolved coverage limitations. No other G2 transition,
production activation, wheel or installer follows from this increment.
