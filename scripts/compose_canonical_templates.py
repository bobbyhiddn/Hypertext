#!/usr/bin/env python3
"""Deterministically compose canonical word and shared Lot template evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import yaml

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "schema/babel_template_matrix.json"
WORD_MANIFEST = ROOT / "templates/card/v001/composed/manifest.json"
LOT_MANIFEST = ROOT / "templates/lot/v001/shared/manifest.json"
EVIDENCE = ROOT / "docs/evidence/deterministic-reconstruction"
CARD_INDEX = ROOT / "series/2026-Q1/cards_index.yml"
CARD_RENDER_MANIFEST = EVIDENCE / "canonical-card-renders/manifest.json"
SIZE = (1024, 1536)
# These rectangles are deliberately disjoint and cover only the approved identity controls.
TYPE_BOX = (45, 0, 345, 205)
RARITY_BOX = (785, 0, 1008, 205)
NAVY = "#171838"
PARCHMENT = "#f0bd79"


def font(size: int):
    return ImageFont.load_default(size=size)


def centered(draw: ImageDraw.ImageDraw, box, value: str, size: int, fill=PARCHMENT) -> None:
    face = font(size)
    bounds = draw.textbbox((0, 0), value, font=face)
    x = box[0] + (box[2] - box[0] - (bounds[2] - bounds[0])) // 2
    y = box[1] + (box[3] - box[1] - (bounds[3] - bounds[1])) // 2
    draw.text((x, y), value, font=face, fill=fill)


def apply_word_identity(image: Image.Image, word_type: str, rarity: str) -> None:
    """Replace only source-limited semantic labels with schema identities."""
    draw = ImageDraw.Draw(image)
    type_pill = (150, 10, 340, 58)
    rarity_pill = (790, 0, 1007, 70)
    draw.rounded_rectangle(type_pill, radius=22, fill=NAVY)
    centered(draw, type_pill, word_type, 25)
    draw.rectangle(rarity_pill, fill=NAVY)
    centered(draw, rarity_pill, rarity, 25)


def apply_lot_values(image: Image.Image, chapter: int, page: int) -> None:
    """Spell out the two rule roles inside the existing reward ribbon."""
    draw = ImageDraw.Draw(image)
    box = (130, 302, 900, 480)
    draw.rectangle(box, fill=NAVY)
    centered(draw, (box[0], 312, box[2], 382), f"CHAPTER: {chapter} POINTS", 32)
    centered(draw, (box[0], 382, box[2], 452), f"PAGE: {page} LETTERS", 32)


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
        apply_word_identity(image, word_type, rarity)
        relative = Path(layers["composed_output_pattern"].format(
            **{"type-lower": word_type.lower(), "rarity-lower": rarity.lower()}))
        output = ROOT / relative
        save(image, output)
        outputs.append({"type": word_type, "rarity": rarity, "visible_type_label": word_type,
                        "visible_rarity_label": rarity, "path": str(relative), "sha256": sha(output)})
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
        image = png(source)
        apply_lot_values(image, chapter, page)
        save(image, output)
        outputs.append({"subtype": f"{cards}-card", "path": str(relative), "source": str(source.relative_to(ROOT)),
                        "chapter_value": {"points": chapter, "visible_label": f"CHAPTER: {chapter} POINTS"},
                        "page_value": {"letters": page, "visible_label": f"PAGE: {page} LETTERS"}, "sha256": sha(output)})
    result = {"schema_version": 1, "scope": "shared-across-all-sets", "family": "Lot",
              "roles": {"table": "Chapter Lot", "player": "Page Lot"}, "canvas": [1024, 1536], "outputs": outputs}
    LOT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    LOT_MANIFEST.write_text(json.dumps(result, indent=2) + "\n")
    contact_sheet([(x["subtype"], ROOT / x["path"]) for x in outputs], EVIDENCE / "shared-lots-contact-sheet.png", 3)
    return result


def render_canonical_cards(words: dict) -> dict:
    """Render every canonical index entry through its exact composed template."""
    cards = (yaml.safe_load(CARD_INDEX.read_text()) or {}).get("cards", [])
    templates = {(x["type"], x["rarity"]): ROOT / x["path"] for x in words["outputs"]}
    outputs = []
    for card in sorted(cards, key=lambda x: (x["type"], x["rarity"], x["number"])):
        image = png(templates[(card["type"], card["rarity"])]).copy()
        draw = ImageDraw.Draw(image)
        draw.rectangle((45, 58, 785, 205), fill="#efbd7e")
        draw.text((55, 70), f'#{card["number"]:03d}', fill="#111111", font=font(24))
        centered(draw, (210, 60, 785, 145), card["word"], 42, "#111111")
        relative = Path(f'docs/evidence/deterministic-reconstruction/canonical-card-renders/{card["number"]:03d}-{card["word"].lower()}.png')
        output = ROOT / relative
        save(image, output)
        outputs.append({"number": card["number"], "word": card["word"], "type": card["type"],
                        "rarity": card["rarity"], "template": str(templates[(card["type"], card["rarity"])].relative_to(ROOT)),
                        "path": str(relative), "sha256": sha(output)})
    result = {"schema_version": 1, "canonical_source": str(CARD_INDEX.relative_to(ROOT)),
              "grouping": ["type", "rarity", "number"], "count": len(outputs), "outputs": outputs}
    CARD_RENDER_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    CARD_RENDER_MANIFEST.write_text(json.dumps(result, indent=2) + "\n")
    contact_sheet([(f'{x["type"]} / {x["rarity"]} / #{x["number"]:03d} {x["word"]}', ROOT / x["path"]) for x in outputs],
                  EVIDENCE / "canonical-cards-by-type-rarity-contact-sheet.png", 5)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--check", action="store_true"); args = parser.parse_args()
    before = {}
    if args.check:
        for root in (WORD_MANIFEST.parent, LOT_MANIFEST.parent, EVIDENCE):
            if root.exists():
                before.update({p: sha(p) for p in root.rglob("*") if p.is_file()})
    words, lots = compose_words(), compose_lots()
    cards = render_canonical_cards(words)
    if len(words["outputs"]) != 20 or len(lots["outputs"]) != 3 or cards["count"] != 31:
        raise RuntimeError("canonical coverage mismatch")
    if args.check:
        after = {p: sha(p) for p in before}
        if before != after: raise RuntimeError("composition is not deterministic")
    print(f'validated {len(words["outputs"])} word templates, {cards["count"]} canonical cards, and {len(lots["outputs"])} shared Lot subtypes')


if __name__ == "__main__": main()
