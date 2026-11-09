from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from starlette.requests import Request

from ...client import TixlError
from ..bridge import TixlBridge
from ..errors import from_tixl_error
from ..middleware import capture_response_metadata
from ..schemas import ApiModel

__all__ = (
    "BridgeDep",
    "CapturesDep",
    "invoke",
    "params",
    "router",
)


def _get_bridge(request: Request) -> TixlBridge:
    return request.app.state.bridge


BridgeDep = Annotated[TixlBridge, Depends(_get_bridge)]


def _get_captures_dir(request: Request) -> Path:
    return request.app.state.captures_dir


CapturesDep = Annotated[Path, Depends(_get_captures_dir)]


def params(body: ApiModel | dict[str, Any] | None) -> dict[str, Any]:
    if body is None:
        return {}

    if isinstance(body, dict):
        return body

    return body.model_dump(by_alias=True, exclude_none=True, mode="json")


async def invoke(
    bridge: TixlBridge,
    method: str,
    body: ApiModel | dict[str, Any] | None = None,
    *,
    timeout: float | None = None,
) -> dict[str, Any]:
    try:
        call = await bridge.call(method, params(body), timeout)
    except TixlError as exc:
        raise from_tixl_error(exc) from exc

    capture_response_metadata(call)
    return call.result


router = APIRouter(prefix="/api")
