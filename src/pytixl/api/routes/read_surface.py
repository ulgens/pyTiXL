"""
"Read surface" group from TiXL docs.
If an operator belongs to a more specific group, it may be in that file - not here.

https://github.com/tixl3d/tixl/blob/b6cc584406c76aebf61910f58d1562bf55c4884e/.agentic/DEBUG_PROTOCOL.md#methods
"""

from typing import Annotated

from fastapi import Query

from ..schemas import (
    GetContextResult,
    GetLogTailRequest,
    GetLogTailResult,
    GetOutputRequest,
    GetOutputResult,
    GetPathsResult,
    GetStructureVersionResult,
    GetVersionResult,
)
from .main import (
    BridgeDep,
    invoke,
    router,
)

__all__ = (
    "get_context",
    "get_log_tail",
    "get_output",
    "get_paths",
    "get_structure_version",
    "get_version",
)

TAG = "Read Surface"


@router.get(
    path="/version",
    response_model=GetVersionResult,
    tags=(TAG,),
)
async def get_version(bridge: BridgeDep):
    return await invoke(bridge, "getVersion")


@router.get(
    path="/paths",
    response_model=GetPathsResult,
    tags=(TAG,),
)
async def get_paths(bridge: BridgeDep):
    return await invoke(bridge, "getPaths")


@router.get(
    path="/structure-version",
    response_model=GetStructureVersionResult,
    tags=(TAG,),
)
async def get_structure_version(bridge: BridgeDep):
    return await invoke(bridge, "getStructureVersion", timeout=30.0)


@router.get(
    path="/context",
    response_model=GetContextResult,
    tags=(TAG,),
)
async def get_context(bridge: BridgeDep):
    return await invoke(bridge, "getContext")


@router.get(
    path="/log-tail",
    response_model=GetLogTailResult,
    tags=(TAG,),
)
async def get_log_tail(
    query: Annotated[GetLogTailRequest, Query()],
    bridge: BridgeDep,
):
    return await invoke(bridge, "getLogTail", query)


@router.get(
    path="/output",
    response_model=GetOutputResult,
    tags=(TAG,),
)
async def get_output(
    query: Annotated[GetOutputRequest, Query()],
    bridge: BridgeDep,
):
    return await invoke(bridge, "getOutput", query)
