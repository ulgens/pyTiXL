"""
"Rendering" group from TiXL docs.

https://github.com/tixl3d/tixl/blob/b6cc584406c76aebf61910f58d1562bf55c4884e/.agentic/DEBUG_PROTOCOL.md#methods
"""

from pathlib import Path

from ..schemas import (
    CancelRenderResult,
    RenderStatusResult,
    StartRenderRequest,
    StartRenderResult,
)
from .main import (
    BridgeDep,
    CapturesDep,
    invoke,
    router,
)

__all__ = (
    "cancel_render",
    "get_render_status",
    "start_render",
)

TAG = "Render"


@router.post(
    path="/start-render",
    response_model=StartRenderResult,
    tags=(TAG,),
)
async def start_render(
    body: StartRenderRequest,
    bridge: BridgeDep,
    captures_dir: CapturesDep,
):
    render_path = Path(body.path).expanduser()

    if not render_path.is_absolute():
        render_path = captures_dir / render_path

    render_path.parent.mkdir(parents=True, exist_ok=True)
    body.path = str(render_path.resolve())

    return await invoke(bridge, "startRender", body)


@router.get(
    path="/render-status",
    response_model=RenderStatusResult,
    tags=(TAG,),
)
async def get_render_status(bridge: BridgeDep):
    return await invoke(bridge, "getRenderStatus")


@router.post(
    path="/cancel-render",
    response_model=CancelRenderResult,
    tags=(TAG,),
)
async def cancel_render(bridge: BridgeDep):
    return await invoke(bridge, "cancelRender")
