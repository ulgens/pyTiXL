"""Procedural patch: one image, two ASCII variants.

This example uses ``Patch.add()`` instead of class attributes. Both filters
read from the same image, and ``set_output()`` switches which one is pinned to
the output window before each capture.
"""

import logging
import sys
from pathlib import Path

from tixl_python import AsciiRender, LoadImage, Operator, Patch

DEFAULT_IMAGE = "Examples:images/t3-logo-alpha.png"


def build(image_path: str) -> tuple[Patch, Operator, Operator]:
    """Create the patch and return it together with the two output operators."""
    patch = Patch()

    image = patch.add(LoadImage(image_path), "image")
    dense = patch.add(
        AsciiRender(
            filter_characters="@%#*+=-:. ",
            font_char_size=(6, 6),
        ),
        "dense",
    )
    sparse = patch.add(
        AsciiRender(
            filter_characters=" .:-=+*#%@",
            font_char_size=(16, 16),
        ),
        "sparse",
    )

    dense.image = image
    sparse.image = image

    return patch, dense, sparse


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    image = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_IMAGE
    output_dir = Path(__file__).parent / "output"

    patch, dense, sparse = build(image)
    with patch:
        patch.set_output(dense)
        dense_capture = patch.screenshot(output_dir / "03_dense.png")

        patch.set_output(sparse)
        sparse_capture = patch.screenshot(output_dir / "03_sparse.png", target="output")

        print(f"project: {patch.project}")
        print(f"dense:   {dense_capture.graph}")
        print(f"dense:   {dense_capture.output}")
        print(f"sparse:  {sparse_capture.output}")


if __name__ == "__main__":
    main()
