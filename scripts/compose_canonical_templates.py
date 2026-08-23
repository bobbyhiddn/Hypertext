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
LOT_SCHEMA = ROOT / "schema/lot_template_family.json"
LOT_REVIEW = ROOT / "operator_review/lot-template-family-d2429168"
EVIDENCE = ROOT / "docs/evidence/deterministic-reconstruction"
CARD_INDEX = ROOT / "series/2026-Q1/cards_index.yml"
CARD_RENDER_MANIFEST = EVIDENCE / "canonical-card-renders/manifest.json"
SIZE = (1024, 1536)
# These rectangles are deliberately disjoint and cover only the approved identity controls.
TYPE_BOX = (45, 0, 345, 205)
RARITY_BOX = (785, 0, 1008, 205)
NAVY = "#171838"
PARCHMENT = "#f0bd79"
LOT_CLEAN_COPY = {
    "verse": "RECORD THIS LOT",
    "context": "Match the composition exactly. Record the word cards in your Pages.",
    "series": "SHARED LOT TEMPLATE",
}
LOT_CLEAN_REGIONS = {
    "verse": (150, 554, 874, 682),
    "context": (98, 1204, 956, 1410),
    "series": (37, 1475, 997, 1535),
}
LOT_FORBIDDEN_COPY = (
    "Example verse text - Book 1:1",
    "This is a template. Replace this text with specific context, rules, and details for the card.",
    "SERIES: 20XX-QX Lots",
)


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


def lot_font(size: int, bold: bool = False):
    name = "DejaVuSerif-Bold.ttf" if bold else "DejaVuSerif.ttf"
    return ImageFont.truetype(name, size)


def lot_centered(draw: ImageDraw.ImageDraw, box, value: str, size: int, *, bold=False, fill=PARCHMENT) -> None:
    face = lot_font(size, bold)
    bounds = draw.textbbox((0, 0), value, font=face)
    x = box[0] + (box[2] - box[0] - (bounds[2] - bounds[0])) // 2
    y = box[1] + (box[3] - box[1] - (bounds[3] - bounds[1])) // 2 - bounds[1]
    draw.text((x, y), value, font=face, fill=fill)


def apply_lot_contract(image: Image.Image, cards: int, role: str, value: int,
                       title: str, recipe: str) -> None:
    """Apply crisp canonical copy within the source template's established panels."""
    draw = ImageDraw.Draw(image)
    # Opaque fills prevent resampling halos around the replaced generated lettering.
    draw.rounded_rectangle((196, 61, 808, 207), radius=14, fill="#efbd7e")
    lot_centered(draw, (196, 72, 808, 137), title, 45, bold=True, fill="#111111")
    lot_centered(draw, (196, 137, 808, 194), f"CANONICAL {cards}-CARD LOT", 23, fill="#111111")
    banner = (130, 302, 900, 484)
    draw.rectangle(banner, fill=NAVY, outline="#d49b72", width=5)
    unit = "POINTS" if role == "chapter" else "LETTERS"
    lot_centered(draw, (145, 322, 885, 397), f"{role.upper()} LOT", 28, bold=True)
    lot_centered(draw, (145, 395, 885, 467), f"{value} {unit}", 39, bold=True)
    panel = (91, 696, 963, 972)
    draw.rounded_rectangle(panel, radius=22, fill="#efbd7e", outline=NAVY, width=8)
    lot_centered(draw, (120, 726, 934, 798), "COMPOSITION", 27, bold=True, fill=NAVY)
    lot_centered(draw, (120, 808, 934, 886), recipe, 32, bold=True, fill="#111111")
    lot_centered(draw, (120, 888, 934, 946), f"EXACTLY {cards} WORD CARDS", 22, fill=NAVY)
    # Remove generated sample copy while retaining the established panels and layout.
    draw.rectangle(LOT_CLEAN_REGIONS["verse"], fill="#efbd7e")
    lot_centered(draw, LOT_CLEAN_REGIONS["verse"], LOT_CLEAN_COPY["verse"], 26,
                 bold=True, fill=NAVY)
    draw.rectangle(LOT_CLEAN_REGIONS["context"], fill="#efbd7e")
    lot_centered(draw, (125, 1230, 929, 1300), "RECORDING INSTRUCTION", 24,
                 bold=True, fill=NAVY)
    lot_centered(draw, (125, 1300, 929, 1378), LOT_CLEAN_COPY["context"], 19,
                 fill="#111111")
    draw.rectangle(LOT_CLEAN_REGIONS["series"], fill=NAVY)
    draw.text((60, 1490), LOT_CLEAN_COPY["series"], font=lot_font(21), fill=PARCHMENT)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def image_region_sha(image: Image.Image, box) -> str:
    return hashlib.sha256(image.crop(box).tobytes()).hexdigest()


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
    schema = json.loads(LOT_SCHEMA.read_text())
    outputs = []
    aliases = []
    for subtype in schema["subtypes"]:
        cards = subtype["cards"]
        source = ROOT / f"templates/lot/v001/{cards}-card/template_1024x1536.png"
        for role in ("chapter", "page"):
            value_key = "points" if role == "chapter" else "letters"
            value = subtype[f"{role}_value"][value_key]
            relative = Path(f"templates/lot/v001/shared/{cards}-card/{role}_template_1024x1536.png")
            output = ROOT / relative
            image = png(source)
            apply_lot_contract(image, cards, role, value, subtype["representative"]["name"],
                               subtype["representative"]["display"])
            clean_region_sha256 = {name: image_region_sha(image, box)
                                   for name, box in LOT_CLEAN_REGIONS.items()}
            save(image, output)
            outputs.append({"subtype": f"{cards}-card", "role": role, "path": str(relative),
                            "source": str(source.relative_to(ROOT)), "source_sha256": sha(source),
                            "value": {value_key: value}, "visible_label": f"{role.upper()} LOT — {value} {value_key.upper()}",
                            "representative": subtype["representative"], "visible_copy": LOT_CLEAN_COPY,
                            "clean_regions": LOT_CLEAN_REGIONS,
                            "clean_region_sha256": clean_region_sha256, "sha256": sha(output)})
        legacy = ROOT / f"templates/lot/v001/shared/{cards}-card/template_1024x1536.png"
        legacy.write_bytes((ROOT / outputs[-2]["path"]).read_bytes())
        aliases.append({"path": str(legacy.relative_to(ROOT)), "canonical": outputs[-2]["path"], "sha256": sha(legacy)})
    result = {"schema_version": 1, "scope": "shared-across-all-sets", "family": "Lot",
              "authoritative_data": str(LOT_SCHEMA.relative_to(ROOT)),
              "roles": {"table": "Chapter Lot", "player": "Page Lot"}, "canvas": [1024, 1536],
              "composition_order": ["checked_in_subtype_source", "opaque_typography_cleanup", "canonical_role_and_recipe"],
              "outputs": outputs, "compatibility_aliases": aliases}
    serialized = json.dumps(result)
    if any(stale in serialized for stale in LOT_FORBIDDEN_COPY):
        raise RuntimeError("placeholder Lot copy escaped into the shared manifest")
    LOT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    LOT_MANIFEST.write_text(json.dumps(result, indent=2) + "\n")
    entries = [(f'{x["subtype"]} / {x["role"].title()} Lot', ROOT / x["path"]) for x in outputs]
    contact_sheet(entries, EVIDENCE / "shared-lots-contact-sheet.png", 3)
    matrix_path = LOT_REVIEW / "lot-template-family-matrix.png"
    contact_sheet(entries, matrix_path, 3)
    review = {"schema_version": 1, "requirements": ["REQ-PPAUG-017", "REQ-PPAUG-004"],
              "label": "Chapter Lot / Page Lot × 5 / 6 / 7 cards",
              "generation_policy": "offline deterministic composition only; scheduled generation disabled",
              "generator": str(Path(__file__).relative_to(ROOT)), "generator_sha256": sha(Path(__file__)),
              "authoritative_data": [
                  {"path": str(LOT_SCHEMA.relative_to(ROOT)), "sha256": sha(LOT_SCHEMA)},
                  {"path": "templates/phases.yml", "sha256": sha(ROOT / "templates/phases.yml")}],
              "matrix": str(matrix_path.relative_to(ROOT)), "matrix_sha256": sha(matrix_path),
              "cells": outputs}
    if any(stale in json.dumps(review) for stale in LOT_FORBIDDEN_COPY):
        raise RuntimeError("placeholder Lot copy escaped into the review manifest")
    (LOT_REVIEW / "manifest.json").write_text(json.dumps(review, indent=2) + "\n")
    (LOT_REVIEW / "README.md").write_text(
        "# Canonical Lot template family review\n\n"
        "This labeled matrix is composed deterministically from the checked-in 5-, 6-, and 7-card "
        "source templates. Each cell identifies its source and digest in `manifest.json`; recipes and "
        "rewards resolve through `schema/lot_template_family.json` to `templates/phases.yml`.\n\n"
        "Review scope: `REQ-PPAUG-017` and `REQ-PPAUG-004`. No model call is part of this composition "
        "path, and scheduled generation remains disabled.\n\n"
        "The compositor currently resolves DejaVu Serif through Pillow by font name. The repository "
        "contains no approved font binary, so pinning a new file would create an unapproved visual "
        "baseline; deterministic runs require the supported environment to provide that font.\n")
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--family", choices=("all", "words", "lots"), default="all")
    args = parser.parse_args()
    before = {}
    if args.check:
        for root in (WORD_MANIFEST.parent, LOT_MANIFEST.parent, EVIDENCE):
            if root.exists():
                before.update({p: sha(p) for p in root.rglob("*") if p.is_file()})
    words = lots = cards = None
    if args.family in ("all", "words"):
        words = compose_words()
        cards = render_canonical_cards(words)
        if len(words["outputs"]) != 20 or cards["count"] != 31:
            raise RuntimeError("canonical word coverage mismatch")
    if args.family in ("all", "lots"):
        lots = compose_lots()
        if len(lots["outputs"]) != 6:
            raise RuntimeError("canonical Lot coverage mismatch")
    if args.check:
        after = {p: sha(p) for p in before}
        if before != after: raise RuntimeError("composition is not deterministic")
    counts = []
    if words: counts.append(f'{len(words["outputs"])} word templates and {cards["count"]} canonical cards')
    if lots: counts.append(f'{len(lots["outputs"])} shared Lot role/size variants')
    print("validated " + " plus ".join(counts))


if __name__ == "__main__": main()
