"""Explicit, typed HTTP routes for every TiXL debug-protocol method."""

from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response

from pytixl.api.bridge import TixlBridge
from pytixl.api.captures import (
    image_response,
    resolve_capture_path,
    screenshot_response,
    timestamped_name,
    wants_image,
)
from pytixl.api.errors import from_tixl_error
from pytixl.api.middleware import capture_response_metadata
from pytixl.api.schemas import (
    AddOpRequest,
    AddOpResult,
    ApiModel,
    AudioRecordingResult,
    CancelRenderResult,
    ConnectRequest,
    DeleteOpRequest,
    DeleteSelectionRequest,
    DeleteSelectionResult,
    EmptyResult,
    FocusGraphViewRequest,
    FocusGraphViewResult,
    GetAudioInputsResult,
    GetContextResult,
    GetFrameSamplesResult,
    GetGraphStateRequest,
    GetGraphStateResult,
    GetLogTailRequest,
    GetLogTailResult,
    GetMetricsResult,
    GetOutputRequest,
    GetOutputResult,
    GetPathsResult,
    GetShaderErrorsRequest,
    GetShaderErrorsResult,
    GetStructureVersionResult,
    GetVersionResult,
    GraphView,
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
    RenderStatusResult,
    ScreenshotRequest,
    ScreenshotResponse,
    ScreenshotWindowRequest,
    SelectRequest,
    SelectResult,
    SetAgentStateRequest,
    SetAgentStateResult,
    SetAudioInputRequest,
    SetAudioInputResult,
    SetBypassRequest,
    SetBypassResult,
    SetFrameLatencyRequest,
    SetFrameLatencyResult,
    SetGraphViewRequest,
    SetGraphViewResult,
    SetInputRequest,
    SetInputResult,
    SetPlaybackRequest,
    SetPlaybackResult,
    SetTargetFrameRateRequest,
    SetTargetFrameRateResult,
    SetTimeRequest,
    SetTimeResult,
    SetVSyncRequest,
    SetVSyncResult,
    StallMainThreadRequest,
    StartRenderRequest,
    StartRenderResult,
    UndoRedoResult,
)
from pytixl.client import TixlError

router = APIRouter(prefix="/api")


def get_bridge(request: Request) -> TixlBridge:
    return request.app.state.bridge


def get_captures_dir(request: Request) -> Path:
    return request.app.state.captures_dir


BridgeDep = Annotated[TixlBridge, Depends(get_bridge)]
CapturesDep = Annotated[Path, Depends(get_captures_dir)]


def _params(body: ApiModel | dict[str, Any] | None) -> dict[str, Any]:
    if body is None:
        return {}
    if isinstance(body, dict):
        return body
    return body.model_dump(by_alias=True, exclude_none=True, mode="json")


async def _invoke(
    bridge: TixlBridge,
    method: str,
    body: ApiModel | dict[str, Any] | None = None,
    *,
    timeout: float | None = None,
) -> dict[str, Any]:
    try:
        call = await bridge.call(method, _params(body), timeout)
    except TixlError as exc:
        raise from_tixl_error(exc) from exc

    capture_response_metadata(call)
    return call.result


# --------------------------------------------------------------------------- #
# System
# --------------------------------------------------------------------------- #


@router.post("/ping", response_model=EmptyResult, tags=["system"], summary="Ping the editor.")
async def ping(bridge: BridgeDep) -> EmptyResult:
    return await _invoke(bridge, "ping")


@router.post(
    "/set-agent-state",
    response_model=SetAgentStateResult,
    tags=["system"],
    summary="Announce whether the agent is busy or ready.",
)
async def set_agent_state(body: SetAgentStateRequest, bridge: BridgeDep) -> SetAgentStateResult:
    return await _invoke(bridge, "setAgentState", body)


@router.get("/version", response_model=GetVersionResult, tags=["system"], summary="Protocol version.")
async def get_version(bridge: BridgeDep) -> GetVersionResult:
    return await _invoke(bridge, "getVersion")


@router.get("/paths", response_model=GetPathsResult, tags=["system"], summary="Editor folders.")
async def get_paths(bridge: BridgeDep) -> GetPathsResult:
    return await _invoke(bridge, "getPaths")


@router.post("/shutdown", response_model=EmptyResult, tags=["system"], summary="Exit the editor.")
async def shutdown(bridge: BridgeDep) -> EmptyResult:
    return await _invoke(bridge, "shutdown")


@router.get(
    "/structure-version",
    response_model=GetStructureVersionResult,
    tags=["system"],
    summary="Symbol-structure version.",
)
async def get_structure_version(bridge: BridgeDep) -> GetStructureVersionResult:
    return await _invoke(bridge, "getStructureVersion", timeout=30.0)


@router.post(
    "/set-vsync",
    response_model=SetVSyncResult,
    tags=["system"],
    summary="Read or change VSync.",
)
async def set_vsync(body: SetVSyncRequest, bridge: BridgeDep) -> SetVSyncResult:
    return await _invoke(bridge, "setVSync", body)


@router.post(
    "/set-target-frame-rate",
    response_model=SetTargetFrameRateResult,
    tags=["system"],
    summary="Read or change the target frame rate.",
)
async def set_target_frame_rate(
    body: SetTargetFrameRateRequest,
    bridge: BridgeDep,
) -> SetTargetFrameRateResult:
    return await _invoke(bridge, "setTargetFrameRate", body)


@router.post(
    "/set-frame-latency",
    response_model=SetFrameLatencyResult,
    tags=["system"],
    summary="Read or change frames in flight.",
)
async def set_frame_latency(
    body: SetFrameLatencyRequest,
    bridge: BridgeDep,
) -> SetFrameLatencyResult:
    return await _invoke(bridge, "setFrameLatency", body)


# --------------------------------------------------------------------------- #
# Diagnostics
# --------------------------------------------------------------------------- #


@router.get(
    "/log-tail",
    response_model=GetLogTailResult,
    tags=["diagnostics"],
    summary="Read recent log entries.",
)
async def get_log_tail(
    query: Annotated[GetLogTailRequest, Query()],
    bridge: BridgeDep,
) -> GetLogTailResult:
    return await _invoke(bridge, "getLogTail", query)


@router.get(
    "/metrics",
    response_model=GetMetricsResult,
    tags=["diagnostics"],
    summary="Frame and GPU metrics.",
)
async def get_metrics(bridge: BridgeDep) -> GetMetricsResult:
    return await _invoke(bridge, "getMetrics")


@router.get(
    "/shader-errors",
    response_model=GetShaderErrorsResult,
    tags=["diagnostics"],
    summary="Recent shader compile failures.",
)
async def get_shader_errors(
    query: Annotated[GetShaderErrorsRequest, Query()],
    bridge: BridgeDep,
) -> GetShaderErrorsResult:
    return await _invoke(bridge, "getShaderErrors", query)


@router.get(
    "/frame-samples",
    response_model=GetFrameSamplesResult,
    tags=["diagnostics"],
    summary="Rolling frame durations.",
)
async def get_frame_samples(bridge: BridgeDep) -> GetFrameSamplesResult:
    return await _invoke(bridge, "getFrameSamples")


@router.post(
    "/stall-main-thread",
    response_model=EmptyResult,
    tags=["diagnostics"],
    summary="Block the main thread to test the stall overlay.",
)
async def stall_main_thread(body: StallMainThreadRequest, bridge: BridgeDep) -> EmptyResult:
    return await _invoke(bridge, "stallMainThread", body, timeout=body.seconds + 60.0)


@router.post(
    "/release-gpu-resources",
    response_model=EmptyResult,
    tags=["diagnostics"],
    summary="Free GPU resources at the next frame.",
)
async def release_gpu_resources(bridge: BridgeDep) -> EmptyResult:
    return await _invoke(bridge, "releaseGpuResources")


# --------------------------------------------------------------------------- #
# Graph
# --------------------------------------------------------------------------- #


@router.get("/context", response_model=GetContextResult, tags=["graph"], summary="Editor context.")
async def get_context(bridge: BridgeDep) -> GetContextResult:
    return await _invoke(bridge, "getContext")


@router.get(
    "/graph-state",
    response_model=GetGraphStateResult,
    tags=["graph"],
    summary="Children, inputs, and connections.",
)
async def get_graph_state(
    query: Annotated[GetGraphStateRequest, Query()],
    bridge: BridgeDep,
) -> GetGraphStateResult:
    return await _invoke(bridge, "getGraphState", query)


@router.post("/select", response_model=SelectResult, tags=["graph"], summary="Change the selection.")
async def select(body: SelectRequest, bridge: BridgeDep) -> SelectResult:
    return await _invoke(bridge, "select", body)


@router.get("/graph-view", response_model=GraphView, tags=["graph"], summary="Graph camera state.")
async def get_graph_view(bridge: BridgeDep) -> GraphView:
    return await _invoke(bridge, "getGraphView")


@router.post(
    "/set-graph-view",
    response_model=SetGraphViewResult,
    tags=["graph"],
    summary="Move or zoom the graph camera.",
)
async def set_graph_view(body: SetGraphViewRequest, bridge: BridgeDep) -> SetGraphViewResult:
    return await _invoke(bridge, "setGraphView", body)


@router.post(
    "/focus-graph-view",
    response_model=FocusGraphViewResult,
    tags=["graph"],
    summary="Frame children or the whole graph.",
)
async def focus_graph_view(
    body: FocusGraphViewRequest,
    bridge: BridgeDep,
) -> FocusGraphViewResult:
    return await _invoke(bridge, "focusGraphView", body)


@router.post("/set-input", response_model=SetInputResult, tags=["graph"], summary="Set an input value.")
async def set_input(body: SetInputRequest, bridge: BridgeDep) -> SetInputResult:
    return await _invoke(bridge, "setInput", body)


@router.get("/output", response_model=GetOutputResult, tags=["graph"], summary="Read an output value.")
async def get_output(
    query: Annotated[GetOutputRequest, Query()],
    bridge: BridgeDep,
) -> GetOutputResult:
    return await _invoke(bridge, "getOutput", query)


@router.post("/pump-frames", response_model=EmptyResult, tags=["graph"], summary="Advance frames.")
async def pump_frames(body: PumpFramesRequest | None = None, *, bridge: BridgeDep) -> EmptyResult:
    return await _invoke(bridge, "pumpFrames", body)


@router.post("/add-op", response_model=AddOpResult, tags=["graph"], summary="Add an operator.")
async def add_op(body: AddOpRequest, bridge: BridgeDep) -> AddOpResult:
    return await _invoke(bridge, "addOp", body)


@router.post("/connect", response_model=EmptyResult, tags=["graph"], summary="Connect output to input.")
async def connect(body: ConnectRequest, bridge: BridgeDep) -> EmptyResult:
    return await _invoke(bridge, "connect", body)


@router.delete("/op", response_model=EmptyResult, tags=["graph"], summary="Delete one operator.")
async def delete_op(
    query: Annotated[DeleteOpRequest, Query()],
    bridge: BridgeDep,
) -> EmptyResult:
    return await _invoke(bridge, "deleteOp", query)


@router.post("/pin", response_model=EmptyResult, tags=["graph"], summary="Pin an operator to the output.")
async def pin(body: PinRequest, bridge: BridgeDep) -> EmptyResult:
    return await _invoke(bridge, "pin", body)


@router.post("/set-bypass", response_model=SetBypassResult, tags=["graph"], summary="Bypass an operator.")
async def set_bypass(body: SetBypassRequest, bridge: BridgeDep) -> SetBypassResult:
    return await _invoke(bridge, "setBypass", body)


@router.post("/reset-view", response_model=EmptyResult, tags=["graph"], summary="Reset the output camera.")
async def reset_view(bridge: BridgeDep) -> EmptyResult:
    return await _invoke(bridge, "resetView")


@router.post(
    "/layout-selection",
    response_model=LayoutSelectionResult,
    tags=["graph"],
    summary="Layout the selection.",
)
async def layout_selection(bridge: BridgeDep) -> LayoutSelectionResult:
    return await _invoke(bridge, "layoutSelection")


@router.delete(
    "/selection",
    response_model=DeleteSelectionResult,
    tags=["graph"],
    summary="Delete the selection.",
)
async def delete_selection(
    query: Annotated[DeleteSelectionRequest, Query()],
    bridge: BridgeDep,
) -> DeleteSelectionResult:
    return await _invoke(bridge, "deleteSelection", query)


@router.post("/undo", response_model=UndoRedoResult, tags=["graph"], summary="Undo one command.")
async def undo(bridge: BridgeDep) -> UndoRedoResult:
    return await _invoke(bridge, "undo")


@router.post("/redo", response_model=UndoRedoResult, tags=["graph"], summary="Redo one command.")
async def redo(bridge: BridgeDep) -> UndoRedoResult:
    return await _invoke(bridge, "redo")


# --------------------------------------------------------------------------- #
# Projects and windows
# --------------------------------------------------------------------------- #


@router.post(
    "/open-project",
    response_model=OpenProjectResult,
    tags=["project"],
    summary="Open an existing project.",
)
async def open_project(body: OpenProjectRequest, bridge: BridgeDep) -> OpenProjectResult:
    return await _invoke(bridge, "openProject", body)


@router.post(
    "/new-project",
    response_model=NewProjectResult,
    tags=["project"],
    summary="Create and open a project.",
)
async def new_project(body: NewProjectRequest, bridge: BridgeDep) -> NewProjectResult:
    return await _invoke(bridge, "newProject", body)


@router.post("/reload", response_model=ReloadResult, tags=["project"], summary="Recompile a project.")
async def reload_project(body: ReloadRequest, bridge: BridgeDep) -> ReloadResult:
    return await _invoke(bridge, "reload", body)


@router.post("/open-window", response_model=OpenWindowResult, tags=["project"], summary="Show a window.")
async def open_window(body: OpenWindowRequest, bridge: BridgeDep) -> OpenWindowResult:
    return await _invoke(bridge, "openWindow", body)


@router.post(
    "/output-setup",
    response_model=EmptyResult,
    tags=["project"],
    summary="Drive the output setup UI.",
)
async def output_setup(body: OutputSetupRequest, bridge: BridgeDep) -> EmptyResult:
    return await _invoke(bridge, "outputSetup", body)


# --------------------------------------------------------------------------- #
# Playback
# --------------------------------------------------------------------------- #


@router.post("/set-time", response_model=SetTimeResult, tags=["playback"], summary="Set playback time.")
async def set_time(body: SetTimeRequest, bridge: BridgeDep) -> SetTimeResult:
    return await _invoke(bridge, "setTime", body)


@router.post(
    "/set-playback",
    response_model=SetPlaybackResult,
    tags=["playback"],
    summary="Set playback speed or playing state.",
)
async def set_playback(body: SetPlaybackRequest, bridge: BridgeDep) -> SetPlaybackResult:
    return await _invoke(bridge, "setPlayback", body)


# --------------------------------------------------------------------------- #
# Audio
# --------------------------------------------------------------------------- #


@router.get(
    "/audio-inputs",
    response_model=GetAudioInputsResult,
    tags=["audio"],
    summary="List capture devices.",
)
async def get_audio_inputs(bridge: BridgeDep) -> GetAudioInputsResult:
    return await _invoke(bridge, "getAudioInputs")


@router.post(
    "/set-audio-input",
    response_model=SetAudioInputResult,
    tags=["audio"],
    summary="Choose the audio input device.",
)
async def set_audio_input(body: SetAudioInputRequest, bridge: BridgeDep) -> SetAudioInputResult:
    return await _invoke(bridge, "setAudioInput", body)


@router.post(
    "/start-audio-recording",
    response_model=AudioRecordingResult,
    tags=["audio"],
    summary="Start recording the input.",
)
async def start_audio_recording(bridge: BridgeDep) -> AudioRecordingResult:
    return await _invoke(bridge, "startAudioRecording")


@router.post(
    "/stop-audio-recording",
    response_model=AudioRecordingResult,
    tags=["audio"],
    summary="Stop recording the input.",
)
async def stop_audio_recording(bridge: BridgeDep) -> AudioRecordingResult:
    return await _invoke(bridge, "stopAudioRecording")


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #


@router.post(
    "/start-render",
    response_model=StartRenderResult,
    tags=["render"],
    summary="Export the pinned output to video.",
)
async def start_render(
    body: StartRenderRequest,
    bridge: BridgeDep,
    captures_dir: CapturesDep,
) -> StartRenderResult:
    render_path = Path(body.path).expanduser()
    if not render_path.is_absolute():
        render_path = captures_dir / render_path
    render_path.parent.mkdir(parents=True, exist_ok=True)
    body.path = str(render_path.resolve())
    return await _invoke(bridge, "startRender", body)


@router.get(
    "/render-status",
    response_model=RenderStatusResult,
    tags=["render"],
    summary="Poll export progress.",
)
async def get_render_status(bridge: BridgeDep) -> RenderStatusResult:
    return await _invoke(bridge, "getRenderStatus")


@router.post(
    "/cancel-render",
    response_model=CancelRenderResult,
    tags=["render"],
    summary="Stop an export.",
)
async def cancel_render(bridge: BridgeDep) -> CancelRenderResult:
    return await _invoke(bridge, "cancelRender")


# --------------------------------------------------------------------------- #
# Captures
# --------------------------------------------------------------------------- #


@router.post(
    "/screenshot",
    response_model=ScreenshotResponse,
    tags=["capture"],
    summary="Capture the output texture or the whole editor UI.",
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
    inline: Annotated[bool, Query(description="Return the image bytes instead of metadata.")] = False,
) -> ScreenshotResponse | Response:
    path = resolve_capture_path(
        captures_dir,
        body.path,
        timestamped_name(f"screen_{body.target}"),
    )
    result = await _invoke(bridge, "screenshot", {"path": str(path), "target": body.target})
    written = Path(result.get("path") or path)
    if inline or wants_image(request):
        return image_response(written)
    return screenshot_response(request, written, captures_dir)


@router.post(
    "/screenshot-window",
    response_model=ScreenshotResponse,
    tags=["capture"],
    summary="Capture the editor window, optionally cropped to the graph.",
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
    inline: Annotated[bool, Query(description="Return the image bytes instead of metadata.")] = False,
) -> ScreenshotResponse | Response:
    stem = "window"
    if body.region:
        stem = body.region
    path = resolve_capture_path(captures_dir, body.path, timestamped_name(stem))
    params: dict[str, Any] = {"path": str(path)}
    if body.region:
        params["region"] = body.region
    result = await _invoke(bridge, "screenshotWindow", params)
    written = Path(result.get("path") or path)
    if inline or wants_image(request):
        return image_response(written)
    return screenshot_response(request, written, captures_dir)
