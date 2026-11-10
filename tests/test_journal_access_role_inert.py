"""Injected role adapter tests and cross-language fixture vectors only."""
import ast
import base64
import ctypes
import io
import json
from pathlib import Path, PureWindowsPath
import sys
from types import SimpleNamespace

import pytest

from project_maya.bridge.protocol import ProtocolError, decode, encode
from project_maya.bridge.transport import PrivateChannel
from project_maya.windows_runtime import journal_access_role as role_probe

ATTEMPT, REQUEST = "a" * 32, "b" * 32
CONTROL, CONTROL_DIR, JOURNAL = "c" * 24, "d" * 24, "e" * 24
DIRECTORY = r"C:\ProgramData\MayaProtectedPython-Startup1" + "\\" + ATTEMPT
MASKS = (1, 2, 4, 65536, 262144, 524288, 64, 2)
CASES = ("read_data", "write_data", "append_data", "delete", "write_dacl", "write_owner", "delete_child", "add_file")


def command(role):
    return dict(v=2, type="journal_access_probe", attempt=ATTEMPT, role=role, request_id=REQUEST)


class Api:
    def __init__(self, role, fault=None):
        self.role, self.fault = role, fault
        self.opens = 0
        self.opened, self.queried, self.closed = [], [], []

    def open(self, path, mask, share, disposition, flags):
        index, position = divmod(self.opens, 2)
        self.opens += 1
        root = PureWindowsPath(DIRECTORY)
        control = root / ("host" if self.role == "worker" else "state") / "journal-access-control"
        expected = (control if index >= 6 else control / "control.bin") if position == 0 else (
            root if index >= 6 else root / "final-output-journal.v1.jsonl")
        assert path == str(expected)
        assert (mask, share, disposition, flags) == (MASKS[index], 7, 3, 0x02200000 if index >= 6 else 0x00200000)
        if position == 1 and not (index == 0 and (self.fault or "").startswith("target-open")):
            return -1, {"sharing": 32, "missing": 2, "no-open-error": 0}.get(self.fault, 5) if index == 0 else 5
        self.opened.append(self.opens)
        return self.opens, 0

    def identity(self, handle, directory):
        assert handle in self.opened and handle not in self.queried and directory == (handle >= 13)
        self.queried.append(handle)
        if (handle == 1 and self.fault == "control-identity") or (handle == 2 and self.fault == "target-open-query"):
            return None, 5
        if handle == 2 and self.fault == "target-open-malformed":
            return "invalid", 0
        if handle == 2 and self.fault == "target-open-both":
            raise OSError("fixture only")
        return (JOURNAL if handle == 2 else CONTROL_DIR if directory else CONTROL), 0

    def close(self, handle):
        assert handle in self.queried and handle not in self.closed
        self.closed.append(handle)
        if handle == 2 and self.fault == "target-open-both":
            raise OSError("fixture only")
        return not ((handle == 1 and self.fault == "control-close") or (handle == 2 and self.fault == "target-open-close"))


def run(role, fault=None):
    api = Api(role, fault)
    session = role_probe.ProbeSession(DIRECTORY, ATTEMPT, role, 1234, REQUEST, api)
    reply = session.execute(command(role))
    assert api.opens == 16 and api.opened == api.queried == api.closed
    with pytest.raises(ProtocolError):
        session.execute(command(role))
    assert api.opens == 16
    return reply


@pytest.mark.parametrize("role", ("worker", "child"))
def test_matrix_exact_and_private_frame_round_trip(role):
    source = io.BytesIO(encode(command(role)))
    output = io.BytesIO()
    channel = PrivateChannel(source, output)
    api = Api(role)
    session = role_probe.ProbeSession(DIRECTORY, ATTEMPT, role, 1234, REQUEST, api)
    result = session.execute(channel.receive())
    assert [(r["case"], r["mask"]) for r in result["rows"]] == list(zip(CASES, MASKS))
    channel.send(result)
    raw = output.getvalue()
    assert int.from_bytes(raw[:4], "little") == len(raw) - 4
    assert decode(raw[4:]) == result == run(role)


@pytest.mark.parametrize("fault,identity_error,closed", [
    ("target-open-query", 5, True), ("target-open-malformed", 13, True),
    ("target-open-close", 0, False), ("target-open-both", 31, False),
])
def test_open_result_survives_later_fault(fault, identity_error, closed):
    status = run("worker", fault)["rows"][0]["target"]
    assert status == dict(opened=True, closed=closed, open_error=0,
                          identity=None if identity_error else JOURNAL, identity_error=identity_error)


@pytest.mark.parametrize("change", [None, {"v": 1}, {"v": True}, {"v": 2.0}, {"type": "other"},
                                    {"role": "child"}, {"path": "other"}, {"mask": 1}, {"request_id": "0" * 32}])
def test_bad_command_consumes_session_without_open(change):
    api = Api("worker")
    session = role_probe.ProbeSession(DIRECTORY, ATTEMPT, "worker", 1234, REQUEST, api)
    with pytest.raises(ProtocolError):
        session.execute(None if change is None else dict(command("worker"), **change))
    with pytest.raises(ProtocolError):
        session.execute(command("worker"))
    assert api.opens == 0


@pytest.mark.parametrize("path", ["C:\\other\\" + ATTEMPT, DIRECTORY + "\\..", DIRECTORY + ":stream",
                                  DIRECTORY.replace("C:", ""), "\\\\?\\" + DIRECTORY, DIRECTORY + "\\"])
def test_invalid_attempt_paths_rejected(path):
    with pytest.raises(ProtocolError):
        role_probe.ProbeSession(path, ATTEMPT, "worker", 1234, REQUEST, Api("worker"))


def test_windows_binding_captures_error_at_failed_call_without_retry(monkeypatch):
    events = []

    class Fn:
        def __init__(self, name, result):
            self.name, self.result = name, result

        def __call__(self, *args):
            events.append(self.name)
            if self.name == "open":
                assert args == (DIRECTORY, 1, 7, None, 3, 0x02200000, None)
            return self.result

    class Kernel:
        CreateFileW = Fn("open", role_probe._INVALID_HANDLE)
        GetFileInformationByHandle = Fn("identity", 0)
        CloseHandle = Fn("close", 0)

    def no_dll(*args, **kwargs):
        raise AssertionError("Native DLL must not load in this test")

    def last_error():
        events.append("last_error")
        return 5

    monkeypatch.setattr(ctypes, "WinDLL", no_dll, raising=False)
    calls = role_probe.WindowsCalls(kernel=Kernel(), last_error=last_error)
    assert calls.open(DIRECTORY, 1, 7, 3, 0x02200000) == (role_probe._INVALID_HANDLE, 5)
    assert calls.identity(123, True) == (None, 5)
    assert calls.close(123) is False
    assert events == ["open", "last_error", "identity", "last_error", "close"]


def handshake(role, *, fault=None, raw=None, destination=None, **changes):
    api = Api(role, fault)
    entry = DIRECTORY + "\\runtime\\journal_access_" + role + "_entry.py"
    source = io.BytesIO(encode(command(role)) if raw is None else raw)
    destination = io.BytesIO() if destination is None else destination
    factories = []

    def backend():
        assert source.tell() == len(source.getvalue())
        factories.append(True)
        return api

    values = dict(platform="win32", version=(3, 13, 14),
                  flags=SimpleNamespace(isolated=1, no_site=1, dont_write_bytecode=1),
                  argv=[entry, ATTEMPT], entry_path=entry,
                  cwd=DIRECTORY + ("\\host" if role == "worker" else "\\state"), pid=1234,
                  source=source, destination=destination, backend_factory=backend)
    result = role_probe.serve_entry(role, **dict(values, **changes))
    return result, destination.getvalue(), factories, api


@pytest.mark.parametrize("role", ("worker", "child"))
def test_handshake_accepts_one_fresh_challenge(role):
    fresh = "9" * 32
    code, frame, factories, api = handshake(role, raw=encode(dict(command(role), request_id=fresh)))
    assert code == 0 and factories == [True] and api.opens == 16
    assert api.opened == api.queried == api.closed
    assert int.from_bytes(frame[:4], "little") == len(frame) - 4
    reply = decode(frame[4:])
    assert reply == dict(run(role), request_id=fresh)


@pytest.mark.parametrize("changes", [
    {"platform": "linux"}, {"version": (3, 13, 13)},
    {"flags": SimpleNamespace(isolated=0, no_site=1, dont_write_bytecode=1)},
    {"flags": SimpleNamespace(isolated=1, no_site=0, dont_write_bytecode=1)},
    {"flags": SimpleNamespace(isolated=1, no_site=1, dont_write_bytecode=0)},
    {"argv": []}, {"argv": ["wrong", ATTEMPT]}, {"argv": ["wrong", ATTEMPT, "extra"]},
    {"entry_path": DIRECTORY + "\\runtime\\journal_access_child_entry.py"},
    {"entry_path": DIRECTORY + "\\other\\journal_access_worker_entry.py"},
    {"cwd": DIRECTORY + "\\state"}, {"pid": True},
])
def test_handshake_preflight_does_not_construct_backend(changes):
    code, frame, factories, api = handshake("worker", **changes)
    assert code == 2 and frame == b"" and not factories and api.opens == 0


@pytest.mark.parametrize("raw", [b"", b"\xff\xff\xff\x7f", encode(command("worker"))[:-1],
    encode(command("worker")) + b"\x01", encode(command("worker")) * 2, encode(command("child")),
    encode(dict(command("worker"), request_id="not-hex")), encode(dict(command("worker"), path="other"))])
def test_handshake_rejects_bad_or_trailing_input_before_opens(raw):
    code, frame, factories, api = handshake("worker", raw=raw)
    assert code == 2 and frame == b"" and not factories and api.opens == 0


def test_handshake_requires_actual_eof_and_never_retries_output():
    class NoEof(io.BytesIO):
        def read(self, count=-1):
            return super().read(count) or None

    code, frame, factories, api = handshake("worker", source=NoEof(encode(command("worker"))))
    assert code == 2 and frame == b"" and not factories and api.opens == 0

    class ShortWrite(io.BytesIO):
        writes = 0
        def write(self, data):
            self.writes += 1
            return super().write(data[:-1])

    output = ShortWrite()
    code, _, factories, api = handshake("worker", destination=output)
    assert code == 2 and factories == [True] and api.opens == 16 and output.writes == 1


@pytest.mark.parametrize("role", ("worker", "child"))
def test_root_wrappers_bind_literal_role_and_fixed_helper_without_execution(role):
    source = Path(role_probe.__file__).with_name(f"journal_access_{role}_entry.py")
    tree = ast.parse(source.read_bytes())
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
    serve = [n for n in calls if n.func.attr == "serve_entry"]
    assert len(serve) == 1 and isinstance(serve[0].args[0], ast.Constant) and serve[0].args[0].value == role
    load = [n for n in calls if n.func.attr == "spec_from_file_location"]
    assert len(load) == 1 and load[0].args[1].right.value == "journal_access_role.py"
    assert all(n.func.attr not in {"WinDLL", "CreateFileW", "resolve"} for n in calls)


def write_vectors(path):
    vectors = []
    for role in ("worker", "child"):
        for fault in (None, "sharing", "missing", "no-open-error", "control-identity", "control-close",
                      "target-open-query", "target-open-malformed", "target-open-close", "target-open-both"):
            first = "denied" if fault is None else "forbidden_open" if fault.startswith("target-open") else "incomplete"
            result = [CASES[0] + ":" + first, *(case + ":denied" for case in CASES[1:])]
            code, frame, factories, api = handshake(role, fault=fault)
            assert code == 0 and factories == [True] and api.opens == 16
            assert api.opened == api.queried == api.closed
            vectors.append(dict(role=role, frame=base64.b64encode(frame).decode("ascii"), expected=result))
    Path(path).write_text(json.dumps(vectors, separators=(",", ":")), encoding="ascii")


if __name__ == "__main__":
    write_vectors(sys.argv[1])
