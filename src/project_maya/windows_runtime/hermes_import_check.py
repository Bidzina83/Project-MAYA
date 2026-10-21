"""Product-owned import-only entry; never constructs or executes an agent."""

import contextlib
import importlib
import importlib.metadata
import inspect
import io
import json
import os
from pathlib import Path
import sys
import time

SCHEMA = "maya.protected_hermes.import.v1"
COMMIT = "b13e2fd6948a59eeb59fe618914147d97a2ee90a"
LIMIT = 65536


class Capture(io.TextIOBase):
    def __init__(self):
        self.count = 0
        self.overflow = False

    def write(self, text):
        count = len(text.encode("utf-8", errors="replace"))
        self.count += count
        if self.count > LIMIT:
            self.overflow = True
            raise RuntimeError("import_output_limit")
        return len(text)

    def flush(self):
        pass


def save(report):
    data = json.dumps(report, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    if len(data) > LIMIT:
        raise ValueError("import_report_size")
    with open("hermes-import.json", "wb") as stream:
        if stream.write(data) != len(data):
            raise OSError("import_report_short_write")


def class_matches(factory, origin, expected):
    return (inspect.isclass(factory) and factory.__name__ == "AIAgent" and
            factory.__module__ == "run_agent" and origin == expected)


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
              "reason_type": "", "missing_module": ""}
    sink = Capture()
    deadline = time.monotonic() + 22
    handles = []

    def budget(frame, event, arg):
        if event == "call" and time.monotonic() >= deadline:
            raise TimeoutError("import_budget")

    try:
        beacon = ("MAYA_PROTECTED_PYTHON_STARTED_V1:" + nonce + "\n").encode("ascii")
        with open("python-startup.txt", "xb") as stream:
            if stream.write(beacon) != len(beacon):
                return 3
        if sys.stdout.buffer.write(beacon) != len(beacon):
            return 3
        sys.stdout.buffer.flush()
        save(report)
        dependencies = runtime / "dependencies"
        # Explicit read-only package paths; never process arbitrary .pth code.
        sys.path[:0] = [str(runtime / "hermes"), str(dependencies)] + [
            str(dependencies / name) for name in ("win32", "win32/lib", "Pythonwin")
            if (dependencies / name).is_dir()]
        for name in ("pywin32_system32", "win32"):
            directory = dependencies / name
            if directory.is_dir():
                handles.append(os.add_dll_directory(str(directory)))
        with (runtime / "hermes-import-contract.json").open(encoding="utf-8") as stream:
            contract = json.load(stream)
        if contract["source_commit"] != COMMIT or contract["schema"] != SCHEMA:
            raise ValueError("import_contract_identity")
        report["stage"] = "distribution_metadata"
        save(report)
        for name, expected in contract["distributions"].items():
            distribution = importlib.metadata.distribution(name)
            location = Path(distribution.locate_file("")).resolve()
            if not location.is_relative_to(runtime) or distribution.version != expected:
                raise ValueError("distribution_identity")
            report["distributions"][name] = distribution.version
        report["stage"] = "run_agent_import"
        save(report)
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            sys.setprofile(budget)
            try:
                module = importlib.import_module("run_agent")
            finally:
                sys.setprofile(None)
        if time.monotonic() >= deadline:
            raise TimeoutError("import_budget")
        report["stage"] = "class_and_origin"
        origin = Path(vars(module).get("__file__", "")).resolve()
        factory = vars(module).get("AIAgent")
        if not class_matches(factory, origin, runtime / "hermes" / "run_agent.py"):
            raise ValueError("class_identity")
        report["module_origin"] = origin.relative_to(runtime).as_posix()
        report["class_verified"] = True
        for loaded in tuple(sys.modules.values()):
            file = vars(loaded).get("__file__") if loaded is not None else None
            if file and not Path(file).resolve().is_relative_to(runtime):
                report["outside_runtime_modules"] += 1
        if report["outside_runtime_modules"] or sink.overflow:
            raise ValueError("import_evidence_incomplete")
        report["stage"] = "import_complete"
        report["status"] = "import_completed"
        return 0
    except Exception as error:
        report["status"] = "import_failed"
        report["reason_type"] = type(error).__name__
        name = getattr(error, "name", "")
        if isinstance(error, ModuleNotFoundError) and isinstance(name, str) and len(name) <= 100 and all(x.isalnum() or x in "._" for x in name):
            report["missing_module"] = name
        return 4
    finally:
        sys.setprofile(None)
        report["captured_output_bytes"] = sink.count
        report["output_overflow"] = sink.overflow
        for handle in reversed(handles):
            handle.close()
        save(report)


if __name__ == "__main__":
    raise SystemExit(main())
