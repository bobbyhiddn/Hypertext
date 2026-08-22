#!/usr/bin/env python3
"""Build contact sheets and machine-readable image validation evidence."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
SHEETS = ROOT / "contact-sheets"
EXPECTED = (1024, 1536)


def images() -> tuple[list[Path], list[Path]]:
    templates = sorted((REPO / "templates/card/v001").glob("*/template_1024x1536.png"))
    templates += sorted((REPO / "templates/lot/v001").glob("*/template_1024x1536.png"))
    cards = sorted(ROOT.glob("cards/*/outputs/card_1024x1536.png"))
    cards += sorted(ROOT.glob("lots/*/outputs/lot_1024x1536.png"))
    return templates, cards


def contact_sheet(paths: list[Path], destination: Path, columns: int) -> None:
    thumb = (256, 384)
    label_h = 34
    rows = (len(paths) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * thumb[0], rows * (thumb[1] + label_h)), "#ddd6c6")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, path in enumerate(paths):
        with Image.open(path) as source:
            card = source.convert("RGB")
            card.thumbnail(thumb, Image.Resampling.LANCZOS)
        x = index % columns * thumb[0]
        y = index // columns * (thumb[1] + label_h)
        sheet.paste(card, (x + (thumb[0] - card.width) // 2, y))
        label = path.parent.name if path.parent.name not in {"outputs"} else path.parent.parent.name
        draw.text((x + 6, y + thumb[1] + 7), label, fill="#102030", font=font)
    destination.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination, "PNG")


def validate(paths: list[Path]) -> list[dict[str, object]]:
    rows = []
    for path in paths:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            rows.append({
                "path": str(path.relative_to(REPO)),
                "format": image.format,
                "width": image.width,
                "height": image.height,
                "mode": image.mode,
                "valid_png": image.format == "PNG",
                "valid_dimensions": image.size == EXPECTED,
            })
    return rows


def main() -> None:
    templates, cards = images()
    if len(templates) != 14 or len(cards) != 7:
        raise SystemExit(f"expected 14 templates and 7 cards, found {len(templates)} and {len(cards)}")
    contact_sheet(templates, SHEETS / "all-14-templates.png", columns=7)
    contact_sheet(cards, SHEETS / "fresh-7-card-sample.png", columns=7)
    report = {
        "expected_dimensions": list(EXPECTED),
        "template_count": len(templates),
        "sample_count": len(cards),
        "templates": validate(templates),
        "sample": validate(cards),
    }
    (ROOT / "image-validation.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
