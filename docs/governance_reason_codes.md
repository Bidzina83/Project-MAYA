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
duplicate | info | Duplicate chunk detected by deduplication
contradictory | warning | Two facts were flagged as contradictory by a provider or analyzer
incomplete_metadata | warning | Missing optional metadata that impairs provenance scoring
provenance_low_quality | warning | Provenance present but scored low (e.g., unknown source)
legal_restriction | error | Content may be restricted due to legal/regulatory constraints
sensitive_personal_data | error | Content contains highly sensitive personal data (PII/PHI)

Notes:
- Codes may be namespaced with additional context, e.g. missing_provenance:field1,field2
  — the validator preserves the colon suffix but maps the root code to the catalog for severity.
- Severity is used by the GovernanceReportV2 annotation to indicate the strongest severity
  applicable to the block (error > warning > info).
