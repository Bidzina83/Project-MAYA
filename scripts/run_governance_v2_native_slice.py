"""Run the approved synthetic native slice only through the LPAC/WFP helper."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from project_maya.audit import AuditRecord
from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins.restricted_broker import BrokerIdentity, RestrictedBroker
from project_maya.hermes_plugins.restricted_broker_http import build_test_broker_server
from project_maya.memory.sqlite_vector import LocalSQLiteVectorRetriever

STAGE = ROOT / ".codex-build/governance-v2-lpac-stage"
HELPER = ROOT / ".codex-build/governance-v2-native-tools/GateANative.exe"
SESSION = "maya-gate-a-synthetic-operator"


class HostAudit:
    def __init__(self, path: Path):
        self.path, self.records = path, []

    def write(self, record: AuditRecord) -> None:
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(record.to_json() + "\n")
            stream.flush()
        self.records.append(record)


def verify_artifacts() -> str:
    manifest_bytes = (STAGE / "runtime-manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    if (manifest["pin"] != "b13e2fd6948a59eeb59fe618914147d97a2ee90a"
            or manifest["patches_applied"] is not False):
        raise ValueError("slice.invalid_manifest")
    for item in manifest["files"]:
        path = (STAGE / item["path"]).resolve()
        if (not path.is_relative_to((STAGE / "runtime").resolve())
                or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]):
            raise ValueError("slice.artifact_changed")
    return hashlib.sha256(manifest_bytes).hexdigest()


def fixture_response(body: dict, index: int) -> dict:
    if index == 1:
        output = [{"id": "fc_gate_a", "type": "function_call", "status": "completed",
                   "call_id": "call_gate_a", "name": "maya_document_read",
                   "arguments": '{"document_id":"doc-1"}'}]
    else:
        output = [{"id": "msg_gate_a", "type": "message", "status": "completed",
                   "role": "assistant", "content": [{"type": "output_text",
                   "text": "Approved synthetic sales total is 120 units.", "annotations": []}]}]
    return {"id": f"resp_gate_a_{index}", "object": "response", "created_at": 1,
            "status": "completed", "model": "gpt-6-luna", "output": output,
            "usage": {"input_tokens": 20, "output_tokens": 10, "total_tokens": 30,
                      "input_tokens_details": {"cached_tokens": 0},
                      "output_tokens_details": {"reasoning_tokens": 0}},
            "error": None, "incomplete_details": None}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=18765)
    args = parser.parse_args()
    digest = verify_artifacts()
    # Before opening the broker or touching synthetic fixtures, require actual
    # native filter verification. Never launch ordinary Python as a fallback.
    checked = subprocess.run([str(HELPER), "verify", str(STAGE), str(args.port)],
                             capture_output=True, text=True, cwd=ROOT, timeout=15)
    if checked.returncode:
        print(json.dumps({"status": "blocked", "reason_code": "slice.enforcement_missing",
                          "production_qualified": False}))
        return 1
    state = STAGE / "state"
    config = state / "config.yaml"
    if not config.exists():
        config.write_text("memory:\n  memory_enabled: true\n  user_profile_enabled: true\n"
                          "  provider: builtin\n", encoding="utf-8")
    host = STAGE / "host"
    document = host / "synthetic-document.txt"
    if not document.exists():
        document.write_text("Approved synthetic sales total is 120 units.\n", encoding="utf-8")
    memory = LocalSQLiteVectorRetriever(host / "smb.sqlite")
    memory.upsert({"id": "smb-1", "content": "Synthetic sales report covers 120 units.",
                   "category": "business", "data_classification": "confidential"})
    audit = HostAudit(host / "audit.jsonl")
    effects = {"document_reads": 0, "memory_reads": 0, "model_requests": 0}
    def read():
        effects["document_reads"] += 1
        return {"document_id": "doc-1", "text": document.read_text(encoding="utf-8"),
                "classification": "confidential"}
    def search(query):
        effects["memory_reads"] += 1
        return memory.search(query, limit=1)
    def model(body):
        effects["model_requests"] += 1
        if effects["model_requests"] > 2:
            raise ValueError("slice.model_budget")
        return fixture_response(body, effects["model_requests"])
    def validate(result):
        data = json.dumps(result, allow_nan=False)
        if "DENIED_DISCLOSURE_MARKER" in data:
            raise ValueError("slice.disclosure_denied")
        return result
    broker = RestrictedBroker(identity=BrokerIdentity("gate-a-operator", "gate-a-request", "confidential"),
        gateway=PolicyAuthorizationGateway(tuple(PolicyRule(capability=c, actor_id="gate-a-operator")
            for c in ("file.read", "memory.search", "model.egress", "model.output"))),
        audit=audit, document_id="doc-1", memory_id="smb-1", read_document=read,
        search_memory=search, model_transport=model, validate_result=validate,
        ttl=180, max_effects=12)
    server = build_test_broker_server(broker, args.port)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        admission = {"token": broker.admission_token, "port": args.port,
                     "session_id": SESSION, "input": "Read the approved sales document and report sales."}
        process = subprocess.run([str(HELPER), "launch", str(STAGE), str(args.port)],
            input=json.dumps(admission) + "\n", text=True, capture_output=True, cwd=ROOT, timeout=100)
        if process.returncode:
            print(json.dumps({"status": "blocked", "reason_code": "slice.native_launch_failed",
                              "native": json.loads(process.stdout), "production_qualified": False}))
            return 1
        native = json.loads(process.stdout)
        exit_code = native.get("exit_code")
        if type(exit_code) is not int or not 0 <= exit_code <= 0xffffffff:
            raise ValueError("slice.invalid_native_exit_code")
        raw_frame = (STAGE / "child-result.json").read_text(encoding="utf-8")
        if not raw_frame.strip():
            print(json.dumps({"status": "blocked", "reason_code": "slice.worker_protocol_missing",
                              "native_exit_code": exit_code, "production_qualified": False}))
            return 1
        frame = json.loads(raw_frame)
        if exit_code != 0 and frame.get("status") == "native_completed":
            raise ValueError("slice.invalid_completion")
        if frame.get("status") != "native_completed":
            safe_stage = frame.get("stage")
            if safe_stage not in {"admission", "native_import", "native_construction", "native_memory", "native_loop"}:
                safe_stage = "unknown"
            print(json.dumps({"status": "blocked", "reason_code": "slice.native_execution_failed",
                              "stage": safe_stage, "production_qualified": False}))
            return 1
        result = broker.deliver(broker.admission_token, frame["result"])
        if effects != {"document_reads": 1, "memory_reads": 1, "model_requests": 2}:
            raise ValueError("slice.unexpected_effects")
        if result.get("final_response") != "Approved synthetic sales total is 120 units.":
            raise ValueError("slice.invalid_final_response")
        print(json.dumps({"status": "native_slice_returned", "effects": effects,
            "runtime_manifest_sha256": digest, "native_origin": frame["origin"],
            "production_qualified": False, "gate_a_accepted": False,
            "remaining": ["A01-A20_denial_and_failure_qualification", "native_memory_resume_checks"]}))
        return 0
    finally:
        broker.revoke()
        server.shutdown()
        server.server_close()
        thread.join(5)
        memory.close()


if __name__ == "__main__":
    raise SystemExit(main())
