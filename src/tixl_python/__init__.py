"""A small, Pythonic library for building and capturing TiXL patches."""

from tixl_python.capture import Capture
from tixl_python.client import TixlClient, TixlError
from tixl_python.editor import EditorSession
from tixl_python.operators import (
    AsciiRender,
    InputRef,
    LoadImage,
    Operator,
    OutputRef,
    Port,
)
from tixl_python.patch import Patch

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
