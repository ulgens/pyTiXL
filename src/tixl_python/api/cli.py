"""``tixl-api`` console script."""

from pathlib import Path
from typing import Annotated

import typer

from tixl_python.api.settings import ApiSettings

app = typer.Typer(add_completion=False, no_args_is_help=True, help="Serve the typed TiXL bridge API.")


@app.command()
def serve(
    host: Annotated[str, typer.Option(help="HTTP bind address.")] = "127.0.0.1",
    port: Annotated[int, typer.Option(help="HTTP port.")] = 8787,
    tixl_host: Annotated[str, typer.Option(help="TiXL debug-bridge host.")] = "127.0.0.1",
    tixl_port: Annotated[int, typer.Option(help="TiXL debug-bridge port.")] = 9042,
    captures_dir: Annotated[Path, typer.Option(help="Directory for screenshots and exports.")] = Path("captures"),
    token: Annotated[
        str | None,
        typer.Option(envvar="TIXL_API_TOKEN", help="Bearer token; required for non-local binds."),
    ] = None,
    cors_origin: Annotated[
        list[str] | None,
        typer.Option(help="Allowed CORS origin; repeat for several."),
    ] = None,
    log_level: Annotated[str, typer.Option(help="uvicorn log level.")] = "info",
) -> None:
    """Attach to a running TiXL editor and expose it over HTTP with Swagger UI."""
    try:
        import uvicorn

        from tixl_python.api.app import create_app
    except ImportError as exc:
        typer.echo(
            "The API extra is not installed. Run: uv sync --extra api",
            err=True,
        )
        raise typer.Exit(code=1) from exc

    settings = ApiSettings(
        host=host,
        port=port,
        tixl_host=tixl_host,
        tixl_port=tixl_port,
        captures_dir=captures_dir,
        token=token,
        cors_origins=tuple(cors_origin or ()),
    )
    try:
        settings.validate()
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"TiXL bridge: http://{settings.host}:{settings.port}/docs")
    typer.echo(f"Attaching to TiXL on {settings.tixl_host}:{settings.tixl_port}")
    uvicorn.run(create_app(settings), host=settings.host, port=settings.port, log_level=log_level, workers=1)


def run() -> None:
    app()
