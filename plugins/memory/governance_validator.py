from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import re
import json

from plugins.memory.retriever_api import RetrievalResult


# Reason-code catalog (basic): code -> {description, severity}
REASON_CODE_CATALOG: Dict[str, Dict[str, Any]] = {
    "low_trust": {"description": "Derived trust below minimum threshold", "severity": "warning"},
    "too_old": {"description": "Document age exceeds max_age_days policy", "severity": "warning"},
    "provider_not_allowed": {"description": "Provider not in allowlist", "severity": "error"},
    "provider_denied": {"description": "Provider explicitly denied", "severity": "error"},
    "missing_provenance": {"description": "Required provenance fields missing", "severity": "warning"},
    "privacy_block": {"description": "Privacy-sensitive pattern matched", "severity": "error"},
    "category_blocked": {"description": "Category is blocked by policy", "severity": "warning"},
    "invalid_timestamp": {"description": "Timestamp could not be parsed", "severity": "warning"},
    "duplicate": {"description": "Duplicate chunk detected by deduplication", "severity": "info"},
    "missing_provenance:fields": {"description": "Specific provenance fields missing (comma-separated)", "severity": "warning"},
}


@dataclass
class GovernancePolicy:
    min_trust: float = 0.0
    max_age_days: Optional[int] = None
    provider_allowlist: Optional[List[str]] = None
    provider_denylist: Optional[List[str]] = None
    required_provenance_fields: List[str] = field(default_factory=list)
    privacy_blocking_regexes: List[str] = field(default_factory=list)
    category_blocklist: List[str] = field(default_factory=list)


# V1 dataclasses retained for compatibility
@dataclass
class AuditEntry:
    chunk_id: str
    provider: str
    action: str  # 'kept' | 'warning'
    reasons: List[str]
    timestamp: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GovernanceReport:
    total: int
    warnings: List[AuditEntry] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "warnings": [w.to_dict() for w in self.warnings],
            "summary": dict(self.summary),
            "generated_at": self.generated_at,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


# V2 dataclasses: structured annotations and summary
@dataclass
class BlockAnnotation:
    chunk_id: str
    provider: str
    action: str  # 'kept' | 'warning'
    reasons: List[str]
    severity: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GovernanceReportV2:
    version: str = "v2"
    total: int = 0
    annotations: List[BlockAnnotation] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "total": self.total,
            "annotations": [a.to_dict() for a in self.annotations],
            "summary": dict(self.summary),
            "generated_at": self.generated_at,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class GovernanceValidator:
    """Passive Governance Validator.

    Versioning:
      - validate(...) still returns the legacy GovernanceReport (for compatibility)
      - A structured GovernanceReportV2 is also produced and stored at self._last_report_v2

    Behavior:
      - Inspects RetrievalResult[]
      - Generates reason codes using REASON_CODE_CATALOG
      - Produces both legacy GovernanceReport and GovernanceReportV2 (v2 is preferred going forward)

    Does NOT filter, modify, or reject records. Callers should use the reports for decision-making.
    """

    def __init__(self, policy: Optional[GovernancePolicy] = None, provider_trust_overrides: Optional[Dict[str, float]] = None):
        self.policy = policy or GovernancePolicy()
        self.provider_trust_overrides = provider_trust_overrides or {}
        # store last reports for explain()/inspection
        self._last_report: Optional[GovernanceReport] = None
        self._last_report_v2: Optional[GovernanceReportV2] = None
        # precompile privacy regexes
        self._privacy_patterns = [re.compile(p) for p in (self.policy.privacy_blocking_regexes or [])]

    def validate(self, retrievals: List[RetrievalResult]) -> GovernanceReport:
        """Legacy validate: returns GovernanceReport (keeps old behavior), but also produces V2 report.

        The V2 report is stored at self._last_report_v2 and includes structured per-block annotations
        with severity levels resolved from the REASON_CODE_CATALOG.
        """
        warnings: List[AuditEntry] = []
        summary_counters: Dict[str, int] = {}
        now = datetime.now(timezone.utc)

        annotations: List[BlockAnnotation] = []

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
                # encode as a namespaced reason so catalog lookups can be approximate
                reasons.append("missing_provenance:" + ",".join(missing))
                details.setdefault("missing_provenance", missing)

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

            # finalize legacy warnings / summary
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

            # Build V2 annotation for this block: derive severity by taking the max severity among reason codes
            severity = "info"
            for rc in reasons:
                # normalize reason key (split missing_provenance:fields to root)
                rc_root = rc.split(":", 1)[0]
                meta = REASON_CODE_CATALOG.get(rc_root)
                if meta:
                    sev = meta.get("severity", "info")
                    if sev == "error":
                        severity = "error"
                        break
                    if sev == "warning" and severity != "error":
                        severity = "warning"
            ba = BlockAnnotation(chunk_id=chunk_id, provider=provider, action=("warning" if reasons else "kept"), reasons=reasons, severity=severity, details=details)
            annotations.append(ba)

        # assemble reports
        legacy_report = GovernanceReport(total=len(retrievals), warnings=warnings, summary=summary_counters, generated_at=now.isoformat())
        v2_report = GovernanceReportV2(version="v2", total=len(retrievals), annotations=annotations, summary=summary_counters, generated_at=now.isoformat())

        self._last_report = legacy_report
        self._last_report_v2 = v2_report
        return legacy_report

    def explain(self, chunk_id: str) -> Optional[AuditEntry]:
        if not self._last_report:
            return None
        for w in self._last_report.warnings:
            if w.chunk_id == chunk_id:
                return w
        return None

    def last_report_v2(self) -> Optional[GovernanceReportV2]:
        return self._last_report_v2


__all__ = ["GovernanceValidator", "GovernancePolicy", "GovernanceReport", "AuditEntry", "GovernanceReportV2", "REASON_CODE_CATALOG"]