from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import re

from plugins.memory.retriever_api import RetrievalResult


@dataclass
class GovernancePolicy:
    min_trust: float = 0.0
    max_age_days: Optional[int] = None
    provider_allowlist: Optional[List[str]] = None
    provider_denylist: Optional[List[str]] = None
    required_provenance_fields: List[str] = field(default_factory=list)
    privacy_blocking_regexes: List[str] = field(default_factory=list)
    category_blocklist: List[str] = field(default_factory=list)


@dataclass
class AuditEntry:
    chunk_id: str
    provider: str
    action: str  # 'kept' | 'warning'
    reasons: List[str]
    timestamp: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GovernanceReport:
    total: int
    warnings: List[AuditEntry] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class GovernanceValidator:
    """Passive Governance Validator (Version 1).

    - Inspects RetrievalResult[]
    - Generates governance warnings with reason codes
    - Produces a GovernanceReport

    Does NOT filter, modify, or reject records. Callers should use the report for decision-making.
    """

    def __init__(self, policy: Optional[GovernancePolicy] = None, provider_trust_overrides: Optional[Dict[str, float]] = None):
        self.policy = policy or GovernancePolicy()
        self.provider_trust_overrides = provider_trust_overrides or {}
        # store last report for explain()
        self._last_report: Optional[GovernanceReport] = None
        # precompile privacy regexes
        self._privacy_patterns = [re.compile(p) for p in (self.policy.privacy_blocking_regexes or [])]

    def validate(self, retrievals: List[RetrievalResult]) -> GovernanceReport:
        warnings: List[AuditEntry] = []
        summary_counters: Dict[str, int] = {}
        now = datetime.now(timezone.utc)

        for r in retrievals:
            chunk_id = r.get("chunk_id") or r.get("id") or ""
            provider = r.get("provider", "unknown")
            reasons: List[str] = []
            details: Dict[str, Any] = {}

            # compute derived trust
            raw_trust = float(r.get("trust_score", 1.0)) if r.get("trust_score") is not None else 1.0
            override = float(self.provider_trust_overrides.get(provider, 1.0))
            derived_trust = max(0.0, min(1.0, raw_trust * override))
            details["derived_trust"] = derived_trust

            if derived_trust < self.policy.min_trust:
                reasons.append("low_trust")

            # age check
            created = r.get("created_at")
            age_days = None
            if created:
                try:
                    t = datetime.fromisoformat(created.replace("Z", "+00:00")) if isinstance(created, str) else created
                    age_days = (now - t).total_seconds() / 86400.0
                    details["age_days"] = age_days
                    if self.policy.max_age_days is not None and age_days > float(self.policy.max_age_days):
                        reasons.append("too_old")
                except Exception:
                    # non-fatal: note parse error
                    reasons.append("invalid_timestamp")

            # provider allow/deny
            if self.policy.provider_allowlist is not None and provider not in self.policy.provider_allowlist:
                reasons.append("provider_not_allowed")
            if self.policy.provider_denylist and provider in self.policy.provider_denylist:
                reasons.append("provider_denied")

            # required provenance
            missing = []
            for f in (self.policy.required_provenance_fields or []):
                if not r.get("meta") or f not in r.get("meta", {}):
                    missing.append(f)
            if missing:
                reasons.append("missing_provenance:" + ",".join(missing))

            # privacy regexes
            content = r.get("content", "") or ""
            for pat in self._privacy_patterns:
                if pat.search(content):
                    reasons.append("privacy_block")
                    details.setdefault("privacy_matches", []).append(pat.pattern)

            # category blocklist (note: category detection not implemented; relies on r.get('meta.category'))
            cat = None
            if r.get("meta"):
                cat = r.get("meta", {}).get("category")
            if cat and cat in (self.policy.category_blocklist or []):
                reasons.append("category_blocked")
                details["category"] = cat

            # finalize
            if reasons:
                ae = AuditEntry(
                    chunk_id=chunk_id,
                    provider=provider,
                    action="warning",
                    reasons=reasons,
                    timestamp=now.isoformat(),
                    details=details,
                )
                warnings.append(ae)
                for rcode in reasons:
                    summary_counters[rcode] = summary_counters.get(rcode, 0) + 1
            else:
                summary_counters["kept"] = summary_counters.get("kept", 0) + 1

        report = GovernanceReport(total=len(retrievals), warnings=warnings, summary=summary_counters, generated_at=now.isoformat())
        self._last_report = report
        return report

    def explain(self, chunk_id: str) -> Optional[AuditEntry]:
        if not self._last_report:
            return None
        for w in self._last_report.warnings:
            if w.chunk_id == chunk_id:
                return w
        return None


__all__ = ["GovernanceValidator", "GovernancePolicy", "GovernanceReport", "AuditEntry"]
