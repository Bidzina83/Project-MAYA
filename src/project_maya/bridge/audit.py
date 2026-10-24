"""Durable append adapter for an already verified private host audit handle."""
from __future__ import annotations

import os
import threading
from typing import BinaryIO

from project_maya.audit import AuditRecord


class RequiredAudit:
    """Uses the existing record format; never opens a child-selected path.

    Host setup must create/verify the non-reparse file and private descriptor
    before passing its exclusive binary handle. An error poisons this sink.
    """
    def __init__(self, stream: BinaryIO, existing_bytes: int = 0) -> None:
        if type(existing_bytes) is not int or not 0 <= existing_bytes <= 131072:
            raise ValueError("bridge.invalid_audit_size")
        self._stream = stream
        self._bytes = existing_bytes
        self._lock = threading.Lock()
        self.failed = False

    def write(self, record: AuditRecord) -> None:
        with self._lock:
            try:
                if self.failed or not isinstance(record, AuditRecord):
                    raise OSError()
                raw = (record.to_json() + "\n").encode("utf-8")
                if self._bytes + len(raw) > 131072:
                    raise OSError()
                if self._stream.write(raw) != len(raw):
                    raise OSError()
                self._stream.flush()
                os.fsync(self._stream.fileno())
                self._bytes += len(raw)
            except Exception:
                self.failed = True
                raise OSError("bridge.required_audit_failed") from None
