"""Capture-path handling and file responses."""

import mimetypes
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from fastapi import Request
from fastapi.responses import FileResponse, Response

from pytixl.api.schemas import ScreenshotResponse


def timestamped_name(stem: str, suffix: str = ".png") -> str:
    stamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S_%f")
    return f"{stem}_{stamp}{suffix}"


def resolve_capture_path(captures_dir: Path, requested: str | None, default_name: str) -> Path:
    """Resolve a client path, keeping relative paths inside the captures folder."""
    if requested is None or not requested.strip():
        path = captures_dir / default_name
    else:
        path = Path(requested).expanduser()
        if not path.is_absolute():
            path = captures_dir / path

    if not path.suffix:
        path = path.with_suffix(".png")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def file_url(request: Request, path: Path, captures_dir: Path) -> str | None:
    """Return the ``/files`` URL when the capture lives in the captures folder."""
    try:
        relative = path.resolve().relative_to(captures_dir.resolve())
    except ValueError:
        return None
    return f"/files/{quote(relative.as_posix())}"


def wants_image(request: Request) -> bool:
    accept = request.headers.get("accept", "").lower()
    return "image/png" in accept or "image/jpeg" in accept


def image_response(path: Path) -> Response:
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return FileResponse(path, media_type=media_type, filename=path.name)


def screenshot_response(request: Request, path: Path, captures_dir: Path) -> ScreenshotResponse:
    return ScreenshotResponse(path=str(path), url=file_url(request, path, captures_dir))
