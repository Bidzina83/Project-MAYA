"""Disconnected role-side v2 access probe. No entry point or native call at import."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from pathlib import PureWindowsPath
import re
from threading import Lock

from project_maya.bridge.protocol import ProtocolError, encode
from project_maya.bridge.transport import PrivateChannel


_CASES = (
    ("read_data", 1), ("write_data", 2), ("append_data", 4), ("delete", 65536),
    ("write_dacl", 262144), ("write_owner", 524288), ("delete_child", 64), ("add_file", 2),
)
_INVALID_HANDLE = ctypes.c_void_p(-1).value
_KEYS = {"v", "type", "attempt", "role", "request_id"}


def _hex(value, length):
    return type(value) is str and len(value) == length and re.fullmatch(r"[0-9a-f]+", value) is not None


def _error(value):
    return value if type(value) is int and 1 <= value <= 65535 else 31


def _status(opened, closed=False, open_error=0, identity=None, identity_error=0):
    return dict(opened=opened, closed=closed, open_error=open_error, identity=identity,
                identity_error=identity_error)


def _attempt_path(directory, attempt):
    if type(directory) is not str or not _hex(attempt, 32):
        raise ProtocolError()
    path = PureWindowsPath(directory)
    if (not re.fullmatch(r"[A-Za-z]:", path.drive) or not path.is_absolute()
            or str(path) != directory or path.name != attempt
            or path.parent.name != "MayaProtectedPython-Startup1"
            or any(part in (".", "..") or part.endswith((".", " "))
                   or any(c in part for c in ':*?"<>|\x00\r\n') for part in path.parts[1:])):
        raise ProtocolError()
    return path


def _challenge(command, attempt, role):
    if (type(command) is not dict or set(command) != _KEYS or type(command["v"]) is not int
            or command["v"] != 2 or command["type"] != "journal_access_probe"
            or command["attempt"] != attempt or command["role"] != role
            or not _hex(command["request_id"], 32)):
        raise ProtocolError()
    return command["request_id"]


class ProbeSession:
    """Trusted caller binds the admitted attempt directory, role and challenge.

    The future launcher must verify the physical paths and real role token. This
    module does not resolve paths on disk or assert authority from role input.
    """

    def __init__(self, directory, attempt, role, pid, request_id, calls):
        if (type(role) is not str or role not in ("worker", "child")
                or type(pid) is not int or not 0 < pid <= 2147483647
                or not _hex(request_id, 32) or calls is None):
            raise ProtocolError()
        path = _attempt_path(directory, attempt)
        self._path, self._attempt, self._role = path, attempt, role
        self._pid, self._request, self._calls = pid, request_id, calls
        self._lock, self._used = Lock(), False

    def _probe(self, path, mask, directory):
        flags = 0x00200000 | (0x02000000 if directory else 0)
        handle, error = self._calls.open(str(path), mask, 7, 3, flags)
        if handle in (None, 0, -1, _INVALID_HANDLE):
            return _status(False, open_error=_error(error))

        identity, identity_error, closed = None, 0, False
        try:
            observed, error = self._calls.identity(handle, directory)
            if type(error) is int and error == 0 and _hex(observed, 24):
                identity = observed
            else:
                identity_error = 13 if type(error) is int and error == 0 else _error(error)
        except Exception:
            identity_error = 31
        finally:
            try:
                closed = self._calls.close(handle) is True
            except Exception:
                closed = False
        return _status(True, closed, identity=identity, identity_error=identity_error)

    def execute(self, command):
        with self._lock:
            if self._used:
                raise ProtocolError()
            self._used = True
        if _challenge(command, self._attempt, self._role) != self._request:
            raise ProtocolError()
        control_dir = self._path / ("host" if self._role == "worker" else "state") / "journal-access-control"
        rows = []
        for index, (case, mask) in enumerate(_CASES):
            directory = index >= 6
            control = control_dir if directory else control_dir / "control.bin"
            target = self._path if directory else self._path / "final-output-journal.v1.jsonl"
            rows.append(dict(case=case, mask=mask, control=self._probe(control, mask, directory),
                             target=self._probe(target, mask, directory)))
        reply = dict(v=2, type="journal_access_result", attempt=self._attempt, role=self._role,
                     pid=self._pid, request_id=self._request, rows=rows)
        encode(reply)  # Enforce the same frame limit before returning to the caller.
        return reply


class _Information(ctypes.Structure):
    _fields_ = [("attributes", wintypes.DWORD), ("created", wintypes.FILETIME),
                ("accessed", wintypes.FILETIME), ("written", wintypes.FILETIME),
                ("volume", wintypes.DWORD), ("size_high", wintypes.DWORD),
                ("size_low", wintypes.DWORD), ("links", wintypes.DWORD),
                ("index_high", wintypes.DWORD), ("index_low", wintypes.DWORD)]


class WindowsCalls:
    """Not constructed by the fixture except with an injected kernel and error reader."""

    def __init__(self, *, kernel=None, last_error=None):
        if kernel is None:
            if os.name != "nt" or last_error is not None:
                raise ProtocolError()
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            last_error = ctypes.get_last_error
        if not callable(last_error):
            raise ProtocolError()
        self._kernel, self._last_error = kernel, last_error
        kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                       ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        kernel.CreateFileW.restype = wintypes.HANDLE
        kernel.GetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.POINTER(_Information)]
        kernel.GetFileInformationByHandle.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL

    def open(self, path, mask, share, disposition, flags):
        handle = self._kernel.CreateFileW(path, mask, share, None, disposition, flags, None)
        error = self._last_error() if handle == _INVALID_HANDLE else 0
        return handle, error

    def identity(self, handle, directory):
        info = _Information()
        if not self._kernel.GetFileInformationByHandle(handle, ctypes.byref(info)):
            return None, self._last_error()
        if bool(info.attributes & 16) != directory or info.attributes & 1024 or not directory and info.links != 1:
            return None, 13
        return f"{info.volume:08x}{info.index_high:08x}{info.index_low:08x}", 0

    def close(self, handle):
        return bool(self._kernel.CloseHandle(handle))


def serve_entry(role, *, platform, version, flags, argv, entry_path, cwd, pid,
                source, destination, backend_factory=WindowsCalls):
    """Fixed wrapper handshake. The coordinator owns I/O deadlines and EOF."""
    try:
        if (role not in ("worker", "child") or platform != "win32" or tuple(version[:3]) != (3, 13, 14)
                or not all((flags.isolated, flags.no_site, flags.dont_write_bytecode))
                or len(argv) != 2 or not _hex(argv[1], 32) or type(pid) is not int or not 0 < pid <= 2147483647):
            raise ProtocolError()
        entry = PureWindowsPath(entry_path)
        if (str(entry) != entry_path or PureWindowsPath(argv[0]) != entry
                or entry.name != "journal_access_" + role + "_entry.py" or entry.parent.name != "runtime"):
            raise ProtocolError()
        attempt = argv[1]
        directory = _attempt_path(str(entry.parent.parent), attempt)
        if PureWindowsPath(cwd) != directory / ("host" if role == "worker" else "state"):
            raise ProtocolError()
        channel = PrivateChannel(source, destination)
        command = channel.receive()
        request = _challenge(command, attempt, role)
        if source.read(1) != b"":
            raise ProtocolError()
        session = ProbeSession(str(directory), attempt, role, pid, request, backend_factory())
        channel.send(session.execute(command))
        return 0
    except Exception:
        return 2
