"""A small, Pythonic library for building and capturing TiXL patches."""

from pytixl.capture import Capture
from pytixl.client import TixlClient, TixlError
from pytixl.editor import EditorSession
from pytixl.operators import (
    AsciiRender,
    InputRef,
    LoadImage,
    Operator,
    OutputRef,
    Port,
)
from pytixl.patch import Patch

__version__ = "0.1.0"

__all__ = [
    "AsciiRender",
    "Capture",
    "EditorSession",
    "InputRef",
    "LoadImage",
    "Operator",
    "OutputRef",
    "Patch",
    "Port",
    "TixlClient",
    "TixlError",
]
