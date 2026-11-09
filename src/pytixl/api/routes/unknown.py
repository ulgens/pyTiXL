# TODO:
#   These routes are not even mentioned in debug protocol page.
#   Find where they came from - do they really exist.
#   https://github.com/tixl3d/tixl/blob/b6cc584406c76aebf61910f58d1562bf55c4884e/.agentic/DEBUG_PROTOCOL.md
from typing import Annotated

from fastapi import Query

from ..schemas import (
    GetFrameSamplesResult,
    GetShaderErrorsRequest,
    GetShaderErrorsResult,
    SetBypassRequest,
    SetBypassResult,
    SetFrameLatencyRequest,
    SetFrameLatencyResult,
)
from .main import (
    BridgeDep,
    invoke,
    router,
)

__all__ = (
    "get_frame_samples",
    "get_shader_errors",
    "set_bypass",
    "set_frame_latency",
)

TAG = "Unknown"


@router.get(
    path="/frame-samples",
    response_model=GetFrameSamplesResult,
    tags=(TAG,),
)
async def get_frame_samples(bridge: BridgeDep):
    return await invoke(bridge, "getFrameSamples")


@router.get(
    path="/shader-errors",
    response_model=GetShaderErrorsResult,
    tags=(TAG,),
)
async def get_shader_errors(
    query: Annotated[GetShaderErrorsRequest, Query()],
    bridge: BridgeDep,
):
    return await invoke(bridge, "getShaderErrors", query)


@router.post(
    path="/set-bypass",
    response_model=SetBypassResult,
    tags=(TAG,),
)
async def set_bypass(body: SetBypassRequest, bridge: BridgeDep):
    return await invoke(bridge, "setBypass", body)


@router.post(
    path="/set-frame-latency",
    response_model=SetFrameLatencyResult,
    tags=(TAG,),
)
async def set_frame_latency(body: SetFrameLatencyRequest, bridge: BridgeDep):
    return await invoke(bridge, "setFrameLatency", body)
