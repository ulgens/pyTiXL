"""Command-line interface built on top of the :class:`Patch` library."""

import json
import logging
import sys
from typing import Annotated

import typer

from pytixl.client import TixlError
from pytixl.config import DEFAULT_IMAGE, DEFAULT_PORT
from pytixl.operators import AsciiRender, LoadImage
from pytixl.patch import Patch

app = typer.Typer(add_completion=False)

log = logging.getLogger(__name__)


@app.command()
def main(
    tixl: Annotated[
        str | None,
        typer.Option("--tixl", help="Path to the TiXL executable (otherwise auto-detected)."),
    ] = None,
    port: Annotated[
        int,
        typer.Option("--port", help="Debug bridge port."),
    ] = DEFAULT_PORT,
    out: Annotated[
        str | None,
        typer.Option(
            "--out",
            help="Output directory or .png base path (default: ./tixl_<timestamp>).",
        ),
    ] = None,
    project: Annotated[
        str | None,
        typer.Option("--project", help="Open an existing project instead of creating a clean one."),
    ] = None,
    name: Annotated[
        str | None,
        typer.Option("--name", help="Short name for a newly created project."),
    ] = None,
    namespace: Annotated[
        str | None,
        typer.Option("--namespace", help="Namespace for a newly created project (user.<name>)."),
    ] = None,
    image: Annotated[
        str,
        typer.Option("--image", help="Image file path or TiXL resource path."),
    ] = DEFAULT_IMAGE,
    window: Annotated[
        str | None,
        typer.Option(
            "--window",
            help="Editor window size as WxH (default: full available screen).",
        ),
    ] = None,
    crop_scale: Annotated[
        str,
        typer.Option("--crop-scale", help="Scale for cropping the graph from the UI screenshot."),
    ] = "auto",
    keep_open: Annotated[
        bool,
        typer.Option("--keep-open", help="Leave the editor running after the capture."),
    ] = False,
) -> None:
    """Build a LoadImage -> AsciiRender patch and capture the graph and output."""
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)

    try:
        with Patch(
            project=project,
            name=name,
            namespace=namespace,
            port=port,
            executable=tixl,
            window=window,
            keep_open=keep_open,
        ) as patch:
            image_node = patch.add(LoadImage(image), "image")
            ascii_node = patch.add(AsciiRender(), "ascii")
            ascii_node.image = image_node
            patch.set_output(ascii_node)

            result = patch.screenshot(out, crop_scale=crop_scale)

            print(f"\nProject: {patch.project}")
            if patch.created:
                print(f"Cleaned {patch.removed_nodes} tutorial node(s) from the new project")

            captures = [path for path in (result.graph, result.output) if path is not None]
            if captures:
                try:
                    state = patch.graph_state()
                    state_path = captures[0].parent / "graph_state.json"
                    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
                except TixlError as error:
                    log.warning("Could not save graph state: %s", error)

            print("\nDone.")
            for path in captures:
                print(f"  {path}")

    except TixlError as error:
        print(f"\nTiXL protocol error: {error}", file=sys.stderr)
        raise typer.Exit(code=1) from error
    except RuntimeError as error:
        print(error, file=sys.stderr)
        raise typer.Exit(code=2) from error
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        raise typer.Exit(code=130) from None


def run() -> None:
    app()


if __name__ == "__main__":
    run()
