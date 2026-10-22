"""Bounded native session persistence. No conversation, model or tool dispatch."""

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

SCHEMA = "maya.protected_hermes.state.v1"
COMMIT = "b13e2fd6948a59eeb59fe618914147d97a2ee90a"
LIMIT = 65536
STORAGE_LIMIT = 32 * 1024 * 1024
MODEL = "maya-construction-only"
URL = "https://maya-construction.invalid/v1"
PLACEHOLDER = "maya-public-nonsecret-construction-only"
CONFIG = {"model": {"context_length": 131072}, "context": {"engine": "compressor"},
          "compression": {"enabled": False}, "agent": {"environment_probe": False},
          "tools": {"tool_search": {"enabled": "off"}}}
DB_FILES = ("state.db", "state.db-wal", "state.db-shm", "state.db-journal")
FLAGS = ("constructor_completed", "client_created", "empty_tools", "memory_disabled",
         "config_consumed", "zero_model_calls", "context_shutdown_returned",
         "close_returned", "client_closed", "db_class_verified", "fresh_db_verified",
         "db_path_verified", "session_created", "agent_db_bound", "write_readback",
         "session_end_verified", "writer_closed", "read_only_reopened",
         "reopen_readback", "reader_closed", "storage_within_limit")


def save(report):
    raw = json.dumps(report, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    if len(raw) > LIMIT:
        raise ValueError("state_report_size")
    with open("hermes-state.json", "wb") as stream:
        if stream.write(raw) != len(raw):
            raise OSError("state_report_short_write")


def config_matches(expected, actual):
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(
            key in actual and config_matches(value, actual[key]) for key, value in expected.items())
    return type(actual) is type(expected) and actual == expected


def synthetic_messages(nonce):
    return (("user", "MAYA_SYNTHETIC_USER_STATE_V1:" + nonce),
            ("assistant", "MAYA_SYNTHETIC_ASSISTANT_FIXTURE_NOT_MODEL_V1:" + nonce))


def storage_bytes(state):
    total = 0
    for name in DB_FILES:
        path = state / name
        try:
            info = path.lstat()
        except FileNotFoundError:
            continue
        if (not stat.S_ISREG(info.st_mode) or
                getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0) or
                path.resolve().parent != state):
            raise ValueError("db_file_path")
        total += info.st_size
    return total


def check_size(state, report):
    total = storage_bytes(state)
    report["db_peak_bytes"] = max(report.get("db_peak_bytes", 0), total)
    report["storage_within_limit"] = 0 < total <= STORAGE_LIMIT and report["db_peak_bytes"] <= STORAGE_LIMIT
    if not report["storage_within_limit"]:
        raise ValueError("db_size_limit")


def inspect_db(db, path, read_only):
    if db.db_path.resolve() != path or db.read_only is not read_only:
        raise ValueError("db_binding")
    main = [row for row in db._conn.execute("PRAGMA database_list").fetchall() if row[1] == "main"]
    if len(main) != 1 or Path(main[0][2]).resolve() != path:
        raise ValueError("db_connection_path")
    return db._conn.execute("PRAGMA journal_mode").fetchone()[0]


def readback(db, session_id, messages, ended):
    session = db.get_session(session_id)
    rows = db.get_messages(session_id, include_inactive=True)
    return (isinstance(session, dict) and session.get("id") == session_id and
            session.get("source") == "maya-state-fixture" and session.get("model") == MODEL and
            session.get("message_count") == 2 and session.get("tool_call_count") == 0 and
            db.session_count(include_archived=True) == 1 and db.message_count() == 2 and
            len(rows) == 2 and tuple((row.get("role"), row.get("content")) for row in rows) == messages and
            all(row.get("session_id") == session_id for row in rows) and
            type(rows[0].get("id")) is int and type(rows[1].get("id")) is int and
            0 < rows[0]["id"] < rows[1]["id"] and
            ((session.get("ended_at") is not None and session.get("end_reason") == "agent_close")
             if ended else (session.get("ended_at") is None and session.get("end_reason") is None)))


def close_database(db):
    import sqlite3
    connection = db._conn
    db.close()
    if connection is None or db._conn is not None:
        raise ValueError("db_close_postcondition")
    try:
        connection.execute("SELECT 1")
    except sqlite3.ProgrammingError:
        return
    raise ValueError("db_connection_still_open")


def exercise_state(factory, db_factory, nonce, state, report):
    writer = reader = agent = client = None
    path = state / "state.db"
    session_id = "maya-state-" + nonce
    messages = synthetic_messages(nonce)
    report.update(db_relative_path="state.db", session_id=session_id, fixture_version="session-two-records-v1")
    try:
        report["stage"] = "db_freshness"
        save(report)
        if any(os.path.lexists(state / name) for name in DB_FILES):
            raise ValueError("db_already_exists")
        report["fresh_db_verified"] = True
        report["stage"] = "db_schema_open"
        save(report)
        writer = db_factory(db_path=path)
        report["journal_mode"] = inspect_db(writer, path, False)
        report["db_path_verified"] = True
        report["fts_enabled"] = bool(writer._fts_enabled)
        report["trigram_available"] = bool(writer._trigram_available)
        check_size(state, report)
        if report["journal_mode"] != "wal" or writer.session_count(include_archived=True) != 0 or writer.message_count() != 0:
            raise ValueError("db_initial_state")
        report["stage"] = "session_create"
        save(report)
        if writer.create_session(session_id, "maya-state-fixture", model=MODEL) != session_id:
            raise ValueError("session_create_result")
        report["session_created"] = True
        check_size(state, report)
        try:
            report["stage"] = "constructor_entry"
            save(report)
            agent = factory(
                provider="custom", api_mode="chat_completions", base_url=URL,
                api_key=PLACEHOLDER, model=MODEL, enabled_toolsets=[], skip_memory=True,
                skip_context_files=True, load_soul_identity=False, session_db=writer,
                checkpoints_enabled=False, fallback_model=None, credential_pool=None,
                quiet_mode=True, save_trajectories=False, verbose_logging=False, session_id=session_id)
            report["constructor_completed"] = True
            report["stage"] = "constructor_postconditions"
            client = agent.client
            from openai import OpenAI
            from agent.context_compressor import ContextCompressor
            report["client_created"] = isinstance(client, OpenAI)
            report["empty_tools"] = agent.tools == [] and agent.valid_tool_names == set()
            report["memory_disabled"] = (agent._memory_manager is None and agent._memory_store is None
                                         and agent._memory_enabled is False and agent._user_profile_enabled is False)
            report["agent_db_bound"] = agent._session_db is writer and agent.session_id == session_id
            report["config_consumed"] = (isinstance(agent.context_compressor, ContextCompressor)
                                         and agent.context_compressor.context_length == 131072
                                         and agent.compression_enabled is False and agent._environment_probe is False
                                         and agent._config_context_length == 131072 and agent._checkpoint_mgr.enabled is False)
            report["zero_model_calls"] = agent.session_api_calls == 0
            if not all(report[name] for name in ("client_created", "empty_tools", "memory_disabled",
                                                 "config_consumed", "agent_db_bound", "zero_model_calls")):
                raise ValueError("constructor_postconditions")
            check_size(state, report)
            for index, (role, text) in enumerate(messages):
                report["stage"] = "message_append_" + str(index + 1)
                save(report)
                if len(text.encode("ascii")) > 512:
                    raise ValueError("fixture_size")
                row_id = writer.append_message(session_id, role, content=text)
                if type(row_id) is not int or row_id <= 0:
                    raise ValueError("message_append_result")
                check_size(state, report)
            report["stage"] = "write_readback"
            save(report)
            report["write_readback"] = readback(writer, session_id, messages, False)
            if not report["write_readback"]:
                raise ValueError("write_readback")
            report["session_count"] = 1
            report["message_count"] = 2
            check_size(state, report)
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
        report["stage"] = "session_end_readback"
        save(report)
        report["session_end_verified"] = readback(writer, session_id, messages, True)
        if not report["session_end_verified"]:
            raise ValueError("session_end_readback")
        check_size(state, report)
        report["stage"] = "writer_close"
        save(report)
        closing, writer = writer, None
        close_database(closing)
        report["writer_closed"] = True
        check_size(state, report)
        report["stage"] = "read_only_reopen"
        save(report)
        reader = db_factory(db_path=path, read_only=True)
        if inspect_db(reader, path, True) != "wal":
            raise ValueError("reader_journal_mode")
        report["read_only_reopened"] = True
        report["stage"] = "reopen_readback"
        save(report)
        report["reopen_readback"] = readback(reader, session_id, messages, True)
        if not report["reopen_readback"]:
            raise ValueError("reopen_readback")
        check_size(state, report)
        report["stage"] = "reader_close"
        save(report)
        closing, reader = reader, None
        close_database(closing)
        report["reader_closed"] = True
        check_size(state, report)
    except Exception:
        if not report["operation_failure_stage"]:
            report["operation_failure_stage"] = report["stage"]
        raise
    finally:
        for remaining in (reader, writer):
            if remaining is not None:
                try:
                    close_database(remaining)
                except Exception as error:
                    report["db_cleanup_reason_type"] = type(error).__name__


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
    report.update(db_module_origin="", db_relative_path="", journal_mode="", fixture_version="",
                  session_id="", session_count=0, message_count=0, db_peak_bytes=0, db_cleanup_reason_type="")
    for name in FLAGS:
        report[name] = False
    deadline = time.monotonic() + 22
    handles = []
    sink = None

    def budget(frame, event, arg):
        if event == "call" and time.monotonic() >= deadline:
            raise TimeoutError("state_budget")

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
        contract = json.loads((runtime / "hermes-state-contract.json").read_text(encoding="utf-8"))
        if contract["source_commit"] != COMMIT or contract["schema"] != SCHEMA:
            raise ValueError("state_contract_identity")
        if contract.get("fixture_version") != "session-two-records-v1" or contract.get("storage_limit") != STORAGE_LIMIT:
            raise ValueError("state_fixture_identity")
        config_bytes = (runtime / "hermes-construction-config.json").read_bytes()
        if (json.loads(config_bytes) != CONFIG or (state / "config.yaml").read_bytes() != config_bytes or
                hashlib.sha256(config_bytes).hexdigest() != contract["config_sha256"]):
            raise ValueError("state_config_identity")
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
                report["stage"] = "db_module_import"
                save(report)
                db_module = importlib.import_module("hermes_state")
                db_factory = vars(db_module).get("SessionDB")
                db_origin = Path(vars(db_module).get("__file__", "")).resolve()
                if (not isinstance(db_factory, type) or db_factory.__module__ != "hermes_state" or
                        db_factory.__name__ != "SessionDB" or db_origin != runtime / "hermes" / "hermes_state.py"):
                    raise ValueError("db_class_identity")
                report["db_class_verified"] = True
                report["db_module_origin"] = db_origin.relative_to(runtime).as_posix()
                exercise_state(factory, db_factory, nonce, state, report)
            finally:
                sys.setprofile(None)
        if time.monotonic() >= deadline:
            raise TimeoutError("state_budget")
        report["config_unchanged"] = (state / "config.yaml").read_bytes() == config_bytes
        for loaded in tuple(sys.modules.values()):
            file = vars(loaded).get("__file__") if loaded is not None else None
            if file and not Path(file).resolve().is_relative_to(runtime):
                report["outside_runtime_modules"] += 1
        if not report["config_unchanged"] or report["outside_runtime_modules"] or sink.overflow:
            raise ValueError("state_evidence_incomplete")
        report["stage"] = "state_complete"
        report["status"] = "state_completed"
        return 0
    except Exception as error:
        report["status"] = "state_failed"
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
