"""Explicit, typed HTTP routes for every TiXL debug-protocol method."""

from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response

from tixl_python import __version__
from tixl_python.api.bridge import CallResult, TixlBridge
from tixl_python.api.captures import (
    image_response,
    resolve_capture_path,
    screenshot_response,
    timestamped_name,
    wants_image,
)
from tixl_python.api.errors import from_tixl_error
from tixl_python.api.protocol import METHODS_BY_NAME
from tixl_python.api.schemas import (
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
    Envelope,
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
    MethodInfo,
    MethodsResponse,
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
    StatusResponse,
    UndoRedoResult,
)
from tixl_python.client import TixlError
from tixl_python.config import DEFAULT_PORT

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
) -> CallResult:
    spec = METHODS_BY_NAME[method]
    try:
        return await bridge.call(method, _params(body), timeout or spec.timeout)
    except TixlError as exc:
        raise from_tixl_error(exc) from exc


def _envelope[T](result_type: type[T], call: CallResult) -> Envelope[T]:
    return Envelope[result_type](
        result=result_type.model_validate(call.result),
        frame=call.frame,
        playback_frame=call.playback_frame,
        structure_version=call.structure_version,
    )


# --------------------------------------------------------------------------- #
# System
# --------------------------------------------------------------------------- #


@router.post("/ping", response_model=Envelope[EmptyResult], tags=["system"], summary="Ping the editor.")
async def ping(bridge: BridgeDep) -> Envelope[EmptyResult]:
    return _envelope(EmptyResult, await _invoke(bridge, "ping"))


@router.post(
    "/setAgentState",
    response_model=Envelope[SetAgentStateResult],
    tags=["system"],
    summary="Announce whether the agent is busy or ready.",
)
async def set_agent_state(body: SetAgentStateRequest, bridge: BridgeDep) -> Envelope[SetAgentStateResult]:
    return _envelope(SetAgentStateResult, await _invoke(bridge, "setAgentState", body))


@router.post("/getVersion", response_model=Envelope[GetVersionResult], tags=["system"], summary="Protocol version.")
async def get_version(bridge: BridgeDep) -> Envelope[GetVersionResult]:
    return _envelope(GetVersionResult, await _invoke(bridge, "getVersion"))


@router.post("/getPaths", response_model=Envelope[GetPathsResult], tags=["system"], summary="Editor folders.")
async def get_paths(bridge: BridgeDep) -> Envelope[GetPathsResult]:
    return _envelope(GetPathsResult, await _invoke(bridge, "getPaths"))


@router.post("/shutdown", response_model=Envelope[EmptyResult], tags=["system"], summary="Exit the editor.")
async def shutdown(bridge: BridgeDep) -> Envelope[EmptyResult]:
    return _envelope(EmptyResult, await _invoke(bridge, "shutdown"))


@router.post(
    "/getStructureVersion",
    response_model=Envelope[GetStructureVersionResult],
    tags=["system"],
    summary="Symbol-structure version.",
)
async def get_structure_version(bridge: BridgeDep) -> Envelope[GetStructureVersionResult]:
    return _envelope(GetStructureVersionResult, await _invoke(bridge, "getStructureVersion"))


@router.post(
    "/setVSync",
    response_model=Envelope[SetVSyncResult],
    tags=["system"],
    summary="Read or change VSync.",
)
async def set_vsync(body: SetVSyncRequest, bridge: BridgeDep) -> Envelope[SetVSyncResult]:
    return _envelope(SetVSyncResult, await _invoke(bridge, "setVSync", body))


@router.post(
    "/setTargetFrameRate",
    response_model=Envelope[SetTargetFrameRateResult],
    tags=["system"],
    summary="Read or change the target frame rate.",
)
async def set_target_frame_rate(
    body: SetTargetFrameRateRequest,
    bridge: BridgeDep,
) -> Envelope[SetTargetFrameRateResult]:
    return _envelope(SetTargetFrameRateResult, await _invoke(bridge, "setTargetFrameRate", body))


@router.post(
    "/setFrameLatency",
    response_model=Envelope[SetFrameLatencyResult],
    tags=["system"],
    summary="Read or change frames in flight.",
)
async def set_frame_latency(
    body: SetFrameLatencyRequest,
    bridge: BridgeDep,
) -> Envelope[SetFrameLatencyResult]:
    return _envelope(SetFrameLatencyResult, await _invoke(bridge, "setFrameLatency", body))


# --------------------------------------------------------------------------- #
# Diagnostics
# --------------------------------------------------------------------------- #


@router.post(
    "/getLogTail",
    response_model=Envelope[GetLogTailResult],
    tags=["diagnostics"],
    summary="Read recent log entries.",
)
async def get_log_tail(body: GetLogTailRequest, bridge: BridgeDep) -> Envelope[GetLogTailResult]:
    return _envelope(GetLogTailResult, await _invoke(bridge, "getLogTail", body))


@router.post(
    "/getMetrics",
    response_model=Envelope[GetMetricsResult],
    tags=["diagnostics"],
    summary="Frame and GPU metrics.",
)
async def get_metrics(bridge: BridgeDep) -> Envelope[GetMetricsResult]:
    return _envelope(GetMetricsResult, await _invoke(bridge, "getMetrics"))


@router.post(
    "/getShaderErrors",
    response_model=Envelope[GetShaderErrorsResult],
    tags=["diagnostics"],
    summary="Recent shader compile failures.",
)
async def get_shader_errors(
    body: GetShaderErrorsRequest,
    bridge: BridgeDep,
) -> Envelope[GetShaderErrorsResult]:
    return _envelope(GetShaderErrorsResult, await _invoke(bridge, "getShaderErrors", body))


@router.post(
    "/getFrameSamples",
    response_model=Envelope[GetFrameSamplesResult],
    tags=["diagnostics"],
    summary="Rolling frame durations.",
)
async def get_frame_samples(bridge: BridgeDep) -> Envelope[GetFrameSamplesResult]:
    return _envelope(GetFrameSamplesResult, await _invoke(bridge, "getFrameSamples"))


@router.post(
    "/stallMainThread",
    response_model=Envelope[EmptyResult],
    tags=["diagnostics"],
    summary="Block the main thread to test the stall overlay.",
)
async def stall_main_thread(body: StallMainThreadRequest, bridge: BridgeDep) -> Envelope[EmptyResult]:
    call = await _invoke(bridge, "stallMainThread", body, timeout=body.seconds + 60.0)
    return _envelope(EmptyResult, call)


@router.post(
    "/releaseGpuResources",
    response_model=Envelope[EmptyResult],
    tags=["diagnostics"],
    summary="Free GPU resources at the next frame.",
)
async def release_gpu_resources(bridge: BridgeDep) -> Envelope[EmptyResult]:
    return _envelope(EmptyResult, await _invoke(bridge, "releaseGpuResources"))


# --------------------------------------------------------------------------- #
# Graph
# --------------------------------------------------------------------------- #


@router.post("/getContext", response_model=Envelope[GetContextResult], tags=["graph"], summary="Editor context.")
async def get_context(bridge: BridgeDep) -> Envelope[GetContextResult]:
    return _envelope(GetContextResult, await _invoke(bridge, "getContext"))


@router.post(
    "/getGraphState",
    response_model=Envelope[GetGraphStateResult],
    tags=["graph"],
    summary="Children, inputs, and connections.",
)
async def get_graph_state(body: GetGraphStateRequest, bridge: BridgeDep) -> Envelope[GetGraphStateResult]:
    return _envelope(GetGraphStateResult, await _invoke(bridge, "getGraphState", body))


@router.post("/select", response_model=Envelope[SelectResult], tags=["graph"], summary="Change the selection.")
async def select(body: SelectRequest, bridge: BridgeDep) -> Envelope[SelectResult]:
    return _envelope(SelectResult, await _invoke(bridge, "select", body))


@router.post("/getGraphView", response_model=Envelope[GraphView], tags=["graph"], summary="Graph camera state.")
async def get_graph_view(bridge: BridgeDep) -> Envelope[GraphView]:
    return _envelope(GraphView, await _invoke(bridge, "getGraphView"))


@router.post(
    "/setGraphView",
    response_model=Envelope[SetGraphViewResult],
    tags=["graph"],
    summary="Move or zoom the graph camera.",
)
async def set_graph_view(body: SetGraphViewRequest, bridge: BridgeDep) -> Envelope[SetGraphViewResult]:
    return _envelope(SetGraphViewResult, await _invoke(bridge, "setGraphView", body))


@router.post(
    "/focusGraphView",
    response_model=Envelope[FocusGraphViewResult],
    tags=["graph"],
    summary="Frame children or the whole graph.",
)
async def focus_graph_view(
    body: FocusGraphViewRequest,
    bridge: BridgeDep,
) -> Envelope[FocusGraphViewResult]:
    return _envelope(FocusGraphViewResult, await _invoke(bridge, "focusGraphView", body))


@router.post("/setInput", response_model=Envelope[SetInputResult], tags=["graph"], summary="Set an input value.")
async def set_input(body: SetInputRequest, bridge: BridgeDep) -> Envelope[SetInputResult]:
    return _envelope(SetInputResult, await _invoke(bridge, "setInput", body))


@router.post("/getOutput", response_model=Envelope[GetOutputResult], tags=["graph"], summary="Read an output value.")
async def get_output(body: GetOutputRequest, bridge: BridgeDep) -> Envelope[GetOutputResult]:
    return _envelope(GetOutputResult, await _invoke(bridge, "getOutput", body))


@router.post("/pumpFrames", response_model=Envelope[EmptyResult], tags=["graph"], summary="Advance frames.")
async def pump_frames(body: PumpFramesRequest | None = None, *, bridge: BridgeDep) -> Envelope[EmptyResult]:
    return _envelope(EmptyResult, await _invoke(bridge, "pumpFrames", body))


@router.post("/addOp", response_model=Envelope[AddOpResult], tags=["graph"], summary="Add an operator.")
async def add_op(body: AddOpRequest, bridge: BridgeDep) -> Envelope[AddOpResult]:
    return _envelope(AddOpResult, await _invoke(bridge, "addOp", body))


@router.post("/connect", response_model=Envelope[EmptyResult], tags=["graph"], summary="Connect output to input.")
async def connect(body: ConnectRequest, bridge: BridgeDep) -> Envelope[EmptyResult]:
    return _envelope(EmptyResult, await _invoke(bridge, "connect", body))


@router.post("/deleteOp", response_model=Envelope[EmptyResult], tags=["graph"], summary="Delete one operator.")
async def delete_op(body: DeleteOpRequest, bridge: BridgeDep) -> Envelope[EmptyResult]:
    return _envelope(EmptyResult, await _invoke(bridge, "deleteOp", body))


@router.post("/pin", response_model=Envelope[EmptyResult], tags=["graph"], summary="Pin an operator to the output.")
async def pin(body: PinRequest, bridge: BridgeDep) -> Envelope[EmptyResult]:
    return _envelope(EmptyResult, await _invoke(bridge, "pin", body))


@router.post("/setBypass", response_model=Envelope[SetBypassResult], tags=["graph"], summary="Bypass an operator.")
async def set_bypass(body: SetBypassRequest, bridge: BridgeDep) -> Envelope[SetBypassResult]:
    return _envelope(SetBypassResult, await _invoke(bridge, "setBypass", body))


@router.post("/resetView", response_model=Envelope[EmptyResult], tags=["graph"], summary="Reset the output camera.")
async def reset_view(bridge: BridgeDep) -> Envelope[EmptyResult]:
    return _envelope(EmptyResult, await _invoke(bridge, "resetView"))


@router.post(
    "/layoutSelection",
    response_model=Envelope[LayoutSelectionResult],
    tags=["graph"],
    summary="Layout the selection.",
)
async def layout_selection(bridge: BridgeDep) -> Envelope[LayoutSelectionResult]:
    return _envelope(LayoutSelectionResult, await _invoke(bridge, "layoutSelection"))


@router.post(
    "/deleteSelection",
    response_model=Envelope[DeleteSelectionResult],
    tags=["graph"],
    summary="Delete the selection.",
)
async def delete_selection(
    body: DeleteSelectionRequest,
    bridge: BridgeDep,
) -> Envelope[DeleteSelectionResult]:
    return _envelope(DeleteSelectionResult, await _invoke(bridge, "deleteSelection", body))


@router.post("/undo", response_model=Envelope[UndoRedoResult], tags=["graph"], summary="Undo one command.")
async def undo(bridge: BridgeDep) -> Envelope[UndoRedoResult]:
    return _envelope(UndoRedoResult, await _invoke(bridge, "undo"))


@router.post("/redo", response_model=Envelope[UndoRedoResult], tags=["graph"], summary="Redo one command.")
async def redo(bridge: BridgeDep) -> Envelope[UndoRedoResult]:
    return _envelope(UndoRedoResult, await _invoke(bridge, "redo"))


# --------------------------------------------------------------------------- #
# Projects and windows
# --------------------------------------------------------------------------- #


@router.post(
    "/openProject",
    response_model=Envelope[OpenProjectResult],
    tags=["project"],
    summary="Open an existing project.",
)
async def open_project(body: OpenProjectRequest, bridge: BridgeDep) -> Envelope[OpenProjectResult]:
    return _envelope(OpenProjectResult, await _invoke(bridge, "openProject", body))


@router.post(
    "/newProject",
    response_model=Envelope[NewProjectResult],
    tags=["project"],
    summary="Create and open a project.",
)
async def new_project(body: NewProjectRequest, bridge: BridgeDep) -> Envelope[NewProjectResult]:
    return _envelope(NewProjectResult, await _invoke(bridge, "newProject", body))


@router.post("/reload", response_model=Envelope[ReloadResult], tags=["project"], summary="Recompile a project.")
async def reload_project(body: ReloadRequest, bridge: BridgeDep) -> Envelope[ReloadResult]:
    return _envelope(ReloadResult, await _invoke(bridge, "reload", body))


@router.post("/openWindow", response_model=Envelope[OpenWindowResult], tags=["project"], summary="Show a window.")
async def open_window(body: OpenWindowRequest, bridge: BridgeDep) -> Envelope[OpenWindowResult]:
    return _envelope(OpenWindowResult, await _invoke(bridge, "openWindow", body))


@router.post(
    "/outputSetup",
    response_model=Envelope[EmptyResult],
    tags=["project"],
    summary="Drive the output setup UI.",
)
async def output_setup(body: OutputSetupRequest, bridge: BridgeDep) -> Envelope[EmptyResult]:
    return _envelope(EmptyResult, await _invoke(bridge, "outputSetup", body))


# --------------------------------------------------------------------------- #
# Playback
# --------------------------------------------------------------------------- #


@router.post("/setTime", response_model=Envelope[SetTimeResult], tags=["playback"], summary="Set playback time.")
async def set_time(body: SetTimeRequest, bridge: BridgeDep) -> Envelope[SetTimeResult]:
    return _envelope(SetTimeResult, await _invoke(bridge, "setTime", body))


@router.post(
    "/setPlayback",
    response_model=Envelope[SetPlaybackResult],
    tags=["playback"],
    summary="Set playback speed or playing state.",
)
async def set_playback(body: SetPlaybackRequest, bridge: BridgeDep) -> Envelope[SetPlaybackResult]:
    return _envelope(SetPlaybackResult, await _invoke(bridge, "setPlayback", body))


# --------------------------------------------------------------------------- #
# Audio
# --------------------------------------------------------------------------- #


@router.post(
    "/getAudioInputs",
    response_model=Envelope[GetAudioInputsResult],
    tags=["audio"],
    summary="List capture devices.",
)
async def get_audio_inputs(bridge: BridgeDep) -> Envelope[GetAudioInputsResult]:
    return _envelope(GetAudioInputsResult, await _invoke(bridge, "getAudioInputs"))


@router.post(
    "/setAudioInput",
    response_model=Envelope[SetAudioInputResult],
    tags=["audio"],
    summary="Choose the audio input device.",
)
async def set_audio_input(body: SetAudioInputRequest, bridge: BridgeDep) -> Envelope[SetAudioInputResult]:
    return _envelope(SetAudioInputResult, await _invoke(bridge, "setAudioInput", body))


@router.post(
    "/startAudioRecording",
    response_model=Envelope[AudioRecordingResult],
    tags=["audio"],
    summary="Start recording the input.",
)
async def start_audio_recording(bridge: BridgeDep) -> Envelope[AudioRecordingResult]:
    return _envelope(AudioRecordingResult, await _invoke(bridge, "startAudioRecording"))


@router.post(
    "/stopAudioRecording",
    response_model=Envelope[AudioRecordingResult],
    tags=["audio"],
    summary="Stop recording the input.",
)
async def stop_audio_recording(bridge: BridgeDep) -> Envelope[AudioRecordingResult]:
    return _envelope(AudioRecordingResult, await _invoke(bridge, "stopAudioRecording"))


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #


@router.post(
    "/startRender",
    response_model=Envelope[StartRenderResult],
    tags=["render"],
    summary="Export the pinned output to video.",
)
async def start_render(
    body: StartRenderRequest,
    bridge: BridgeDep,
    captures_dir: CapturesDep,
) -> Envelope[StartRenderResult]:
    render_path = Path(body.path).expanduser()
    if not render_path.is_absolute():
        render_path = captures_dir / render_path
    render_path.parent.mkdir(parents=True, exist_ok=True)
    body.path = str(render_path.resolve())
    return _envelope(StartRenderResult, await _invoke(bridge, "startRender", body))


@router.post(
    "/getRenderStatus",
    response_model=Envelope[RenderStatusResult],
    tags=["render"],
    summary="Poll export progress.",
)
async def get_render_status(bridge: BridgeDep) -> Envelope[RenderStatusResult]:
    return _envelope(RenderStatusResult, await _invoke(bridge, "getRenderStatus"))


@router.post(
    "/cancelRender",
    response_model=Envelope[CancelRenderResult],
    tags=["render"],
    summary="Stop an export.",
)
async def cancel_render(bridge: BridgeDep) -> Envelope[CancelRenderResult]:
    return _envelope(CancelRenderResult, await _invoke(bridge, "cancelRender"))


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
    call = await _invoke(bridge, "screenshot", {"path": str(path), "target": body.target})
    written = Path(call.result.get("path") or path)
    if inline or wants_image(request):
        return image_response(written)
    return screenshot_response(request, written, captures_dir)


@router.post(
    "/screenshotWindow",
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
    call = await _invoke(bridge, "screenshotWindow", params)
    written = Path(call.result.get("path") or path)
    if inline or wants_image(request):
        return image_response(written)
    return screenshot_response(request, written, captures_dir)


# --------------------------------------------------------------------------- #
# Server metadata
# --------------------------------------------------------------------------- #


@router.get("/methods", response_model=MethodsResponse, tags=["status"], summary="List typed methods.")
async def list_methods() -> MethodsResponse:
    methods = [
        MethodInfo(
            name=spec.name,
            tag=spec.tag,
            summary=spec.summary,
            timeout_seconds=spec.timeout,
            http_path=f"/api/{spec.name}",
        )
        for spec in METHODS_BY_NAME.values()
    ]
    return MethodsResponse(count=len(methods), methods=methods)


@router.get("/status", response_model=StatusResponse, tags=["status"], summary="Bridge status.")
async def status(bridge: BridgeDep, captures_dir: CapturesDep) -> StatusResponse:
    return StatusResponse(
        connected=bridge.connected,
        tixl_host=bridge.host,
        tixl_port=bridge.port,
        captures_dir=str(captures_dir),
        requests_sent=bridge.request_count,
    )


@router.get("/version", tags=["status"], summary="API version.")
async def api_version() -> dict[str, str]:
    return {"name": "tixl-python", "version": __version__, "default_tixl_port": str(DEFAULT_PORT)}
