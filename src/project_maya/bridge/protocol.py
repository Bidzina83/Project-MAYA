"""Bounded incremental framing for private product-owned byte channels."""
from __future__ import annotations

import json
import math
import struct
import time
from collections.abc import Callable

FRAME_LIMIT = 8192
CHANNEL_LIMIT = 131072


class ProtocolError(ValueError):
    def __init__(self) -> None:
        super().__init__("bridge.invalid_protocol")


def _object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProtocolError()
        result[key] = value
    return result


def _constant(_: str) -> None:
    raise ProtocolError()


def _validate(value: object, depth: int = 0) -> None:
    if isinstance(value, (dict, list)):
        if depth >= 8:
            raise ProtocolError()
        if isinstance(value, dict):
            for key, item in value.items():
                if type(key) is not str:
                    raise ProtocolError()
                key.encode("utf-8", errors="strict")
                _validate(item, depth + 1)
        else:
            for item in value:
                _validate(item, depth + 1)
    elif type(value) is str:
        value.encode("utf-8", errors="strict")
    elif value is None or type(value) in (bool, int):
        return
    elif type(value) is float and math.isfinite(value):
        return
    else:
        raise ProtocolError()


def decode(raw: bytes) -> dict:
    try:
        if type(raw) is not bytes or not 1 <= len(raw) <= FRAME_LIMIT or raw.startswith(b"\xef\xbb\xbf"):
            raise ProtocolError()
        value = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=_object,
                           parse_constant=_constant)
        if type(value) is not dict:
            raise ProtocolError()
        _validate(value)
        return value
    except (ValueError, UnicodeError, RecursionError, OverflowError):
        raise ProtocolError() from None


def encode(value: dict) -> bytes:
    try:
        if type(value) is not dict:
            raise ProtocolError()
        _validate(value)
        raw = json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode("ascii")
        if not 1 <= len(raw) <= FRAME_LIMIT:
            raise ProtocolError()
        return struct.pack("<I", len(raw)) + raw
    except (ValueError, UnicodeError, RecursionError, OverflowError):
        raise ProtocolError() from None


class Decoder:
    """Caller must tick deadlines and stop the owning channel on any error.

    No pipe I/O occurs here. Native cancellation/read deadlines belong to the
    coordinator, so a blocked stream cannot bypass them inside this codec.
    """
    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._buffer = bytearray()
        self._size: int | None = None
        self._started: float | None = None
        self.total = 0
        self.closed = False

    def _fail(self) -> None:
        self.closed = True
        self._buffer.clear()
        raise ProtocolError()

    def tick(self) -> None:
        if self.closed or (self._started is not None and self._clock() - self._started >= 1):
            self._fail()

    def feed(self, chunk: bytes) -> list[dict]:
        self.tick()
        if type(chunk) is not bytes or self.total + len(chunk) > CHANNEL_LIMIT:
            self._fail()
        self.total += len(chunk)
        result = []
        offset = 0
        try:
            while offset < len(chunk):
                if self._started is None:
                    self._started = self._clock()
                needed = (4 if self._size is None else self._size) - len(self._buffer)
                take = min(needed, len(chunk) - offset)
                self._buffer.extend(chunk[offset:offset + take])
                offset += take
                if len(self._buffer) != (4 if self._size is None else self._size):
                    continue
                if self._size is None:
                    self._size = struct.unpack("<I", self._buffer)[0]
                    self._buffer.clear()
                    if not 1 <= self._size <= FRAME_LIMIT:
                        self._fail()
                else:
                    result.append(decode(bytes(self._buffer)))
                    self._buffer.clear()
                    self._size = self._started = None
            return result
        except (ProtocolError, TypeError, ValueError):
            self._fail()

    def eof(self) -> None:
        if self.closed or self._size is not None or self._buffer:
            self._fail()
        self.closed = True


class Encoder:
    def __init__(self) -> None:
        self.total = 0
        self.closed = False

    def frame(self, value: dict) -> bytes:
        if self.closed:
            raise ProtocolError()
        try:
            raw = encode(value)
            if self.total + len(raw) > CHANNEL_LIMIT:
                raise ProtocolError()
            self.total += len(raw)
            return raw
        except ProtocolError:
            self.closed = True
            raise
