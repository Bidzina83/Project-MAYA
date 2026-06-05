"""Governance helpers: normalize confidence and provenance fields.

Provides:
- apply_governance_defaults(record): ensures provenance.timestamp, normalizes confidence.
- resolve_conflicts(results): deduplicate by entity_id using governance tie-break rules.

This module reads governance_config.DEFAULT_CONFIDENCE and authority/source mappings.
"""
from datetime import datetime
from typing import Dict, Any, List

from plugins.memory import governance_config


def _now_iso_z():
    # UTC ISO-8601 with Z suffix
    return datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'


def normalize_confidence(val) -> float:
    # handle None
    if val is None:
        return float(governance_config.DEFAULT_CONFIDENCE)
    try:
        v = float(val)
    except Exception:
        return float(governance_config.DEFAULT_CONFIDENCE)
    if v < 0:
        return 0.0
    # Heuristic:
    # - Treat values in [10, 100] as percentages (e.g. 75 -> 0.75) to support commonly provided percentage inputs.
    # - Treat small integers (>1 and <10) as explicit multipliers (e.g. 3 stays 3.0).
    # - Clamp to a reasonable upper bound to avoid runaway boosts from accidental huge inputs.
    MAX_CONFIDENCE = 10.0
    if 10.0 <= v <= 100.0:
        v = v / 100.0
    if v > MAX_CONFIDENCE:
        return float(MAX_CONFIDENCE)
    return v


def _parse_iso_z(ts: str) -> float:
    """Return POSIX seconds for an ISO timestamp. If parse fails, return 0."""
    if not ts:
        return 0.0
    try:
        # accept trailing Z or offset; convert Z -> +00:00 for fromisoformat
        t = ts
        if ts.endswith('Z'):
            t = ts[:-1] + '+00:00'
        else:
            # if ts already contains explicit offset (+/-) after the date, keep it; else assume UTC
            # RFC3339-like check: look for '+' or '-' in the timezone portion
            if ('+' not in ts[10:]) and ('-' not in ts[10:]):
                t = ts + '+00:00'
        dt = datetime.fromisoformat(t)
        return dt.timestamp()
    except Exception:
        return 0.0


def apply_governance_defaults(record: Dict[str, Any]) -> Dict[str, Any]:
    """Mutates and returns the record with normalized governance fields.

    - Ensures record['provenance']['timestamp'] is present and in UTC ISO-8601 Z.
    - Normalizes record['confidence'] according to governance_config.DEFAULT_CONFIDENCE.
    - Populates authority from governance_config when missing.
    """
    if record is None:
        return record
    # provenance
    prov = record.get('provenance')
    if prov is None:
        prov = {}
        record['provenance'] = prov
    # ensure timestamp
    ts = prov.get('timestamp')
    if not ts:
        prov['timestamp'] = _now_iso_z()
    else:
        if ts.endswith('Z'):
            prov['timestamp'] = ts
        else:
            try:
                datetime.fromisoformat(ts)
                prov['timestamp'] = ts
            except Exception:
                prov['timestamp'] = _now_iso_z()
    # confidence
    record['confidence'] = normalize_confidence(record.get('confidence'))
    # authority: if missing, derive from provenance.actor or provenance.source via governance_config
    if record.get('authority') is None:
        prov_actor = record.get('provenance', {}).get('actor')
        prov_source = record.get('provenance', {}).get('source')
        # prefer actor mapping, then source mapping, else global default
        if prov_actor:
            record['authority'] = governance_config.get_authority_for(prov_actor)
        elif prov_source:
            record['authority'] = governance_config.get_authority_for(prov_source)
        else:
            record['authority'] = float(governance_config.GLOBAL_DEFAULT_AUTHORITY)
    return record


def resolve_conflicts(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate results by explicit entity_id using tie-break rules.

    Tie-break ordering (approved):
      1) Higher authority
      2) Higher confidence
      3) Freshness (newer provenance.timestamp)
      4) Source priority (from governance_config: lower index => higher priority)
      5) Deterministic record id (lexicographic)

    Returns a list of winners (one per entity) preserving relative ordering by score
    (after deduplication winners are sorted by score desc as final ordering).
    """
    import hashlib

    groups: Dict[str, List[Dict[str, Any]]] = {}
    others: List[Dict[str, Any]] = []
    for r in results:
        rec = r.get('record', {})
        eid = rec.get('entity_id')
        if eid:
            groups.setdefault(eid, []).append(r)
        else:
            others.append(r)

    winners: List[Dict[str, Any]] = []
    for eid, hits in groups.items():
        # choose winner by tie-break
        def sort_key(hit: Dict[str, Any]):
            rec = hit.get('record', {})
            # authority desc, confidence desc, freshness desc, source priority asc, id asc
            auth = float(rec.get('authority', governance_config.GLOBAL_DEFAULT_AUTHORITY))
            conf = float(rec.get('confidence', governance_config.DEFAULT_CONFIDENCE))
            ts = _parse_iso_z(rec.get('provenance', {}).get('timestamp'))
            src = rec.get('provenance', {}).get('source')
            src_pri = governance_config.get_source_priority_index(src) if src else len(governance_config._source_priority) + 1000
            rid = rec.get('id') or ''
            # negative for desc
            return (-auth, -conf, -ts, src_pri, rid)

        hits_sorted = sorted(hits, key=sort_key)
        winner = hits_sorted[0]
        winners.append(winner)

        # build governance decision metadata for this conflict resolution
        related_ids = [h.get('id') for h in hits]
        winner_rec = winner.get('record', {})
        winner_id = winner.get('id')
        reason_codes = []
        if len(hits_sorted) > 1:
            runner = hits_sorted[1]
            wr = winner.get('record', {})
            rr = runner.get('record', {})
            # compare authority
            wa = float(wr.get('authority', governance_config.GLOBAL_DEFAULT_AUTHORITY))
            ra = float(rr.get('authority', governance_config.GLOBAL_DEFAULT_AUTHORITY))
            if wa != ra:
                reason_codes.append('HIGHER_AUTHORITY')
            else:
                # compare confidence
                wc = float(wr.get('confidence', governance_config.DEFAULT_CONFIDENCE))
                rc = float(rr.get('confidence', governance_config.DEFAULT_CONFIDENCE))
                if wc != rc:
                    reason_codes.append('HIGHER_CONFIDENCE')
                else:
                    # freshness
                    wts = _parse_iso_z(wr.get('provenance', {}).get('timestamp'))
                    rts = _parse_iso_z(rr.get('provenance', {}).get('timestamp'))
                    if wts != rts:
                        reason_codes.append('NEWER_RECORD')
                    else:
                        # source priority
                        wsrc = wr.get('provenance', {}).get('source')
                        rsrc = rr.get('provenance', {}).get('source')
                        wsp = governance_config.get_source_priority_index(wsrc) if wsrc else len(governance_config._source_priority) + 1000
                        rsp = governance_config.get_source_priority_index(rsrc) if rsrc else len(governance_config._source_priority) + 1000
                        if wsp != rsp:
                            reason_codes.append('SOURCE_PRIORITY')
                        else:
                            reason_codes.append('DETERMINISTIC_RECORD_ID')
        else:
            reason_codes.append('NO_CONFLICT')

        # deterministic decision id based on decision_type + entity and related ids
        m = hashlib.sha1()
        key = f"CONFLICT_RESOLUTION|{eid}|{winner_id}|{','.join(sorted([str(x) for x in related_ids]))}"
        m.update(key.encode('utf-8'))
        decision_id = m.hexdigest()
        decision = {
            'decision_id': decision_id,
            'decision_type': 'CONFLICT_RESOLUTION',
            'reason_codes': reason_codes,
            'winning_record_id': winner_id,
            'related_record_ids': related_ids,
        }
        # attach to winner record metadata under a stable top-level key 'governance'
        if 'record' in winner:
            winner['governance'] = decision
        # record decision in in-process collector if enabled
        try:
            if getattr(governance_config, 'ENABLE_AUDIT_COLLECTOR', False):
                from plugins.memory.governance_collector import record_decision
                record_decision(decision)
        except Exception:
            # best-effort: do not fail resolution if collector unavailable
            pass
        # emit to structured governance logger adapter if registered (best-effort)
        try:
            from plugins.memory import governance_logger
            governance_logger.emit_decision(decision)
        except Exception:
            pass

    # combine others (no entity_id) with winners
    combined = others + winners
    # final sort by score desc
    combined.sort(key=lambda h: float(h.get('score', 0.0)), reverse=True)
    return combined
