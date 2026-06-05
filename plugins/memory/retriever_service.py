from __future__ import annotations
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
import math

from plugins.memory.retriever_api import Retriever, RetrievalResult, RetrieverError, ProviderInfo
from plugins.memory.governance_validator import GovernanceValidator, GovernanceReport, GovernanceReportV2
from plugins.memory.context_builder import build_context
from plugins.memory.governance_audit import persist_report


class RetrieverService:
    """Service abstraction that routes to registered Retriever providers,
    applies governance (min_trust, temporal decay), normalizes results, and
    supports simple fallback behavior.

    Usage:
      svc = RetrieverService(primary_local='local')
      svc.register_provider('local', adapter)

      results = svc.query_vector([...])

    Governance rules applied here (configurable at init):
    - min_trust: drop results with trust_score < min_trust
    - temporal_decay_half_life: days; 0 disables decay
    - score normalization: ensures score in [0,1]
    """

    def __init__(
        self,
        primary_local: str = "local",
        fallback: Optional[List[str]] = None,
        min_trust: float = 0.0,
        temporal_decay_half_life_days: int = 0,
        governance_validator: Optional[GovernanceValidator] = None,
        token_budget: int = 2048,
    ) -> None:
        self.providers: Dict[str, Retriever] = {}
        self.provider_info: Dict[str, ProviderInfo] = {}
        self.primary_local = primary_local
        self.fallback = fallback or []
        self.min_trust = float(min_trust)
        self.half_life = int(temporal_decay_half_life_days)
        # simple metrics
        self.metrics: Dict[str, int] = {"queries": 0, "fallbacks": 0, "upserts": 0}
        # governance validator (passive). If provided, query operations will generate a GovernanceReport
        self.governance_validator = governance_validator
        # store last governance report for callers that want to inspect it
        self.last_governance_report: Optional[GovernanceReport] = None
        # store last OperationalContext produced by ContextBuilder
        self.last_operational_context: Optional[Dict[str, Any]] = None
        # token budget for context building
        self.token_budget = int(token_budget)
        # path to last persisted governance audit (if any)
        self.last_persisted_report_path: Optional[str] = None

    def register_provider(self, name: str, provider: Retriever, info: Optional[ProviderInfo] = None) -> None:
        self.providers[name] = provider
        self.provider_info[name] = info or ProviderInfo(name=name, read=True, write=True, capabilities=[])

    def upsert(self, doc: Dict[str, Any], dual_write: bool = False, providers: Optional[List[str]] = None) -> None:
        """Upsert document to write-enabled providers. By default writes only to primary_local,
        unless dual_write=True in which case writes to all write-enabled providers or a provided list.
        """
        targets = []
        if providers:
            targets = [p for p in providers if p in self.providers]
        elif dual_write:
            targets = [n for n, i in self.provider_info.items() if i.write and n in self.providers]
        else:
            if self.primary_local in self.providers:
                targets = [self.primary_local]
            else:
                targets = list(self.providers.keys())[:1]

        for name in targets:
            try:
                self.providers[name].upsert(doc)
                self.metrics["upserts"] += 1
            except Exception as e:
                # swallow provider errors but log metric (higher-level code can inspect metrics)
                self.metrics.setdefault(f"upsert_err_{name}", 0)
                self.metrics[f"upsert_err_{name}"] += 1

    def bulk_upsert(self, docs: List[Dict[str, Any]], dual_write: bool = False) -> None:
        for d in docs:
            self.upsert(d, dual_write=dual_write)

    def get(self, id: str, provider: Optional[str] = None) -> Optional[RetrievalResult]:
        target = provider or self.primary_local
        p = self.providers.get(target)
        if not p:
            return None
        try:
            r = p.get(id)
            if not r:
                # still build empty context for callers
                self.last_operational_context = build_context([], token_budget=self.token_budget)
                return None
            normalized = self._apply_governance_and_normalize(r, provider_name=target)
            # passive governance check
            if self.governance_validator:
                report = self.governance_validator.validate([normalized])
                self.last_governance_report = report
                # build an operational context from the normalized results including governance
                v2 = self.governance_validator.last_report_v2()
                gov = v2.to_dict() if v2 else None
                # persist v2 report if present
                if v2 is not None:
                    try:
                        path = persist_report(v2)
                        self.last_persisted_report_path = path
                    except Exception:
                        # do not fail callers if audit persistence fails; just skip
                        pass
                self.last_operational_context = build_context([normalized], token_budget=self.token_budget, governance=gov)
            else:
                # always update last_operational_context for callers even if no governance
                self.last_operational_context = build_context([normalized], token_budget=self.token_budget)
            return normalized
        except RetrieverError:
            return None

    def query_vector(self, vector: List[float], top_k: int = 10, provider: Optional[str] = None) -> List[RetrievalResult]:
        self.metrics["queries"] += 1
        tried = []
        provider_order = [provider] if provider else [self.primary_local] + self.fallback
        for p_name in provider_order:
            if not p_name:
                continue
            p = self.providers.get(p_name)
            if not p:
                continue
            try:
                raw = p.query_vector(vector, top_k=top_k)
                # normalize and govern
                results = [self._apply_governance_and_normalize(r, provider_name=p_name) for r in raw]
                results = [r for r in results if r and (r.get("trust_score", 1.0) >= self.min_trust)]
                if results:
                    # passive governance check: produce a report but do not alter results
                    if self.governance_validator:
                        report = self.governance_validator.validate(results)
                        self.last_governance_report = report
                        v2 = self.governance_validator.last_report_v2()
                        gov = v2.to_dict() if v2 else None
                        # persist v2 report if present
                        if v2 is not None:
                            try:
                                path = persist_report(v2)
                                self.last_persisted_report_path = path
                            except Exception:
                                pass
                        # build operational context including governance annotations
                        self.last_operational_context = build_context(results, token_budget=self.token_budget, governance=gov)
                    else:
                        # always build an operational context for callers
                        self.last_operational_context = build_context(results, token_budget=self.token_budget)
                    return results
                tried.append(p_name)
            except RetrieverError:
                self.metrics["fallbacks"] += 1
                tried.append(p_name)
                continue
        # If we get here, no provider returned results; return empty
        # still run a governance report (empty)
        if self.governance_validator:
            report = self.governance_validator.validate([])
            self.last_governance_report = report
            v2 = self.governance_validator.last_report_v2()
            if v2 is not None:
                try:
                    path = persist_report(v2)
                    self.last_persisted_report_path = path
                except Exception:
                    pass
        # update last_operational_context to empty
        self.last_operational_context = build_context([], token_budget=self.token_budget)
        return []

    def search(self, query: str, category: Optional[str] = None, limit: int = 10, provider: Optional[str] = None) -> List[RetrievalResult]:
        provider_order = [provider] if provider else [self.primary_local] + self.fallback
        for p_name in provider_order:
            p = self.providers.get(p_name)
            if not p:
                continue
            try:
                raw = p.search(query, category=category, limit=limit)
                results = [self._apply_governance_and_normalize(r, provider_name=p_name) for r in raw]
                results = [r for r in results if r and (r.get("trust_score", 1.0) >= self.min_trust)]
                if results:
                    if self.governance_validator:
                        report = self.governance_validator.validate(results)
                        self.last_governance_report = report
                        v2 = self.governance_validator.last_report_v2()
                        gov = v2.to_dict() if v2 else None
                        # persist v2 report if present
                        if v2 is not None:
                            try:
                                path = persist_report(v2)
                                self.last_persisted_report_path = path
                            except Exception:
                                pass
                        self.last_operational_context = build_context(results, token_budget=self.token_budget, governance=gov)
                    else:
                        self.last_operational_context = build_context(results, token_budget=self.token_budget)
                    return results
            except RetrieverError:
                self.metrics["fallbacks"] += 1
                continue
        if self.governance_validator:
            report = self.governance_validator.validate([])
            self.last_governance_report = report
            v2 = self.governance_validator.last_report_v2()
            if v2 is not None:
                try:
                    path = persist_report(v2)
                    self.last_persisted_report_path = path
                except Exception:
                    pass
        self.last_operational_context = build_context([], token_budget=self.token_budget)
        return []

    def normalize_score(self, score: Optional[float]) -> float:
        if score is None:
            return 0.0
        try:
            s = float(score)
            if s < 0.0:
                s = 0.0
            if s > 1.0:
                s = 1.0
            return s
        except Exception:
            return 0.0

    def _apply_governance_and_normalize(self, raw: RetrievalResult, provider_name: str) -> RetrievalResult:
        # Ensure provider field (service-level canonical provider name)
        raw["provider"] = provider_name
        # Ensure trust_score
        trust = raw.get("trust_score")
        if trust is None:
            trust = 1.0
            raw["trust_score"] = trust
        # Score normalization
        score = raw.get("score")
        if score is None:
            # fall back to similarity if present
            sim = raw.get("similarity")
            if sim is not None:
                score = sim
            else:
                score = 0.0
        score = float(score)
        score = self.normalize_score(score)
        # Apply temporal decay
        if self.half_life and (raw.get("updated_at") or raw.get("created_at")):
            ts = raw.get("updated_at") or raw.get("created_at")
            try:
                t = datetime.fromisoformat(ts.replace("Z", "+00:00")) if isinstance(ts, str) else ts
                age_days = (datetime.now(timezone.utc) - t).total_seconds() / 86400.0
                if age_days > 0:
                    decay = math.pow(0.5, age_days / self.half_life)
                    score *= decay
            except Exception:
                pass
        # Multiply by trust
        score *= float(trust)
        raw["score"] = self.normalize_score(score)
        return raw

    def stats(self) -> Dict[str, Any]:
        return dict(self.metrics)


__all__ = ["RetrieverService"]