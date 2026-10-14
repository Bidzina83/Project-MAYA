"""Loopback HTTP transport for the test-only broker; not network containment."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from typing import Any

from .restricted_broker import BrokerDenied, RestrictedBroker


def build_test_broker_server(broker: RestrictedBroker, port: int = 0) -> HTTPServer:
    """Bind a host-only test endpoint; no remote bind or production registration."""
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"

        def log_message(self, *args: Any) -> None:
            # Native request paths/headers are untrusted and may contain secrets.
            return

        def send_error(self, code: int, message: str | None = None,
                       explain: str | None = None) -> None:
            # BaseHTTPRequestHandler otherwise reflects untrusted method text.
            self._reply(code, {"error": "broker.invalid_http"})

        def _reply(self, status: int, body: Any) -> None:
            data = json.dumps(body, allow_nan=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(data)
            self.close_connection = True

        def do_POST(self) -> None:
            try:
                self.connection.settimeout(3)
                lengths = self.headers.get_all("Content-Length", [])
                tokens = self.headers.get_all("Authorization", [])
                hosts = self.headers.get_all("Host", [])
                if (self.headers.get_all("Transfer-Encoding") or len(lengths) != 1
                        or not lengths[0].isascii() or not lengths[0].isdigit()
                        or not 0 < int(lengths[0]) <= 256 * 1024
                        or len(tokens) != 1 or not tokens[0].startswith("Bearer ")
                        or hosts != [f"127.0.0.1:{self.server.server_port}"]
                        or self.headers.get("Content-Type") != "application/json"):
                    raise BrokerDenied("broker.invalid_request")
                size = int(lengths[0])
                raw = self.rfile.read(size)
                if len(raw) != size:
                    raise BrokerDenied("broker.invalid_request")
                result = broker.handle(tokens[0][7:], self.path, raw)
                self._reply(200, result)
            except BrokerDenied:
                self._reply(403, {"error": "broker.denied"})
            except Exception:
                self._reply(503, {"error": "broker.unavailable"})

        def do_GET(self) -> None:
            self._reply(405, {"error": "broker.method_denied"})

    class Server(HTTPServer):
        def get_request(self):
            connection, address = super().get_request()
            connection.settimeout(3)
            return connection, address

        def handle_error(self, request: Any, client_address: Any) -> None:
            # No raw request/service exception traceback goes to public stderr.
            return

    server = Server(("127.0.0.1", port), Handler)
    return server
