"""
Routes from "Capturing the editor UI" section.

https://github.com/tixl3d/tixl/blob/b6cc584406c76aebf61910f58d1562bf55c4884e/.agentic/DEBUG_PROTOCOL.md#looking-at-the-graph
"""

from pathlib import Path
from typing import Annotated

from fastapi import Query, Request
from fastapi.responses import Response

from ..captures import (
    image_response,
    resolve_capture_path,
    screenshot_response,
    timestamped_name,
    wants_image,
)
from ..schemas import (
    ScreenshotRequest,
    ScreenshotResponse,
    ScreenshotWindowRequest,
)
from .main import (
    BridgeDep,
    CapturesDep,
    invoke,
    router,
)

__all__ = (
    "screenshot",
    "screenshot_window",
)

TAG = "UI Capture"


@router.post(
    path="/screenshot",
    response_model=ScreenshotResponse,
    tags=(TAG,),
    responses={
        200: {
            "description": "Metadata, or image bytes when inline is requested.",
            "content": {"image/png": {}, "image/jpeg": {}},
        },
    },
)
async def screenshot(
    body: ScreenshotRequest,
    request: Request,
    bridge: BridgeDep,
    captures_dir: CapturesDep,
    inline: Annotated[
        bool,
        Query(description="Return the image bytes instead of metadata."),
    ] = False,
) -> ScreenshotResponse | Response:
    path = resolve_capture_path(
        captures_dir,
        body.path,
        timestamped_name(f"screen_{body.target}"),
    )

    result = await invoke(bridge, "screenshot", {"path": str(path), "target": body.target})
    written = Path(result.get("path") or path)

    if inline or wants_image(request):
        return image_response(written)

    return screenshot_response(request, written, captures_dir)


@router.post(
    path="/screenshot-window",
    response_model=ScreenshotResponse,
    tags=(TAG,),
    responses={
        200: {
            "description": "Metadata, or image bytes when inline is requested.",
            "content": {"image/png": {}, "image/jpeg": {}},
        },
    },
)
async def screenshot_window(
    body: ScreenshotWindowRequest,
    request: Request,
    bridge: BridgeDep,
    captures_dir: CapturesDep,
    inline: Annotated[
        bool,
        Query(description="Return the image bytes instead of metadata."),
    ] = False,
) -> ScreenshotResponse | Response:
    stem = "window"

    if body.region:
        stem = body.region

    path = resolve_capture_path(captures_dir, body.path, timestamped_name(stem))
    params = {"path": str(path)}

    if body.region:
        params["region"] = body.region

    result = await invoke(bridge, "screenshotWindow", params)
    written = Path(result.get("path") or path)

    if inline or wants_image(request):
        return image_response(written)

    return screenshot_response(request, written, captures_dir)
