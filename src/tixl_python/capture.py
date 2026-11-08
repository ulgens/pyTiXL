"""Capturing the graph view and the rendered output."""

import contextlib
import logging
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from tixl_python.client import TixlClient, TixlError

log = logging.getLogger(__name__)

__all__ = [
    "Capture",
    "CapturePaths",
    "capture_graph",
    "capture_output",
    "resolve_capture_paths",
]


@dataclass(frozen=True)
class Capture:
    """Files produced by :meth:`tixl_python.Patch.screenshot`."""

    graph: Path | None = None
    output: Path | None = None
    ui: Path | None = None


@dataclass(frozen=True)
class CapturePaths:
    graph: Path
    output: Path
    ui: Path


def resolve_capture_paths(
    path: str | Path | None,
    *,
    target: str = "all",
) -> CapturePaths:
    """Resolve the user-facing ``path`` argument into concrete file paths.

    A directory (or no path) receives ``patch_graph.png`` and
    ``patch_output.png``. A ``.png``/``.jpg`` path is treated as the output
    image; the graph is written next to it with a ``_graph`` suffix.
    """
    if path is None:
        directory = Path.cwd() / f"tixl_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output = directory / "patch_output.png"
        graph = directory / "patch_graph.png"
        ui = directory / "patch_ui_full.png"
        directory.mkdir(parents=True, exist_ok=True)
        return CapturePaths(graph=graph, output=output, ui=ui)

    resolved = Path(path).expanduser()
    is_file_path = resolved.suffix.lower() in {".png", ".jpg", ".jpeg"}

    if not is_file_path:
        resolved.mkdir(parents=True, exist_ok=True)
        return CapturePaths(
            graph=resolved / "patch_graph.png",
            output=resolved / "patch_output.png",
            ui=resolved / "patch_ui_full.png",
        )

    resolved.parent.mkdir(parents=True, exist_ok=True)
    stem = resolved.stem
    suffix = resolved.suffix
    if target == "graph":
        return CapturePaths(
            graph=resolved,
            output=resolved.with_name(f"{stem}_output{suffix}"),
            ui=resolved.with_name(f"{stem}_ui{suffix}"),
        )
    return CapturePaths(
        graph=resolved.with_name(f"{stem}_graph{suffix}"),
        output=resolved,
        ui=resolved.with_name(f"{stem}_ui{suffix}"),
    )


def crop_image(src: Path, dst: Path, box: tuple[int, int, int, int]) -> bool:
    """Crop src to (x, y, width, height). Returns True on success."""
    x, y, width, height = box
    if width <= 0 or height <= 0:
        return False

    try:
        from PIL import Image  # type: ignore[import-not-found]

        with Image.open(src) as image:
            image.crop((x, y, x + width, y + height)).save(dst)
        return True
    except ImportError:
        pass
    except Exception:
        return False

    if sys.platform == "darwin" and shutil.which("sips"):
        result = subprocess.run(
            [
                "sips",
                "-c",
                str(height),
                str(width),
                "--cropOffset",
                str(y),
                str(x),
                str(src),
                "--out",
                str(dst),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0 and dst.exists()

    for tool in ("magick", "convert"):
        exe = shutil.which(tool)
        if exe:
            result = subprocess.run(
                [exe, str(src), "-crop", f"{width}x{height}+{x}+{y}", "+repage", str(dst)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return result.returncode == 0 and dst.exists()

    if shutil.which("ffmpeg"):
        result = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(src),
                "-vf",
                f"crop={width}:{height}:{x}:{y}",
                str(dst),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0 and dst.exists()

    return False


def capture_graph(
    client: TixlClient,
    graph_path: Path,
    child_ids: list[str],
    *,
    crop_scale: str = "auto",
    ui_path: Path | None = None,
) -> Path | None:
    """Frame and capture the graph canvas containing ``child_ids``."""
    graph_path.unlink(missing_ok=True)
    ui_path = ui_path or graph_path.with_name(f"{graph_path.stem}_ui_full{graph_path.suffix}")

    # This is the behaviour behind TiXL's F shortcut: fit the canvas to the
    # selection (plus padding) so the patch is centred and fully visible.
    try:
        client.call("select", childIds=child_ids)
        client.call("focusGraphView", childIds=child_ids, padding=80)
        client.pump(75)
    except TixlError as error:
        log.warning("Could not focus the graph: %s", error)

    # Windows-only native capture of exactly the graph canvas.
    try:
        client.call(
            "screenshotWindow",
            timeout=120,
            path=str(graph_path.resolve()),
            region="graph",
        )
        if graph_path.exists():
            log.info("Saved graph screenshot: %s", graph_path)
            return graph_path
    except TixlError as error:
        log.info("Native graph capture unavailable (%s); using a UI crop.", error.code)

    # macOS/Linux: capture the whole editor UI from the back buffer and crop to
    # the graph canvas using getGraphView's screen rectangle.
    try:
        view = client.call("getGraphView")
        client.call("screenshot", timeout=120, path=str(ui_path.resolve()), target="ui")
        client.pump(2)

        scale = 1.0 if crop_scale == "auto" else float(crop_scale)
        box = (
            round(float(view.get("windowX", 0)) * scale),
            round(float(view.get("windowY", 0)) * scale),
            round(float(view.get("windowWidth", 0)) * scale),
            round(float(view.get("windowHeight", 0)) * scale),
        )
        if crop_image(ui_path, graph_path, box):
            log.info("Saved graph screenshot (UI crop, scale %g): %s", scale, graph_path)
            return graph_path

        log.warning("Could not crop the UI capture; kept the full window image: %s", ui_path)
        return ui_path
    except TixlError as error:
        log.warning("Could not capture the graph: %s", error)
        return None


def capture_output(
    client: TixlClient,
    output_path: Path,
    child_id: str,
) -> Path | None:
    """Pin ``child_id`` and capture its rendered output."""
    output_path.unlink(missing_ok=True)

    with contextlib.suppress(TixlError):
        client.call("openWindow", name="OutputWindow")

    for attempt in range(3):
        try:
            client.call("pin", childId=child_id)
            client.pump(15)
            client.call(
                "screenshot",
                timeout=120,
                path=str(output_path.resolve()),
                target="output",
            )
            log.info("Saved output screenshot: %s", output_path)
            return output_path
        except TixlError as error:
            if error.code == "SCREENSHOT_BUSY" and attempt < 2:
                time.sleep(0.5)
                client.pump(5)
                continue
            if error.code == "NO_OUTPUT" and attempt == 0:
                with contextlib.suppress(TixlError):
                    client.call("openWindow", name="OutputWindow")
                    client.pump(5)
                continue
            log.warning("Could not capture the output: %s", error)
            return None

    return None
