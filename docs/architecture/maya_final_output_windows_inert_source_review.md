# Windows Final-Output Inert Adapter Review

Approved fixture-only source preparation completed 2026-11-09. The evidence
contract is in `maya_final_output_windows_inert_contract.md`. The adapter is
compiled only with `MAYA_FINAL_OUTPUT_INERT_FIXTURE`. No product route, profile,
command handler, real sink, or consent UI was enabled.

The adapter validates the exact synthetic seal and bounded four-record worker
prefix against coordinator-supplied attempt, channel, actor, request, response,
finish and delivery identities. It independently checks stage order, strict
JSON, timestamps and exact metadata. It requires a matching fixture candidate
and trusted prior-delivery, positive-child and natural-exit observations.
Those observations are fixture inputs, not authenticated here by a real worker
process or channel. No worker is started or sent an evidence-finish command.

A single owner orders policy, cancellation, consume, intent append/readback,
recheck, and one synchronous fake effect. Consent is separately bound to exact
output bytes and destination; it is not launch consent. Intent and terminal
records bind the same identities and deadlines. Journal readback compares exact
expected bytes, rejects pre-existing bytes, and never restores a permit. A
post-intent denial can record a pre-effect stop. An invoked effect without
confirmed journal readback becomes terminal unknown and is never replayed.

112 C# fixture assertions passed, including cross-attempt and channel binding,
malformed prefix, negative child and worker evidence, both expiry boundaries,
policy and revocation races at fixture checkpoints, duplicate concurrent release,
torn writes, stale journal and lost acknowledgement. The fixture fails to compile
without the inert define as expected. 108 focused Python tests passed (existing
pytest cache_dir warning only). No product executable or VM ran.

The journal is a memory fixture with injected flush/readback failures. This is
not proof of Windows durable persistence, safe opened-handle provisioning,
authenticated worker seal/exit observation, process-wide retention limits, or
restart cleanup. The stale-receipt test uses a different trusted attempt ID;
fresh identity issuance must still be enforced by the launcher. Original
dispatch replay enforcement is unchanged, not exercised by this C# fixture.
Those boundaries require separate source review before any packaging decision.
Final3 remains blocked, and all qualification flags remain unchanged.
