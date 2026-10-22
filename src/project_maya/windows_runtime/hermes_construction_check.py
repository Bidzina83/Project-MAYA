"""Bounded product-owned construction entry. No conversation or tool execution."""

import contextlib
import hashlib
import importlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

SCHEMA = "maya.protected_hermes.construction.v1"
COMMIT = "b13e2fd6948a59eeb59fe618914147d97a2ee90a"
LIMIT = 65536
MODEL = "maya-construction-only"
URL = "https://maya-construction.invalid/v1"
PLACEHOLDER = "maya-public-nonsecret-construction-only"
CONFIG = {"model": {"context_length": 131072}, "context": {"engine": "compressor"},
          "compression": {"enabled": False}, "agent": {"environment_probe": False},
          "tools": {"tool_search": {"enabled": "off"}}}


def save(report):
    raw = json.dumps(report, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    if len(raw) > LIMIT:
        raise ValueError("construction_report_size")
    with open("hermes-construction.json", "wb") as stream:
        if stream.write(raw) != len(raw):
            raise OSError("construction_report_short_write")


def config_matches(expected, actual):
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(
            key in actual and config_matches(value, actual[key]) for key, value in expected.items())
    return type(actual) is type(expected) and actual == expected


def construct_and_close(factory, nonce, report):
    agent = None
    client = None
    try:
        report["stage"] = "constructor_entry"
        save(report)
        agent = factory(
            provider="custom", api_mode="chat_completions", base_url=URL,
            api_key=PLACEHOLDER, model=MODEL, enabled_toolsets=[], skip_memory=True,
            skip_context_files=True, load_soul_identity=False, session_db=None,
            checkpoints_enabled=False, fallback_model=None, credential_pool=None,
            quiet_mode=True, save_trajectories=False, verbose_logging=False,
            session_id="maya-construction-" + nonce)
        report["constructor_completed"] = True
        report["stage"] = "constructor_postconditions"
        client = agent.client
        from openai import OpenAI
        from agent.context_compressor import ContextCompressor
        report["client_created"] = isinstance(client, OpenAI)
        report["empty_tools"] = agent.tools == [] and agent.valid_tool_names == set()
        report["memory_disabled"] = (agent._memory_manager is None and agent._memory_store is None
                                     and agent._memory_enabled is False and agent._user_profile_enabled is False)
        report["config_consumed"] = (isinstance(agent.context_compressor, ContextCompressor)
                                     and agent.context_compressor.context_length == 131072
                                     and agent.compression_enabled is False
                                     and agent._environment_probe is False
                                     and agent._config_context_length == 131072
                                     and agent._session_db is None
                                     and agent._checkpoint_mgr.enabled is False)
        report["zero_model_calls"] = agent.session_api_calls == 0
        if not all(report[name] for name in (
                "client_created", "empty_tools", "memory_disabled", "config_consumed", "zero_model_calls")):
            raise ValueError("constructor_postconditions")
        report["stage"] = "context_shutdown_entry"
        save(report)
        agent.shutdown_memory_provider([])
        report["context_shutdown_returned"] = True
    except Exception:
        report["operation_failure_stage"] = report["stage"]
        raise
    finally:
        # A failed __init__ never yields a usable instance. The host job is the
        # outer cleanup boundary; do not bypass __init__ to recover a fake agent.
        if agent is not None:
            report["stage"] = "close_entry"
            try:
                save(report)
            finally:
                agent.close()
            report["close_returned"] = True
            report["client_closed"] = (client is not None and client.is_closed() is True
                                       and agent.client is None)
            report["zero_model_calls"] = report["zero_model_calls"] and agent.session_api_calls == 0
            if not report["client_closed"] or not report["zero_model_calls"]:
                raise ValueError("shutdown_postconditions")


def main():
    if (sys.platform != "win32" or sys.version_info[:3] != (3, 13, 14) or
            not all((sys.flags.isolated, sys.flags.no_site, sys.flags.dont_write_bytecode)) or
            len(sys.argv) != 2 or len(sys.argv[1]) != 32 or
            any(x not in "0123456789abcdef" for x in sys.argv[1])):
        return 2
    nonce = sys.argv[1]
    runtime = Path(__file__).resolve().parent
    state = Path.cwd().resolve()
    if (state != runtime.parent / "state" or
            os.environ.get("HERMES_DISABLE_LAZY_INSTALLS") != "1" or
            Path(os.environ.get("HERMES_HOME", "")).resolve() != state):
        return 2
    report = {"schema": SCHEMA, "nonce": nonce, "source_commit": COMMIT,
              "status": "pending", "stage": "python_entry", "class_verified": False,
              "module_origin": "", "outside_runtime_modules": 0, "distributions": {},
              "captured_output_bytes": 0, "output_overflow": False,
              "reason_type": "", "missing_module": "", "config_verified": False,
              "config_unchanged": False, "operation_failure_stage": ""}
    for name in ("constructor_completed", "client_created", "empty_tools", "memory_disabled",
                 "config_consumed", "zero_model_calls", "context_shutdown_returned",
                 "close_returned", "client_closed"):
        report[name] = False
    deadline = time.monotonic() + 22
    handles = []
    sink = None

    def budget(frame, event, arg):
        if event == "call" and time.monotonic() >= deadline:
            raise TimeoutError("construction_budget")

    try:
        beacon = ("MAYA_PROTECTED_PYTHON_STARTED_V1:" + nonce + "\n").encode("ascii")
        with open("python-startup.txt", "xb") as stream:
            if stream.write(beacon) != len(beacon):
                return 3
        if sys.stdout.buffer.write(beacon) != len(beacon):
            return 3
        sys.stdout.buffer.flush()
        save(report)
        helper_spec = importlib.util.spec_from_file_location("maya_import_support", runtime / "hermes_import_check.py")
        helper = importlib.util.module_from_spec(helper_spec)
        helper_spec.loader.exec_module(helper)
        sink = helper.Capture()
        dependencies = runtime / "dependencies"
        sys.path[:0] = [str(runtime / "hermes"), str(dependencies)] + [
            str(dependencies / name) for name in ("win32", "win32/lib", "Pythonwin")
            if (dependencies / name).is_dir()]
        for name in ("pywin32_system32", "win32"):
            directory = dependencies / name
            if directory.is_dir():
                handles.append(os.add_dll_directory(str(directory)))
        contract = json.loads((runtime / "hermes-construction-contract.json").read_text(encoding="utf-8"))
        if contract["source_commit"] != COMMIT or contract["schema"] != SCHEMA:
            raise ValueError("construction_contract_identity")
        config_bytes = (runtime / "hermes-construction-config.json").read_bytes()
        if (json.loads(config_bytes) != CONFIG or (state / "config.yaml").read_bytes() != config_bytes or
                hashlib.sha256(config_bytes).hexdigest() != contract["config_sha256"]):
            raise ValueError("construction_config_identity")
        report["config_verified"] = True
        report["config_sha256"] = contract["config_sha256"]
        report["stage"] = "distribution_metadata"
        save(report)
        for name, expected in contract["distributions"].items():
            distribution = importlib.metadata.distribution(name)
            if (not Path(distribution.locate_file("")).resolve().is_relative_to(runtime)
                    or distribution.version != expected):
                raise ValueError("distribution_identity")
            report["distributions"][name] = distribution.version
        report["stage"] = "run_agent_import"
        save(report)
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            sys.setprofile(budget)
            try:
                module = importlib.import_module("run_agent")
                origin = Path(vars(module).get("__file__", "")).resolve()
                factory = vars(module).get("AIAgent")
                if not helper.class_matches(factory, origin, runtime / "hermes" / "run_agent.py"):
                    raise ValueError("class_identity")
                report["class_verified"] = True
                report["module_origin"] = origin.relative_to(runtime).as_posix()
                from hermes_cli import managed_scope
                from hermes_cli.config import load_config, get_config_path
                if managed_scope.get_managed_dir() is not None or get_config_path().resolve() != state / "config.yaml":
                    raise ValueError("ambient_config")
                config = load_config()
                if not config_matches(CONFIG, config):
                    raise ValueError("effective_config")
                construct_and_close(factory, nonce, report)
            finally:
                sys.setprofile(None)
        if time.monotonic() >= deadline:
            raise TimeoutError("construction_budget")
        report["config_unchanged"] = (state / "config.yaml").read_bytes() == config_bytes
        for loaded in tuple(sys.modules.values()):
            file = vars(loaded).get("__file__") if loaded is not None else None
            if file and not Path(file).resolve().is_relative_to(runtime):
                report["outside_runtime_modules"] += 1
        if not report["config_unchanged"] or report["outside_runtime_modules"] or sink.overflow:
            raise ValueError("construction_evidence_incomplete")
        report["stage"] = "construction_complete"
        report["status"] = "construction_completed"
        return 0
    except Exception as error:
        report["status"] = "construction_failed"
        report["reason_type"] = type(error).__name__
        name = getattr(error, "name", "")
        if isinstance(error, ModuleNotFoundError) and isinstance(name, str) and len(name) <= 100 and all(x.isalnum() or x in "._" for x in name):
            report["missing_module"] = name
        return 4
    finally:
        sys.setprofile(None)
        report["captured_output_bytes"] = sink.count if sink is not None else 0
        report["output_overflow"] = sink.overflow if sink is not None else False
        for handle in reversed(handles):
            handle.close()
        save(report)


if __name__ == "__main__":
    raise SystemExit(main())
