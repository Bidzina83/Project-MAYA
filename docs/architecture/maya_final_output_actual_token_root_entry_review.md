# Fixed Role Entries And Private Challenge Review

Review only, 2026-11-10. No root entry, launcher selector, payload, profile,
permission or execution change. Final3 remains blocked.

## Fixed Entry Identity

Prepare two tiny root entries, `journal_access_worker_entry.py` and
`journal_access_child_entry.py`, each passing a literal role to common code in
`journal_access_role.py`. The future launch path selects the file itself, not a
role or module supplied by a user, command or environment variable. Require
Windows, bundled Python 3.13.14, isolated/no-site/no-bytecode flags and exactly
one 32-lowercase-hex attempt argument. Use the sealed runtime root as the
module origin; no fallback to a module from the current directory, ambient
Python path or an alternate interpreter. Keep wrappers absent from older
payload profiles. Launch and payload provenance remain coordinator obligations.

Derive the attempt directory lexically from the fixed runtime entry path.
Require its attempt name to match the argument and its runtime leaf to be
`runtime`. Verify the role's working directory matches `host` or `state`
under that attempt. Obtain the process's own PID. Do not resolve the protected
journal by path or require metadata access to it in bootstrap. The coordinator
will independently verify the actual extracted entry, directories and objects.
Preflight failure must produce no probe open, success frame or raw traceback.

## One Challenge, One Reply

Use the existing `PrivateChannel` framing on the original inherited stdin and
stdout handles. The coordinator already owns the fresh request ID and retains
the exact process and pipe pair. It sends one v2 challenge, then closes its
write end of role stdin before awaiting a reply. There is no separate ready
frame or second command. Use existing bounded channel/write/read/EOF/exit
controls. Do not increase a deadline or resume a role again on timeout.

The role first reads one bounded frame, validates exact keys, v2/type, the
literal role and the local attempt, and validates the 32-hex challenge ID.
That ID is a correlation value, not authority. Bind it from the first valid
message on the pre-established private pipe, never from a command-line or
environment value. Require input EOF after the frame and before opening any
object; any trailing byte rejects the entire command. The coordinator must
close stdin for this handshake, so a missing close is a blocked protocol
failure, not permission to start the matrix early. No bootstrap opens the
Windows backend until these checks pass.

Execute the one-use `ProbeSession` with local attempt, fixed role and local
PID, echo the validated challenge in exactly one reply, flush and exit. Exit
zero means protocol completion, not an access-test pass. In particular, an
opened target with failed identity or close still appears as a forbidden-open
observation. Do not erase it or repeat the open. The coordinator still needs
exact reply admission, no extra stdout frame or unexpected stderr, clean EOF
and natural exit on the retained process handle. If lifecycle verification
fails after a bound forbidden-open frame, preserve that observation as
provisional and block the run. No negative or success is inferred from exit
status alone. No journal handle is inherited or transferred.

## Source And Test Gate

Recommend **root wrapper and shared handshake source, with inert tests only**.
Keep Windows calls injected and execute wrappers only with a fake bootstrap or
as inert source/AST checks, not as native role entry points. Exercise invalid
version/flags/arguments/role/CWD, malformed/extra/partial frame, missing EOF or
second command, fresh request binding, one flush/reply, short write, and native
backend not constructed before preflight and EOF. Compare success and forbidden
open frames with the C# v2 admission fixture. Do not add `ProductFiles` entries,
launcher selectors, runnable profile, or assembly in this step.

A later launcher source review must freeze the exact compile symbols,
three-member root admission, role control inventory and provisioning/cleanup
ordering. Assembly and one exact guest run are still separate approvals. No
actual token outcome, containment or M08 success follows from this review.
