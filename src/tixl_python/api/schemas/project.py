"""Project and window schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import model_validator

from tixl_python.api.schemas.common import ApiModel, ResultModel


class OpenProjectRequest(ApiModel):
    name: str | None = None
    symbol_id: UUID | None = None
    pin_output: bool = True

    @model_validator(mode="after")
    def _needs_a_target(self) -> OpenProjectRequest:
        if self.name is None and self.symbol_id is None:
            message = "openProject needs either name or symbol_id"
            raise ValueError(message)
        return self


class OpenProjectResult(ResultModel):
    root_symbol_id: str | None = None
    root_symbol_name: str | None = None
    pinned_output: bool


class NewProjectRequest(ApiModel):
    name: str


class NewProjectResult(ResultModel):
    display_name: str
    home_symbol_id: str


class ReloadRequest(ApiModel):
    project: str


class ReloadResult(ResultModel):
    duration_seconds: float


class OpenWindowRequest(ApiModel):
    name: str
    section: str | None = None


class OpenWindowResult(ResultModel):
    window: str
