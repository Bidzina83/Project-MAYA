# Journal Access Profile Source Review

The approved source-only candidate is `0.2.2-journal-access.1` (file version
`0.2.2.1`), scope `offline-journal-access-matrix-v1`. It compiles with
`HERMES_JOURNAL_ACCESS,HERMES_BRIDGE,HERMES_CONSTRUCTION,HERMES_IMPORT`.
The last three flags provide the existing private worker and child launch
topology, not a Hermes conversation or model bridge. Known incompatible
model, state, memory and fixture symbols are rejected at compilation.

- `ProductFiles` accepts and requires the three exact journal role roots only
  in the access profile. Existing extraction checks still bind contents to the
  embedded index. No new index or payload was assembled.
- `ProtectedPython`, `WindowsIsolation` and `WindowsBridgeProcess` select the
  access coordinator and fixed Python role entries. The coordinator creates
  only the two approved control files and journal, then closes its writer
  before either role resumes. Existing worker and AppContainer token checks,
  handle allowlists, job limits, grants and WFP settings are unchanged.
- The coordinator probes the worker first, withholds the child probe after a
  forbidden open, and checks each admitted reply against the retained process,
  pipe, challenge and role. It requires input closure, output EOF and natural
  zero exit. The coordinator independently checks control and journal
  identities, descriptors and bytes before and after the role exchanges.
  A forbidden observation with incomplete lifecycle evidence stays
  provisional, never a denial.
- Only both complete denied matrices, journal readback and successful product
  cleanup can yield `access_matrix_denied_pending_independent_cleanup`.
  Incomplete and forbidden outcomes stay blocked, with the existing
  cleanup-pending status taking precedence if cleanup fails. The source
  does not enable the fixture role runners, scratch constructor or fake sink.

Verification: exact launcher compilation without execution; 83 access-profile
and 8 assertions each in the document bridge and Final3 profiles; 25 rejected
compile configurations; source check for stop-before-revocation order.
The existing injected coordinator journal (833 assertions) and native v2 token
matrix (692 assertions) checks passed, as did 47 inert Python role tests and
20 framed Python/C# v2 parity vectors (61 assertions). Final3 ZIP and EXE
and all 401 frozen source entries rehashed successfully. The only changed
working-tree product paths from the Final3 manifest are the four launcher
and index files named above; the journal-specific sources are outside that
manifest.

No package assembly, product/native/bundled-runtime/VM execution, actual
worker or child opens, inference, publication, retry, or qualification
occurred. Native control inheritance, exact OS access outcomes and
post-run independent cleanup remain unverified. M08 remains blocked, M09
remains pending, and Gate A stays open. Separate assembly review must
pin the exact payload and dependencies before any separate artifact-specific
one-run approval and fresh consent.
