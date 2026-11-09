"""Minimal JSON-lines client for TiXL's local debug bridge."""

from __future__ import annotations

import contextlib
import json
import socket


class TixlError(RuntimeError):
    """A failed debug-protocol request."""

    def __init__(self, method: str, code: str, detail: str):
        super().__init__(f"{method} failed: {code} - {detail}")
        self.method = method
        self.code = code
        self.detail = detail


class TixlClient:
    """JSON-lines client speaking to TiXL's debug bridge."""

    def __init__(self, sock: socket.socket):
        self._sock = sock
        self._sock.settimeout(120)
        self._reader = sock.makefile("r", encoding="utf-8", newline="\n")
        self._next_id = 0

    @classmethod
    def connect(cls, host: str, port: int, timeout: float = 2.0) -> TixlClient:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.settimeout(120)
        return cls(sock)

    def call(self, method: str, timeout: float | None = None, **params):
        if timeout is not None:
            self._sock.settimeout(timeout)

        self._next_id += 1
        request = {"id": str(self._next_id), "method": method, **params}
        self._sock.sendall((json.dumps(request) + "\n").encode("utf-8"))

        try:
            line = self._reader.readline()
        except TimeoutError as exc:
            raise TixlError(method, "TIMEOUT", "no response within the socket timeout") from exc

        if not line:
            raise TixlError(method, "CONNECTION_CLOSED", "the editor closed the connection")

        envelope = json.loads(line)
        if not envelope.get("ok"):
            error = envelope.get("error") or {}
            raise TixlError(
                method,
                error.get("code", "UNKNOWN"),
                error.get("detail", str(envelope)),
            )

        return envelope.get("result") or {}

    def send_only(self, method: str, **params) -> None:
        """Send a request without waiting for its response (e.g. shutdown)."""
        self._next_id += 1
        request = {"id": str(self._next_id), "method": method, **params}
        self._sock.sendall((json.dumps(request) + "\n").encode("utf-8"))

    def pump(self, count: int = 10) -> None:
        self.call("pumpFrames", timeout=120, count=count)

    def close(self) -> None:
        with contextlib.suppress(Exception):
            self._reader.close()
        with contextlib.suppress(Exception):
            self._sock.close()


def try_connect(port: int, timeout: float = 1.0) -> TixlClient | None:
    try:
        return TixlClient.connect("127.0.0.1", port, timeout)
    except OSError:
        return None
