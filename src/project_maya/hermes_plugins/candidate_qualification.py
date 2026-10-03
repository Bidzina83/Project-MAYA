"""Installed-artifact, offline governance qualification; never a production host."""

from __future__ import annotations

import argparse
import io
import json
import os
import threading
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from uuid import uuid4
from unittest.mock import Mock, patch

from ..config import config_from_mapping
from .candidate import ACKNOWLEDGEMENT, build_test_only_product, initialize_test_only_home
from .governance import GovernanceBoundaryError, bind_request_identity, require_runtime_contract


SCENARIOS = ("model-denial", "model-allow", "tool-denial", "tool-allow",
             "compression-denial", "background-denial")


def _configure_native_shell() -> None:
    """Use Hermes's explicit Git Bash override, never the Windows WSL shim."""
    if os.name == "nt":
        custom = os.environ.get("HERMES_GIT_BASH_PATH")
        candidates = [Path(custom)] if custom else [
            Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe",
            Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Git/bin/bash.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Git/bin/bash.exe",
        ]
        for candidate in candidates:
            if candidate.is_file() and "system32" not in {part.lower() for part in candidate.parts}:
                os.environ["HERMES_GIT_BASH_PATH"] = str(candidate.resolve())
                break
        else:
            raise RuntimeError("candidate.native_shell_missing")
    from tools.environments.local import _find_bash
    try:
        _find_bash()
    except Exception:
        raise RuntimeError("candidate.native_shell_missing") from None


def _qualify_persistence_observers(agent) -> dict:
    """Probe installed native helpers; denial precedes real store entry."""
    from hermes_cli import middleware
    from hermes_cli.plugins import PluginContext, PluginManifest, get_plugin_manager
    if agent._get_session_db_for_recall() is None:
        raise RuntimeError("candidate.native_session_db_missing")
    previous = agent._session_messages
    messages = [{"role": "user", "content": "Synthetic persistence question"}]
    denied = 0
    with patch.object(agent, "_save_session_log", wraps=agent._save_session_log) as save, \
         patch.object(agent, "_flush_messages_to_session_db", wraps=agent._flush_messages_to_session_db) as flush, \
         patch.object(agent._session_db, "append_message", wraps=agent._session_db.append_message) as append, \
         patch.object(agent, "save_trajectories", True), \
         patch.object(agent, "_convert_to_trajectory_format", wraps=agent._convert_to_trajectory_format) as convert, \
         bind_request_identity("candidate-denied-operator"):
        for action in (lambda: agent._persist_session(messages, []),
                       lambda: agent._flush_messages_to_session_db(messages, []),
                       lambda: agent._save_trajectory(messages, "Synthetic persistence question", True)):
            try:
                action()
            except middleware.MandatoryMiddlewareError:
                denied += 1
            else:
                raise RuntimeError("candidate.persistence_denial_missing")
        checks = {"native_persistence_denial_propagated": denied == 3,
                  "denied_session_state_preserved": agent._session_messages is previous,
                  "zero_denied_store_calls": save.call_count == 0 and flush.call_count == 1
                                            and append.call_count == 0 and convert.call_count == 0}
    manager = get_plugin_manager()
    context = PluginContext(PluginManifest(name="maya-persistence-observer-probe"), manager)
    observer = Mock()
    for name in ("pre_api_request", "post_api_request", "api_request_error"):
        context.register_hook(name, observer)
        if manager.invoke_hook(name, request="Synthetic observer body") != []:
            raise RuntimeError("candidate.raw_observer_result_invalid")
    checks["raw_api_observers_suppressed"] = observer.call_count == 0
    return checks


def qualify(install_dir: Path, data_root: Path, *, scenario: str = "model-denial") -> dict:
    """Use real installed Maya/Hermes and policy, with inert external transports."""
    if scenario not in SCENARIOS:
        raise ValueError("candidate.scenario_invalid")
    install_dir = install_dir.resolve()
    root = data_root.resolve() / ("run-" + uuid4().hex)
    home = initialize_test_only_home(root, acknowledgement=ACKNOWLEDGEMENT)
    # Isolate the qualification process from inherited customer credentials.
    for name in tuple(os.environ):
        if name.endswith(("API_KEY", "TOKEN", "PASSWORD")) or name in {"MAYA_CONFIG", "MAYA_EMBEDDING_MODEL_DIR"}:
            os.environ.pop(name, None)
    os.environ["HERMES_HOME"] = str(home)
    os.environ["MAYA_DATA_DIR"] = str(root)
    os.environ["HOME"] = str(root)
    os.environ["USERPROFILE"] = str(root)
    os.environ["TERMINAL_ENV"] = "local"
    os.environ["TERMINAL_CWD"] = str(root)
    template = json.loads((install_dir / "config-templates/candidate.json").read_text(encoding="utf-8"))
    template["deployment"]["data_dir"] = str(root)
    template["governance"]["policy_file"] = str(root / "governance/policy.json")
    policy = root / "governance/policy.json"
    policy.parent.mkdir()
    rules = [
        {"capability": "runtime.execute", "actor_id": "candidate-operator"},
        {"capability": "memory.read", "actor_id": "candidate-operator"},
        {"capability": "model.output", "actor_id": "candidate-operator"},
    ]
    if scenario not in {"model-denial", "compression-denial"}:
        rules.extend({"capability": capability, "actor_id": "candidate-operator"}
                     for capability in ("model.egress",))
    documents = root / "documents"
    documents.mkdir(exist_ok=True)
    sentinel = documents / "denied.txt"
    sentinel.write_text("Candidate protected file content", encoding="utf-8")
    approved = documents / "approved.txt"
    approved.write_text("Candidate approved business record", encoding="utf-8")
    if scenario == "tool-allow":
        rules.append({"capability": "file.read", "target": str(approved.resolve()),
                      "operation": "read", "actor_id": "candidate-operator"})
    policy.write_text(json.dumps({"allow": rules}), encoding="utf-8")
    (root / "config.json").write_text(json.dumps(template, indent=2), encoding="utf-8")
    wheels = list((install_dir / "wheels").glob("hermes_agent-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError("candidate.wheel_count_invalid")
    product = build_test_only_product(config_from_mapping(template), wheel_path=wheels[0],
                                      acknowledgement=ACKNOWLEDGEMENT, actor_id="candidate-operator",
                                      iteration_limit=3 if scenario == "tool-allow" else 1)
    from hermes_cli import middleware
    from run_agent import AIAgent
    from agent import background_review
    captured = io.StringIO()
    transport = Mock()
    startup_binding_checked = False
    requests = []
    clients = []
    followup_validated = False
    native_agents = []
    recovery_checks = {}

    original_init = AIAgent.__init__
    def construct(agent, *args, **kwargs):
        original_init(agent, *args, **kwargs)
        native_agents.append(agent)
        if scenario == "background-denial":
            # Trigger the existing finalizer review branch; no alternate worker.
            agent._skill_nudge_interval = 1
            agent._iters_since_skill = 1
            agent.valid_tool_names = list(set(agent.valid_tool_names) | {"skill_manage"})

    def respond(request):
        nonlocal followup_validated
        from .candidate_transport import completion_response
        records = [json.loads(line) for line in (root / "governance/audit/runtime.jsonl").read_text(encoding="utf-8").splitlines()]
        allowed = [r for r in records if r["capability"] == "model.egress" and r["decision"] == "allow"]
        if len(allowed) != len(requests) + 1:
            raise RuntimeError("candidate.transport_before_authorization")
        if scenario == "tool-allow" and requests:
            body = json.loads(request.content)
            results = [message for message in body.get("messages", []) if message.get("role") == "tool"]
            if len(requests) != 1 or len(results) != 1 or results[0].get("tool_call_id") != "candidate-read":
                raise RuntimeError("candidate.followup_tool_result_invalid")
            result = json.loads(results[0]["content"])
            if result.get("error") or "Candidate approved business record" not in result.get("content", ""):
                raise RuntimeError("candidate.native_file_read_failed")
            if not any(r["event_type"] == "validation.hermes_tool_result" and r["capability"] == "file.read" for r in records):
                raise RuntimeError("candidate.tool_result_not_validated")
            followup_validated = True
        requests.append(request.url.path)
        return completion_response(request, tool=scenario == "tool-denial" or (scenario == "tool-allow" and len(requests) == 1),
                                   tool_path="approved.txt" if scenario == "tool-allow" else "denied.txt")

    def client(**kwargs):
        nonlocal startup_binding_checked
        if middleware.validate_mandatory_middleware() is not True:
            raise RuntimeError("candidate.binding_before_construction_missing")
        startup_binding_checked = True
        if scenario in {"model-denial", "compression-denial"}:
            return transport
        import httpx
        from openai import OpenAI
        kwargs["max_retries"] = 0
        kwargs["http_client"] = httpx.Client(transport=httpx.MockTransport(respond), trust_env=False)
        sdk = OpenAI(**kwargs)
        clients.append(sdk)
        return sdk

    from tools.registry import registry
    definitions = registry.get_definitions(["read_file"], quiet=True) if scenario in {"tool-denial", "tool-allow"} else []
    if scenario in {"tool-denial", "tool-allow"} and len(definitions) != 1:
        raise RuntimeError("candidate.native_file_tool_missing")
    dependencies = {}
    if scenario == "tool-allow":
        _configure_native_shell()
        dependencies["native_shell"] = {"component": "bash", "bundled": False,
                                        "ownership": "customer_managed"}

    started = False
    try:
        with redirect_stdout(captured), redirect_stderr(captured), \
             patch("run_agent.OpenAI", side_effect=client), \
             patch.object(AIAgent, "__init__", construct), \
             patch("run_agent.get_tool_definitions", return_value=definitions), \
             patch("run_agent.check_toolset_requirements", return_value={}), \
             patch.object(registry, "dispatch", wraps=registry.dispatch) as dispatch, \
             patch("socket.socket.connect", side_effect=RuntimeError("candidate.network_blocked")) as sockets, \
             patch.object(background_review, "spawn_background_review_thread", wraps=background_review.spawn_background_review_thread) as background, \
             patch("run_agent.threading.Thread", wraps=threading.Thread) as threads:
            product.start()
            started = True
            health = product.health()
            if health.state.value != "healthy" or health.details.get("production_qualified") != "false":
                raise RuntimeError("candidate.lifecycle_failed")
            construction_sockets = sockets.call_count
            if scenario in {"model-allow", "tool-allow"}:
                if product.run("Synthetic business question") != "Synthetic approved response":
                    raise RuntimeError("candidate.allowed_response_invalid")
            else:
                try:
                    product.run("Synthetic business question")
                except middleware.MandatoryMiddlewareError as exc:
                    if scenario == "background-denial" and str(exc) != "mandatory_middleware.background_review_unqualified":
                        raise RuntimeError("candidate.background_denial_invalid") from None
                else:
                    raise RuntimeError("candidate.denial_missing")
            if sockets.call_count != construction_sockets or transport.chat.completions.create.call_count:
                raise RuntimeError("candidate.denied_request_reached_transport")
            expected_attempts = 2 if scenario == "tool-allow" else 1
            if scenario not in {"model-denial", "compression-denial"} and requests != ["/v1/chat/completions"] * expected_attempts:
                raise RuntimeError("candidate.transport_attempt_count_invalid")
            if dispatch.call_count != (1 if scenario == "tool-allow" else 0):
                raise RuntimeError("candidate.denied_tool_reached_handler")
            if scenario == "tool-allow":
                name, args = dispatch.call_args.args[:2]
                if name != "read_file" or Path(args["path"]).resolve() != approved.resolve():
                    raise RuntimeError("candidate.executed_tool_target_invalid")
            if scenario == "compression-denial":
                from agent import context_compressor
                compressor = native_agents[0].context_compressor
                previous = compressor._previous_summary
                cooldown = compressor._summary_failure_cooldown_until
                def governed_summary(**kwargs):
                    return middleware.run_llm_execution_middleware(
                        {"model": template["llm"]["model"], "messages": kwargs["messages"]},
                        transport, provider=template["llm"]["provider"], base_url=template["llm"]["endpoint"],
                    )
                # Exercise the complete native consumer at its auxiliary-call seam.
                # Auxiliary route selection is not qualified by this scenario.
                with patch.object(context_compressor, "call_llm", side_effect=governed_summary) as summary, \
                     patch.object(compressor, "_fallback_to_main_for_compression", wraps=compressor._fallback_to_main_for_compression) as fallback, \
                     bind_request_identity("candidate-operator"):
                    try:
                        compressor._generate_summary([{"role": "user", "content": "Synthetic compression question"}])
                    except middleware.MandatoryMiddlewareError:
                        pass
                    else:
                        raise RuntimeError("candidate.compression_denial_missing")
                recovery_checks = {"compression_denial_propagated": True,
                                   "single_summary_attempt": summary.call_count == 1,
                                   "zero_summary_fallbacks": fallback.call_count == 0,
                                   "summary_state_preserved": compressor._previous_summary == previous and compressor._summary_failure_cooldown_until == cooldown,
                                   "zero_summary_transport": transport.call_count == 0}
            if scenario == "background-denial":
                recovery_checks = {"finalizer_background_denial_propagated": True,
                                   "native_background_factory_called": background.call_count == 1,
                                   "zero_background_threads": not any(call.kwargs.get("name") == "bg-review" for call in threads.call_args_list),
                                   "zero_background_agents": len(native_agents) == 1}
            recovery_checks.update(_qualify_persistence_observers(native_agents[0]))
            product.stop()
            started = False
        audit = (root / "governance/audit/runtime.jsonl").read_text(encoding="utf-8")
        records = [json.loads(line) for line in audit.splitlines()]
        checks = {
            "binding_before_construction": startup_binding_checked,
            "public_runtime_authorized": any(r["capability"] == "runtime.execute" and r["decision"] == "allow" for r in records),
            "governed_memory_retrieval": any(r["capability"] == "memory.read" and r["decision"] == "allow" for r in records),
            "native_model_denial_audited": any(r["capability"] == "model.egress" and r["decision"] == "deny"
                                               and r["reason_code"] == "governance.denied" for r in records),
            "sqlite_initialized": (root / "memory/memory.sqlite3").is_file(),
            "zero_denied_request_transport": True,
            "secret_safe": all(value not in audit + captured.getvalue()
                               for value in ("Synthetic business question", "Synthetic compression question", "Synthetic persistence question", "Synthetic observer body", "local-test-only", "Candidate protected file content")),
        }
        checks.update(recovery_checks)
        if scenario not in {"model-denial", "compression-denial"}:
            del checks["native_model_denial_audited"]
            del checks["zero_denied_request_transport"]
            checks["native_model_allow_audited"] = any(r["capability"] == "model.egress" and r["decision"] == "allow" for r in records)
            checks["single_sdk_attempt"] = len(requests) == (2 if scenario == "tool-allow" else 1) and all(c.max_retries == 0 for c in clients)
            if scenario in {"model-allow", "tool-allow", "background-denial"}:
                checks["native_output_validated"] = any(r["event_type"] == "validation.hermes_model_output" for r in records)
                if scenario == "tool-allow":
                    del checks["single_sdk_attempt"]
                    checks["zero_sdk_retries"] = bool(clients) and all(c.max_retries == 0 for c in clients)
                    checks["two_model_requests"] = len(requests) == 2
                    checks["native_file_allow_audited"] = any(r["capability"] == "file.read" and r["decision"] == "allow" for r in records)
                    checks["native_tool_result_validated"] = any(r["event_type"] == "validation.hermes_tool_result" and r["capability"] == "file.read" for r in records)
                    checks["one_native_tool_dispatch"] = dispatch.call_count == 1
                    checks["followup_model_reauthorized"] = followup_validated and len([r for r in records if r["capability"] == "model.egress" and r["decision"] == "allow"]) == 2
                    checks["approved_file_unchanged"] = approved.read_text(encoding="utf-8") == "Candidate approved business record"
            else:
                checks["native_file_denial_audited"] = any(r["capability"] == "file.read" and r["decision"] == "deny"
                                                          and r["reason_code"] == "governance.denied" for r in records)
                checks["zero_tool_handler_calls"] = dispatch.call_count == 0
                checks["protected_file_unchanged"] = sentinel.read_text(encoding="utf-8") == "Candidate protected file content"
        try:
            require_runtime_contract(middleware)
        except GovernanceBoundaryError:
            checks["production_guard_preserved"] = True
        else:
            checks["production_guard_preserved"] = False
        if not all(checks.values()):
            raise RuntimeError("candidate.qualification_failed")
        report = {"qualification": "test_only_unqualified", "production_qualified": False,
                  "status": "passed", "checks": checks,
                  "scenario": scenario,
                  "dependencies": dependencies,
                  "scope": ("native compression consumer at governed auxiliary-call seam; no provider selection qualification" if scenario == "compression-denial"
                            else "native loop/finalizer background denial; synthetic HTTP fixture, no background worker" if scenario == "background-denial"
                            else "offline startup and native model denial; inert transport/tool catalogue" if scenario == "model-denial"
                            else "real SDK and native loop; synthetic HTTP fixture, no live provider or sockets"),
                  "remaining": ["live_provider", "managed_shell_runtime", "additional_tool_capabilities", "recovery_background", "clean_install_lifecycle"]}
        (root / "qualification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report
    finally:
        for sdk in clients:
            sdk.close()
        if started:
            with redirect_stdout(captured), redirect_stderr(captured):
                product.stop()
        else:
            close = getattr(product.retriever, "close", None)
            if callable(close):
                close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Offline installed Maya governance candidate qualification")
    parser.add_argument("--install-dir", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--scenario", choices=SCENARIOS, default="model-denial")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(qualify(args.install_dir, args.data_root, scenario=args.scenario), sort_keys=True))
        return 0
    except Exception as exc:
        reason = "candidate.native_shell_missing" if str(exc) == "candidate.native_shell_missing" else "candidate.qualification_failed"
        print(json.dumps({"qualification": "test_only_unqualified", "production_qualified": False,
                          "status": "blocked", "scenario": args.scenario, "reason_code": reason}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
