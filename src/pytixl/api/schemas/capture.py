"""Screenshot and server-status schemas."""

from typing import Literal

from pydantic import Field

from pytixl.api.schemas.common import ApiModel, ResultModel

ScreenshotTarget = Literal["output", "ui"]
ScreenshotRegion = Literal["graph"]


class ScreenshotRequest(ApiModel):
    path: str | None = None
    target: ScreenshotTarget = "output"


class ScreenshotWindowRequest(ApiModel):
    path: str | None = None
    region: ScreenshotRegion | None = None


class ScreenshotResponse(ResultModel):
    path: str
    url: str | None = None


class HealthResponse(ResultModel):
    status: Literal["ok", "degraded"]
    connected: bool
    tixl_host: str
    tixl_port: int
    api_version: str
    captures_dir: str
    protocol_version: int | None = None
    editor_version: str | None = None
    requests_sent: int
    last_error: str | None = None


class MethodInfo(ResultModel):
    name: str
    tag: str
    summary: str
    timeout_seconds: float
    http_path: str


class MethodsResponse(ResultModel):
    count: int
    methods: list[MethodInfo] = Field(default_factory=list)
