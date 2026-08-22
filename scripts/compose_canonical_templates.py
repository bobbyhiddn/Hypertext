#!/usr/bin/env python3
"""Deterministically compose canonical word and shared Lot template evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "schema/babel_template_matrix.json"
WORD_MANIFEST = ROOT / "templates/card/v001/composed/manifest.json"
LOT_MANIFEST = ROOT / "templates/lot/v001/shared/manifest.json"
EVIDENCE = ROOT / "docs/evidence/deterministic-reconstruction"
SIZE = (1024, 1536)
# These rectangles are deliberately disjoint and cover only the approved identity controls.
TYPE_BOX = (45, 0, 345, 205)
RARITY_BOX = (785, 0, 1008, 205)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png(path: Path) -> Image.Image:
    image = Image.open(path)
    image.load()
    if image.format != "PNG" or image.size != SIZE:
        raise ValueError(f"not a true {SIZE[0]}x{SIZE[1]} PNG: {path}")
    return image.convert("RGB")


def save(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "PNG", optimize=False, compress_level=9)


def contact_sheet(entries: list[tuple[str, Path]], path: Path, cols: int) -> None:
    tw, th, label = 256, 384, 28
    rows = (len(entries) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * (th + label)), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (name, source) in enumerate(entries):
        card = png(source).resize((tw, th), Image.Resampling.LANCZOS)
        x, y = (index % cols) * tw, (index // cols) * (th + label)
        sheet.paste(card, (x, y)); draw.text((x + 5, y + th + 5), name, fill="black")
    save(sheet, path)


def compose_words() -> dict:
    matrix = json.loads(MATRIX.read_text())
    layers = matrix["layers"]
    base_path = ROOT / layers["base"]
    base = png(base_path)
    outputs = []
    for item in matrix["valid_combinations"]:
        word_type, rarity = item["type"], item["rarity"]
        type_path = ROOT / layers["type_structure"][word_type]
        rarity_path = ROOT / layers["rarity_treatment"][rarity]
        image = base.copy()
        image.paste(png(type_path).crop(TYPE_BOX), TYPE_BOX)
        image.paste(png(rarity_path).crop(RARITY_BOX), RARITY_BOX)
        relative = Path(layers["composed_output_pattern"].format(
            **{"type-lower": word_type.lower(), "rarity-lower": rarity.lower()}))
        output = ROOT / relative
        save(image, output)
        outputs.append({"type": word_type, "rarity": rarity, "path": str(relative), "sha256": sha(output)})
    result = {"schema_version": 1, "matrix": str(MATRIX.relative_to(ROOT)),
              "canvas": [1024, 1536], "base": str(base_path.relative_to(ROOT)),
              "base_sha256": sha(base_path), "bounded_regions": {"type": TYPE_BOX, "rarity": RARITY_BOX},
              "composition_order": ["frozen_base", "bounded_type", "bounded_rarity"], "outputs": outputs}
    WORD_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    WORD_MANIFEST.write_text(json.dumps(result, indent=2) + "\n")
    contact_sheet([(f'{x["type"]} / {x["rarity"]}', ROOT / x["path"]) for x in outputs],
                  EVIDENCE / "word-templates-contact-sheet.png", 5)
    return result


def compose_lots() -> dict:
    rewards = {5: (8, 2), 6: (10, 2), 7: (14, 3)}
    outputs = []
    for cards, (chapter, page) in rewards.items():
        source = ROOT / f"templates/lot/v001/{cards}-card/template_1024x1536.png"
        relative = Path(f"templates/lot/v001/shared/{cards}-card/template_1024x1536.png")
        output = ROOT / relative
        save(png(source), output)
        outputs.append({"subtype": f"{cards}-card", "path": str(relative), "source": str(source.relative_to(ROOT)),
                        "chapter_value": {"points": chapter}, "page_value": {"letters": page}, "sha256": sha(output)})
    result = {"schema_version": 1, "scope": "shared-across-all-sets", "family": "Lot",
              "roles": {"table": "Chapter Lot", "player": "Page Lot"}, "canvas": [1024, 1536], "outputs": outputs}
    LOT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    LOT_MANIFEST.write_text(json.dumps(result, indent=2) + "\n")
    contact_sheet([(x["subtype"], ROOT / x["path"]) for x in outputs], EVIDENCE / "shared-lots-contact-sheet.png", 3)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--check", action="store_true"); args = parser.parse_args()
    before = {}
    if args.check:
        for root in (WORD_MANIFEST.parent, LOT_MANIFEST.parent, EVIDENCE):
            if root.exists():
                before.update({p: sha(p) for p in root.rglob("*") if p.is_file()})
    words, lots = compose_words(), compose_lots()
    if len(words["outputs"]) != 20 or len(lots["outputs"]) != 3:
        raise RuntimeError("canonical coverage mismatch")
    if args.check:
        after = {p: sha(p) for p in before}
        if before != after: raise RuntimeError("composition is not deterministic")
    print(f'validated {len(words["outputs"])} word templates and {len(lots["outputs"])} shared Lot subtypes')


if __name__ == "__main__": main()
