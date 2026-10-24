"""Blocking private-stream adapter; coordinator enforces native I/O deadlines."""
from __future__ import annotations

from typing import BinaryIO

from .protocol import Decoder, Encoder, ProtocolError, encode


class PrivateChannel:
    def __init__(self, source: BinaryIO, destination: BinaryIO) -> None:
        self._source, self._destination = source, destination
        self._decoder, self._encoder = Decoder(), Encoder()
        self.closed = False

    def receive(self) -> dict:
        try:
            if self.closed:
                raise ProtocolError()
            # Reading one byte avoids consuming a later unsolicited frame.
            while True:
                raw = self._source.read(1)
                if not raw:
                    self._decoder.eof()
                    raise ProtocolError()
                frames = self._decoder.feed(raw)
                if frames:
                    return frames[0]
        except Exception:
            self.closed = True
            raise ProtocolError() from None

    def send(self, message: dict) -> int:
        return self.send_frame(encode(message))

    def send_frame(self, raw: bytes) -> int:
        try:
            if self.closed:
                raise ProtocolError()
            # Service-created frames must also consume this writer's budget.
            decoder = Decoder()
            decoded = decoder.feed(raw)
            decoder.eof()
            if len(decoded) != 1:
                raise ProtocolError()
            if self._encoder.frame(decoded[0]) != raw:
                raise ProtocolError()
            if self._destination.write(raw) != len(raw):
                raise ProtocolError()
            self._destination.flush()
            return len(raw)
        except Exception:
            self.closed = True
            raise ProtocolError() from None
