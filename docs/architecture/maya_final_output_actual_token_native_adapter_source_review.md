# Native Token Open/Close Adapter Source Review

Approved source preparation and injected tests completed 2026-11-10. The
versioned contract is `maya_final_output_actual_token_native_status_contract.md`.
The new adapter requires both token fixture symbols and is disconnected from
the launcher and both real roles. There is no executable native role entry.

`JournalTokenAccessNativeFixture.cs` constructs only the reviewed fixed paths
under the attempt, uses the exact shared matrix masks and flags, and accepts
one bound v2 command. The Windows backend captures failed-open errors, queries
identity on the same exact-mask handle, and attempts close once after every
successful open. Identity and close failures do not overwrite the open result.
No data read/write, metadata change, privilege change, reopen or retry exists.

The v2 verifier accepts an explicit identity failure on an opened handle.
A successful target open remains forbidden even without identity or successful
close. A control still needs the matching identity and successful close. The
existing single-use launch/provenance gate is shared; v1 and v2 reject each
other's replies. The v1 wire shape and matrix are unchanged.

692 native-adapter injected assertions, 399 v1 assertions, both sets of compile
exclusions and 108 focused Python tests passed (existing cache_dir warning).
Only fixture entry points ran; no Windows backend call or actual token launch
occurred. No native descriptor access or same-mask identity behavior was
measured. The actual child may still have incomplete specialized controls.

Next: review the synthetic inventory and exact launcher integration before
source wiring. Actual worker/child access, native identity query and cleanup
need separate approvals and evidence. No ACL change, package, VM run or
qualification occurred. Final3 remains blocked.
