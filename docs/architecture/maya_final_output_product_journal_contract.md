# Coordinator Journal Adapter Contract

Source and inert tests only, 2026-11-09. No runnable profile, worker command,
native file operation, permission change, package or VM run is authorized.

- Fixed leaf `final-output-journal.v1.jsonl`, directly beneath the verified
  `ProductFiles.Root/<32 lowercase hex attempt>` directory, outside `host`.
  Trusted admission supplies the pinned parent identity and local volume ID.
  The boundary must request exclusive create, no sharing and no inheritance.
  No reopen, lookup fallback, truncation, arbitrary leaf, or recovery writer.
- Candidate creation descriptor `O:BAG:BAD:P(A;;FA;;;BA)(A;;FA;;;SY)S:(ML;;NW;;;ME)`.
  Require Administrators owner/group, protected DACL, exactly two ordinary
  noninheriting allow ACEs for Administrators and SYSTEM with mask `0x001f01ff`,
  and exactly one queried Medium mandatory label with no-write-up and no flags.
  Only the two allow entries may appear in either order. No user/worker/child
  ACE. This is an inert candidate descriptor, not a deployed ACL or proof of
  exclusion under actual tokens.
- The injected opened-handle transport reports retained token, pinned parent,
  volume/file identity, regular local NTFS object, one link, no reparse,
  exclusivity, noninheritance, exact length and raw scoped security descriptor.
  Validate each observation on the same handle before and after I/O. Creation
  returns a new empty handle. Any fault poisons the writer; never retry a
  write, flush or readback. Close only the owned handle; preserve the evidence.
- The coordinator supplies immutable trusted bindings: attempt, channel,
  actor, runtime delivery ID, request/response/output digests, output byte
  length, exact synthetic destination, consent ID, epoch and deadline.
  Emit the exact prior version-1 JSONL fields; only the adapter sets event.
  Allow one intent, then at most one matching `delivery_confirmed` or
  `pre_effect_stop`, each at most 8192 bytes and total at most 16384 bytes.
  Each write requires exact count, flush, and byte-exact same-handle readback
  of the complete prefix. No output text is journaled. This adapter grants no
  authority and has no sink. Epoch and deadline are integer fixture values,
  not operational limits or a change to the original dispatch lease.
- Restart remains read-only and cannot construct a writer from prior bytes.
  Keep the prior evidence-only classifier; no native recovery reader is
  implemented here. A real transport must establish all observations with
  opened handles and be tested separately on actual Windows product tokens.
