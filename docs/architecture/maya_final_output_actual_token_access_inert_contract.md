# Actual-Token Access Inert Contract

Approved source and inert checks, 2026-11-10. No native open or process launch.
The entire fixture path requires `MAYA_JOURNAL_TOKEN_ACCESS_FIXTURE`.

Fixed ordered case/mask pairs: `read_data` 1, `write_data` 2, `append_data` 4,
`delete` 65536, `write_dacl` 262144, `write_owner` 524288, `delete_child` 64,
`add_file` 2. The last two are directory rights. Requests use OPEN_EXISTING
(3), share read/write/delete (7), leaf no-follow (0x00200000), and the directory
handle flag (0x02000000) only for directory cases. No privilege changes or
backup intent beyond the flag needed to open directory handles. No generic masks.

Fixed attempt-relative targets: `final-output-journal.v1.jsonl` for leaf cases
and the attempt directory itself for parent cases. Fixed controls:
`host/journal-access-control/control.bin` and its parent for `worker`;
`state/journal-access-control/control.bin` and its parent for `child`.
These are proposed synthetic-only inventory additions, not deployed files or
grants. Legacy inventory is unchanged. If existing access cannot support a
same-mask control, report incomplete; do not create permissions to force a pass.

Prospective command exact keys: `v`, `type`, `attempt`, `role`, `request_id`;
v1 type `journal_access_probe`. No path, mask or free-form target in a command.
Reply exact keys: `v`, `type`, `attempt`, `role`, `pid`, `request_id`, `rows`;
v1 type `journal_access_result`. Exact row keys: `case`, `mask`, `control`,
`target`. Status keys: `opened`, `closed`, `error`, `identity`. Success has
error 0 and an opened 24-hex volume/file identity; `closed` is recorded
independently. Failure has error 1..65535, closed false and null identity.
Raw reply limit is 8192 bytes. Match exact roles, original process/pipe tokens,
PID, attempt, request ID, ordered complete matrix, verified actual token,
writer closed, target identity verified before/after, EOF and natural exit
before cleanup. The last checks are trusted fixture inputs, not wire assertions.

Admit a denial only when the matching control opened and closed the exact
expected object and the target returned access denied (5). A valid report of
any forbidden open fails the case, including a failed close or unexpected
opened identity. Other cases remain incomplete; malformed or unbound evidence
is rejected. An admitted denial is not a qualification. No replay of a reply
or probe session; no native adapter, launcher, ACL change, package or VM run.
