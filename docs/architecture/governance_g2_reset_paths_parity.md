# G2 Reset Step 4 Paths And Parity

## Plan Location

This is the remaining unsafe-path and ordinary-mode parity item in G2 work
package 3 reset Step 4, following the approved Patch 35 correction and its 200
bounded requalification cases. The user authorized continuation after committing
and reporting green CI. No native/host runtime edits, new patch, schema authority,
production activation, runtime pin, wheel or installer changes are introduced.

The source candidate remains `.codex-build/governance-g2-publisher-20261008-a`.
`governance-g2-reset-paths.json` separately pins the parent input, the path test,
27 unchanged fixtures, ordinary suite selection and unchanged cache controls.
Earlier manifests and source inventories are preserved.

## Unsafe Path Evidence

2026-10-08: all 26 native cases pass, without skips, on the unchanged corrected
candidate. The module verifies frozen parent ancestry and complete source/host
inventories before using actual native SessionStore and SQLite.

| Cases | Boundary and observations |
| --- | --- |
| Five real Windows directory junctions | Replace the session directory before reset, after native commit, after temporary-file close/fsync, before acknowledgement, or before acknowledged route selection. Unsafe routing/publication denies; sentinel and complete projection bytes remain unchanged by the denied operation. |
| Sixteen platform-attribute probes | Inject reparse/symlink attributes for session directory, native database, projection and lockfile, before reset or after commit. These execute the real native caller and path guard; they are not real file-link creation tests. |
| Four missing/non-file storage cases | Move the actual projection or lockfile aside, leave it absent or replace it with a directory. Deny without recreating/adopting a fallback file or allocating a reset. |
| One UNC rejection | Configured UNC session directory denies before filesystem access; no remote share is contacted. |

Precommit failures preserve the complete original database/projection. Postcommit
failures retain exactly one reset with source transcript/metadata and empty target,
blocked pending publication or pending caller state, no host confirmation and no
agent/model dispatch. The acknowledged-reader case preserves its already committed
state while denying selection through the unsafe path. No fake rollback or repair
is claimed. Integrity/foreign keys, transaction cleanup, cache and temporary-file
cleanup are checked. Junctions are explicitly restored inside isolated fixtures;
this test cleanup does not grant product recovery authority.

The native run retains the known disabled-cache-provider configuration warning.
Continuous hostile filesystem races, ACL attacks, actual file-symlink escapes,
power-loss durability and production storage provisioning remain excluded from
this bounded source profile.

## Ordinary Mode Parity

The final ordinary comparison passes bounded parity. The reproducible runner exports the
pinned Hermes Git objects without patches, verifies the full baseline inventory,
copies the verified corrected native source, and runs each native suite in its
own process. Working directories/homes are isolated, ambient credentials are
removed, and both inventories must remain unchanged after testing.

The selected native suites are session, approval and slash confirmation, followed
by the two unchanged ordinary prompt-cache controls. Native test and conftest bytes
must match pinned originals. Structured JUnit outcomes must match case-for-case;
skips, collection/process errors, missing reports, unexpected failures or changed
inventories block the report. The nine previously documented Windows absolute
shell-path failures are executed and retained, not skipped or reclassified as
passes. They remain a shell/platform qualification issue for later gates.

Generated disposable copies, JUnit files and the final `parity-report.json` stay
under `.codex-build` and must not be committed. The final parity outcome is
retained at `.codex-build/governance-g2-reset-path-parity-20261008-final/parity-report.json`.
The initial diagnostic also matched, but the final run additionally enforces
exact counts (88 native session, 225 approval, 16 slash confirmation and two cache
cases) and removes ambient pytest filtering/plugin overrides. Both profiles run
all 331 cases: 322 passed, nine failed identically, zero skipped or collection
errors. This is case-for-case compatibility, not an all-passing native suite.
The full copied source inventories remain unchanged after execution; native test
and conftest bytes match pinned Git objects.

The final 26-case path run passes on the frozen input contract (82.30 seconds).
All 77 product/provenance regressions pass; the final six portable checks also
pass after exact-count contract tightening. Context, syntax, whitespace and
post-run frozen source/host verification pass, including parity input binding.

Reset Step 4 acceptance requires the criterion
review and explicit user decision; green CI alone is not acceptance. G2 and
production remain unaccepted.
