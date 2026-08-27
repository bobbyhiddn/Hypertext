#!/usr/bin/env python3
"""Project established type label pills onto the canonical blank Word matrix.

The promoted reconstruction already contains the accepted blank structure, type
silhouettes, and rarity treatments.  Its frozen base, however, carries NOUN in
every cell.  This correction copies only the complete label pill from each
checked-in historical type witness; no card content or generated art is used.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "templates/card/v001/composed/manifest.json"
SHEET = ROOT / "docs/evidence/deterministic-reconstruction/word-templates-contact-sheet.png"
TYPES = ("NOUN", "VERB", "ADJECTIVE", "NAME", "TITLE")
RARITIES = ("COMMON", "UNCOMMON", "RARE", "GLORIOUS")
# The complete navy pill, including its antialiased edge.  This is disjoint
# from the number field and type silhouette on the 848x1264 canonical canvas.
LABEL_BOX = (122, 24, 274, 58)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_rgb(path: Path) -> Image.Image:
    with Image.open(path) as source:
        source.load()
        if source.format != "PNG" or source.size != (848, 1264):
            raise ValueError(f"not a canonical 848x1264 PNG: {path}")
        return source.convert("RGB")


def witness(card_type: str) -> Path:
    return (ROOT / "operator_review/constrained/e50961ad0f4d/edits/type" /
            card_type.lower() / "historical_witness.png")


def label_patch(card_type: str) -> Image.Image:
    return load_rgb(witness(card_type)).crop(LABEL_BOX)


def compose_sheet(outputs: dict[tuple[str, str], Path]) -> None:
    thumb = (212, 316)
    caption = 24
    sheet = Image.new("RGB", (4 * thumb[0], 5 * (thumb[1] + caption)), "white")
    draw = ImageDraw.Draw(sheet)
    for row, card_type in enumerate(TYPES):
        for col, rarity in enumerate(RARITIES):
            card = load_rgb(outputs[(card_type, rarity)]).resize(thumb, Image.Resampling.LANCZOS)
            x, y = col * thumb[0], row * (thumb[1] + caption)
            sheet.paste(card, (x, y))
            draw.text((x + 5, y + thumb[1] + 4), f"{card_type}/{rarity}", fill="black")
    SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(SHEET, "PNG", optimize=False, compress_level=9)


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    by_key = {(item["type"], item["rarity"]): item for item in manifest["outputs"]}
    if set(by_key) != {(card_type, rarity) for card_type in TYPES for rarity in RARITIES}:
        raise RuntimeError("canonical matrix is not the exact 5x4 cross product")

    output_paths = {}
    for card_type in TYPES:
        patch = label_patch(card_type)
        for rarity in RARITIES:
            item = by_key[(card_type, rarity)]
            path = ROOT / item["path"]
            image = load_rgb(path)
            image.paste(patch, LABEL_BOX[:2])
            image.save(path, "PNG", optimize=False, compress_level=9)
            item["sha256"] = sha256(path)
            item["visible_type_label"] = card_type
            item["type_label_source"] = str(witness(card_type).relative_to(ROOT))
            output_paths[(card_type, rarity)] = path

    manifest["type_label_box"] = list(LABEL_BOX)
    manifest["type_label_method"] = (
        "Exact RGB crop of the established navy type-label pill from the checked-in "
        "historical type example; applied after accepted icon and rarity construction."
    )
    stage_name = "historical_type_label_pill"
    manifest["composition_order"] = [
        name for name in manifest["composition_order"] if name != stage_name
    ] + [stage_name]
    manifest["construction_stages"][stage_name] = {
        "operation": "paste_type_label_crop",
        "box": list(LABEL_BOX),
        "source_field": "type_label_source",
    }
    manifest["integrity"] = (
        "Each canonical PNG reconstructs from the accepted candidate evidence plus the "
        "established type-label crop declared by its output record; sha256 is authoritative."
    )
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    compose_sheet(output_paths)
    print(f"corrected 20 canonical labels; wrote {SHEET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
