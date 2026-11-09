"""System, playback, diagnostics, and agent-state schemas."""

from typing import Literal

from pydantic import Field

from pytixl.api.schemas.common import ApiModel, ResultModel

LogLevel = Literal["debug", "info", "warning", "warn", "error"]
AgentState = Literal["busy", "ready", ""]


class SetAgentStateRequest(ApiModel):
    state: AgentState = ""
    note: str | None = None


class SetAgentStateResult(ResultModel):
    state: str


class GetVersionResult(ResultModel):
    protocol_version: int
    editor_version: str | None = None


class GetPathsResult(ResultModel):
    settings: str | None = None
    log: str | None = None
    temp: str | None = None
    cache: str | None = None
    projects: str | None = None


class GetStructureVersionResult(ResultModel):
    symbol_structure_version: int


class LogEntry(ResultModel):
    seq: int
    time: str
    level: str
    message: str
    source_id: str | None = None


class GetLogTailRequest(ApiModel):
    since_seq: int = -1
    max_count: int = 200
    min_level: LogLevel = "debug"


class GetLogTailResult(ResultModel):
    entries: list[LogEntry] = Field(default_factory=list)
    latest_seq: int
    oldest_available_seq: int


class PlaybackTime(ResultModel):
    time_in_bars: float
    time_in_secs: float
    playback_speed: float
    is_playing: bool
    bpm: float


class SelectedChild(ResultModel):
    child_id: str
    name: str


class OutputView(ResultModel):
    is_pinned: bool
    child_id: str | None = None
    symbol_name: str | None = None
    path: list[str] | None = None


class GetContextResult(ResultModel):
    has_open_project: bool
    time: PlaybackTime
    composition_symbol_id: str | None = None
    composition_name: str | None = None
    composition_path: list[str] | None = None
    selected_children: list[SelectedChild] | None = None
    output_view: OutputView | None = None


class GpuMemory(ResultModel):
    current_usage_mb: float
    budget_mb: float
    resource_mb: float | None = None


class GetMetricsResult(ResultModel):
    frame_delta_seconds: float
    fps: float
    frame_period_ms: float
    refresh_rate_hz: float
    visual_delta_ms: float
    vblanks_per_frame: float
    frame_speed_factor: float
    gpu_frame_ms: float
    presentation_mode: str
    queued_frames: int
    gc_total_memory_mb: float
    state_stack_depth: int
    render_stats: dict[str, int] = Field(default_factory=dict)
    gpu_memory: GpuMemory | None = None
    live_gpu_resources: int


class ShaderFailure(ResultModel):
    time: str
    name: str
    entry_point: str
    reason: str
    owner_path: str | None = None
    owner_id: str | None = None
    source_path: str | None = None
    source_line_count: int | None = None
    source: str | None = None
    source_error: str | None = None


class GetShaderErrorsRequest(ApiModel):
    clear: bool = False
    include_source: bool = False


class GetShaderErrorsResult(ResultModel):
    cleared: bool | None = None
    count: int | None = None
    failures: list[ShaderFailure] = Field(default_factory=list)


class GetFrameSamplesResult(ResultModel):
    total_frames: int
    frame_ms: list[float] = Field(default_factory=list)
    cpu_ms: list[float] = Field(default_factory=list)
    present_ms: list[float] = Field(default_factory=list)


class PumpFramesRequest(ApiModel):
    count: int = Field(default=1, ge=1, le=100_000)


class StallMainThreadRequest(ApiModel):
    seconds: float = Field(default=5.0, ge=0.0, le=120.0)
    estimate_key: str | None = None
    message: str = "Simulating work..."


class SetVSyncRequest(ApiModel):
    value: bool | None = None


class SetVSyncResult(ResultModel):
    use_vsync: bool


class SetTargetFrameRateRequest(ApiModel):
    value: int | None = Field(default=None, ge=0)


class SetTargetFrameRateResult(ResultModel):
    target_frame_rate: int


class SetFrameLatencyRequest(ApiModel):
    value: int | None = Field(default=None, ge=1, le=2)


class SetFrameLatencyResult(ResultModel):
    frame_latency: int


class SetTimeRequest(ApiModel):
    time_in_bars: float | None = None
    time_in_secs: float | None = None


class SetTimeResult(ResultModel):
    time_in_bars: float
    time_in_secs: float


class SetPlaybackRequest(ApiModel):
    speed: float | None = None
    playing: bool | None = None


class SetPlaybackResult(ResultModel):
    playback_speed: float


class UndoRedoResult(ResultModel):
    can_undo: bool
    can_redo: bool
