"""Native AIAgent worker, staged read-only and launched only by the LPAC helper."""

import contextlib
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import sys
from urllib.request import Request, build_opener, ProxyHandler


def require_lpac() -> None:
    if os.name != "nt":
        raise RuntimeError("worker.windows_required")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    advapi.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                       ctypes.POINTER(wintypes.HANDLE)]
    advapi.GetTokenInformation.argtypes = [wintypes.HANDLE, ctypes.c_int,
        ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    advapi.DuplicateToken.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.POINTER(wintypes.HANDLE)]
    advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.DWORD)]
    advapi.ConvertSidToStringSidW.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
    class Mapping(ctypes.Structure):
        _fields_ = [("read", wintypes.DWORD), ("write", wintypes.DWORD),
                    ("execute", wintypes.DWORD), ("all", wintypes.DWORD)]
    advapi.AccessCheck.argtypes = [ctypes.c_void_p, wintypes.HANDLE, wintypes.DWORD,
        ctypes.POINTER(Mapping), ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.BOOL)]
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    token, duplicate, needed = wintypes.HANDLE(), wintypes.HANDLE(), wintypes.DWORD()
    if not advapi.OpenProcessToken(kernel.GetCurrentProcess(), 10, ctypes.byref(token)):
        raise RuntimeError("worker.token_unavailable")
    try:
        value = wintypes.DWORD()
        if (not advapi.GetTokenInformation(token, 29, ctypes.byref(value),
                ctypes.sizeof(value), ctypes.byref(needed)) or value.value != 1):
            raise RuntimeError("worker.appcontainer_required")
        def sid_text(kind):
            memory = ctypes.create_string_buffer(256)
            if not advapi.GetTokenInformation(token, kind, memory, 256, ctypes.byref(needed)):
                raise RuntimeError("worker.token_query_failed")
            text = ctypes.c_void_p()
            if not advapi.ConvertSidToStringSidW(ctypes.c_void_p.from_buffer(memory), ctypes.byref(text)):
                raise RuntimeError("worker.sid_query_failed")
            try:
                return ctypes.wstring_at(text)
            finally:
                if kernel.LocalFree(text):
                    raise RuntimeError("worker.sid_cleanup_failed")
        package, user, integrity = sid_text(31), sid_text(1), sid_text(25)
        if integrity != "S-1-16-4096":
            raise RuntimeError("worker.low_integrity_required")
        if not advapi.DuplicateToken(token, 2, ctypes.byref(duplicate)):
            raise RuntimeError("worker.duplicate_token_failed")
        def probe(grant):
            sddl = f"O:BAG:BAD:P(A;;0x1;;;{user})"
            if grant is not None:
                sddl += f"(A;;0x1;;;{grant})"
            descriptor = ctypes.c_void_p()
            size, length = wintypes.DWORD(), wintypes.DWORD(256)
            granted, allowed = wintypes.DWORD(), wintypes.BOOL()
            privileges = ctypes.create_string_buffer(256)
            mapping = Mapping(1, 2, 4, 7)
            if not advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW(
                    sddl, 1, ctypes.byref(descriptor), ctypes.byref(size)):
                raise RuntimeError("worker.probe_descriptor_failed")
            try:
                if not advapi.AccessCheck(descriptor, duplicate, 1, ctypes.byref(mapping),
                        privileges, ctypes.byref(length), ctypes.byref(granted), ctypes.byref(allowed)):
                    raise RuntimeError("worker.probe_api_failed")
                if length.value > 256 or granted.value != (1 if allowed.value else 0):
                    raise RuntimeError("worker.probe_result_failed")
                return bool(allowed.value)
            finally:
                if kernel.LocalFree(descriptor):
                    raise RuntimeError("worker.descriptor_cleanup_failed")
        wrong = "S-1-15-2-987654321-987654321-987654321-987654321-987654321-987654321-987654321"
        if not probe(package) or probe("S-1-15-2-1") or probe(wrong) or probe(None):
            raise RuntimeError("worker.lpac_behavior_required")
    finally:
        duplicate_closed = not duplicate.value or kernel.CloseHandle(duplicate)
        token_closed = kernel.CloseHandle(token)
        if not duplicate_closed or not token_closed:
            raise RuntimeError("worker.token_cleanup_failed")


def main() -> int:
    raw_output = sys.stdout
    stage = "admission"
    try:
        require_lpac()
        runtime = Path(__file__).resolve().parent
        sys.path[:0] = [str(runtime / "hermes"), str(runtime / "dependencies")]
        # -S avoids ambient .pth execution. The curated pywin32 DLL directory is
        # explicitly selected rather than activating a developer environment.
        dll_handles = []
        for folder in ("pywin32_system32", "win32", "win32/lib"):
            path = runtime / "dependencies" / folder
            if path.is_dir():
                sys.path.append(str(path))
                if folder == "pywin32_system32":
                    dll_handles.append(os.add_dll_directory(str(path)))
        raw = sys.stdin.readline(65537)
        if len(raw) > 65536:
            raise RuntimeError("worker.admission_too_large")
        admission = json.loads(raw)
        if set(admission) != {"token", "port", "input", "session_id"}:
            raise RuntimeError("worker.invalid_admission")
        port = admission["port"]
        if type(port) is not int or not 1024 <= port <= 65535:
            raise RuntimeError("worker.invalid_port")
        base_url = f"http://127.0.0.1:{port}"
        opener = build_opener(ProxyHandler({}))
        def broker(route, body):
            request = Request(base_url + route, data=json.dumps(body).encode(), headers={
                "Authorization": "Bearer " + admission["token"],
                "Content-Type": "application/json",
            })
            with opener.open(request, timeout=10) as response:
                return json.load(response)

        # The worker's console is private captured IPC. Only the final protocol
        # record uses stdout; native logs and construction prints are discarded.
        with contextlib.redirect_stdout(sys.stderr):
            stage = "native_import"
            import run_agent
            from hermes_state import SessionDB
            from agent.memory_provider import MemoryProvider
            from tools.registry import registry
            origin = Path(run_agent.__file__).resolve()
            if origin != (runtime / "hermes" / "run_agent.py").resolve():
                raise RuntimeError("worker.wrong_runtime_origin")
            class SMBProvider(MemoryProvider):
                @property
                def name(self):
                    return "maya_gate_a"
                def is_available(self):
                    return True
                def initialize(self, session_id, **kwargs):
                    return
                def prefetch(self, query, *, session_id=""):
                    result = broker("/maya/memory/search", {"memory_id": "smb-1", "query": query})
                    return json.dumps(result)
                def get_tool_schemas(self):
                    return []
                def handle_tool_call(self, tool_name, arguments):
                    raise RuntimeError("worker.unsupported_memory_tool")
                def shutdown(self):
                    return

            def read_document(arguments, **kwargs):
                if arguments != {"document_id": "doc-1"}:
                    raise RuntimeError("worker.invalid_document")
                return json.dumps(broker("/maya/document/read", arguments))
            registry.register(name="maya_document_read", toolset="maya_gate_a", schema={
                "name": "maya_document_read", "description": "Read the approved synthetic document.",
                "parameters": {"type": "object", "properties": {
                    "document_id": {"type": "string", "enum": ["doc-1"]}},
                    "required": ["document_id"], "additionalProperties": False},
            }, handler=read_document, check_fn=lambda: True)
            stage = "native_construction"
            database = SessionDB(Path(os.environ["HERMES_HOME"]) / "state.db")
            history = database.get_messages_as_conversation(admission["session_id"])
            agent = run_agent.AIAgent(model="gpt-6-luna", provider="openai",
                base_url=base_url + "/v1", api_key=admission["token"],
                api_mode="codex_responses", enabled_toolsets=["maya_gate_a", "memory"],
                max_iterations=3, quiet_mode=True, session_id=admission["session_id"],
                save_trajectories=False, session_db=database)
            try:
                if agent._memory_manager is None or agent._memory_store is None:
                    raise RuntimeError("worker.native_memory_missing")
                agent._memory_manager.add_provider(SMBProvider())
                if agent._memory_manager.get_provider("maya_gate_a") is None:
                    raise RuntimeError("worker.provider_missing")
                stage = "native_memory"
                agent._memory_store.add("memory", "Gate A uses synthetic business records.")
                agent._memory_store.add("user", "The test operator prefers concise answers.")
                stage = "native_loop"
                result = agent.run_conversation(admission["input"], conversation_history=history)
            finally:
                agent.close()
                database.close()
        raw_output.write(json.dumps({"status": "native_completed", "result": result,
                                     "origin": "hermes/run_agent.py"}, allow_nan=False) + "\n")
        raw_output.flush()
        return 0
    except Exception:
        raw_output.write(json.dumps({"status": "blocked", "reason_code": "worker.execution_failed",
                                     "stage": stage}) + "\n")
        raw_output.flush()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
