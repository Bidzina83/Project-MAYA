Governance Reason Codes (Catalog)

This document enumerates the canonical governance reason codes used by the
GovernanceValidator and GovernanceReportV2. Each code has a short description
and a severity (info | warning | error).

Format: code | severity | description

low_trust | warning | Derived trust below minimum threshold
too_old | warning | Document age exceeds max_age_days policy
provider_not_allowed | error | Provider not in allowlist
provider_denied | error | Provider explicitly denied
missing_provenance | warning | Required provenance fields missing (fields listed in details)
privacy_block | error | Privacy-sensitive pattern matched in content
category_blocked | warning | Category is blocked by policy
invalid_timestamp | warning | Timestamp could not be parsed
duplicate | info | Duplicate chunk detected by deduplication step

Notes:
- Codes may be namespaced with additional context, e.g. missing_provenance:field1,field2
  — the validator preserves the colon suffix but maps the root code to the catalog for severity.
- Severity is used by the GovernanceReportV2 annotation to indicate the strongest severity
  applicable to the block (error > warning > info).
