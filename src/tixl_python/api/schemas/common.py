"""Shared schema primitives.

Wire field names follow TiXL's camelCase protocol. Python code uses snake_case;
``model_dump(by_alias=True)`` produces the protocol spelling, and FastAPI
serializes responses by alias as well.
"""

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    """Base for request bodies: strict about unknown fields."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )


class ResultModel(BaseModel):
    """Base for response bodies: tolerant of fields added by newer editors."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )


class EmptyResult(ResultModel):
    """The protocol's empty ``{}`` result."""


class Vector2(ApiModel):
    x: float = Field(alias="X")
    y: float = Field(alias="Y")


class Vector3(ApiModel):
    x: float = Field(alias="X")
    y: float = Field(alias="Y")
    z: float = Field(alias="Z")


class Vector4(ApiModel):
    x: float = Field(alias="X")
    y: float = Field(alias="Y")
    z: float = Field(alias="Z")
    w: float = Field(alias="W")


class Int2(ApiModel):
    x: int = Field(alias="X")
    y: int = Field(alias="Y")


class Rect(ResultModel):
    min_x: float
    min_y: float
    max_x: float
    max_y: float
