"""Middleware for exposing TiXL response metadata as HTTP headers."""

from contextvars import ContextVar

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from tixl_python.api.bridge import CallResult

FRAME_HEADER = "X-TiXL-Frame"
PLAYBACK_FRAME_HEADER = "X-TiXL-Playback-Frame"
STRUCTURE_VERSION_HEADER = "X-TiXL-Structure-Version"
TIXL_RESPONSE_HEADERS = (FRAME_HEADER, PLAYBACK_FRAME_HEADER, STRUCTURE_VERSION_HEADER)

_response_call: ContextVar[CallResult | None] = ContextVar("tixl_response_call", default=None)


def capture_response_metadata(call: CallResult) -> None:
    """Make a successful bridge call's metadata available to the middleware."""
    _response_call.set(call)


class TixlMetadataMiddleware:
    """Add metadata from the current request's bridge call to its response."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        token = _response_call.set(None)

        async def send_with_metadata(message: Message) -> None:
            if message["type"] == "http.response.start" and (call := _response_call.get()) is not None:
                headers = MutableHeaders(scope=message)
                headers[FRAME_HEADER] = str(call.frame)
                headers[PLAYBACK_FRAME_HEADER] = str(call.playback_frame)
                headers[STRUCTURE_VERSION_HEADER] = str(call.structure_version)
            await send(message)

        try:
            await self.app(scope, receive, send_with_metadata)
        finally:
            _response_call.reset(token)
