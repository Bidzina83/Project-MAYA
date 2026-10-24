"""Fixed native registry/bridge slice, not a conversation or model request."""
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

CASES = ("N01", "N02", "N03", "N04", "N05", "N06", "N07", "N08", "N10", "N12")


def main():
    if (sys.platform != "win32" or sys.version_info[:3] != (3, 13, 14) or
            not all((sys.flags.isolated, sys.flags.no_site, sys.flags.dont_write_bytecode)) or
            len(sys.argv) != 2 or len(sys.argv[1]) != 32 or any(c not in "0123456789abcdef" for c in sys.argv[1])):
        return 2
    attempt = sys.argv[1]
    runtime = Path(__file__).resolve().parent
    state = Path.cwd().resolve()
    if (state != runtime.parent / "state" or Path(os.environ.get("HERMES_HOME", "")).resolve() != state
            or os.environ.get("HERMES_DISABLE_LAZY_INSTALLS") != "1"):
        return 2
    deadline = time.monotonic() + 22
    def budget(frame, event, arg):
        if event == "call" and time.monotonic() >= deadline:
            raise TimeoutError("bridge.cooperative_deadline")
    agent = client = None
    handles = []
    report = dict(schema="maya.authorization_bridge.child.v1", attempt=attempt, completed=False,
                  constructor_verified=False, sdk_closed=False, config_unchanged=False,
                  distributions_verified=False, origins_verified=False, zero_model_calls=False,
                  snapshots=[], captured_output_bytes=0, reason_type="")
    try:
        with open("python-startup.txt", "xb") as stream:
            stream.write(("MAYA_PROTECTED_PYTHON_STARTED_V1:"+attempt+"\n").encode("ascii"))
        support_spec = importlib.util.spec_from_file_location("maya_import_support", runtime / "hermes_import_check.py")
        support = importlib.util.module_from_spec(support_spec)
        support_spec.loader.exec_module(support)
        sink = support.Capture()
        sys.path[:0] = [str(runtime), str(runtime / "hermes"), str(runtime / "dependencies")]
        for name in ("win32", "win32/lib", "Pythonwin"):
            directory = runtime / "dependencies" / name
            if directory.is_dir():
                sys.path.append(str(directory))
        for name in ("pywin32_system32", "win32"):
            directory = runtime / "dependencies" / name
            if directory.is_dir():
                handles.append(os.add_dll_directory(str(directory)))
        contract = json.loads((runtime / "bridge-contract.json").read_text())
        if contract["schema"] != "maya.authorization_bridge.package.v1" or contract["cases"] != list(CASES):
            raise ValueError("bridge.contract")
        config_bytes = (runtime / "hermes-construction-config.json").read_bytes()
        if (hashlib.sha256(config_bytes).hexdigest() != contract["config_sha256"] or
                (state / "config.yaml").read_bytes() != config_bytes):
            raise ValueError("bridge.config")
        for name, version in contract["distributions"].items():
            dist = importlib.metadata.distribution(name)
            if dist.version != version or not Path(dist.locate_file("")).resolve().is_relative_to(runtime):
                raise ValueError("bridge.distribution")
        report["distributions_verified"] = len(contract["distributions"]) == 64
        from project_maya.bridge.transport import PrivateChannel
        channel = PrivateChannel(sys.stdin.buffer, sys.stdout.buffer)
        channel.send(dict(v=1, type="hello", attempt=attempt))
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            sys.setprofile(budget)
            try:
                module = importlib.import_module("run_agent")
                if not support.class_matches(module.AIAgent, Path(module.__file__).resolve(), runtime / "hermes" / "run_agent.py"):
                    raise ValueError("bridge.agent_identity")
                from project_maya.hermes_plugins.bridge import BridgeClient, TOOL, SCHEMA
                from project_maya.bridge.service import RESOURCE
                from tools.registry import registry
                from hermes_cli import managed_scope
                from hermes_cli.config import get_config_path, load_config
                if managed_scope.get_managed_dir() is not None or get_config_path().resolve() != state / "config.yaml":
                    raise ValueError("bridge.ambient_config")
                expected_config = json.loads(config_bytes)
                actual_config = load_config()
                def matches(expected, observed):
                    if isinstance(expected, dict):
                        return isinstance(observed, dict) and all(k in observed and matches(v, observed[k]) for k, v in expected.items())
                    return type(expected) is type(observed) and expected == observed
                if not matches(expected_config, actual_config):
                    raise ValueError("bridge.effective_config")
                adapter = BridgeClient(channel, attempt)
                adapter.register(registry)
                agent = module.AIAgent(provider="custom", api_mode="chat_completions",
                    base_url="https://maya-construction.invalid/v1", api_key="maya-public-nonsecret-construction-only",
                    model="maya-construction-only", enabled_toolsets=["maya_bridge"], skip_memory=True,
                    skip_context_files=True, load_soul_identity=False, session_db=None, checkpoints_enabled=False,
                    fallback_model=None, credential_pool=None, quiet_mode=True, save_trajectories=False,
                    verbose_logging=False, session_id="maya-bridge-"+attempt)
                client = agent.client
                from openai import OpenAI
                from agent.context_compressor import ContextCompressor
                report["constructor_verified"] = (isinstance(client, OpenAI) and agent.valid_tool_names == {TOOL}
                    and len(agent.tools) == 1 and agent.tools[0].get("function") == SCHEMA
                    and agent._memory_store is None and agent._memory_manager is None
                    and agent._memory_enabled is False and agent._user_profile_enabled is False
                    and agent._session_db is None and agent._checkpoint_mgr.enabled is False
                    and isinstance(agent.context_compressor, ContextCompressor)
                    and agent.context_compressor.context_length == 131072 and agent.compression_enabled is False
                    and agent._environment_probe is False and agent._config_context_length == 131072)
                if not report["constructor_verified"]:
                    raise ValueError("bridge.constructor")
                channel.send(dict(v=1, type="ready", attempt=attempt, constructor_verified=True))
                consumed_token = None
                for case in CASES:
                    control = channel.receive()
                    if (set(control) != {"v", "type", "attempt", "case", "grant"} or control["v"] != 1
                            or control["type"] != "case" or control["attempt"] != attempt or control["case"] != case):
                        raise ValueError("bridge.control")
                    adapter.bind_grant(control["grant"])
                    if case == "N02":
                        adapter.request()
                        observations = []
                        for name in ("document.txt", "policy.json", "audit.jsonl", "worker.json"):
                            for mode in ("rb", "r+b"):
                                try:
                                    with (runtime.parent / "host" / name).open(mode):
                                        observations.append(False)
                                except PermissionError:
                                    observations.append(True)
                        passed = len(observations) == 8 and all(observations)
                        channel.send(dict(v=1, type="case_complete", attempt=attempt, case=case,
                                          passed=passed, digest="", bytes=0))
                        if not passed:
                            raise ValueError("bridge.direct_access")
                        continue
                    if case == "N01":
                        consumed_token = control["grant"]["lease"]
                        response = json.loads(registry.dispatch(TOOL, {"resource": RESOURCE}))
                    else:
                        request = adapter.request()
                        if case == "N04": request["resource"] = "maya.other.document"
                        if case == "N05": request["actor_id"] = "administrator"
                        if case == "N06": request["lease"] = consumed_token
                        if case == "N07": time.sleep(2.1)
                        if case == "N12": request["operation"] = "execute"
                        response = adapter.call(request)
                    if case == "N01":
                        data = response["data"]["text"].encode("utf-8")
                        passed = response["status"] == "ok"
                        digest = hashlib.sha256(data).hexdigest()
                        size = len(data)
                    else:
                        passed = response["status"] == "denied" and response["data"] is None
                        digest, size = "", 0
                    channel.send(dict(v=1, type="case_complete", attempt=attempt, case=case,
                                      passed=passed, digest=digest, bytes=size))
                    if not passed:
                        raise ValueError("bridge.case_failed")
                agent.shutdown_memory_provider([])
                agent.close()
                report["sdk_closed"] = client.is_closed() is True and agent.client is None
                report["zero_model_calls"] = agent.session_api_calls == 0
                report["config_unchanged"] = (state / "config.yaml").read_bytes() == config_bytes
                report["origins_verified"] = all(not vars(loaded).get("__file__") or
                    Path(vars(loaded)["__file__"]).resolve().is_relative_to(runtime)
                    for loaded in tuple(sys.modules.values()) if loaded is not None)
                report["captured_output_bytes"] = sink.count
                report["completed"] = all(report[key] for key in ("constructor_verified", "sdk_closed", "zero_model_calls",
                    "config_unchanged", "origins_verified", "distributions_verified")) and not sink.overflow
                if not report["completed"]:
                    raise ValueError("bridge.postconditions")
                channel.send(dict(v=1, type="child_complete", attempt=attempt, report=report))
                return 0
            finally:
                sys.setprofile(None)
                if agent is not None and agent.client is not None:
                    agent.close()
    except Exception as error:
        report["reason_type"] = type(error).__name__
        return 3
    finally:
        sys.setprofile(None)
        for handle in reversed(handles):
            handle.close()
        raw = json.dumps(report, ensure_ascii=True, separators=(",", ":")).encode("ascii")
        if len(raw) <= 65536:
            Path("bridge-child.json").write_bytes(raw)


if __name__ == "__main__":
    raise SystemExit(main())
