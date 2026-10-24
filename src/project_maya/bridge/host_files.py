"""Windows host-only handles. Never accept a runtime-provided path."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import os
from pathlib import Path
from typing import BinaryIO


class HostFileError(OSError):
    def __init__(self) -> None:
        super().__init__("bridge.host_file_rejected")


class _Information(ctypes.Structure):
    _fields_ = [("attributes", wintypes.DWORD), ("created", wintypes.FILETIME),
                ("accessed", wintypes.FILETIME), ("written", wintypes.FILETIME),
                ("volume", wintypes.DWORD), ("size_high", wintypes.DWORD),
                ("size_low", wintypes.DWORD), ("links", wintypes.DWORD),
                ("index_high", wintypes.DWORD), ("index_low", wintypes.DWORD)]


def open_private(path: Path, root: Path, *, writable: bool = False, limit: int = 1024) -> BinaryIO:
    """ACL-verified host directory is supplied by the trusted Windows coordinator.

    Open-existing, exclusive sharing, reject reparse/directory/multiple-hardlink
    objects, compare the final handle path and bound size before CRT conversion.
    The coordinator must separately verify every ancestor and its actual ACL.
    """
    if os.name != "nt" or path.parent != root or not path.is_absolute():
        raise HostFileError()
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    api.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                               ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    api.CreateFileW.restype = wintypes.HANDLE
    api.GetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.POINTER(_Information)]
    api.GetFileInformationByHandle.restype = wintypes.BOOL
    api.GetFinalPathNameByHandleW.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD]
    api.GetFinalPathNameByHandleW.restype = wintypes.DWORD
    api.CloseHandle.argtypes = [wintypes.HANDLE]
    api.CloseHandle.restype = wintypes.BOOL
    handle = api.CreateFileW(str(path), 0xC0000000 if writable else 0x80000000,
                             0, None, 3, 0x00200000, None)
    if handle in (None, ctypes.c_void_p(-1).value):
        raise HostFileError()
    try:
        info = _Information()
        final = ctypes.create_unicode_buffer(32768)
        count = api.GetFinalPathNameByHandleW(handle, final, len(final), 0)
        if (not api.GetFileInformationByHandle(handle, ctypes.byref(info)) or
                info.attributes & (0x10 | 0x400) or info.links != 1 or info.size_high != 0 or
                info.size_low > limit or not 0 < count < len(final) or
                os.path.normcase(final.value) != os.path.normcase("\\\\?\\" + str(path))):
            raise HostFileError()
        import msvcrt
        fd = msvcrt.open_osfhandle(handle, os.O_BINARY | (os.O_RDWR if writable else os.O_RDONLY))
        handle = None
        try:
            return os.fdopen(fd, "r+b" if writable else "rb", buffering=0)
        except Exception:
            os.close(fd)
            raise
    finally:
        if handle is not None:
            api.CloseHandle(handle)


class HostDocument:
    def __init__(self, root: Path, expected_sha256: str) -> None:
        self._root, self._expected = root, expected_sha256
        self.opens = 0

    def read(self) -> bytes:
        with open_private(self._root / "document.txt", self._root) as stream:
            self.opens += 1
            data = stream.read(1025)
            if not data or len(data) > 1024 or hashlib.sha256(data).hexdigest() != self._expected:
                raise HostFileError()
            data.decode("utf-8", errors="strict")
            return data
