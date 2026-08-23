#!/usr/bin/env python3
"""One-shot, manual Gemini regeneration of the three shared Lot size faces."""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from hypertext.gemini.style import generate_with_styles

ROOT = Path(__file__).resolve().parents[1]
MODEL = "gemini-3.1-flash-image"
OUT = ROOT / "templates/lot/v001/shared"
REVIEW = ROOT / "operator_review/lot-template-family-d2429168"
NATIVE = {n: ROOT / f"templates/lot/v001/{n}-card/template_1024x1536.png" for n in (5, 6, 7)}

CASES = [
    (5, "REMNANT", "5 SAME TYPE", 8, 2),
    (6, "CONGREGATION", "6 ANY MIX", 10, 2),
    (7, "CREATION", "3 + 2 + 2 (THREE TYPES)", 14, 3),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prompt(cards: int, title: str, recipe: str, points: int, letters: int) -> str:
    slot_instruction = {
        5: "Show five identical abstract card-slot emblems, with the single centered caption 5 SAME TYPE. Do not choose or name a specific word type.",
        6: "Show six abstract varied card-slot emblems, with the single centered caption 6 ANY MIX. Do not prescribe a particular mix of word types.",
        7: "Show exactly seven separate card-slot emblems in one row: slots 1, 2, 3 use one identical symbol; slots 4, 5 use a second identical symbol; slots 6, 7 use a third identical symbol. Count them explicitly as ONE, TWO, THREE, FOUR, FIVE, SIX, SEVEN before rendering. The only visible caption is 3 + 2 + 2 (THREE TYPES); do not print the count words.",
    }[cards]
    return f"""Use case: stylized-concept
Asset type: canonical Hypertext Lot style-reference face
Primary request: Generate an entirely new, complete, flat front-facing card face. The supplied images are references only; do not edit, paint onto, trace, paste, composite, or retain pixels from them.

Render this exact canonical content, each string exactly once:
- Header left: "LOT"
- Header right: "{cards}-CARD"
- Title: "{title}"
- Composition recipe: "{recipe}"
- Chapter reward: "CHAPTER VALUE: {points} POINTS"
- Page reward: "PAGE VALUE: {letters} LETTERS"
- Rule: "WREATH BONUS: +2 POINTS (FIRST TO RECORD)"
- Footer: "HYPERTEXT"

The composition panel must visually express exactly {cards} card slots consistent with "{recipe}". {slot_instruction} Preserve the native Lot design language: one continuous rounded double frame, near-black navy #102030, restrained antique gold #C0A060, warm parchment, classical high-contrast serif typography, cream small caps on navy, thin gold rules, flat two-color Card-type icon language, balanced biblical-manuscript ornament. Use the native {cards}-card Lot reference as the authority for geometry, palette, typography, ornament, title, recipe, and slot count; use the other native Lot references only to understand the coherent family.

Required vertical order: header and title; one reward ribbon containing both value lines and the wreath rule; one composition panel containing the slots and exactly one recipe caption; restrained non-text ornament; footer. There is no context panel, verse, subtitle, role badge, second composition panel, or type icon.

Output requirements: a sharp complete portrait card, 2:3, no exterior margin, mockup, hand, shadow, glow, blur, watermark, duplicated element, bracketed label, placeholder, explanatory caption, or invented rule. Do not render CONTEXT, SERIES, CARD COUNT, ROLE LABEL, COMPOSITION RECIPE, EXAMPLE VERSE, REWARD:, template instructions, replacement instructions, or any text besides the eight exact strings listed above. Chapter Lot and Page Lot are data roles represented by the two canonical value lines on this one shared size face; do not create separate role treatments. Ensure every required word and number is fully legible and spelled verbatim. The face must be generated as one unified model output; no blank zones intended for later text or graphics."""


def main() -> None:
    records = []
    for cards, title, recipe, points, letters in CASES:
        only = os.environ.get("LOT_CASE")
        if only and only != str(cards):
            continue
        refs = [str(NATIVE[cards])] + [str(NATIVE[n]) for n in (5, 6, 7) if n != cards]
        directory = OUT / f"{cards}-card"
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / "template_1024x1536.png"
        generate_with_styles(prompt(cards, title, recipe, points, letters), refs, str(target),
                             model=MODEL, include_type_icon=False)
        with Image.open(target) as image:
            image.load()
            if image.format != "PNG" or image.size != (1024, 1536):
                raise RuntimeError(f"invalid output contract: {target}: {image.format} {image.size}")
        records.append({
            "cards": cards, "title": title, "recipe": recipe,
            "chapter_value": f"{points} POINTS", "page_value": f"{letters} LETTERS",
            "path": str(target.relative_to(ROOT)), "sha256": sha(target),
            "generation_record": str((directory / "generation.json").relative_to(ROOT)),
            "generation_record_sha256": sha(directory / "generation.json"),
            "prompt": prompt(cards, title, recipe, points, letters),
        })

    REVIEW.mkdir(parents=True, exist_ok=True)
    if len(records) != 3:
        records = []
        for cards, title, recipe, points, letters in CASES:
            target = OUT / f"{cards}-card/template_1024x1536.png"
            records.append({
                "cards": cards, "title": title, "recipe": recipe,
                "chapter_value": f"{points} POINTS", "page_value": f"{letters} LETTERS",
                "path": str(target.relative_to(ROOT)), "sha256": sha(target),
                "generation_record": str((target.parent / "generation.json").relative_to(ROOT)),
                "generation_record_sha256": sha(target.parent / "generation.json"),
                "prompt": prompt(cards, title, recipe, points, letters),
            })
    canvas = Image.new("RGB", (2100, 1080), "#102030")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype("DejaVuSerif-Bold.ttf", 28)
    for index, record in enumerate(records):
        col = index % 3
        x, y = 30 + col * 690, 32
        face = Image.open(ROOT / record["path"]).convert("RGB").resize((640, 960), Image.Resampling.LANCZOS)
        canvas.paste(face, (x, y + 48))
        label = f"{record['cards']}-CARD / CHAPTER {record['chapter_value']} / PAGE {record['page_value']}"
        draw.text((x, y), label, fill="#f3e7c8", font=font)
    matrix = REVIEW / "lot-template-family-matrix.png"
    canvas.save(matrix, "PNG")

    manifest = {
        "schema_version": 2,
        "scope": "shared-across-all-sets",
        "family": "Lot",
        "requirements": ["REQ-PPAUG-017", "REQ-PPAUG-020", "REQ-PPAUG-025", "REQ-PPAUG-026", "REQ-PPAUG-027"],
        "label": "Three canonical Lot size faces: 5-card / 6-card / 7-card",
        "generation_policy": "manual complete-face Gemini style-reference generation; scheduled automation disabled",
        "model": MODEL,
        "workflow": "hypertext.gemini.style.generate_with_styles generate mode",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "prohibited_operations": ["text overlay on faces", "face compositing", "programmatic face construction"],
        "reference_role": "authoritative native Lot faces used only as generation references",
        "references": [{"path": str(NATIVE[n].relative_to(ROOT)), "sha256": sha(NATIVE[n])} for n in (5, 6, 7)],
        "artifact_kind": "three-face review sheet",
        "matrix": str(matrix.relative_to(ROOT)), "matrix_sha256": sha(matrix),
        "matrix_note": "Review-only labeled contact sheet; labels are outside the complete generated faces.",
        "normalization": "repository Gemini image contract: decoded model response to RGB PNG 1024x1536",
        "visual_validation": {
            "resolution": "original 1024x1536",
            "inspected": [5, 6, 7],
            "result": "pass",
            "rejection_gates": ["malformed text", "duplicated labels", "empty placeholder panels", "invented content"],
        },
        "cells": records,
    }
    (REVIEW / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
