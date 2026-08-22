"""Deterministically render the numeric stat pips on a generated card."""

import json
from pathlib import Path

from PIL import Image, ImageDraw


NAVY = "#0B1F3B"
GOLD = "#C9A44C"
PARCHMENT = "#F3E7C8"

# Normalized centers measured from the fixed 1024x1536 card contract.
_ROWS = ((108, 160, 212, 264, 316),
         (414, 466, 518, 570, 622),
         (721, 773, 825, 877, 929))
_BASE_WIDTH = 1024
_BASE_HEIGHT = 1536
_BASE_Y = 601
_BASE_RADIUS = 22


def render_stat_pips(image_path: str | Path, card_json_path: str | Path) -> None:
    """Replace all 15 model-drawn pips with binary circles from card.json."""
    image_path = Path(image_path)
    with open(card_json_path, encoding="utf-8") as stream:
        content = json.load(stream)["content"]
    values = tuple(int(content[key]) for key in
                   ("STAT_LORE", "STAT_CONTEXT", "STAT_COMPLEXITY"))
    if any(value < 0 or value > 5 for value in values):
        raise ValueError(f"stat pip values must be between 0 and 5: {values}")

    with Image.open(image_path) as source:
        image = source.convert("RGB")
    sx, sy = image.width / _BASE_WIDTH, image.height / _BASE_HEIGHT
    radius = max(1, round(_BASE_RADIUS * min(sx, sy)))
    outline_width = max(2, round(3 * min(sx, sy)))
    y = round(_BASE_Y * sy)
    draw = ImageDraw.Draw(image)
    for row, filled in zip(_ROWS, values):
        for index, base_x in enumerate(row):
            x = round(base_x * sx)
            bbox = (x - radius, y - radius, x + radius, y + radius)
            if index < filled:
                draw.ellipse(bbox, fill=NAVY, outline=GOLD, width=outline_width)
            else:
                draw.ellipse(bbox, fill=PARCHMENT, outline=NAVY,
                             width=outline_width)
    image.save(image_path, format="PNG")


def read_stat_pips(image_path: str | Path) -> tuple[int, int, int]:
    """Read exact renderer-owned center pixels; reject non-binary or gapped rows."""
    with Image.open(image_path) as source:
        image = source.convert("RGB")
    sx, sy = image.width / _BASE_WIDTH, image.height / _BASE_HEIGHT
    y = round(_BASE_Y * sy)
    navy = Image.new("RGB", (1, 1), NAVY).getpixel((0, 0))
    parchment = Image.new("RGB", (1, 1), PARCHMENT).getpixel((0, 0))
    values = []
    for row in _ROWS:
        states = []
        for base_x in row:
            pixel = image.getpixel((round(base_x * sx), y))
            navy_match = max(abs(a - b) for a, b in zip(pixel, navy)) <= 5
            parchment_match = max(abs(a - b) for a, b in zip(pixel, parchment)) <= 5
            if not (navy_match or parchment_match):
                raise ValueError(f"non-binary stat pip center color: {pixel}")
            states.append(navy_match)
        filled = sum(states)
        if states != [True] * filled + [False] * (5 - filled):
            raise ValueError(f"stat pips are not filled left-to-right: {states}")
        values.append(filled)
    return tuple(values)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("card_dirs", nargs="+")
    args = parser.parse_args()
    for directory in args.card_dirs:
        directory = Path(directory)
        render_stat_pips(directory / "outputs/card_1024x1536.png",
                         directory / "card.json")
