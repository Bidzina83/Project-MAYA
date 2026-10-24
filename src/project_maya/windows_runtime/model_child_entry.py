"""One real pinned Hermes conversation against an explicitly synthetic wire peer."""
import contextlib
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


def main():
    if (sys.platform != "win32" or sys.version_info[:3] != (3, 13, 14) or
            not all((sys.flags.isolated, sys.flags.no_site, sys.flags.dont_write_bytecode)) or
            len(sys.argv) != 2 or len(sys.argv[1]) != 32 or any(c not in "0123456789abcdef" for c in sys.argv[1])):
        return 2
    attempt = sys.argv[1]
    runtime, state = Path(__file__).resolve().parent, Path.cwd().resolve()
    if (state != runtime.parent/"state" or Path(os.environ.get("HERMES_HOME", "")).resolve() != state
            or os.environ.get("HERMES_DISABLE_LAZY_INSTALLS") != "1"):
        return 2
    deadline = time.monotonic()+22

    def budget(frame, event, arg):
        if event == "call" and time.monotonic() >= deadline:
            raise TimeoutError("model_bridge.cooperative_deadline")

    report = dict(schema="maya.offline.model.child.v1", attempt=attempt, completed=False,
        native_constructor=False, native_conversation=False, sdk_closed=False, origins_verified=False,
        distributions_verified=False, config_unchanged=False, model_requests=0, client_objects=0,
        real_inference=False, reason_type="")
    agent = None
    closed = False
    handles = []
    try:
        with open("python-startup.txt", "xb") as stream:
            stream.write(("MAYA_PROTECTED_PYTHON_STARTED_V1:"+attempt+"\n").encode("ascii"))
        spec = importlib.util.spec_from_file_location("maya_import_support", runtime/"hermes_import_check.py")
        support = importlib.util.module_from_spec(spec); spec.loader.exec_module(support)
        sink = support.Capture()
        sys.path[:0] = [str(runtime), str(runtime/"hermes"), str(runtime/"dependencies")]
        for name in ("win32", "win32/lib", "Pythonwin"):
            directory = runtime/"dependencies"/name
            if directory.is_dir(): sys.path.append(str(directory))
        for name in ("pywin32_system32", "win32"):
            directory = runtime/"dependencies"/name
            if directory.is_dir(): handles.append(os.add_dll_directory(str(directory)))
        contract = json.loads((runtime/"model-contract.json").read_text())
        config_bytes = (runtime/"model-config.json").read_bytes()
        if (contract["schema"] != "maya.offline.model.package.v1"
                or hashlib.sha256(config_bytes).hexdigest() != contract["config_sha256"]
                or (state/"config.yaml").read_bytes() != config_bytes):
            raise ValueError("model_bridge.config")
        for name, version in contract["distributions"].items():
            dist = importlib.metadata.distribution(name)
            if dist.version != version or not Path(dist.locate_file("")).resolve().is_relative_to(runtime):
                raise ValueError("model_bridge.distribution")
        report["distributions_verified"] = len(contract["distributions"]) == 64
        from project_maya.bridge.transport import PrivateChannel
        from project_maya.bridge.protocol import ProtocolError
        from project_maya.hermes_plugins.model_bridge import ModelChannelClient, offline_agent_class
        from project_maya.bridge.model_service import MODEL, ORIGIN, PUBLIC_KEY
        channel = PrivateChannel(sys.stdin.buffer, sys.stdout.buffer)
        channel.send(dict(v=1, type="model_child_hello", attempt=attempt))
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            sys.setprofile(budget)
            import run_agent as native_module
            AIAgent = native_module.AIAgent
            if not support.class_matches(AIAgent, Path(native_module.__file__).resolve(), runtime/"hermes/run_agent.py"):
                raise ProtocolError()
            from hermes_cli import managed_scope
            from hermes_cli.config import get_config_path, load_config
            if managed_scope.get_managed_dir() is not None or get_config_path().resolve() != state/"config.yaml":
                raise ProtocolError()
            config = load_config()
            if (config.get("timezone") != "UTC" or config.get("agent", {}).get("api_max_retries") != 1
                    or config.get("compression", {}).get("enabled") is not False):
                raise ProtocolError()
            adapter = ModelChannelClient(channel, attempt)
            agent = offline_agent_class()(maya_model_channel=adapter, provider="custom", api_mode="chat_completions",
                base_url=ORIGIN+"/v1", api_key=PUBLIC_KEY, model=MODEL, max_tokens=32, max_iterations=1,
                enabled_toolsets=[], skip_memory=True, skip_context_files=True, load_soul_identity=False,
                session_db=None, checkpoints_enabled=False, fallback_model=None, credential_pool=None,
                quiet_mode=True, save_trajectories=False, verbose_logging=False,
                request_overrides={"stream":False}, session_id="maya-offline-model-"+attempt)
            from openai import OpenAI
            report["native_constructor"] = (isinstance(agent, AIAgent) and isinstance(agent.client, OpenAI)
                and agent.valid_tool_names == set() and agent.tools == [] and agent._session_db is None
                and agent._memory_store is None and agent._memory_manager is None
                and agent._memory_enabled is False and agent._user_profile_enabled is False
                and agent.compression_enabled is False and agent._environment_probe is False
                and agent._checkpoint_mgr.enabled is False and agent._disable_streaming is True
                and agent._api_max_retries == 1 and agent.max_tokens == 32)
            if not report["native_constructor"]: raise ProtocolError()
            channel.send(dict(v=1, type="model_child_ready", attempt=attempt, native_constructor=True))
            control = channel.receive()
            if (set(control) != {"v", "type", "attempt", "canary", "grant"}
                    or type(control["v"]) is not int or control["v"] != 1
                    or control["type"] != "model_begin" or control["attempt"] != attempt
                    or type(control["canary"]) is not str or len(control["canary"]) != 64
                    or any(c not in "0123456789abcdef" for c in control["canary"])):
                raise ProtocolError()
            adapter.bind_grant(control["grant"])
            result = agent.run_conversation("MAYA_OFFLINE_MODEL_REQUEST:"+control["canary"])
            final = result.get("final_response") if type(result) is dict else None
            report["model_requests"] = adapter.requests
            report["client_objects"] = len(agent._maya_model_clients)
            report["native_conversation"] = (type(final) is str and 1 <= len(final.encode("utf-8")) <= 1024
                and adapter.requests == 1 and agent.session_api_calls == 1 and report["client_objects"] >= 2)
            if not report["native_conversation"]: raise ProtocolError()
            agent.shutdown_memory_provider([]); agent.close(); agent.close_model_clients()
            closed = True
            report["sdk_closed"] = agent.client is None and all(c.is_closed() is True for c, _, _ in agent._maya_model_clients)
            report["config_unchanged"] = (state/"config.yaml").read_bytes() == config_bytes
            report["origins_verified"] = all(not vars(m).get("__file__") or
                Path(vars(m)["__file__"]).resolve().is_relative_to(runtime)
                for m in tuple(sys.modules.values()) if m is not None)
            report["completed"] = all(report[k] for k in ("native_constructor", "native_conversation", "sdk_closed",
                "config_unchanged", "origins_verified", "distributions_verified")) and not sink.overflow
            if not report["completed"]: raise ProtocolError()
            channel.send(dict(v=1, type="model_child_complete", attempt=attempt, text=final, report=report))
            return 0
    except Exception as error:
        report["reason_type"] = type(error).__name__
        return 3
    finally:
        sys.setprofile(None)
        if agent is not None and not closed:
            try: agent.close(); agent.close_model_clients()
            except Exception: report["sdk_closed"] = report["completed"] = False
        for handle in reversed(handles): handle.close()
        raw = json.dumps(report, ensure_ascii=True, separators=(",", ":")).encode("ascii")
        if len(raw) <= 65536: Path("model-child.json").write_bytes(raw)


if __name__ == "__main__": raise SystemExit(main())
