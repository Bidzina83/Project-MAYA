# Protected Hermes Native Memory 1 Proposal

## Subsequent Preparation Approval

The user subsequently approved implementation, inert verification and separate
Native Memory 1 package preparation. See maya_protected_hermes_memory_handoff.md.
This supersedes the proposal-only status below for preparation, not execution.
Native Hermes configuration/bootstrap can create an empty memories directory;
freshness is therefore checked before Hermes imports, followed by rejection of
any preexisting memory content before construction. No new permission, runtime
patch, dependency, VM run or qualification is approved by preparation.

## Status And Purpose

2026-10-22: the user approved preparation of this proposal, not package
implementation or another VM run. The next test concerns native memory-file
functionality, not repeating the already demonstrated private-storage write
permission or SQLite test. No runtime source, package, native execution or
Windows setting is changed by this document. Preserve all prior frozen inputs.

The question is whether the real agent's MemoryStore can add, replace, remove
and reload synthetic entries in MEMORY.md and USER.md under the existing
AppContainer/WFP restrictions. No model traffic, customer data, external memory
provider, authoritative-state mutation or protected business action is included.

## Completed Session State 1 Evidence

The matching-hash report for 0.1.3-hermes-state.1 identifies launcher SHA256
E508C0CBF0340683593F77FFC75A4F3BD31A1F84C83D0A6152AD11CD933A7524
on Windows 26300.9711. UTC interval 2026-10-22T17:10:47.1823717Z through
17:13:03.9324204Z includes setup/cleanup, not only Python execution.

Python and the real Hermes agent started, native SessionDB used WAL, exactly
one synthetic session and two messages matched before and after read-only
reopen, session ending and both connection closures verified, and the SDK
reported closed. Peak observed DB/sidecar size was 424,176 bytes, below 32 MiB.
Config stayed unchanged, the Hermes model-call counter stayed zero, natural
child exit was 0 and host evidence admission passed. FTS/trigram availability
was reported, not full-search qualification. This establishes same-process
close/reopen persistence, not process restart or crash durability.

The launcher initially remained open after the result; after normal closure,
the operator's read-only checks found no matching host/child/Maya processes.
Further checks found no recursive reparse points and no package-SID ACE among
7,391 entries (zero failures), and confirmed restored Medium state integrity.
The WFP export succeeded with exit 0 and 2,167,941 bytes; complete fragment-aware
XML traversal found none of the six exact filter keys or the attempt sublayer.

These are scoped independent cleanup checks. AppContainer profile removal
remains product-reported only; do not rewrite the original independent-cleanup
flag or claim complete containment. The Session State 1 run allowance is
consumed. No rerun or additional VM command follows this record.

## Pinned Source Findings

Use the same unmodified Hermes commit
b13e2fd6948a59eeb59fe618914147d97a2ee90a and existing dependency set.

| Source/interface | Observed contract and test consequence |
| --- | --- |
| tools/memory_tool.py:get_memory_dir | Resolves get_hermes_home()/memories, not SQLite. Verify it remains within the attempt's private state. |
| MemoryStore.__init__/load_from_disk | Loads two separate live entry lists and captures frozen prompt snapshots. Default limits are 2200/1375 characters. |
| agent/agent_init.py built-in memory setup | Supported memory flags and skip_memory=False create the agent's real MemoryStore. Initialization exceptions can be swallowed, so construction alone is insufficient evidence. |
| MemoryStore.add/replace/remove | Uses content scanning, target-specific lists, char limits, disk reload under lock and save_to_disk after successful mutation. Check success and exact file/readback, not merely a returned dictionary. |
| MemoryStore._file_lock | Uses a separate .md.lock file; Windows uses msvcrt.locking. If neither lock implementation is available upstream can proceed unlocked; the test must reject missing Windows locking support. |
| MemoryStore._write_file | Creates .mem_*.tmp beside the target, writes UTF-8, flushes/fsyncs and calls utils.atomic_replace; cleans its temp on failure where possible. |
| utils.atomic_replace | Resolves symlinks and includes EXDEV/EBUSY copy fallback. Use fresh non-link paths; a successful final readback does not independently prove atomic replacement or which internal branch ran. |
| MemoryStore._read_file | Can return [] for unreadable files. Required nonempty expected records and direct readable-file checks must prevent this degradation from passing as success. |
| MemoryStore._detect_external_drift | May create .bak.<timestamp> and refuse a write on unexpected external formatting/size drift. No external edit or backup-recovery experiment is proposed. |
| format_for_system_prompt | Returns the load-time snapshot, not current live entries. Frozen original snapshots after mutation are expected, not a persistence defect. A fresh store should reflect the final on-disk entries. |
| memory_tool/_apply_write_gate | The tool-facing wrapper has separate approval behavior, including an upstream fail-open import path. Direct store compatibility does not test or qualify that authorization path. Do not disable, patch or rely on it as Maya's enforcement boundary. |

These findings are static inspection, not proof of Windows lock, save or reload
compatibility. Before building, verify the packaged methods, signatures and
dependency identities against this exact source; do not model a guessed API.

## Proposed Bounded Workflow

1. Reuse Maya's consent, setup, verified payload, restricted launch, reporting
   and cleanup. Use a fresh private home with no memories directory, memory
   files, lock/temp/backup files or imported profile. No operator pre-grants.
2. Change only the supported memory-specific configuration/constructor choices:
   skip_memory=False; memory.memory_enabled=True;
   memory.user_profile_enabled=True; memory.provider="";
   memory.memory_char_limit=2200; memory.user_char_limit=1375.
   Keep all other offline settings from Construction 2, including session_db=None.
   This test does not combine SQLite and file-memory qualification.
3. Construct one real AIAgent. Require the actual pinned MemoryStore at
   agent._memory_store, both native enable flags True, external manager None,
   exact limits, correct private paths and no tools. No manually attached fake
   store or substitute reader/writer. Explicitly load through load_from_disk
   where needed to expose constructor-suppressed exceptions. Require the fresh
   lists and initial frozen snapshots to be empty.
4. For each exact target (memory and user), add two fixed benign ASCII entries,
   each no more than 256 characters including the nonce. Labels must state
   synthetic fixture, not describe the real operator or actual preferences.
   Call the native add method and check success, list order and actual saved
   contents after each call. Do not serialize the files in the product checker.
5. Replace the first entry with a distinct fixed synthetic revision through
   native replace, then remove the second through native remove. Require the
   expected success and exact one-entry final list/file for each target.
   This is eight fixed mutations total; no model-generated action loop.
6. Create a fresh instance of the real MemoryStore with the same limits and
   load_from_disk. Require exact final entries for both targets. The original
   agent store's snapshot should remain its empty initial snapshot; the fresh
   instance's formatted snapshot must include only the expected final synthetic
   entries, with no blocked placeholder substituted for the expected content.
   No formatted block is sent to a model or external service.
7. Verify both final files are readable regular non-reparse files within
   state/memories. Compare exact decoded entries using the native delimiter;
   account for normal Windows newline handling rather than assuming LF-only
   raw bytes. Record hashes of observed bytes and confirm reload itself does
   not alter them. No unexpected .mem_*.tmp or .bak.* residue may pass.
8. Retain the two expected lock files. Propose a single nonblocking acquire/
   release check on each exact lock file after native calls to observe that
   this process has not left its lock held. No parallel writer, blocked-lock
   wait, lock suppression or Windows policy change is proposed. This does not
   establish interprocess/concurrent-writer correctness.
9. Shut down context and close the agent as previously qualified; verify the
   SDK method result, detached client and unchanged zero model-call counter.
   The host must confirm job stop before normal security cleanup and admission.
   Preserve synthetic files and bounded reports for inspection, not deletion
   or an unapproved recovery attempt.

This exercises the real store attached by the agent, then a fresh reader object
in the same process. It does not establish a second agent lifecycle, process/OS
restart, crash/power-loss recovery, concurrent access, backups or complete
injection protection. The ordinary benign scanner path runs unchanged; no
malicious promptware, exfiltration or security scanner test corpus is included.

## Path Impact And Bounds

The new disclosed private content is state/memories/MEMORY.md, USER.md,
MEMORY.md.lock and USER.md.lock, transient native .mem_*.tmp files, and a
bounded result report. Native unexpected drift may leave a backup on failure;
report and stop rather than deleting evidence or correcting permissions.
Existing private config/cache/logs/sessions remain. There is no customer profile
import, shared memory directory or copying into Maya's authoritative store.

Preserve native 2200/1375-character limits. Add a proposed aggregate 64 KiB
acceptance ceiling for memory/lock/temp/backup files, checked at bounded stages,
with peak retained. This is not a disk quota or an in-call growth guarantee.
Each operation is fixed and bounded; the checker does not return raw native
memory responses, prompt blocks or arbitrary directory dumps to the operator.

Keep the same public non-secret SDK placeholder and synthetic model/.invalid
endpoint. Tools, external providers, context files, checkpoints, compression,
tool search and environment probing remain disabled. No conversation or model
request is invoked, and all network access including localhost remains denied.

Ordinary AppContainer, zero capabilities, reduced same-user token, one-process
job, child-process policy, three inherited pipes and six WFP denies remain.
All writes occur under existing private-state permissions; no additional ACL,
registry grant, loopback exemption, OS tuning, supervisor, system Python/PATH
change or new dependency is proposed. Existing All Application Packages access
remains an unqualified boundary limitation, not complete customer-data isolation.

Keep 22-second cooperative and 30-second host deadlines, 8192-file/4-MiB payload
inventory limits, 32-MiB per-file/256-MiB expanded bounds, 4096-byte stdout and
65536-byte captured-text/report bounds. Stop on timing/locking failure instead
of increasing deadlines or replacing native locking/atomic-write behavior.

## Evidence And Acceptance

Bind all results to the immutable source/payload/config/fixture identities and
attempt nonce. Record actual native store attachment/flags/limits, paths,
success/readback for all eight operations, fresh-load contents match, expected
snapshot behavior, readable file hashes/sizes, lock/residue observations,
SDK/agent shutdown, natural exit and product security cleanup. Required
nonempty readbacks must not accept a silent empty-read fallback. Missing
locking support or incomplete evidence blocks, not a partial success verdict.

Only a natural exit 0, matching startup beacons, all admitted memory predicates
and reported security cleanup can establish bounded native-memory compatibility.
Independent cleanup checks still follow a separately approved VM run. Keep all
production, containment and independent-cleanup qualification flags False.

This fixed synthetic internal-storage exercise does not authorize arbitrary
tool-mediated memory changes or waive local authorization of customer-data
ingestion, authoritative writes, disclosure, models or business effects. Native
optional approval hooks and scanner checks are not Maya's security boundary.
The separate tool wrapper's fail-open behavior remains unqualified, not repaired
or approved for protected use. Follow restricted_hermes_execution_contract.md.

## Next Decision

Approve preparation of this native-memory-only product package, including the
explicit memory configuration delta, eight fixed mutations, fresh-store reload,
scoped file/lock observations and acceptance ceiling. Preparation would use
source/AST inspection, inert fixtures and offline compilation only. Return
any new permission, dependency or scope requirement for review. After exact
artifact/impact review, obtain separate approval for one RDP VM run with fresh
product consent. No build, VM command, retry, new grant or runtime correction
is authorized by this proposal alone.
