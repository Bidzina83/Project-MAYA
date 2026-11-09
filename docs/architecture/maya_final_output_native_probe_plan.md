# Native Handle And Process-Interruption Probe Plan

Review only, 2026-11-09. The inert source review remains valid as fixture
evidence. No native probe has been implemented, compiled, or run in this step.
No product integration, assembly, VM activity, or Final3 retry is approved.

## Why A Separate Probe

`WindowsIsolation.cs:Native.SetLabel` applies and reads the integrity label by
path. `BridgeHostFiles.cs:Write` closes its creation handle before that step.
`ProductFiles.cs:NoLinks` checks named ancestors but does not retain them.
These existing paths are not the proposed same-handle journal proof. The
fixture's descriptor fingerprint and flush callback cannot settle whether the
opened object, handle rights, actual descriptor and persistence match on Windows.
See `maya_final_output_windows_handle_review.md` for reviewed API references.

Start with a separate disposable Windows probe, not a new MAYA profile. It must
not link or call the product entry point, launch Python or a MAYA worker, create
an AppContainer/WFP rule, change VM settings, or touch protected product roots.
The probe writes only bounded synthetic records under a fresh, explicitly
approved scratch root on a local NTFS volume. Verify the volume and record the
actual Windows build, token and file-system facts before interpreting results.
Refuse a redirected, remote, reparse or unsupported root. Do not request new
privileges or retry with weaker checks. Inability to provision or read back the
required descriptor is a blocked result, not permission to weaken it.

## Source Contract For The Probe

Use a fresh attempt ID and a supervisor-owned expected binding. The supervisor
owns the private checkpoint channel and process handle; it never finds a target
by name or PID alone. A helper performs only scratch-file operations and a
synthetic acknowledgement handshake. It has no real output destination. Keep
the expected intent/terminal bytes outside the helper's journal so recovery
does not trust arbitrary bytes from the object being evaluated.

Freeze a probe-only descriptor: current test owner/group, protected DACL with
only the explicitly expected test principal and SYSTEM, and a Medium
no-write-up file label. Freeze exact access masks and inheritance in source
review; the probe descriptor does not authorize a production descriptor change.
Treat the supervisor, helper, test user and machine administrators as trusted
for this experiment. A same-principal or privileged attacker is not covered.

Pin the validated directory chain across create/open, without delete sharing,
or demonstrate an equivalently reviewed parent-relative open. Create the leaf
exclusively with a non-inheritable, no-sharing handle. Verify owner, group,
protected DACL, label, volume/file ID, file type, attributes, link count and
bound length on that handle. Append, flush and read back on the same handle.
Use at most the fixture's 16 KiB journal budget. No fallback path, path-only
descriptor check, reopen-to-readback, or automatic recovery writer. Independent
read-only inspection after helper exit verifies its own opened-object identity
against the identity retained by the supervisor. Clean up only explicitly
created scratch artifacts after evidence is retained, under the run approval.

## Validation Order

1. Source and compile-only checks first. Review handle ownership, access masks,
   no-follow/ancestor strategy, allocation and close paths, exact record bytes,
   and every permitted scratch path. Compile only a standalone probe entry
   point. Do not execute it under source approval.
2. Under separate execution approval, establish a baseline create/write/flush/
   readback and independent read. Exercise collision, competing open/rename,
   wrong identity or descriptor, hard-link and reparse cases using only probe
   objects. A case whose precondition cannot be created with the approved
   token is untested, not a pass. Do not change OS policy to manufacture it.
3. Under explicit interruption approval, stop only the helper launched for the
   exact attempt, using its retained process handle. Use barrier acknowledgements,
   not sleeps, to locate each interruption. Wait for that handle to signal
   before the supervisor inspects the journal read-only. No restored permit,
   recovered writer, or second fake effect.

| Controlled interruption point | Required conservative evidence result |
| --- | --- |
| Before intent write | No confirmed evidence; absence is not general proof of no effect |
| After intentionally partial intent write | Invalid/unknown; do not parse a partial record as complete |
| After intent flush and readback, before fake acceptance | Intent alone is unknown to the journal reader, even if the supervisor knows where it stopped |
| After fake acceptance, before confirmation | Intent alone is unknown and must not replay |
| After partial confirmation | Invalid/unknown; do not upgrade it to confirmed |
| After complete confirmation flush and readback | Confirmed as recorded only if exact binding and opened identity match |

The deliberate partial-write cases are fault injection. A process stop does not
simulate a machine power loss. Native success would establish only observed
behavior on the tested volume, build and interruption points. It would not prove
power-loss durability, arbitrary crash atomicity, real-sink semantics, actual
worker seal provenance, or containment. Worker protocol integration and live
token/pipe/exit validation remain separate later work.

## Next Approval

Recommend separate approval for **standalone probe source and compile-only
checks**, with a fresh exact-artifact and scratch-target execution approval
after review. No native execution or process termination is authorized here.
Keep Final3 blocked, preserve frozen builds, and leave qualification unchanged.
