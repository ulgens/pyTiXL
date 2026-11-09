"""
Operator related routes
"""

from typing import Annotated

from fastapi import Query

from ..schemas import (
    AddOpRequest,
    AddOpResult,
    ConnectRequest,
    DeleteOpRequest,
    EmptyResult,
)
from .main import (
    BridgeDep,
    invoke,
    router,
)

__all__ = (
    "add_operator",
    "connect_operators",
    "delete_operator",
)

TAG = "Operators"


@router.post(
    "/operators",
    response_model=AddOpResult,
    tags=(TAG,),
)
async def add_operator(body: AddOpRequest, bridge: BridgeDep):
    return await invoke(bridge, "addOp", body)


@router.delete(
    "/operators",
    response_model=EmptyResult,
    tags=(TAG,),
)
async def delete_operator(
    query: Annotated[DeleteOpRequest, Query()],
    bridge: BridgeDep,
):
    return await invoke(bridge, "deleteOp", query)


@router.post(
    "/connect-operators",
    response_model=EmptyResult,
    tags=(TAG,),
)
async def connect_operators(body: ConnectRequest, bridge: BridgeDep):
    return await invoke(bridge, "connect", body)
