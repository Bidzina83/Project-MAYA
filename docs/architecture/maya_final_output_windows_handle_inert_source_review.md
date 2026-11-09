# Worker And Handle Inert Source Review

Approved source preparation completed 2026-11-09. See
`maya_final_output_windows_handle_inert_contract.md` for the frozen fixture
contract. All new adapter code requires `MAYA_FINAL_OUTPUT_INERT_FIXTURE`.
No production worker command, profile, launcher change or Win32 call was added.

`FinalOutputInertHandles.cs` validates injected original process/pipe identities,
finish/close/seal/EOF/natural-exit order, exit and stderr status, budget, and
worker audit identity before and after a bounded read. It forwards the seal and
prefix to the existing strict adapter only after that handoff succeeds. One
handoff cannot be reused. The fake journal checks opened identity and length on
one retained handle token through write, flush and readback, rejecting and
poisoning on injected faults. The read-only evidence classifier compares against
independently supplied canonical records and cannot restore a permission.

219 C# fixture assertions passed, including the composed worker handoff, journal
and one fake effect; identity, order, short write, flush, torn confirmation and
replay failures; and exact restart evidence classification. The fixture does not
compile without the inert define. 108 focused Python tests passed with the prior
pytest cache_dir warning. No product entry point or VM ran.

Injected metadata, lifecycle events, flush and byte transfers are not evidence of
Windows behavior. The descriptor fingerprint is a stand-in, not native ACL or
label verification. No real parent-relative open, protected handle provisioning,
worker finish protocol, durable restart evidence reader or crash persistence was
validated. The classifier assumes trusted expected records rather than rebuilding
them from a recovered journal. Native adapters and any process-interruption test
need separately reviewed source and execution approval. No assembly or real
publication occurred. Final3 remains blocked and qualification flags are unchanged.
