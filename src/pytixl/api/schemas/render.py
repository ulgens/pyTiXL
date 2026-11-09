"""Render-export schemas."""

from pydantic import Field

from pytixl.api.schemas.common import ApiModel, ResultModel


class StartRenderRequest(ApiModel):
    path: str
    duration_secs: float = Field(gt=0)
    start_secs: float = Field(default=0.0, ge=0)
    fps: float = Field(default=60.0, gt=0)
    export_audio: bool = True
    codec: str | None = None


class StartRenderResult(ResultModel):
    path: str
    frame_count: int


class RenderStatusResult(ResultModel):
    state: str
    is_exporting: bool
    progress: float
    frame_index: int
    message: str | None = None


class CancelRenderResult(ResultModel):
    message: str | None = None
