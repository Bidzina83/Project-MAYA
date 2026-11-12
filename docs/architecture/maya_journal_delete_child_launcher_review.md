# Delete-Child Launcher Integration Review

Review only. The 44 inert assertions cover descriptor, retained-handle
lifecycle and verdict logic with injected inputs. The compiled Windows
adapter was not invoked. Access 2 remains blocked.

## Integration Boundaries

- Use a separate compile profile and fixed child entry. The existing
  Access 2 child entry emits an eight-row matrix and is not a valid
  one-right probe. Keep its selector, payload roots, report and admission
  unchanged. Do not enable broad fixture symbols in the new launcher.
- Use the existing verified AppContainer child launch and private pipe
  allowlist. The new child accepts one challenge, uses only the two fixed
  directory opens, closes any handle and emits one bounded reply. The
  coordinator, not the child, binds process, pipe, attempt and challenge
  and verifies EOF and natural exit. The inert classifier's boolean
  inputs are not a substitute for these observations.
- Keep the elevated control handle outside the child handle allowlist.
  Validate the fixed empty directory, its inherited baseline, integrity
  label and distinct identity before applying the approved DACL delta.
  Keep ownership of the handle and restoration plan even if the write
  throws. Recheck placement, descriptor and identity before and after
  the probe. Do not add access bits to the child's probe handle if the
  same-handle identity query fails; report incomplete.
- Restore the test-only entry after the owned jobs stop and before
  ordinary state-grant revocation. The existing package-SID cleanup
  does not remove the operator entry. Verify restoration on the same
  object. If Windows normalizes the descriptor so exact verification
  cannot succeed, fail closed; do not relax the comparison or try a
  path-based repair. Do not report a pass if cleanup is pending.

Before assembly, add inert integration cases for a stale reply, wrong
directory, early setup failure after a possible write, uncertain stop,
failed restoration and descriptor drift. Keep the Access 2 profile
regressions. A target open remains forbidden even if the positive
control fails. A valid result covers only this directory open, not an
actual deletion or containment qualification.

Next approval: isolated launcher source wiring and inert integration
only. No package assembly, live permission change or Windows run follows
from this review. Access 2, M08, M09 and qualification flags are unchanged.
