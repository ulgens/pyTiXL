"""
Route packages. Importing the submodules registers the routes in them.

Loosely follows TiXL docs to group the routes.
https://github.com/tixl3d/tixl/blob/b6cc584406c76aebf61910f58d1562bf55c4884e/.agentic/DEBUG_PROTOCOL.md#methods
"""

# TODO: Revisit the "import to register" behaviour.

from . import (  # noqa: F401
    audio_input,
    control_surface,
    diagnosis,
    graph,
    operator,
    read_surface,
    rendering,
    ui_capture,
    uncategorized,
    unknown,
)
from .main import router  # noqa: F401
