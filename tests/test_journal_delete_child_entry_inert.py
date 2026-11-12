import io
from pathlib import PureWindowsPath

import pytest

from project_maya.bridge.protocol import encode
from project_maya.bridge.transport import PrivateChannel
from project_maya.windows_runtime import journal_access_role, journal_delete_child_entry


@pytest.mark.parametrize("fault", [None, "extra_frame", "wrong_attempt", "extra_field", "wrong_cwd"])
def test_fixed_request(monkeypatch, fault):
    monkeypatch.setitem(__import__("sys").modules, "journal_access_role", journal_access_role)
    attempt, request = "a" * 32, "b" * 32
    root = PureWindowsPath(r"C:\ProgramData\MayaProtectedPython-Startup1") / attempt
    entry = str(root / "runtime" / "journal_delete_child_entry.py")
    cwd = root / ("host" if fault == "wrong_cwd" else "state")
    command = dict(v=1, type="delete_child_probe", attempt=attempt, request_id=request)
    if fault == "wrong_attempt":
        command["attempt"] = "c" * 32
    if fault == "extra_field":
        command["path"] = str(root)
    frame = encode(command)
    source, output = io.BytesIO(frame * (2 if fault == "extra_frame" else 1)), io.BytesIO()
    calls = []

    class Backend:
        def open(self, path, mask, share, disposition, flags):
            assert (mask, share, disposition, flags) == (64, 7, 3, 0x02200000)
            calls.append(path)
            return (1, 0) if len(calls) == 1 else (-1, 5)

        def identity(self, handle, directory):
            assert handle == 1 and directory
            return "d" * 24, 0

        def close(self, handle):
            assert handle == 1
            return True

    result = journal_delete_child_entry.serve([entry, attempt], entry, str(cwd), 10, source, output, Backend)
    if fault:
        assert result == 2 and not calls and not output.getvalue()
        return
    assert result == 0
    assert calls == [str(root / "state" / "delete-child-control"), str(root)]
    output.seek(0)
    reply = PrivateChannel(output, io.BytesIO()).receive()
    assert (reply["type"], reply["pid"], reply["attempt"], reply["request_id"]) == (
        "delete_child_result", 10, attempt, request)
    assert reply["control"]["closed"] and reply["target"]["open_error"] == 5
    assert output.read() == b""
