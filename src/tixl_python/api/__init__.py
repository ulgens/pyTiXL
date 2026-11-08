"""Optional FastAPI bridge over TiXL's debug port.

The package is only importable when the ``api`` extra is installed:

    uv sync --extra api
    tixl-api --tixl-port 9042
"""

from tixl_python.api.app import create_app
from tixl_python.api.bridge import TixlBridge
from tixl_python.api.settings import ApiSettings

__all__ = ["ApiSettings", "TixlBridge", "create_app"]
