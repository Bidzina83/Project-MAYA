"""Bounded observations of values already evaluated by the original guard."""
import math

UNSAMPLED = object()
PHASES = frozenset(("new", "issued", "admitted", "dispatched", "runtime_prepared",
    "runtime_delivered", "operator_admitted", "operator_prepared", "complete"))


def observe_guard(expected, closed, audit_failed, revoked, phase, sample, deadline,
                  expired, decision, issued):
    flags = (closed, audit_failed, revoked)
    if any(v is not UNSAMPLED and type(v) is not bool for v in flags):
        return None
    clock_called = (closed is False and audit_failed is False and revoked is False
                    and type(phase) is str and phase == expected)
    returned = sample is not UNSAMPLED
    compared = type(expired) is bool
    if decision == "allowed":
        cause = "allowed"
    elif closed is True:
        cause = "closed"
    elif audit_failed is True:
        cause = "audit_failed"
    elif revoked is True:
        cause = "revoked"
    elif phase is not UNSAMPLED and phase != expected:
        cause = "phase_mismatch"
    elif compared and expired:
        cause = "expired"
    elif clock_called:
        cause = "clock_value_exception" if returned else "clock_exception"
    else:
        cause = "state_exception"
    def finite(value):
        return type(value) in (int, float) and math.isfinite(value)
    issue_sampled = finite(issued)
    timing = clock_called and returned and compared and issue_sampled and finite(sample) and finite(deadline)
    elapsed = remaining = None
    if timing:
        elapsed = int((sample-issued)*1000)
        remaining = int((deadline-sample)*1000)
        timing = 0 <= elapsed <= 2147483647 and -2147483647 <= remaining <= 2147483647
        if not timing:
            elapsed = remaining = None
    return dict(expected_phase=expected, phase=None if phase is UNSAMPLED else phase if phase in PHASES else "other",
        closed=None if closed is UNSAMPLED else closed,
        audit_failed=None if audit_failed is UNSAMPLED else audit_failed,
        revoked=None if revoked is UNSAMPLED else revoked, clock_called=clock_called,
        clock_returned=returned, comparison_evaluated=compared,
        at_or_after_deadline=expired if compared else None,
        decision=decision, cause=cause, timing_valid=timing, issue_sampled=issue_sampled,
        elapsed_ms=elapsed, remaining_ms=remaining, ttl_ms=2000)
