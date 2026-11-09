"""
Routes from "Looking at the graph" section.

https://github.com/tixl3d/tixl/blob/b6cc584406c76aebf61910f58d1562bf55c4884e/.agentic/DEBUG_PROTOCOL.md#looking-at-the-graph
"""

from typing import Annotated

from fastapi import Query

from ..schemas import (
    FocusGraphViewRequest,
    FocusGraphViewResult,
    GetGraphStateRequest,
    GetGraphStateResult,
    GraphView,
    SelectRequest,
    SelectResult,
    SetGraphViewRequest,
    SetGraphViewResult,
)
from .main import (
    BridgeDep,
    invoke,
    router,
)

__all__ = (
    "focus_graph_view",
    "get_graph_view",
    "select",
    "set_graph_view",
)

TAG = "Graph Operations"


@router.post(
    path="/select",
    response_model=SelectResult,
    tags=(TAG,),
)
async def select(body: SelectRequest, bridge: BridgeDep):
    return await invoke(bridge, "select", body)


@router.get(
    path="/graph-view",
    response_model=GraphView,
    tags=(TAG,),
)
async def get_graph_view(bridge: BridgeDep):
    return await invoke(bridge, "getGraphView")


@router.post(
    path="/set-graph-view",
    response_model=SetGraphViewResult,
    tags=(TAG,),
)
async def set_graph_view(body: SetGraphViewRequest, bridge: BridgeDep):
    return await invoke(bridge, "setGraphView", body)


@router.post(
    path="/focus-graph-view",
    response_model=FocusGraphViewResult,
    tags=(TAG,),
)
async def focus_graph_view(body: FocusGraphViewRequest, bridge: BridgeDep):
    return await invoke(bridge, "focusGraphView", body)


@router.get(
    path="/graph-state",
    response_model=GetGraphStateResult,
    tags=(TAG,),
)
async def get_graph_state(
    query: Annotated[GetGraphStateRequest, Query()],
    bridge: BridgeDep,
):
    return await invoke(bridge, "getGraphState", query)
