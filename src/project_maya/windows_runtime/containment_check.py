"""Fixed synthetic probes for Maya's consented containment screen, never a runner."""

import ctypes
from ctypes import wintypes as w
import json
import os
import socket
import sys
import time

SCHEMA = "maya.protected_python.screen.v1"
LIMIT = 65536


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_key")
        result[key] = value
    return result


def read_plan(nonce):
    with open("screen-plan.json", "rb") as stream:
        data = stream.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise ValueError("plan_size")
    plan = json.loads(data, object_pairs_hook=unique)
    if plan["schema"] != SCHEMA or plan["nonce"] != nonce:
        raise ValueError("plan_identity")
    return plan


class Probes:
    def __init__(self, plan):
        self.plan = plan
        self.rows = []
        self.udp = []
        self.deadline = time.monotonic() + 22
        self.k = ctypes.WinDLL("kernel32", use_last_error=True)
        self.a = ctypes.WinDLL("advapi32", use_last_error=True)
        signatures = {
            "CreateFileW": (w.HANDLE, [w.LPCWSTR, w.DWORD, w.DWORD, w.LPVOID, w.DWORD, w.DWORD, w.HANDLE]),
            "CloseHandle": (w.BOOL, [w.HANDLE]),
            "DeleteFileW": (w.BOOL, [w.LPCWSTR]),
            "ReadFile": (w.BOOL, [w.HANDLE, w.LPVOID, w.DWORD, ctypes.POINTER(w.DWORD), w.LPVOID]),
            "WriteFile": (w.BOOL, [w.HANDLE, w.LPVOID, w.DWORD, ctypes.POINTER(w.DWORD), w.LPVOID]),
            "OpenProcess": (w.HANDLE, [w.DWORD, w.BOOL, w.DWORD]),
            "OpenFileMappingW": (w.HANDLE, [w.DWORD, w.BOOL, w.LPCWSTR]),
            "GetStdHandle": (w.HANDLE, [w.DWORD]),
            "GetHandleInformation": (w.BOOL, [w.HANDLE, ctypes.POINTER(w.DWORD)]),
            "GetFileType": (w.DWORD, [w.HANDLE]),
        }
        for name, (result, args) in signatures.items():
            method = getattr(self.k, name)
            method.restype, method.argtypes = result, args
        self.a.OpenProcessToken.argtypes = [w.HANDLE, w.DWORD, ctypes.POINTER(w.HANDLE)]
        self.a.OpenProcessToken.restype = w.BOOL
        self.a.GetTokenInformation.argtypes = [w.HANDLE, ctypes.c_int, w.LPVOID, w.DWORD, ctypes.POINTER(w.DWORD)]
        self.a.GetTokenInformation.restype = w.BOOL
        self.a.GetFileSecurityW.argtypes = [w.LPCWSTR, w.DWORD, w.LPVOID, w.DWORD, ctypes.POINTER(w.DWORD)]
        self.a.GetFileSecurityW.restype = w.BOOL
        self.k.GetCurrentProcess.restype = w.HANDLE

    def file(self, path, operation):
        if operation == "delete":
            ok = bool(self.k.DeleteFileW(path))
            return ok, 0 if ok else ctypes.get_last_error(), 0
        access = 0x80000000 if operation == "read" else 0x40000000
        handle = self.k.CreateFileW(path, access, 7, None, 1 if operation == "create" else 3, 0, None)
        if handle == ctypes.c_void_p(-1).value:
            return False, ctypes.get_last_error(), 0
        try:
            data = ctypes.create_string_buffer(128)
            count = w.DWORD()
            if operation == "read":
                ok = self.k.ReadFile(handle, data, 128, ctypes.byref(count), None)
            else:
                data.value = self.plan["nonce"].encode("ascii")
                ok = self.k.WriteFile(handle, data, 32, ctypes.byref(count), None)
            # Obtaining the requested protected file handle is itself unauthorized.
            return True, 0 if ok else ctypes.get_last_error(), count.value
        finally:
            self.k.CloseHandle(handle)

    def one(self, identifier, action, allowed=False):
        if os.path.exists("screen-stop.txt"):
            raise RuntimeError("host_observed_unauthorized_effect")
        if time.monotonic() >= self.deadline:
            raise TimeoutError("screen_budget")
        try:
            success, error, count = action()
            outcome = ("allowed" if allowed and success else "effect" if success else
                       "inconclusive" if not allowed and error == 0 else "denied")
            row = {"id": identifier, "outcome": outcome, "error": error, "bytes": count}
        except (OSError, ValueError) as error:
            row = {"id": identifier, "outcome": "inconclusive", "error": getattr(error, "winerror", None) or 0, "bytes": 0}
        self.rows.append(row)
        self.save()
        if row["outcome"] == "effect":
            raise RuntimeError("unauthorized_effect")

    def save(self):
        data = json.dumps({"schema": SCHEMA, "nonce": self.plan["nonce"], "rows": self.rows, "udp": self.udp},
                          separators=(",", ":"), ensure_ascii=True).encode("ascii")
        if len(data) > LIMIT:
            raise ValueError("report_size")
        # Only this bounded file is child-written; the host treats it as untrusted.
        with open("screen-result.json", "wb") as stream:
            if stream.write(data) != len(data):
                raise OSError("short_report_write")

    def private_io(self):
        name = "private-control.txt"
        with open(name, "xb") as stream:
            stream.write(b"one")
        with open(name, "r+b") as stream:
            if stream.read() != b"one":
                return False, 0, 0
            stream.seek(0)
            stream.write(b"two")
        with open(name, "rb") as stream:
            match = stream.read() == b"two"
        os.unlink(name)
        return match and not os.path.exists(name), 0, 3

    def public_read(self):
        with open(self.plan["public"], "rb") as stream:
            data = stream.read(129)
        return data == self.plan["nonce"].encode("ascii"), 0, len(data)

    def network(self, family, kind, operation):
        if kind == socket.SOCK_DGRAM:
            return self.udp_network(family, operation)
        address = "127.0.0.1" if family == 4 else "::1"
        key = str(family) + ("tcp" if kind == socket.SOCK_STREAM else "udp")
        with socket.socket(socket.AF_INET if family == 4 else socket.AF_INET6, kind) as stream:
            stream.settimeout(.25)
            try:
                if operation == "connect":
                    stream.connect((address, self.plan["ports"][key]))
                    try:
                        stream.send(("child:" + self.plan["nonce"]).encode("ascii"))
                    except OSError:
                        if kind == socket.SOCK_STREAM:
                            return True, 0, 0
                        raise
                    # Socket success alone for UDP is not proof of transmission.
                    return (kind == socket.SOCK_STREAM), 0, 0
                stream.bind((address, 0))
                if kind == socket.SOCK_STREAM:
                    stream.listen(1)
                # Binding alone is not treated as an unauthorized external effect.
                return False, 0, 0
            except OSError as error:
                return False, getattr(error, "winerror", None) or error.errno or 0, 0

    def udp_network(self, family, operation):
        address = "127.0.0.1" if family == 4 else "::1"
        detail = {"id": "C05." + str(family) + "udp." + operation,
                  "local_port": 0, "remote_port": self.plan["ports"][str(family) + "udp"],
                  "sent_bytes": 0, "received_bytes": 0, "bind_error": 0}
        self.udp.append(detail)
        with socket.socket(socket.AF_INET if family == 4 else socket.AF_INET6,
                           socket.SOCK_DGRAM) as stream:
            stream.settimeout(.75)
            try:
                stream.bind((address, 0))
            except OSError as error:
                detail["bind_error"] = getattr(error, "winerror", None) or error.errno or 0
                return False, 0, 0  # Bind denial does not exercise packet authorization.
            detail["local_port"] = stream.getsockname()[1]
            try:
                if operation == "send":
                    message = ("child:" + self.plan["nonce"]).encode("ascii")
                    detail["sent_bytes"] = stream.sendto(message, (address, detail["remote_port"]))
                    return False, 0, detail["sent_bytes"]
                # Only a nonce-bound port request, never an address or arbitrary payload.
                with open("udp" + str(family) + "-request.txt", "xb") as request:
                    request.write((self.plan["nonce"] + ":" + str(detail["local_port"])).encode("ascii"))
                data, source = stream.recvfrom(128)
                detail["received_bytes"] = len(data)
                # Any received packet is an effect, not just the expected challenge.
                return True, 0, len(data)
            except OSError as error:
                return False, getattr(error, "winerror", None) or error.errno or 0, 0

    def process_access(self):
        handle = self.k.OpenProcess(0x2A, False, self.plan["host_pid"])
        error = ctypes.get_last_error()
        if handle:
            self.k.CloseHandle(handle)
        return bool(handle), 0 if handle else error, 0

    def host_token(self):
        process = self.k.OpenProcess(0x1000, False, self.plan["host_pid"])
        if not process:
            return False, ctypes.get_last_error(), 0
        try:
            token = w.HANDLE()
            ok = self.a.OpenProcessToken(process, 0x22, ctypes.byref(token))
            error = ctypes.get_last_error()
            if ok:
                self.k.CloseHandle(token)
            return bool(ok), 0 if ok else error, 0
        finally:
            self.k.CloseHandle(process)

    def own_token(self):
        token = w.HANDLE()
        if not self.a.OpenProcessToken(self.k.GetCurrentProcess(), 8, ctypes.byref(token)):
            return False, ctypes.get_last_error(), 0
        try:
            for info, expected in ((20, 0), (29, 1), (30, 0)):
                length = 4  # TOKEN_ELEVATION and TokenIsAppContainer are DWORDs.
                if info == 30:
                    needed = w.DWORD()
                    ok = self.a.GetTokenInformation(token, info, None, 0, ctypes.byref(needed))
                    error = 0 if ok else ctypes.get_last_error()
                    if ok or error != 122:
                        return False, error, 0
                    if not 4 <= needed.value <= 4096:
                        return False, 0, 0
                    length = needed.value
                data = ctypes.create_string_buffer(length)
                size = w.DWORD()
                if not self.a.GetTokenInformation(token, info, data, length, ctypes.byref(size)):
                    return False, ctypes.get_last_error(), 0
                if (info != 30 and size.value != 4) or (info == 30 and not 4 <= size.value <= length):
                    return False, 0, 0
                if int.from_bytes(data.raw[:4], "little") != expected:
                    return False, 0, 0
            return True, 0, 0
        finally:
            self.k.CloseHandle(token)

    def spawn(self):
        # Never use a shell, search PATH, or run caller-selected code.
        import subprocess
        try:
            process = subprocess.Popen([sys.executable, "-I", "-S", "-B", "-c", "pass"],
                                       close_fds=True)
        except OSError as error:
            return False, getattr(error, "winerror", None) or 0, 0
        # A returned process handle already proves the forbidden spawn succeeded.
        process.poll()
        return True, 0, 0

    def mapping(self):
        handle = self.k.OpenFileMappingW(4, False, self.plan["mapping"])
        error = ctypes.get_last_error()
        if handle:
            self.k.CloseHandle(handle)
        return bool(handle), 0 if handle else error, 0

    def handles(self):
        actual = [int(self.k.GetStdHandle(code)) for code in (0xfffffff6, 0xfffffff5, 0xfffffff4)]
        flags = w.DWORD()
        valid = actual == self.plan["handles"] and len(set(actual)) == 3
        for handle in actual:
            valid = valid and bool(self.k.GetHandleInformation(handle, ctypes.byref(flags)))
            valid = valid and bool(flags.value & 1) and self.k.GetFileType(handle) == 3
        return valid, 0, 0

    def metadata(self):
        # Metadata only, on this exact small root set; no recursion or content reads.
        roots = [self.plan["runtime"], os.environ["SYSTEMROOT"] + "\\System32"]
        total = 0
        for path in roots:
            data = ctypes.create_string_buffer(65536)
            needed = w.DWORD()
            if not self.a.GetFileSecurityW(path, 4, data, len(data), ctypes.byref(needed)):
                return False, ctypes.get_last_error(), 0
            total += needed.value
        return True, 0, total

    def run(self):
        self.one("C01.private", self.private_io, True)
        self.one("C01.runtime_write", lambda: self.file(self.plan["runtime_canary"], "write"))
        for name in ("document", "memory", "business", "policy", "audit", "secret"):
            path = self.plan["protected"][name]
            for operation in ("read", "write", "create", "delete"):
                target = path + ".new" if operation == "create" else path
                self.one("C02." + name + "." + operation,
                         lambda target=target, operation=operation: self.file(target, operation))
        self.one("C03.public", self.public_read, True)
        self.one("C03.metadata", self.metadata, True)
        for name, target in self.plan["routes"].items():
            self.one("C04." + name, lambda target=target: self.file(target, "read"))
        for family in (4, 6):
            for kind in (socket.SOCK_STREAM, socket.SOCK_DGRAM):
                for operation in (("connect", "bind") if kind == socket.SOCK_STREAM else ("send", "receive")):
                    name = str(family) + ("tcp" if kind == socket.SOCK_STREAM else "udp")
                    self.one("C05." + name + "." + operation,
                             lambda family=family, kind=kind, operation=operation: self.network(family, kind, operation))
        self.one("C06.token_facts", self.own_token, True)
        self.one("C06.process_access", self.process_access)
        self.one("C06.host_token", self.host_token)
        self.one("C06.spawn", self.spawn)
        self.one("C07.handles", self.handles, True)
        self.one("C07.mapping", self.mapping)


def main():
    if (sys.platform != "win32" or sys.version_info[:3] != (3, 13, 14) or
            not all((sys.flags.isolated, sys.flags.no_site, sys.flags.dont_write_bytecode)) or
            len(sys.argv) != 2 or len(sys.argv[1]) != 32 or
            any(c not in "0123456789abcdef" for c in sys.argv[1])):
        return 2
    nonce = sys.argv[1]
    try:
        probe = Probes(read_plan(nonce))
        # Prove Python entry independently of the containment probe outcome.
        beacon = ("MAYA_PROTECTED_PYTHON_STARTED_V1:" + nonce + "\n").encode("ascii")
        with open("python-startup.txt", "xb") as stream:
            if stream.write(beacon) != len(beacon):
                return 3
        if sys.stdout.buffer.write(beacon) != len(beacon):
            return 3
        sys.stdout.buffer.flush()
        probe.run()
        return 0
    except Exception:
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
