"""Registry of TiXL debug-protocol methods exposed by the HTTP API."""

from dataclasses import dataclass

# Generous enough for a compile or a slow screenshot; the bridge serializes calls.
DEFAULT_TIMEOUT = 120.0


@dataclass(frozen=True, slots=True)
class MethodSpec:
    name: str
    tag: str
    summary: str
    timeout: float = DEFAULT_TIMEOUT


METHODS: tuple[MethodSpec, ...] = (
    MethodSpec("ping", "system", "Check that the debug bridge responds."),
    MethodSpec("setAgentState", "system", "Announce whether the agent is busy or ready."),
    MethodSpec("getVersion", "system", "Protocol and editor version."),
    MethodSpec("getPaths", "system", "Settings, log, temp, cache, and project folders."),
    MethodSpec("shutdown", "system", "Ask the editor to exit.", timeout=30.0),
    MethodSpec("getStructureVersion", "system", "Global symbol-structure version."),
    MethodSpec("getLogTail", "diagnostics", "Read recent buffered log entries."),
    MethodSpec("getContext", "graph", "Focused composition, selection, and output view."),
    MethodSpec("getGraphState", "graph", "Children, inputs, and connections of a composition."),
    MethodSpec("getMetrics", "diagnostics", "Frame, GPU, memory, and render statistics."),
    MethodSpec("getShaderErrors", "diagnostics", "Recent shader compile failures."),
    MethodSpec("getFrameSamples", "diagnostics", "Rolling frame, CPU, and present durations."),
    MethodSpec("screenshot", "capture", "Write an output or full-UI screenshot."),
    MethodSpec("screenshotWindow", "capture", "Capture the editor window or its graph region."),
    MethodSpec("openProject", "project", "Open an existing project.", timeout=300.0),
    MethodSpec("openWindow", "project", "Show an editor window by type name."),
    MethodSpec("select", "graph", "Change the graph selection."),
    MethodSpec("getGraphView", "graph", "Camera scale, scroll, and visible area."),
    MethodSpec("setGraphView", "graph", "Move or zoom the graph camera."),
    MethodSpec("focusGraphView", "graph", "Frame children, the selection, or the whole graph."),
    MethodSpec("setInput", "graph", "Set one input value on a child operator."),
    MethodSpec("getOutput", "graph", "Read an operator output value or summary."),
    MethodSpec("pumpFrames", "graph", "Advance a number of editor frames.", timeout=300.0),
    MethodSpec("newProject", "project", "Scaffold and open a new project.", timeout=900.0),
    MethodSpec("addOp", "graph", "Add an operator to the focused composition."),
    MethodSpec("getAudioInputs", "audio", "List capture devices and the active input."),
    MethodSpec("setAudioInput", "audio", "Choose the composition's audio input device."),
    MethodSpec("startAudioRecording", "audio", "Start writing the input to a WAV file."),
    MethodSpec("stopAudioRecording", "audio", "Stop the WAV recording and return its path."),
    MethodSpec("startRender", "render", "Export the pinned texture to a video file.", timeout=60.0),
    MethodSpec("getRenderStatus", "render", "Poll export progress."),
    MethodSpec("cancelRender", "render", "Stop an in-progress export."),
    MethodSpec("connect", "graph", "Connect an output to an input."),
    MethodSpec("deleteOp", "graph", "Delete one child operator."),
    MethodSpec("pin", "graph", "Pin an operator to the output window."),
    MethodSpec("setBypass", "graph", "Bypass or restore a child operator."),
    MethodSpec("outputSetup", "project", "Drive the output window's setup UI."),
    MethodSpec("resetView", "graph", "Reset the output camera."),
    MethodSpec("reload", "project", "Recompile an editable project.", timeout=300.0),
    MethodSpec("stallMainThread", "diagnostics", "Block the main thread to test the stall overlay.", timeout=180.0),
    MethodSpec("setVSync", "system", "Read or change the VSync setting."),
    MethodSpec("releaseGpuResources", "diagnostics", "Free GPU resources at the next frame."),
    MethodSpec("setTargetFrameRate", "system", "Read or change the target frame rate."),
    MethodSpec("setFrameLatency", "system", "Read or change frames in flight."),
    MethodSpec("layoutSelection", "graph", "Run the graph's layout action on the selection."),
    MethodSpec("deleteSelection", "graph", "Delete the current selection."),
    MethodSpec("undo", "graph", "Undo one command."),
    MethodSpec("redo", "graph", "Redo one command."),
    MethodSpec("setTime", "playback", "Set playback time in bars or seconds."),
    MethodSpec("setPlayback", "playback", "Set playback speed or playing state."),
)

METHODS_BY_NAME: dict[str, MethodSpec] = {spec.name: spec for spec in METHODS}
