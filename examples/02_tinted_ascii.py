"""Custom operator: tint an image, then render it as ASCII.

The ``Tint`` wrapper is defined in this file to show how any TiXL symbol can be
exposed as a Python operator.
"""

import logging
import sys
from pathlib import Path
from typing import ClassVar

from pytixl import AsciiRender, LoadImage, Operator, Patch, Port

DEFAULT_IMAGE = "Examples:images/t3-logo-alpha.png"


class Tint(Operator):
    """Map an image's dark and bright values to colours."""

    symbol = "Tint"
    input_ports: ClassVar[dict[str, Port]] = {
        "texture": Port("Texture2d", "texture"),
        "amount": Port("Amount", "float"),
        "map_black_to": Port("MapBlackTo", "color"),
        "map_white_to": Port("MapWhiteTo", "color"),
        "exposure": Port("Exposure", "float"),
        "channel_weights": Port("ChannelWeights", "color"),
        "gain_and_bias": Port("GainAndBias", "vec2"),
    }
    output_ports: ClassVar[dict[str, Port]] = {"texture": Port("Output", "texture")}


class TintedAscii(Patch):
    """LoadImage -> Tint -> AsciiRender, declared with class attributes."""

    image = LoadImage()

    tint = Tint(
        amount=1.0,
        map_black_to=(0.02, 0.0, 0.08, 1.0),
        map_white_to=(1.0, 0.72, 0.25, 1.0),
    )

    ascii = AsciiRender()
    ascii.filter_characters = " .:-=+*#%@"
    ascii.mix_in_colors = 1.0

    image >> tint
    tint >> ascii

    def __init__(self, image: str = DEFAULT_IMAGE, **options: object) -> None:
        super().__init__(**options)
        self.image.path = image


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    image = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_IMAGE
    output = Path(__file__).parent / "output" / "02_tinted_ascii.png"

    with TintedAscii(image) as patch:
        capture = patch.screenshot(output)
        print(f"project: {patch.project}")
        print(f"graph:   {capture.graph}")
        print(f"output:  {capture.output}")


if __name__ == "__main__":
    main()
