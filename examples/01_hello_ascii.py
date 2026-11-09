"""Minimal declarative patch: load an image and render it as ASCII.

Run with an optional image path (a local file or a TiXL resource path):

    python examples/01_hello_ascii.py
    python examples/01_hello_ascii.py ~/Pictures/portrait.jpg
"""

import logging
import sys
from pathlib import Path

from pytixl import AsciiRender, LoadImage, Patch

DEFAULT_IMAGE = "Examples:images/t3-logo-alpha.png"


class HelloAscii(Patch):
    """A LoadImage -> AsciiRender patch declared with class attributes."""

    image = LoadImage()
    ascii = AsciiRender()
    ascii.filter_characters = "@%#*+=-:. "

    image >> ascii

    def __init__(self, image: str = DEFAULT_IMAGE, **options: object) -> None:
        super().__init__(**options)
        self.image.path = image


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    image = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_IMAGE
    output = Path(__file__).parent / "output" / "01_hello_ascii.png"

    with HelloAscii(image) as patch:
        capture = patch.screenshot(output)
        print(f"project: {patch.project}")
        print(f"graph:   {capture.graph}")
        print(f"output:  {capture.output}")


if __name__ == "__main__":
    main()
