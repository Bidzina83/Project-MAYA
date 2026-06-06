# Normalized Vector Schema and Lifecycle

Schema fields (first-class columns on entries table):
- normalized_vector (TEXT)
  - JSON-encoded array of floats representing the L2-normalized vector (or other algorithm output).
- normalized_vector_dim (INTEGER)
  - Dimensionality of normalized_vector (redundant but convenient).
- normalized_vector_algo (TEXT)
  - Algorithm name, e.g. "l2-v1".
- normalized_at (TEXT)
  - ISO timestamp when normalization was computed.
- normalized_version (INTEGER)
  - Version number to indicate algorithm semantics; bump when algorithm changes.

Lifecycle and rules
- The original embedding column (embedding) is authoritative and must never be overwritten by normalization.
- The backfill script creates normalized_* columns if missing and writes normalized_vector only when absent or when algo/version mismatch is detected.
- Retrieval prefers normalized_vector when present and matching desired algo/version. If absent, retrieval computes normalization from embedding at query-time.
- When algorithm or version changes (normalized_vector_algo or normalized_version), re-run backfill with the new algorithm and increment normalized_version; do not overwrite unless version differs.

Operator guidance
- Always run backfill with --dry-run first to estimate updates.
- Keep backups prior to any non-dry-run backfill.
- Document any algorithm upgrades and the corresponding normalized_version used in backfills.
