"""Validate design invariants; this is not native-runtime qualification."""
import json
from pathlib import Path

from prepare_governance_g2_reader import reader_contract, digest

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "docs/architecture/governance-g2-caller-contract.json"
STATES = {
    "committed_pending_projection": ["projection_verified"],
    "projection_verified": ["published_pending_caller"],
    "published_pending_caller": ["caller_acknowledged", "caller_quarantined"],
    "caller_acknowledged": [], "caller_quarantined": [], "published": [],
}
BINDING = {"instance_id", "database", "principal", "classification", "binding_version", "route_slot",
           "route_version", "target_session", "correlation_id", "descriptor_digest",
           "projection_generation", "projection_hash", "thread_id", "task", "deadline"}
INVARIANTS = {"no_dispatch_inside_preparation", "normal_exit_only_acknowledgement",
              "fresh_policy_and_audit_before_ack_commit", "guarded_native_sqlite_compare_and_swap",
              "pending_is_fail_closed", "cleanup_failure_preserves_original_exception",
              "no_legacy_adoption", "no_automatic_repair_or_compensation", "separate_reader_reauthorization"}
CASES = {"successful_exit", "caller_exception", "cancellation", "expiry", "revocation",
         "process_exit_before_ack", "ack_policy_denial", "ack_audit_failure", "ack_sql_failure",
         "unknown_ack_commit", "quarantine_failure", "duplicate_ack", "foreign_receipt",
         "stale_route", "legacy_published", "reader_before_ack", "reader_after_ack"}


def validate(data):
    parent = reader_contract()
    raw = (json.dumps(parent, sort_keys=True, indent=2) + "\n").encode()
    expected_keys = {"schema_version", "contract", "status", "production_qualified", "runtime_enforced",
                     "parent_reader_manifest_sha256", "scope", "acknowledgement_operation",
                     "selectable_states", "blocked_states", "transitions", "required_binding",
                     "invariants", "required_cases"}
    def exact_members(value, expected):
        return isinstance(value, list) and all(isinstance(item, str) for item in value) and len(value) == len(expected) and set(value) == expected
    if (not isinstance(data, dict) or set(data) != expected_keys
            or type(data["schema_version"]) is not int or data["schema_version"] != 1
            or data["contract"] != "project-maya.create-caller-acknowledgement.v1"
            or data["status"] != "design_only" or data["production_qualified"] is not False
            or data["runtime_enforced"] is not False
            or data["parent_reader_manifest_sha256"] != digest(raw)
            or data["scope"] != "host_owned_synchronous_preparation"
            or data["acknowledgement_operation"] != "acknowledge_create"
            or data["selectable_states"] != ["caller_acknowledged"]
            or not exact_members(data["blocked_states"], set(STATES) - {"caller_acknowledged"})
            or data["transitions"] != STATES
            or not exact_members(data["required_binding"], BINDING)
            or not isinstance(data["invariants"], dict) or set(data["invariants"]) != INVARIANTS
            or any(value is not True for value in data["invariants"].values())
            or not exact_members(data["required_cases"], CASES)):
        raise ValueError("g2.caller_design_invalid")
    return data


if __name__ == "__main__":
    validate(json.loads(INPUTS.read_text()))
    print("G2 caller acknowledgement design is consistent; runtime enforcement is not implemented.")
