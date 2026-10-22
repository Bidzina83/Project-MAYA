"""Bounded product-owned native memory workflow; never dispatches tools or models."""
import contextlib
import hashlib
import importlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import time

SCHEMA = "maya.protected_hermes.memory.v1"
COMMIT = "b13e2fd6948a59eeb59fe618914147d97a2ee90a"
LIMIT = 65536
STORAGE_LIMIT = 65536
MODEL = "maya-construction-only"
URL = "https://maya-construction.invalid/v1"
PLACEHOLDER = "maya-public-nonsecret-construction-only"
CONFIG = {"model": {"context_length": 131072}, "context": {"engine": "compressor"},
          "compression": {"enabled": False}, "agent": {"environment_probe": False},
          "tools": {"tool_search": {"enabled": "off"}}, "memory": {
              "memory_enabled": True, "user_profile_enabled": True, "provider": "",
              "memory_char_limit": 2200, "user_char_limit": 1375}}
TARGETS = {"memory": "MEMORY.md", "user": "USER.md"}
OPERATIONS = tuple(target + "." + action for target in TARGETS
                   for action in ("add_first", "add_second", "replace", "remove"))
FLAGS = ("constructor_completed", "client_created", "empty_tools", "memory_enabled",
         "external_memory_disabled", "db_disabled", "config_consumed", "zero_model_calls",
         "context_shutdown_returned", "close_returned", "client_closed", "fresh_home_verified",
         "memory_class_verified", "store_attached", "memory_paths_verified", "windows_locking_available",
         "initial_empty", "fresh_reload_matches", "snapshot_behavior_matches",
         "files_unchanged_after_reload", "residue_absent", "lock_probes_passed", "storage_within_limit")


def save(report):
    raw = json.dumps(report, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    if len(raw) > LIMIT:
        raise ValueError("memory_report_size")
    with open("hermes-memory.json", "wb") as stream:
        if stream.write(raw) != len(raw):
            raise OSError("memory_report_short_write")


def config_matches(expected, actual):
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(
            key in actual and config_matches(value, actual[key]) for key, value in expected.items())
    return type(actual) is type(expected) and actual == expected


def fixture(target, nonce):
    return tuple("MAYA synthetic fixture " + target + " " + phase + " " + nonce
                 for phase in ("first", "scratch", "revision"))


def plain_path(path, parent, directory=False):
    info = path.lstat()
    kind = stat.S_ISDIR if directory else stat.S_ISREG
    if (not kind(info.st_mode) or path.resolve().parent != parent or
            getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)):
        raise ValueError("memory_path_rejected")
    return info


def inventory(directory, report):
    plain_path(directory, directory.parent, directory=True)
    total = 0
    count = 0
    allowed = {name + suffix for name in TARGETS.values() for suffix in ("", ".lock")}
    for path in directory.iterdir():
        count += 1
        if count > 8:
            raise ValueError("memory_file_count")
        total += plain_path(path, directory).st_size
        report["memory_peak_bytes"] = max(report.get("memory_peak_bytes", 0), total)
        if total > STORAGE_LIMIT or report["memory_peak_bytes"] > STORAGE_LIMIT:
            report["storage_within_limit"] = False
            raise ValueError("memory_size_limit")
        if path.name not in allowed:
            report["residue_absent"] = False
            raise ValueError("memory_unexpected_file")
    report["storage_within_limit"] = True
    report["residue_absent"] = True


def entries(store, target):
    return store.memory_entries if target == "memory" else store.user_entries


def verify_target(store, module, target, expected, directory, report):
    path = directory / TARGETS[target]
    if plain_path(path, directory).st_size > STORAGE_LIMIT:
        raise ValueError("memory_size_limit")
    # Read independently: upstream's reader can silently return [] on I/O failure.
    text = path.read_text(encoding="utf-8")
    if entries(store, target) != expected or text != module.ENTRY_DELIMITER.join(expected):
        raise ValueError("memory_readback")
    inventory(directory, report)


def file_hashes(directory):
    result = {}
    for name in TARGETS.values():
        path = directory / name
        if plain_path(path, directory).st_size > STORAGE_LIMIT:
            raise ValueError("memory_size_limit")
        result["memories/" + name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def probe_locks(directory, locking):
    count = 0
    for name in TARGETS.values():
        path = directory / (name + ".lock")
        plain_path(path, directory)
        with path.open("r+b") as stream:
            stream.seek(0)
            locking.locking(stream.fileno(), locking.LK_NBLCK, 1)
            try:
                count += 1
            finally:
                stream.seek(0)
                locking.locking(stream.fileno(), locking.LK_UNLCK, 1)
    return count


def exercise_memory(factory, module, locking, nonce, state, report):
    directory = state / "memories"
    agent = client = None
    try:
        report["stage"] = "memory_bootstrap_freshness"
        save(report)
        if directory.exists():
            plain_path(directory, state, directory=True)
            if any(directory.iterdir()):
                raise ValueError("memory_already_populated")
        report["stage"] = "constructor_entry"
        save(report)
        agent = factory(
            provider="custom", api_mode="chat_completions", base_url=URL,
            api_key=PLACEHOLDER, model=MODEL, enabled_toolsets=[], skip_memory=False,
            skip_context_files=True, load_soul_identity=False, session_db=None,
            checkpoints_enabled=False, fallback_model=None, credential_pool=None,
            quiet_mode=True, save_trajectories=False, verbose_logging=False, session_id="maya-memory-" + nonce)
        report["constructor_completed"] = True
        report["stage"] = "constructor_postconditions"
        client = agent.client
        from openai import OpenAI
        from agent.context_compressor import ContextCompressor
        store = agent._memory_store
        report["client_created"] = isinstance(client, OpenAI)
        report["empty_tools"] = agent.tools == [] and agent.valid_tool_names == set()
        report["memory_enabled"] = agent._memory_enabled is True and agent._user_profile_enabled is True
        report["external_memory_disabled"] = agent._memory_manager is None
        report["db_disabled"] = agent._session_db is None
        report["store_attached"] = isinstance(store, module.MemoryStore)
        report["config_consumed"] = (isinstance(agent.context_compressor, ContextCompressor)
                                     and agent.context_compressor.context_length == 131072
                                     and agent.compression_enabled is False and agent._environment_probe is False
                                     and agent._config_context_length == 131072 and agent._checkpoint_mgr.enabled is False)
        report["zero_model_calls"] = agent.session_api_calls == 0
        if not all(report[key] for key in ("client_created", "empty_tools", "memory_enabled", "external_memory_disabled",
                                          "db_disabled", "store_attached", "config_consumed", "zero_model_calls")):
            raise ValueError("constructor_postconditions")
        report["memory_char_limit"] = store.memory_char_limit
        report["user_char_limit"] = store.user_char_limit
        if store.memory_char_limit != 2200 or store.user_char_limit != 1375:
            raise ValueError("memory_limits")
        report["windows_locking_available"] = module.fcntl is None and module.msvcrt is locking and callable(getattr(locking, "locking", None))
        if not report["windows_locking_available"]:
            raise ValueError("windows_locking_missing")
        report["memory_paths_verified"] = (module.get_memory_dir().resolve() == directory and
            all(store._path_for(target).resolve() == directory / name for target, name in TARGETS.items()))
        if not report["memory_paths_verified"]:
            raise ValueError("memory_binding")
        report["stage"] = "memory_initial_load"
        save(report)
        store.load_from_disk()
        inventory(directory, report)
        report["initial_empty"] = (not any(directory.iterdir()) and
            all(entries(store, target) == [] and store.format_for_system_prompt(target) is None for target in TARGETS))
        if not report["initial_empty"]:
            raise ValueError("memory_initial_state")
        final = {}
        for target in TARGETS:
            first, scratch, revision = fixture(target, nonce)
            if any(len(text.encode("ascii")) > 256 for text in (first, scratch, revision)):
                raise ValueError("memory_fixture_size")
            for action, args, expected in (
                    ("add_first", (target, first), [first]),
                    ("add_second", (target, scratch), [first, scratch]),
                    ("replace", (target, first, revision), [revision, scratch]),
                    ("remove", (target, scratch), [revision])):
                report["stage"] = target + "." + action
                save(report)
                method = store.add if action.startswith("add_") else getattr(store, action)
                result = method(*args)
                if (not isinstance(result, dict) or result.get("success") is not True or result.get("done") is not True
                        or result.get("target") != target or result.get("entry_count") != len(expected)):
                    raise ValueError("memory_mutation_result")
                verify_target(store, module, target, expected, directory, report)
                report["operation_checks"][target + "." + action] = True
                report["mutations_verified"] += 1
            final[target] = [revision]
        report["stage"] = "memory_fresh_reload"
        save(report)
        before = file_hashes(directory)
        fresh = module.MemoryStore(memory_char_limit=2200, user_char_limit=1375)
        fresh.load_from_disk()
        report["fresh_reload_matches"] = all(entries(fresh, target) == final[target] for target in TARGETS)
        snapshots = True
        for target in TARGETS:
            verify_target(fresh, module, target, final[target], directory, report)
            block = fresh.format_for_system_prompt(target)
            snapshots = snapshots and (store.format_for_system_prompt(target) is None and
                isinstance(block, str) and block == fresh._render_block(target, final[target]) and
                final[target][0] in block and "[BLOCKED:" not in block)
        report["snapshot_behavior_matches"] = snapshots
        after = file_hashes(directory)
        report["file_hashes"] = after
        report["files_unchanged_after_reload"] = before == after
        if not all(report[key] for key in ("fresh_reload_matches", "snapshot_behavior_matches", "files_unchanged_after_reload")):
            raise ValueError("memory_reload_postconditions")
        report["memory_entry_count"] = len(fresh.memory_entries)
        report["user_entry_count"] = len(fresh.user_entries)
        report["stage"] = "memory_lock_probes"
        save(report)
        report["lock_probe_count"] = probe_locks(directory, locking)
        report["lock_probes_passed"] = report["lock_probe_count"] == 2
        inventory(directory, report)
        if not report["lock_probes_passed"]:
            raise ValueError("memory_lock_probes")
        report["stage"] = "context_shutdown_entry"
        save(report)
        agent.shutdown_memory_provider([])
        report["context_shutdown_returned"] = True
    except Exception:
        report["operation_failure_stage"] = report["stage"]
        raise
    finally:
        if agent is not None:
            report["stage"] = "close_entry"
            try:
                save(report)
            finally:
                agent.close()
            report["close_returned"] = True
            report["client_closed"] = client is not None and client.is_closed() is True and agent.client is None
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
    for name in FLAGS:
        report[name] = False
    report.update(operation_checks={name: False for name in OPERATIONS}, mutations_verified=0,
                  lock_probe_count=0, memory_peak_bytes=0, memory_entry_count=0, user_entry_count=0,
                  file_hashes={}, memory_module_origin="", memory_dir_relative="memories",
                  fixture_version="native-memory-eight-mutations-v1")
    deadline = time.monotonic() + 22
    handles = []
    sink = None

    def budget(frame, event, arg):
        if event == "call" and time.monotonic() >= deadline:
            raise TimeoutError("memory_budget")

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
        contract = json.loads((runtime / "hermes-memory-contract.json").read_text(encoding="utf-8"))
        if contract["source_commit"] != COMMIT or contract["schema"] != SCHEMA:
            raise ValueError("memory_contract_identity")
        config_bytes = (runtime / "hermes-memory-config.json").read_bytes()
        if (json.loads(config_bytes) != CONFIG or (state / "config.yaml").read_bytes() != config_bytes or
                hashlib.sha256(config_bytes).hexdigest() != contract["config_sha256"]):
            raise ValueError("memory_config_identity")
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
        if os.path.lexists(state / "memories"):
            raise ValueError("memory_home_not_fresh")
        report["fresh_home_verified"] = True
        if contract.get("fixture_version") != "native-memory-eight-mutations-v1" or contract.get("storage_limit") != STORAGE_LIMIT:
            raise ValueError("memory_fixture_identity")
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
                memory_module = importlib.import_module("tools.memory_tool")
                memory_origin = Path(vars(memory_module).get("__file__", "")).resolve()
                store_type = vars(memory_module).get("MemoryStore")
                if (memory_origin != runtime / "hermes" / "tools" / "memory_tool.py" or
                        not isinstance(store_type, type) or store_type.__module__ != "tools.memory_tool" or
                        store_type.__name__ != "MemoryStore"):
                    raise ValueError("memory_class_identity")
                report["memory_class_verified"] = True
                report["memory_module_origin"] = memory_origin.relative_to(runtime).as_posix()
                locking = importlib.import_module("msvcrt")
                exercise_memory(factory, memory_module, locking, nonce, state, report)
            finally:
                sys.setprofile(None)
        if time.monotonic() >= deadline:
            raise TimeoutError("memory_budget")
        report["config_unchanged"] = (state / "config.yaml").read_bytes() == config_bytes
        for loaded in tuple(sys.modules.values()):
            file = vars(loaded).get("__file__") if loaded is not None else None
            if file and not Path(file).resolve().is_relative_to(runtime):
                report["outside_runtime_modules"] += 1
        if not report["config_unchanged"] or report["outside_runtime_modules"] or sink.overflow:
            raise ValueError("memory_evidence_incomplete")
        report["stage"] = "memory_complete"
        report["status"] = "memory_completed"
        return 0
    except Exception as error:
        report["status"] = "memory_failed"
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
