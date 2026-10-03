"""Opt-in full-loop denial probe for an isolated, patched Hermes checkout.

Set MAYA_HERMES_CANDIDATE_ROOT to a checkout of the pinned fork with the
candidate patch series applied. This never enables Maya's production gate.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from ipaddress import ip_address
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PINNED_HERMES_COMMIT = "b13e2fd6948a59eeb59fe618914147d97a2ee90a"


def _probe(candidate: Path) -> None:
    sys.path[:0] = [str(candidate), str(ROOT / "src"), str(ROOT)]

    from unittest.mock import Mock, patch

    from hermes_cli import middleware
    from hermes_cli.plugins import PluginContext, PluginManifest, get_plugin_manager
    from run_agent import AIAgent

    from project_maya.audit import LocalJsonlAuditSink
    from project_maya.config import config_from_mapping
    from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
    from project_maya.hermes_plugins.governance import (
        GovernanceBoundaryError,
        MayaGovernancePlugin,
        bind_request_identity,
        require_runtime_contract,
    )
    if Path(middleware.__file__).resolve() != (candidate / "hermes_cli" / "middleware.py").resolve():
        raise AssertionError("Hermes middleware did not load from the candidate checkout")
    if Path(sys.modules["run_agent"].__file__).resolve() != (candidate / "run_agent.py").resolve():
        raise AssertionError("Hermes agent did not load from the candidate checkout")
    if hasattr(middleware, "MAYA_GOVERNANCE_CONTRACT"):
        raise AssertionError("Candidate must not claim the qualified Maya contract")
    try:
        require_runtime_contract(middleware)
    except GovernanceBoundaryError as exc:
        if str(exc) != "governance.hermes_contract_unsupported":
            raise
    else:
        raise AssertionError("Production contract unexpectedly accepted candidate")

    home = Path(os.environ["HERMES_HOME"])
    fixture_spec = spec_from_file_location("_maya_candidate_config", ROOT / "tests" / "test_phase0_contracts.py")
    if fixture_spec is None or fixture_spec.loader is None:
        raise AssertionError("Maya config fixture is unavailable")
    fixture = module_from_spec(fixture_spec)
    fixture_spec.loader.exec_module(fixture)
    data = fixture.valid_config_mapping()
    data["deployment"]["data_dir"] = str(home / "maya-data")
    data["llm"].update(
        mode="local", provider="openai", model="synthetic-model",
        endpoint="http://127.0.0.1:9/v1",
    )
    config = config_from_mapping(data)
    audit_path = home / "maya-data" / "audit.jsonl"
    plugin = MayaGovernancePlugin(
        config, PolicyAuthorizationGateway((PolicyRule("model.output", actor_id="maya-operator"),)),
        LocalJsonlAuditSink(audit_path),
    )

    # Register the real callbacks in Hermes's native registry without calling
    # Maya's guarded production registration path or inventing a contract marker.
    manager = get_plugin_manager()
    ctx = PluginContext(PluginManifest(name="maya-denial-probe"), manager)
    for kind, callback in (
        ("llm_execution", plugin.model_execution),
        ("tool_execution", plugin.tool_execution),
        ("tool_result", plugin.tool_result),
        ("model_output", plugin.model_output),
    ):
        ctx.register_middleware(kind, callback)
        middleware.require_middleware(kind, callback)
    if middleware.validate_mandatory_middleware() is not True:
        raise AssertionError("Mandatory gates did not bind")

    transport = Mock()
    with patch("run_agent.OpenAI", return_value=transport), \
         patch("run_agent.get_tool_definitions", return_value=[]), \
         patch("run_agent.check_toolset_requirements", return_value={}), \
         patch("socket.socket.connect", side_effect=AssertionError("network attempted")) as connect:
        agent = AIAgent(
            api_key="synthetic-only", base_url="http://127.0.0.1:9/v1",
            provider="openai", api_mode="chat_completions", model="synthetic-model",
            quiet_mode=True, skip_context_files=True, skip_memory=True,
            enabled_toolsets=[], max_iterations=1,
            ephemeral_system_prompt="Synthetic test agent.",
        )
        construction_transport_calls = transport.chat.completions.create.call_count
        construction_connect_calls = connect.call_count
        if middleware.validate_mandatory_middleware() is not True:
            raise AssertionError("Agent construction removed mandatory gates")
        try:
            with bind_request_identity("maya-operator", "internal"):
                agent.run_conversation("Synthetic business question")
        except middleware.MandatoryMiddlewareError as exc:
            denial = str(exc)
        else:
            raise AssertionError("Denied request returned a normal conversation result")

    if denial != "mandatory_middleware.callback_failed":
        raise AssertionError(f"Unexpected denial code: {denial}")
    request_transport_calls = transport.chat.completions.create.call_count - construction_transport_calls
    request_connect_calls = connect.call_count - construction_connect_calls
    if request_transport_calls or request_connect_calls:
        raise AssertionError(
            f"Denied request reached transport: sdk={request_transport_calls}, socket={request_connect_calls}"
        )
    records = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
    if not any(r["capability"] == "model.egress" and r["decision"] == "deny"
               and r["reason_code"] == "governance.denied" for r in records):
        raise AssertionError("Model denial was not audited")
    audit_text = audit_path.read_text(encoding="utf-8")
    if "Synthetic business question" in audit_text or "synthetic-only" in audit_text:
        raise AssertionError("Prompt or test credential leaked into audit")
    def is_loopback(call: object) -> bool:
        args = getattr(call, "args", ())
        address = args[0] if args else None
        host = address[0] if isinstance(address, tuple) and address else None
        if host == "localhost":
            return True
        try:
            return ip_address(host).is_loopback
        except (TypeError, ValueError):
            return False

    construction_external_calls = sum(
        not is_loopback(call) for call in connect.call_args_list[:construction_connect_calls]
    )
    print(json.dumps({
        "status": "denied", "transport_calls": 0, "audit_safe": True,
        "construction_transport_calls": construction_transport_calls,
        "construction_socket_calls": construction_connect_calls,
        "construction_external_socket_calls": construction_external_calls,
    }))


def _startup_probe(candidate: Path, wheel: Path) -> None:
    sys.path[:0] = [str(candidate), str(ROOT / "src"), str(ROOT)]
    from unittest.mock import Mock, patch
    from project_maya.config import config_from_mapping
    from project_maya.hermes_plugins.candidate import (
        ACKNOWLEDGEMENT, build_test_only_product, initialize_test_only_home,
    )
    from project_maya.hermes_plugins.governance import GovernanceBoundaryError, require_runtime_contract

    root = Path(os.environ["HERMES_HOME"]) / "isolated-product"
    home = initialize_test_only_home(root, acknowledgement=ACKNOWLEDGEMENT)
    os.environ["HERMES_HOME"] = str(home)
    fixture_spec = spec_from_file_location("_maya_startup_config", ROOT / "tests/test_phase0_contracts.py")
    fixture = module_from_spec(fixture_spec)
    fixture_spec.loader.exec_module(fixture)
    data = fixture.valid_config_mapping()
    data["deployment"]["data_dir"] = str(root)
    data["governance"]["policy_file"] = str(root / "governance/policy.json")
    data["llm"].update(mode="local", provider="openai-compatible", model="synthetic-model",
                        endpoint="http://127.0.0.1:9/v1", credential_ref=None)
    data["runtime"]["enabled_profiles"] = ["maya-core"]
    data["broker"] = {"mode": "disabled"}
    data["metabase"]["enabled"] = False
    for integration in data["integrations"].values():
        integration["enabled"] = False
        integration["credential_mode"] = "customer_owned"
    policy = root / "governance/policy.json"
    policy.parent.mkdir()
    policy.write_text(json.dumps({"allow": [
        {"capability": "runtime.execute", "actor_id": "maya-operator"},
        {"capability": "memory.read", "actor_id": "maya-operator"},
    ]}), encoding="utf-8")
    product = build_test_only_product(
        config_from_mapping(data), wheel_path=wheel,
        acknowledgement=ACKNOWLEDGEMENT, actor_id="maya-operator",
    )
    from hermes_cli import middleware
    from run_agent import AIAgent
    transport = Mock()
    def client(**kwargs):
        if not middleware.validate_mandatory_middleware():
            raise AssertionError("Hermes constructed before mandatory governance binding")
        return transport
    with patch("run_agent.OpenAI", side_effect=client), \
         patch("run_agent.get_tool_definitions", return_value=[]), \
         patch("run_agent.check_toolset_requirements", return_value={}), \
         patch("socket.socket.connect", side_effect=AssertionError("network attempted")) as connect:
        product.start()
        if not product.health().state.value == "healthy":
            raise AssertionError("Candidate lifecycle did not start")
        if product.health().details.get("production_qualified") != "false":
            raise AssertionError("Candidate health omitted qualification warning")
        construction_calls = connect.call_count
        try:
            product.run("Synthetic business question")
        except middleware.MandatoryMiddlewareError as exc:
            denial_code = str(exc)
        else:
            raise AssertionError("Denied request returned success through product facade")
        if connect.call_count != construction_calls or transport.chat.completions.create.call_count:
            raise AssertionError("Denied product request reached transport")
        product.stop()
    records = [json.loads(line) for line in (root / "governance/audit/runtime.jsonl").read_text(encoding="utf-8").splitlines()]
    if not any(r["capability"] == "model.egress" and r["decision"] == "deny"
               and r["reason_code"] == "governance.denied" for r in records):
        safe_records = [{k: r[k] for k in ("capability", "decision", "reason_code")} for r in records]
        raise AssertionError(f"Native model denial not audited: {denial_code}; {safe_records}")
    if not any(r["capability"] == "runtime.execute" and r["decision"] == "allow" for r in records):
        raise AssertionError("Public runtime facade was not exercised")
    if not any(r["capability"] == "memory.read" and r["decision"] == "allow" for r in records):
        raise AssertionError("Governed Maya memory retrieval was not exercised")
    if not (root / "memory/memory.sqlite3").is_file():
        raise AssertionError("Real Maya persistent memory not initialized")
    try:
        require_runtime_contract(middleware)
    except GovernanceBoundaryError:
        pass
    else:
        raise AssertionError("Production guard changed")
    print(json.dumps({"status": "denied", "startup_bound_before_construction": True,
                      "transport_calls": 0, "public_product_lifecycle": True, "production_guard_preserved": True}))


class TestHermesCandidateDenial(unittest.TestCase):
    @unittest.skipUnless(os.environ.get("MAYA_HERMES_CANDIDATE_WHEEL") and os.environ.get("MAYA_HERMES_CANDIDATE_ROOT"), "candidate wheel and extracted runtime not supplied")
    def test_explicit_candidate_product_startup(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temporary:
            env = {k: os.environ[k] for k in ("PATH", "SystemRoot", "WINDIR", "TEMP", "TMP") if k in os.environ}
            env.update(HERMES_HOME=temporary, HOME=temporary, USERPROFILE=temporary,
                       PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
            result = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--startup-probe",
                 os.environ["MAYA_HERMES_CANDIDATE_ROOT"], os.environ["MAYA_HERMES_CANDIDATE_WHEEL"]],
                cwd=temporary, env=env, capture_output=True, text=True, timeout=120,
            )
            self.assertEqual(result.returncode, 0, result.stderr[-4000:] + result.stdout[-2000:])
            self.assertNotIn("Synthetic business question", result.stdout + result.stderr)
            self.assertNotIn("local-test-only", result.stdout + result.stderr)
            outcome = json.loads(result.stdout.splitlines()[-1])
            self.assertEqual(outcome["status"], "denied")
            self.assertEqual(outcome["transport_calls"], 0)
            self.assertTrue(outcome["startup_bound_before_construction"])
            self.assertTrue(outcome["production_guard_preserved"])

    @unittest.skipUnless(os.environ.get("MAYA_HERMES_CANDIDATE_ROOT"), "patched Hermes checkout not supplied")
    def test_full_loop_model_denial(self) -> None:
        candidate = Path(os.environ["MAYA_HERMES_CANDIDATE_ROOT"]).resolve()
        commit = subprocess.run(
            ["git", "-c", f"safe.directory={candidate.as_posix()}", "-C", str(candidate), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        self.assertEqual(commit, PINNED_HERMES_COMMIT)
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temporary:
            safe_env = {
                key: os.environ[key]
                for key in ("PATH", "SystemRoot", "WINDIR", "TEMP", "TMP")
                if key in os.environ
            }
            safe_env.update(
                HERMES_HOME=temporary,
                HOME=temporary,
                USERPROFILE=temporary,
                PYTHONIOENCODING="utf-8",
                PYTHONUTF8="1",
                PYTHONDONTWRITEBYTECODE="1",
            )
            result = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--probe", str(candidate)],
                cwd=temporary, env=safe_env, capture_output=True, text=True,
                timeout=120, check=False,
            )
            self.assertNotIn("Synthetic business question", result.stdout + result.stderr)
            self.assertNotIn("synthetic-only", result.stdout + result.stderr)
            self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-4000:])
            outcome = json.loads(result.stdout.splitlines()[-1])
            self.assertEqual(outcome["status"], "denied")
            self.assertEqual(outcome["transport_calls"], 0)
            self.assertTrue(outcome["audit_safe"])
            self.assertEqual(outcome["construction_transport_calls"], 0)
            self.assertEqual(outcome["construction_external_socket_calls"], 0, outcome)


if __name__ == "__main__" and len(sys.argv) == 3 and sys.argv[1] == "--probe":
    _probe(Path(sys.argv[2]).resolve())
elif __name__ == "__main__" and len(sys.argv) == 4 and sys.argv[1] == "--startup-probe":
    _startup_probe(Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve())
