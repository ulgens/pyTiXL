"""HTTP error mapping for TiXL debug-protocol failures."""

from pytixl.client import TixlError

# TiXL protocol codes grouped by the HTTP status a client should see.
_STATUS_BY_CODE: dict[str, int] = {
    # Bad input
    "PARSE_ERROR": 400,
    "MISSING_PARAM": 422,
    "MISSING_METHOD": 400,
    "INVALID_PARAM": 422,
    "UNKNOWN_METHOD": 400,
    "AMBIGUOUS": 409,
    "TYPE_MISMATCH": 422,
    "BAD_PATH": 422,
    "BAD_DURATION": 422,
    # Missing state
    "NOT_FOUND": 404,
    "NO_COMPOSITION": 404,
    "NO_GRAPH_WINDOW": 404,
    "NOTHING_TO_FOCUS": 404,
    "NO_OUTPUT": 409,
    # Operations that the editor refused
    "CREATE_FAILED": 409,
    "COMPILE_FAILED": 409,
    "OPEN_FAILED": 409,
    "RENDER_NOT_READY": 409,
    "SCREENSHOT_BUSY": 409,
    "SCREENSHOT_FAILED": 502,
    "NOT_BYPASSABLE": 409,
    "CYCLE": 409,
    # Transport
    "TIMEOUT": 504,
    "CONNECTION_CLOSED": 503,
    "BRIDGE_UNAVAILABLE": 503,
    "INTERNAL_ERROR": 502,
}


class ApiError(Exception):
    """An error rendered with the API's stable error body."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 502,
        method: str | None = None,
        tixl_code: str | None = None,
        detail: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.method = method
        self.tixl_code = tixl_code
        self.detail = detail

    def as_body(self) -> dict[str, object]:
        return {
            "code": self.code,
            "message": self.message,
            "method": self.method,
            "tixlCode": self.tixl_code,
            "detail": self.detail,
        }


def from_tixl_error(error: TixlError) -> ApiError:
    """Translate a protocol error into an HTTP-aware exception."""
    status = _STATUS_BY_CODE.get(error.code, 502)
    return ApiError(
        error.code,
        str(error),
        status_code=status,
        method=error.method,
        tixl_code=error.code,
        detail=error.detail,
    )
