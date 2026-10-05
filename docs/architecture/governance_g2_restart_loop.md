# G2 Process-Restart Conversation Qualification

## Current Step

G2 work package 3/create Step 4/caller-refinement Step 3, following the approved
no-snapshot profile. This increment adds separate qualification inputs and tests,
not a new Hermes patch. Frozen Patch 31 and all parent input hashes stay unchanged.
No G2 acceptance, production activation, runtime pin, wheel or installer change.

The integration plan defines package 3 as enabling one native transition at a
time only after allowed and denied tests pass. The current create substeps are:

1. Connect owner-bound authority to the explicit native create entry.
2. Commit native SQLite state under bounded projection exclusion.
3. Strictly publish/acknowledge and compose the verified reader/conversation scope.
4. Qualify allowed/denied, version, failure, crash/restart, race and unsafe-path cases.

The first three have scoped source implementations. Step 4 remains unaccepted.
Its approved caller refinement has four ordered substeps: contract definition,
separate implementation overlay, complete caller qualification, then acceptance
review. This test is within the third, not a general resume transition or a jump
to another work package.

## Test Contract

One real process explicitly provisions an isolated fixture, creates/acknowledges
the native session and executes the actual native caller/AIAgent using the real
SDK with synthetic HTTP transport and zero retries. It commits the conversation
and terminates. Only then does a second process reopen those existing records,
register the five native governance gates afresh, configure the exact host owner
and bind a new request/task/executor lease through the existing reader.

The restarted host grants no create/acknowledgement permission. Its identity is
defined by trusted synthetic host authentication, never inferred from SQLite,
session IDs, the projection or command arguments. No previous in-memory lease,
agent, middleware registry, SDK client or prompt cache can survive the process
boundary. Existing native transcripts supply resumed history, not fabricated
test messages. The database, acknowledged receipt, route and projection remain
the same; the restarted allowed conversation adds independently governed messages.

Four cases cover allowed continuation, wrong owner, denied no-snapshot mode and
a stale projection. Denied cases require zero model requests, unchanged native
rows and projection bytes, and no agent construction for owner/projection denial.
A stale/sensitive synthetic snapshot must neither be restored by the cache helper,
sent in the effective model request, overwritten nor emitted in captured output.
Other native metadata readers remain outside this cache claim.

The effective native/Maya inventory digests are frozen in
`governance-g2-restart-loop.json`. The supervisor verifies the complete Patch 31
ancestry; each new worker independently checks both complete effective trees,
the frozen parent marker, test and fixture hashes before native construction.
`verify_governance_g2_restart.py` performs those checks without changing the stage.
Temporary fixture records and generated source exports must not be committed.
Workers establish an isolated Hermes home before native imports. Creation requires
an empty fixture directory; restart requires the matching test-only marker.
The marker is an accidental-use guard, never an identity or authorization source.

## Exclusions And Next Gate

This is a bounded test-only host, not the production setup/launcher process.
Existing-fixture native database reopen does not qualify production schema
initialization, automatic repair or privileged maintenance; those remain G3.
Synthetic host authentication does not qualify Telegram/API/CLI credentials.
No live provider, connector delivery, tools, title/background workers, crash
during inference, power-loss durability or full application startup/shutdown is
qualified by these tests. Socket connection/send guards apply during conversation;
asyncio's native loop self-pipe initialization precedes those guards.

After bounded restart evidence, reconcile complete create-loop evidence against
the Step 3/Step 4 criteria. Do not enable reset/switch/rotation, compose frontends
or rebuild an installer without the corresponding gate and approvals.

## Evidence (2026-10-05)

All four final cases pass, each with a creator process that terminates before a
distinct process is started. Allowed restart loads actual prior assistant/user
history and appends the next governed turn without allocating another native
session. Wrong-owner/projection cases construct no agent; cache-mode denial
originates at the native helper and executes no model request. Denied cases
preserve all native records; every case preserves projection and snapshot bytes.
Each worker verifies the complete reviewed native/Maya inventories independently.

The frozen parent remains `governance-g2-prompt-cache.json`, SHA256
`3eb251230aa8dd8f5e0631c1cc4567ede6bafa4d0c687d430e94a1a52bf52cc0`.
The separate final native test SHA256 is
`e71a64c25aa5b3d9c0cdd541598e58acf6112d55ac7eba090360924e77bfd7a2`.
Native pytest has one existing unknown `cache_dir` warning with its cache plugin
disabled; no cases skip. Six restart/cache provenance and actual Windows-style
checkout controls pass. All 47 required product regressions pass. No original
source overlay, fixture hash, runtime pin, wheel, installer or activation changes.

Next is Step 3/create-loop evidence reconciliation and the Step 4 acceptance
review. This test result does not itself accept the create transition, complete
work package 3 or close G2. Other transition and frontend work remains gated.
