"""
Uncategorized routes
"""

from ..schemas import (
    EmptyResult,
    SetAgentStateRequest,
    SetAgentStateResult,
    SetTargetFrameRateRequest,
    SetTargetFrameRateResult,
    SetVSyncRequest,
    SetVSyncResult,
    StallMainThreadRequest,
)
from .main import (
    BridgeDep,
    invoke,
    router,
)

__all__ = (
    "release_gpu_resources",
    "set_agent_state",
    "set_target_frame_rate",
    "set_vsync",
    "stall_main_thread",
)

TAG = "Uncategorized"


@router.post(
    path="/release-gpu-resources",
    response_model=EmptyResult,
    tags=(TAG,),
)
async def release_gpu_resources(bridge: BridgeDep):
    return await invoke(bridge, "releaseGpuResources")


@router.post(
    path="/set-agent-state",
    response_model=SetAgentStateResult,
    tags=(TAG,),
)
async def set_agent_state(body: SetAgentStateRequest, bridge: BridgeDep):
    return await invoke(bridge, "setAgentState", body)


@router.post(
    path="/set-target-frame-rate",
    response_model=SetTargetFrameRateResult,
    tags=(TAG,),
)
async def set_target_frame_rate(body: SetTargetFrameRateRequest, bridge: BridgeDep):
    return await invoke(bridge, "setTargetFrameRate", body)


@router.post(
    path="/set-vsync",
    response_model=SetVSyncResult,
    tags=(TAG,),
)
async def set_vsync(body: SetVSyncRequest, bridge: BridgeDep):
    return await invoke(bridge, "setVSync", body)


@router.post(
    path="/stall-main-thread",
    response_model=EmptyResult,
    tags=(TAG,),
)
async def stall_main_thread(body: StallMainThreadRequest, bridge: BridgeDep):
    return await invoke(bridge, "stallMainThread", body, timeout=body.seconds + 60.0)
