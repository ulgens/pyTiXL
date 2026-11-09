"""Async bridge between HTTP requests and TiXL's JSON-lines debug port.

The editor answers sequentially on one TCP connection, so requests are serialized
with a single I/O lock. A failure that can desynchronize the stream (timeout,
closed socket) tears the connection down; the reconnect loop then restores it.
"""

import asyncio
import contextlib
import json
import logging
from dataclasses import dataclass
from typing import Any

from pytixl.client import TixlError

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 120.0
CONNECT_TIMEOUT = 2.0
RECONNECT_INTERVAL = 2.0


@dataclass(slots=True)
class CallResult:
    """One successful response envelope."""

    result: dict[str, Any]
    frame: int = -1
    playback_frame: int = -1
    structure_version: int = -1


@dataclass(frozen=True, slots=True)
class VersionInfo:
    protocol_version: int | None
    editor_version: str | None


class TixlBridge:
    """One persistent, serialized connection to a running TiXL debug server."""

    def __init__(
        self,
        host: str,
        port: int,
        *,
        connect_timeout: float = CONNECT_TIMEOUT,
        reconnect_interval: float = RECONNECT_INTERVAL,
    ) -> None:
        self.host = host
        self.port = port
        self._connect_timeout = connect_timeout
        self._reconnect_interval = reconnect_interval

        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._connected = False
        self._last_error: str | None = None
        self._request_id = 0

        self._io_lock = asyncio.Lock()
        self._connect_lock = asyncio.Lock()
        self._reconnect_task: asyncio.Task[None] | None = None
        self._closing = False

        self._protocol_version: int | None = None
        self._editor_version: str | None = None

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def last_error(self) -> str | None:
        return self._last_error

    @property
    def request_count(self) -> int:
        return self._request_id

    async def start(self) -> None:
        """Attach once and keep retrying in the background if TiXL is absent."""
        self._closing = False
        await self._try_connect()
        self._reconnect_task = asyncio.create_task(self._reconnect_loop(), name="tixl-bridge-reconnect")

    async def close(self) -> None:
        self._closing = True
        if self._reconnect_task is not None:
            self._reconnect_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._reconnect_task
            self._reconnect_task = None
        await self._drop_connection()

    async def _reconnect_loop(self) -> None:
        while not self._closing:
            if not self._connected:
                await self._try_connect()
            await asyncio.sleep(self._reconnect_interval)

    async def _try_connect(self) -> bool:
        async with self._connect_lock:
            if self._connected:
                return True

            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port),
                    timeout=self._connect_timeout,
                )
            except (OSError, TimeoutError) as exc:
                self._last_error = f"{type(exc).__name__}: {exc}"
                return False

            self._reader = reader
            self._writer = writer
            self._connected = True
            self._last_error = None
            logger.info("Connected to the TiXL debug bridge at %s:%s", self.host, self.port)
            return True

    async def _drop_connection(self) -> None:
        async with self._connect_lock:
            self._connected = False
            writer = self._writer
            self._reader = None
            self._writer = None
            if writer is not None:
                writer.close()
                with contextlib.suppress(Exception):
                    await writer.wait_closed()

    async def call(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> CallResult:
        """Send one request and wait for its envelope."""
        if not self._connected:
            await self._try_connect()

        if not self._connected:
            raise TixlError(
                method,
                "BRIDGE_UNAVAILABLE",
                self._last_error or f"nothing is listening on {self.host}:{self.port}",
            )

        async with self._io_lock:
            try:
                return await self._call_locked(method, params or {}, timeout)
            except TixlError as exc:
                if exc.code in {"TIMEOUT", "CONNECTION_CLOSED", "WRITE_FAILED"}:
                    await self._drop_connection()
                raise

    async def _call_locked(
        self,
        method: str,
        params: dict[str, Any],
        timeout: float,
    ) -> CallResult:
        reader = self._reader
        writer = self._writer
        if reader is None or writer is None:
            raise TixlError(method, "BRIDGE_UNAVAILABLE", "the connection was closed")

        self._request_id += 1
        request_id = str(self._request_id)
        payload = {"id": request_id, "method": method, **params}
        line = json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n"

        try:
            writer.write(line.encode("utf-8"))
            await asyncio.wait_for(writer.drain(), timeout=timeout)
            raw = await asyncio.wait_for(reader.readline(), timeout=timeout)
        except TimeoutError as exc:
            raise TixlError(method, "TIMEOUT", f"no response within {timeout:g}s") from exc
        except (OSError, ConnectionError) as exc:
            raise TixlError(method, "WRITE_FAILED", str(exc)) from exc

        if not raw:
            raise TixlError(method, "CONNECTION_CLOSED", "the editor closed the connection")

        try:
            envelope = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise TixlError(method, "PARSE_ERROR", f"invalid response line: {exc}") from exc

        if not envelope.get("ok"):
            error = envelope.get("error") or {}
            raise TixlError(
                method,
                error.get("code", "UNKNOWN"),
                error.get("detail", str(envelope)),
            )

        result = envelope.get("result")
        if method == "getVersion" and isinstance(result, dict):
            self._protocol_version = result.get("protocolVersion")
            self._editor_version = result.get("editorVersion")

        return CallResult(
            result=result if isinstance(result, dict) else {},
            frame=int(envelope.get("frame", -1)),
            playback_frame=int(envelope.get("playbackFrame", -1)),
            structure_version=int(envelope.get("structureVersion", -1)),
        )

    async def version_info(self) -> VersionInfo:
        """Return the cached version, asking the editor once if needed."""
        if self._protocol_version is None and self._connected:
            with contextlib.suppress(TixlError):
                await self.call("getVersion", timeout=5.0)
        return VersionInfo(self._protocol_version, self._editor_version)
