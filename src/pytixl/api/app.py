"""FastAPI application factory for the TiXL bridge."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from pytixl import __version__
from pytixl.api.auth import require_token
from pytixl.api.bridge import TixlBridge
from pytixl.api.errors import ApiError
from pytixl.api.middleware import TIXL_RESPONSE_HEADERS, TixlMetadataMiddleware
from pytixl.api.routes import router
from pytixl.api.settings import ApiSettings

logger = logging.getLogger(__name__)


DESCRIPTION = """
Typed HTTP facade over TiXL's local JSON-lines debug bridge.

Start TiXL with `--debug-server 9042`, then launch this server and open `/docs`.
Every protocol method has its own endpoint under `/api`; request and response
bodies use the editor's camelCase spelling while Python fields stay snake_case.
"""


def create_app(settings: ApiSettings | None = None) -> FastAPI:
    """Build the app. The bridge attaches lazily and never launches TiXL."""
    settings = settings or ApiSettings()
    settings.validate()
    captures_dir = settings.resolved_captures_dir()
    captures_dir.mkdir(parents=True, exist_ok=True)

    bridge = TixlBridge(settings.tixl_host, settings.tixl_port)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        await bridge.start()
        try:
            yield
        finally:
            await bridge.close()

    app = FastAPI(
        title=settings.title,
        version=__version__,
        description=DESCRIPTION,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.bridge = bridge
    app.state.captures_dir = captures_dir

    app.add_middleware(TixlMetadataMiddleware)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_origins),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=list(TIXL_RESPONSE_HEADERS),
        )

    @app.exception_handler(ApiError)
    async def _api_exception(_request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.as_body())

    @app.exception_handler(HTTPException)
    async def _http_exception(_request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": "UNAUTHORIZED" if exc.status_code == 401 else "HTTP_ERROR",
                "message": str(exc.detail),
                "method": None,
                "tixlCode": None,
                "detail": None,
            },
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_exception(_request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "code": "VALIDATION_ERROR",
                "message": "Request body or query parameters are invalid.",
                "method": None,
                "tixlCode": None,
                "detail": jsonable_encoder(exc.errors()),
            },
        )

    @app.get("/", include_in_schema=False)
    async def _root() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    app.include_router(router, dependencies=[Depends(require_token)])
    app.mount("/files", StaticFiles(directory=str(captures_dir), check_dir=False), name="files")
    return app


# Create an entrypoint for `fastapi run`
# TODO:
#   fastapi entrypoint duplicates the uvicorn entrypoint, but with "--reload option"
#   uvicorn.run(reload=True) causes an issue that I don't understand yet.
#   There should be one and only entrypoint that supports reload and accessible via pyproject scripts.
app = create_app()


def run() -> None:
    """Console-script entry point kept for ``uvicorn pytixl.api.app:app`` users."""
    from pytixl.api.cli import run as cli_run

    cli_run()
