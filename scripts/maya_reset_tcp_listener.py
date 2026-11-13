"""Temporary receipt counter for the private Maya reset test route."""

import argparse
import json
import re
import select
import socket
import time
from uuid import UUID


def observe(listener, peer, seconds, emit):
    deadline = time.monotonic() + seconds
    receipts = 0
    emit({"event": "ready"})
    while (remaining := deadline - time.monotonic()) > 0:
        listener.settimeout(remaining)
        try:
            connection, (address, _) = listener.accept()
        except TimeoutError:
            break
        with connection:
            if address == peer:
                receipts += 1
                emit({"event": "receipt", "ordinal": receipts})
    emit({"event": "window_closed", "peer_receipts": receipts})


def observe_controlled(listener, peer, seconds, emit):
    """Use the first peer connection as the host control and count later accepts."""
    deadline = time.monotonic() + seconds
    listener.settimeout(seconds)
    control, (address, _) = listener.accept()
    with control:
        if address != peer:
            raise ValueError("Unexpected control peer")
        control.settimeout(min(5, max(0.001, deadline - time.monotonic())))
        command = b""
        while len(command) < 39 and not command.endswith(b"\n"):
            control.settimeout(min(5, max(0.001, deadline - time.monotonic())))
            chunk = control.recv(1)
            if not chunk:
                break
            command += chunk
        if not re.fullmatch(rb"START [0-9a-f]{32}\n", command):
            raise ValueError("Invalid start request")
        token = command[6:-1]
        report = emit
        emit = lambda record: report(dict(record, attempt=token.decode("ascii")))
        emit({"event": "ready"})
        control.sendall(b"START " + token + b"\n")
        receipts = 1
        emit({"event": "receipt", "ordinal": receipts})
        stop = b"STOP " + token + b"\n"
        command = b""
        while (remaining := deadline - time.monotonic()) > 0:
            readable, _, _ = select.select([listener, control], [], [], remaining)
            if listener in readable:
                connection, (source, _) = listener.accept()
                with connection:
                    if source == peer:
                        receipts += 1
                        emit({"event": "receipt", "ordinal": receipts})
                continue
            if control in readable:
                chunk = control.recv(len(stop) + 1 - len(command))
                command += chunk
                if not chunk or not stop.startswith(command):
                    raise ValueError("Invalid stop acknowledgment request")
                if command == stop:
                    listener.setblocking(False)
                    while True:
                        if time.monotonic() >= deadline or receipts > 64:
                            raise TimeoutError("Receipt drain exceeded observation bounds")
                        try:
                            pending, (source, _) = listener.accept()
                        except BlockingIOError:
                            break
                        with pending:
                            if source == peer:
                                receipts += 1
                                emit({"event": "receipt", "ordinal": receipts})
                    control.sendall(b"CLOSED " + token + b" " + str(receipts).encode("ascii") + b"\n")
                    emit({"event": "window_closed", "peer_receipts": receipts})
                    return
        raise TimeoutError("Observation ended without a stop acknowledgment")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=UUID)
    parser.add_argument("--controlled", action="store_true")
    args = parser.parse_args()
    if not args.controlled and args.attempt is None:
        parser.error("--attempt is required without --controlled")

    def emit(record):
        print(json.dumps({
            "schema": "maya.reset.tcp.listener.v1",
            "attempt": args.attempt.hex if args.attempt else None,
            **record,
        }), flush=True)

    # Keep this listener bound to the approved test interface and peer.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("100.127.155.29", 49187))
        listener.listen()
        if args.controlled:
            observe_controlled(listener, "100.72.228.70", 120, emit)
        else:
            observe(listener, "100.72.228.70", 90, emit)


if __name__ == "__main__":
    main()
