Governance Validator: design notes & API

Purpose
- The Governance Validator enforces retrieval and context rules before downstream consumption. It is the authoritative policy-enforcement component between retrieval and the Context Builder.
- It provides deterministic validation decisions, produces remediation suggestions, and emits audit records for all enforcement actions.

Responsibilities
- Accept candidate RetrievalResult[] and policy configuration; return the filtered list and an AuditReport describing decisions.
- Provide pluggable policy checks (min_trust, recency, provider allow/deny lists, privacy redaction, content-category blocking, provenance requirements).
- Calculate derived signals (e.g., computed trust_score adjustments) deterministically based on provider and meta.
- Expose an API for "explain" that returns the reason(s) a given chunk was filtered or downgraded.

Policy primitives
- min_trust: float — drop anything below this trust_score
- max_age_days: Optional[int] — drop older entries
- provider_allowlist/denylist: Optional[List[str]] — explicit source controls
- required_provenance_fields: List[str] — e.g., ['source_url', 'file_id'] — chunks without these fields may be downgraded
- privacy_blocking_regexes: List[str] — blocks content matching these patterns
- category_blocklist: List[str] — semantic categories forbidden by policy

Validator pipeline
1. Normalize input (ensure RetrievalResult fields exist and types are canonical)
2. For each retrieval:
   - Compute derived_trust = provider_trust_override(provider) * retrieval.trust_score (if present) else 1.0
   - Apply min_trust: if derived_trust < min_trust => mark as 'filtered' with reason 'low_trust'
   - Apply recency: if created_at older than max_age_days => 'filtered' with reason 'too_old'
   - Apply provider rules: allow/deny checks
   - Apply privacy/semantic checks: run regexes and category detectors
   - If only partial failures (e.g., missing provenance): either downgrade score or mark as 'requires_review' depending on policy
3. Output: (kept: List[RetrievalResult], removed: List[AuditEntry], modified: List[RetrievalResult])

Audit records
- AuditEntry structure:
  - chunk_id: str
  - provider: str
  - action: 'kept' | 'filtered' | 'downgraded' | 'requires_review'
  - reasons: List[str]
  - timestamp: str
  - details: Dict[str,Any]

APIs (Python-like)

class GovernancePolicy(NamedTuple):
    min_trust: float = 0.0
    max_age_days: Optional[int] = None
    provider_allowlist: Optional[List[str]] = None
    provider_denylist: Optional[List[str]] = None
    required_provenance_fields: List[str] = []
    privacy_blocking_regexes: List[str] = []
    category_blocklist: List[str] = []

class GovernanceValidator:
    def __init__(self, policy: GovernancePolicy, provider_trust_overrides: Optional[Dict[str,float]] = None):
        ...

    def validate(self, retrievals: List[RetrievalResult]) -> Tuple[List[RetrievalResult], List[AuditEntry]]:
        """Return (kept_or_modified, audit_entries). Calls are deterministic and idempotent."""

    def explain(self, chunk_id: str) -> AuditEntry:
        """Return the last audit decision for the given chunk_id."""

Trust adjustments and overrides
- The validator accepts a provider_trust_overrides map: provider -> multiplier in [0,1]. This allows system operators to adjust trust per provider without changing stored data.
- Derived trust = clamp(retrieval.trust_score * provider_override, 0, 1)

Redaction and partial release
- For privacy-blocked chunks, two options are supported by policy:
  - full_block: remove from returned set entirely
  - redact: produce a redacted chunk where matched substrings are replaced by '[REDACTED]' and an audit reason is recorded
- Redaction must preserve chunk_id and provenance and clearly mark content as redacted

Integration with ContextBuilder & RetrieverService
- RetrieverService should call GovernanceValidator.validate() before passing retrievals to ContextBuilder.
- GovernanceValidator returns both the filtered/modified retrievals and an audit log that is attached to ContextPackage.audit for downstream tracing.

Testing guidance
- Unit tests: cover each policy primitive (min_trust, recency, provider lists, redaction regex)
- E2E tests: retrieval -> governance.validate -> context_builder.build_context ensures provenance is preserved and audit entries recorded

Observability & metrics
- Expose counters: filtered_by_trust, filtered_by_age, redacted_count, downgraded_count
- Emit structured logs for each validate call: {call_id, query_id, policy_id, kept_count, filtered_count, top_reasons}

Failure & remediation
- Non-deterministic detectors (e.g., category classifier) must be isolated behind a deterministic wrapper (seeded model or fixed thresholds) for test reproducibility. If not available, mark category checks as 'skipped' in the audit.
- If validation fails catastrophically (e.g., invalid timestamps), validator should return an explicit error with a safe default: reject all results and set audit reason 'validation_error'.

Next steps
- Implement GovernanceValidator skeleton at plugins/memory/governance_validator.py with a minimal policy and unit tests under plugins/memory/ingest/tests/test_governance_validator.py.
- Wire RetrieverService.query_vector(...) to call GovernanceValidator.validate() before returning results, and annotate returned RetrievalResult list with audit metadata.

