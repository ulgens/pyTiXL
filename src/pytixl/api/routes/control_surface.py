"""
"Control surface" group from TiXL docs.
If an operator belongs to a more specific group, it may be in that file - not here.

https://github.com/tixl3d/tixl/blob/b6cc584406c76aebf61910f58d1562bf55c4884e/.agentic/DEBUG_PROTOCOL.md#methods
"""

from typing import Annotated

from fastapi import Query

from ..schemas import (
    DeleteSelectionRequest,
    DeleteSelectionResult,
    EmptyResult,
    LayoutSelectionResult,
    NewProjectRequest,
    NewProjectResult,
    OpenProjectRequest,
    OpenProjectResult,
    OpenWindowRequest,
    OpenWindowResult,
    OutputSetupRequest,
    PinRequest,
    PumpFramesRequest,
    ReloadRequest,
    ReloadResult,
    SetInputRequest,
    SetInputResult,
    SetPlaybackRequest,
    SetPlaybackResult,
    SetTimeRequest,
    SetTimeResult,
    UndoRedoResult,
)
from .main import (
    BridgeDep,
    invoke,
    router,
)

__all__ = (
    "delete_selection",
    "layout_selection",
    "new_project",
    "open_project",
    "output_setup",
    "pin",
    "pump_frames",
    "redo",
    "reload_project",
    "reset_view",
    "set_input",
    "set_playback",
    "set_time",
    "shutdown",
    "undo",
)

TAG = "Control Surface"


@router.post(
    path="/open-project",
    response_model=OpenProjectResult,
    tags=(TAG,),
)
async def open_project(body: OpenProjectRequest, bridge: BridgeDep):
    return await invoke(bridge, "openProject", body)


@router.post(
    path="/new-project",
    response_model=NewProjectResult,
    tags=(TAG,),
)
async def new_project(body: NewProjectRequest, bridge: BridgeDep):
    return await invoke(bridge, "newProject", body)


@router.post(
    path="/set-input",
    response_model=SetInputResult,
    tags=(TAG,),
)
async def set_input(body: SetInputRequest, bridge: BridgeDep):
    return await invoke(bridge, "setInput", body)


@router.post(
    path="/pump-frames",
    response_model=EmptyResult,
    tags=(TAG,),
)
async def pump_frames(
    body: PumpFramesRequest | None = None,
    *,
    bridge: BridgeDep,
):
    return await invoke(bridge, "pumpFrames", body)


@router.post(
    path="/pin",
    response_model=EmptyResult,
    tags=(TAG,),
)
async def pin(body: PinRequest, bridge: BridgeDep):
    return await invoke(bridge, "pin", body)


@router.post(
    path="/reset-view",
    response_model=EmptyResult,
    tags=(TAG,),
)
async def reset_view(bridge: BridgeDep):
    return await invoke(bridge, "resetView")


@router.post(
    path="/layout-selection",
    response_model=LayoutSelectionResult,
    tags=(TAG,),
)
async def layout_selection(bridge: BridgeDep):
    return await invoke(bridge, "layoutSelection")


@router.delete(
    path="/selection",
    response_model=DeleteSelectionResult,
    tags=(TAG,),
)
async def delete_selection(
    query: Annotated[DeleteSelectionRequest, Query()],
    bridge: BridgeDep,
):
    return await invoke(bridge, "deleteSelection", query)


# TODO: resetView wrapper


@router.post(
    path="/reload",
    response_model=ReloadResult,
    tags=(TAG,),
)
async def reload_project(body: ReloadRequest, bridge: BridgeDep):
    return await invoke(bridge, "reload", body)


@router.post(
    path="/undo",
    response_model=UndoRedoResult,
    tags=(TAG,),
)
async def undo(bridge: BridgeDep):
    return await invoke(bridge, "undo")


@router.post(
    path="/redo",
    response_model=UndoRedoResult,
    tags=(TAG,),
)
async def redo(bridge: BridgeDep):
    return await invoke(bridge, "redo")


@router.post(
    path="/set-time",
    response_model=SetTimeResult,
    tags=(TAG,),
)
async def set_time(body: SetTimeRequest, bridge: BridgeDep):
    return await invoke(bridge, "setTime", body)


@router.post(
    path="/set-playback",
    response_model=SetPlaybackResult,
    tags=(TAG,),
)
async def set_playback(body: SetPlaybackRequest, bridge: BridgeDep):
    return await invoke(bridge, "setPlayback", body)


@router.post(
    path="/shutdown",
    response_model=EmptyResult,
    tags=(TAG,),
)
async def shutdown(bridge: BridgeDep):
    return await invoke(bridge, "shutdown")


@router.post(
    path="/output-setup",
    response_model=EmptyResult,
    tags=(TAG,),
)
async def output_setup(body: OutputSetupRequest, bridge: BridgeDep):
    return await invoke(bridge, "outputSetup", body)


@router.post(
    path="/open-window",
    response_model=OpenWindowResult,
    tags=(TAG,),
)
async def open_window(body: OpenWindowRequest, bridge: BridgeDep):
    return await invoke(bridge, "openWindow", body)
