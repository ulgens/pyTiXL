"""Graph, node, connection, and selection schemas."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from pytixl.api.schemas.common import ApiModel, Rect, ResultModel


class SelectRequest(ApiModel):
    child_id: UUID | None = None
    child_ids: list[UUID] | None = None
    add: bool = False


class SelectResult(ResultModel):
    selected_count: int
    not_found: list[str] | None = None


class GraphView(ResultModel):
    scale: float
    scroll_x: float
    scroll_y: float
    visible_area: Rect
    window_x: float
    window_y: float
    window_width: float
    window_height: float


class SetGraphViewRequest(ApiModel):
    area: Rect | None = None
    center_x: float | None = None
    center_y: float | None = None
    scale: float | None = None
    zoom_by: float | None = None
    scroll_by_x: float | None = None
    scroll_by_y: float | None = None
    smooth: bool = False


class SetGraphViewResult(ResultModel):
    """Either ``{appliesNextFrame: true}`` or a full ``GraphView``."""

    applies_next_frame: bool | None = None
    scale: float | None = None
    scroll_x: float | None = None
    scroll_y: float | None = None
    visible_area: Rect | None = None
    window_x: float | None = None
    window_y: float | None = None
    window_width: float | None = None
    window_height: float | None = None


class FocusGraphViewRequest(ApiModel):
    child_ids: list[UUID] | None = None
    all: bool = False
    include_missing: bool = False
    padding: float = 100.0
    smooth: bool = False


class FocusGraphViewResult(ResultModel):
    applies_next_frame: bool
    area: Rect


class GraphInput(ResultModel):
    id: str
    name: str
    is_default: bool
    value: Any = None


class GraphChild(ResultModel):
    child_id: str
    symbol_id: str
    symbol_name: str
    name: str | None = None
    is_bypassed: bool | None = None
    is_disabled: bool | None = None
    pos_x: float | None = None
    pos_y: float | None = None
    inputs: list[GraphInput] = Field(default_factory=list)


class GraphConnection(ResultModel):
    source_parent_or_child_id: str
    source_slot_id: str
    target_parent_or_child_id: str
    target_slot_id: str


class MissingChild(ResultModel):
    child_id: str
    symbol_id: str
    display_name: str
    pos_x: float | None = None
    pos_y: float | None = None


class MissingConnection(GraphConnection):
    multi_input_index: int = 0


class GetGraphStateRequest(ApiModel):
    composition_id: UUID | None = None
    include_defaults: bool = False


class GetGraphStateResult(ResultModel):
    symbol_id: str
    symbol_name: str
    children: list[GraphChild] = Field(default_factory=list)
    connections: list[GraphConnection] = Field(default_factory=list)
    missing_children: list[MissingChild] | None = None
    missing_connections: list[MissingConnection] | None = None


class SetInputRequest(ApiModel):
    composition_id: UUID | None = None
    child_id: UUID
    input_id: UUID | None = None
    input_name: str | None = None
    value: Any

    @model_validator(mode="after")
    def _needs_an_input(self) -> SetInputRequest:
        if self.input_id is None and self.input_name is None:
            message = "setInput needs either input_id or input_name"
            raise ValueError(message)
        return self


class SetInputResult(ResultModel):
    input: str


class GetOutputRequest(ApiModel):
    child_id: UUID | None = None
    output_id: UUID | None = None
    output_name: str | None = None
    update: bool = False
    dump_obj: str | None = None
    read_count: int | None = Field(default=None, ge=0)
    read_offset: int | None = Field(default=None, ge=0)


class GetOutputResult(ResultModel):
    output_id: str
    value_type: str
    value: Any = None


class AddOpRequest(ApiModel):
    composition_id: UUID | None = None
    symbol_id: UUID | None = None
    symbol_name: str | None = None
    pos_x: float | None = None
    pos_y: float | None = None

    @model_validator(mode="after")
    def _needs_a_symbol(self) -> AddOpRequest:
        if self.symbol_id is None and self.symbol_name is None:
            message = "addOp needs either symbol_id or symbol_name"
            raise ValueError(message)
        return self


class AddOpResult(ResultModel):
    child_id: str
    symbol_id: str


class DeleteOpRequest(ApiModel):
    composition_id: UUID | None = None
    child_id: UUID


class ConnectRequest(ApiModel):
    composition_id: UUID | None = None
    source_child_id: UUID
    target_child_id: UUID
    source_output: str | None = None
    target_input: str | None = None
    multi_input_index: int = Field(default=0, ge=0)


class PinRequest(ApiModel):
    child_id: UUID


class SetBypassRequest(ApiModel):
    composition_id: UUID | None = None
    child_id: UUID
    bypassed: bool = True


class SetBypassResult(ResultModel):
    bypassed: bool


class LayoutSelectionResult(ResultModel):
    changed: bool
    selected_ids: list[str] = Field(default_factory=list)


class DeleteSelectionRequest(ApiModel):
    disconnect: bool = False


class DeleteSelectionResult(ResultModel):
    deleted: bool
    selected_ids: list[str] = Field(default_factory=list)


class OutputSetupRequest(ApiModel):
    entity: str | None = None
    mode: str | None = None
