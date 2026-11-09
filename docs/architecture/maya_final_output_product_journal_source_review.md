# Coordinator Journal Candidate Source Review

Approved compile-gated source preparation and inert checks completed
2026-11-09. See `maya_final_output_product_journal_contract.md` for the fixed
path, descriptor, records and I/O contract. No runnable profile or worker
command was added. No native product journal was opened.

`CoordinatorJournalCandidate.cs` owns a single injected create-new handle at
the fixed attempt-relative leaf. It verifies the pinned parent, exact volume
and file identity, retained handle token, ordinary file attributes and the
candidate descriptor before and after I/O. `CoordinatorJournalDescriptor.cs`
uses bounded binary descriptor checks, with the same narrow allow-ACE order
exception as the standalone probe but a different expected principal set.
The original probe parser and binaries were not changed.

The candidate emits only the bound intent and at most one terminal record.
It verifies the previous prefix before appending and requires an exact write,
flush and complete byte-exact readback. Same-length corruption is rejected.
Any ambiguous I/O poisons the writer; no reopen, retry or authority restoration
exists. It supplies neither authorization nor a sink.

276 candidate assertions, 219 prior C# assertions and 108 focused Python tests
passed. The candidate is excluded without `MAYA_FINAL_OUTPUT_INERT_FIXTURE`.
The first prior-fixture build reported unassigned observation-field warnings
as errors; immutable constructor initialization corrected that compile issue,
and both final fixture builds passed. Only fixture entry points ran. Final3,
401 frozen files, 167 original product files and the V2 probe remain unchanged.

This source accepts injected observations and does not implement native
provisioning. Actual token exclusion, ancestor pinning, opened descriptor
round-trip and share mode, flush behavior, independent read-only restart
provenance and live worker seal remain unverified. Do not treat the scratch
probe's different descriptor as evidence for this descriptor. No product/VM
run, package, ACL change or qualification occurred. Final3 remains blocked.

Next: review a native transport and a narrowly scoped token-access validation
plan before wiring in a worker or requesting a product package.
