"""Optional FastAPI bridge over TiXL's debug port.

The package is only importable when the ``api`` extra is installed:

    uv sync --extra api
    pytixl-api --tixl-port 9042
"""

from pytixl.api.bridge import TixlBridge
from pytixl.api.settings import ApiSettings

__all__ = ["ApiSettings", "TixlBridge"]
