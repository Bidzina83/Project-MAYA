# Observer Host - Stage 3 Candidate Review

## Scope And Status

2026-10-17: the user requested continuation of the existing Stage 3 entry-point,
permission-check and persistent-attempt work. This delivers a separate x64 console
host against the unchanged frozen supervisor library, not another launcher,
Hermes patch, security provisioner or product installer. The predecessor
[review record](governance-v2-observer-review-package.json) remains unchanged;
[the successor host record](governance-v2-observer-host-review.json) identifies
the new sources and retained build bytes. Neither record is execution permission.

The host executable was compiled, **not executed**, including no help, refusal
or native preflight launch. Only the separately selected inert fixture entry point
ran. No real VM/WMI/token/job operation, helper/reference/Python startup, upload
or guest change occurred. Gate A, native compatibility and production stay open.

## Reviewed Entry Sequence

1. Accept only one A-D case, its fixed authorization-file location and the exact
   reviewed manifest SHA256. No default case, alternate root, batch loop, override,
   fallback, resume or retry switch exists. Reject redirected standard input.
2. Read bounded canonical JSON, reject duplicate/unknown/missing keys, ambiguous
   types, BOMs, suffixes and hash drift. Require explicit execution authorization,
   the pinned library/review/contract hashes, exact case, actual named operator
   and package SIDs, nonempty VM UUID/adapter inventory, console session ID and
   a UTC approval window no longer than 30 minutes. No live manifest is supplied.
3. Check the guest build/edition, VM UUID/model, local elevated operator/session,
   fixed cwd and loaded host/library locations/hashes. Rehash the manifest and
   seven private reviewed records: authorization, baseline, console, external
   attempt reservation, inventory, parent context and security. Enumerate the
   WMI adapter inventory, excluding only loopback type 24, require administrative
   Down (2) and exact GUID equality. Disconnected-but-enabled is not accepted.
4. Require the exact interactive `AUTHORIZE CASE <case> <manifest SHA256>` phrase.
   Repeat preflight/expiry checks, exclusively create and flush/read back the
   local claim, then invoke the existing supervisor. Its native permission callback
   is single-use, rechecks inputs/environment/expiry and expires on return/failure.
   A swallowed failed callback cannot qualify a synthetic result as authorized.
5. Persist an allowlisted outcome before printing it. Raw exceptions, paths,
   SIDs, environment, console streams and record contents are not printed. Any
   persistence, cleanup or evidence uncertainty returns blocked. No result grants
   security-cleanup verification, networking permission or product qualification.

This is lab operational authorization by the trusted operator, not cryptographic
proof of a human decision or protection against the VM administrator. Hashing an
attestation binds its reviewed bytes; it does not prove its statements. The seven
records require actual evidence and explicit review under
[the existing Azure procedure](governance_v2_python_azure_procedure.md), not dummy
files with convenient hashes. WFP/profile/ACL/registry restoration and SAC identity
are not automatically established by a checkbox or this host's WMI query. Their
permission/read-back obligations remain intact. No independent cloud inventory
or Azure API access is implemented by the host.

Native preflight queries and redirected-console behavior have not been exercised.
An unavailable provider, missing adapter/identity, unsupported console or changed
build stops the case; do not improvise another query, actor or transport. WMI's
timeout does not guarantee a hard preflight deadline. Before dispatch there is
no selected payload; after dispatch the unchanged supervisor's common 100-second
clock and 95-second termination request remain the case budget. No extra matrix
or startup experiment is introduced by these source-level tests.

## Local Claims And Snapshot Resets

The precreated trusted `observer\attempts` directory must be empty. A new
`attempt.claim` is created exclusively before native dispatch, written with
write-through, flushed and read back, and held without sharing. No deletion,
truncation, overwrite or automatic recovery exists. A claim with no outcome,
an incomplete file, an old outcome or any unexpected entry blocks another case.
Normal completion creates a separate `outcome.json` exclusively, flushes/read-backs
its bytes, and retains the claim after the host exits. A second host cannot reuse
the baseline directory, even for another case. Isolated ordinary-file tests cover
these decisions; power-loss/guest filesystem behavior is not qualified.

**Restoring the baseline OS disk also restores its files.** The local claim does
not survive that restore and cannot independently enforce a one-run budget across
snapshots. The existing trusted out-of-band procedure must reserve A, B, C, D in
order in a journal outside the guest and restored disk; freeze that reservation
in `external_attempt.json` before each case. Preserve failed/uncertain reservations
without reuse. The host verifies its reviewed hash, not an external service's
atomic state. No cloud journal service or additional credential is introduced.
Do not put live authorization/reservation records into the baseline snapshot.
Missing, interrupted or disputed external records stop the remaining matrix.
No broad cross-snapshot anti-replay or rollback-proof claim is made.

## Proposed Placement And Exact Command Format

Under the existing proposed `C:\MayaGateA` workspace:

```text
observer\Maya.GateA.ObserverHost.exe
observer\Maya.GateA.Supervision.dll
observer\authorization\A\execution.json
observer\authorization\A\authorization.json
observer\authorization\A\baseline.json
observer\authorization\A\console.json
observer\authorization\A\external_attempt.json
observer\authorization\A\inventory.json
observer\authorization\A\parent_context.json
observer\authorization\A\security.json
observer\attempts\                       empty before the authorized case
```

The same authorization layout applies separately to B-D after their prescribed
baseline restore and new reviewed reservation. The observer/authorization/journal
area must not be granted to the restricted child. Exact guest ACLs remain part
of preparation review. The frozen payload, helper and reference use the paths
already recorded in the predecessor; they are not changed by this host.

The command format, **not an authorized command to run now**, is:

```text
cwd: C:\MayaGateA
C:\MayaGateA\observer\Maya.GateA.ObserverHost.exe --case A --manifest C:\MayaGateA\observer\authorization\A\execution.json --manifest-sha256 <reviewed-64-lowercase-hex-SHA256>
```

The manifest hash is a fingerprint, not a secret. The file itself contains private
guest identities and evidence bindings and stays outside Git. The checked-in
[disabled template](governance-v2-observer-host-template.json) has false consent,
null identities/records/times and no adapters; it is deliberately unusable. The
eventual approved manifest must have all values verified, sorted ordinal keys,
ASCII compact JSON, no whitespace/newline/BOM and no unused fields. This strict
format makes duplicate-key or type ambiguity rejectable; merely changing false
to true in the template does not produce a valid execution decision.

Exit 0 means Python entry/exit was observed in this bounded test, not product
health. Exit 2 means a complete observed startup failure; exit 3 means blocked or
uncertain. All outcomes preserve production/security-cleanup/networking false.
No successful exit authorizes the next case or a network reconnect.

## Validation And Next Boundary

Both host and inert fixtures compile x64 with warnings treated as errors, using
the existing Windows .NET Framework compiler and System.Management/System.Web
references. The executable links the retained library, rather than recompiling
or patching it. Retained host SHA256:
`80544d3a608f8ca5b876fd42b80138ff5709add4ca0346e0c95eba7ed4e44bd7`.
The DLL remains
`1a07c156ddd55b5e18066d747344721b71100083c1e9a29ad0011d6344aafcdc`.
Local build artifacts are ignored under
`.codex-build/governance-v2-observer-host-20261017`; neither fixture executables nor
development tools are part of the proposed VM payload.

The inert fixture reports **97 passing checks**, including A-D policy decisions,
manifest drift/types/duplicates/expiry, confirmation refusal, permission revocation,
swallowed callback denial, result sanitization, missing/failed persistence,
process-restart decisions and isolated two-thread file-claim contention. It never
constructs the native host environment or dispatches a launcher. The command
sandbox initially denied temporary-fixture folder access; the permissioned fixture
run passes. This is not an LPAC startup result or a reason to change guest security.

Final local validation: **53 tests pass**, zero skips, across host, supervisor,
Python-reproduction and line-ending suites. This includes 97 host and 200
supervisor fixture checks. Product-context validation, Python compilation and
diff whitespace checks pass. The prior review-package/source hashes and both
frozen bundle manifest hashes remain unchanged. No compiled binary is tracked
in Git and no native host/launcher/Python comparison was run.

This supplies the previously missing executable-host and invocation **candidate**
within Stage 3. User review, exact guest inventory, preparation impact/permission,
console/baseline rehearsal, per-case evidence, final execution manifest and the
separate A-D allowance are still required. Do not create a ready-to-run manifest,
upload, prepare security resources or execute the host from this source approval.
The next decision is review of this candidate, then the already defined VM
preparation-impact gate; no additional startup diagnostic is proposed.

Primary references checked during implementation:
[MSFT_NetAdapter administrative state and GUID](https://learn.microsoft.com/en-us/windows/win32/fwp/wmi/netadaptercimprov/msft-netadapter),
[exclusive file creation](https://learn.microsoft.com/en-us/dotnet/api/system.io.filemode?view=netframework-4.8.1),
[FileStream flush](https://learn.microsoft.com/en-us/dotnet/api/system.io.filestream.flush?view=netframework-4.8.1).
Those API contracts are not native qualification of this candidate.

## User Acceptance - Local Preparation Only

2026-10-17: the user explicitly stated "Reviewed and approved" in response to
this candidate review. Source and retained host/library hashes were rechecked
and match the reviewed record. Accepted review-record SHA256:
`fc129f07411b8ad72d2fc24b9d4a09d810dd254c940251b302d92fe0946ca7f7`.
The frozen JSON retains its original candidate status; this dated decision is
the acceptance record, not a rewrite of earlier evidence.

This closes the local source/fixture preparation and Stage 3 candidate review
within Azure procedure Step 1. It does not qualify native operation, change Gate A
status or authorize deployment/execution. Proceed to the existing Step 2 inventory
and preparation-impact review. Actual guest identities, console, disks, network
and baseline evidence, transfer/licensing/cost approval, rehearsal and final
per-case execution permission remain separate. No ready-to-run manifest is created.
