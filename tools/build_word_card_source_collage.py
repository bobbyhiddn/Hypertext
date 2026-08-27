#!/usr/bin/env python3
"""Build the REQ-PPAUG-024 read-only Word Card source collage.

This script only scales and places existing repository images. It does not alter,
generate, crop, retouch, or synthesize any card face.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "operator_review/constructed/e50961ad0f4d"
AUTHORITY = "e50961ad0f4d66f398f81706f092a7d0ea9cb0f4"
REMOTE = "https://github.com/bobbyhiddn/Hypertext.git"

NATIVE = [
    ("templates/card/outputs/template_1024x1536.png", "native template — baseline output"),
    ("templates/card/v001/base/template_1024x1536.png", "native template — v001 base geometry"),
    *[(f"templates/card/v001/{kind}/template_1024x1536.png", f"native template — word type: {kind}")
      for kind in ("adjective", "name", "noun", "title", "verb")],
    *[(f"templates/card/v001/{rarity}/template_1024x1536.png", f"native template — rarity: {rarity}")
      for rarity in ("common", "glorious", "rare", "uncommon")],
]
SAMPLES = [
    (f"templates/example_cards/{n:03d}-{name}/outputs/card_1024x1536.png",
     f"completed sample card — {n:03d} {name.upper()}")
    for n, name in enumerate(("grace", "covenant", "wisdom", "glory", "redeem", "forgive",
                              "sanctify", "bless", "holy", "righteous", "eternal", "sacred",
                              "moses", "david", "elijah", "abraham", "shepherd", "redeemer",
                              "savior", "messiah"), 1)
]

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    face = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{face}", size)

def git_bytes(path: str) -> bytes:
    return subprocess.run(["git", "-C", str(ROOT), "show", f"{AUTHORITY}:{path}"],
                          check=True, capture_output=True).stdout

def wrap(draw: ImageDraw.ImageDraw, text: str, width: int, face: ImageFont.FreeTypeFont) -> list[str]:
    lines, current = [], ""
    for token in text.replace("/", "/ ").split():
        candidate = f"{current} {token}".strip()
        if current and draw.textlength(candidate, font=face) > width:
            lines.append(current.replace("/ ", "/")); current = token
        else:
            current = candidate
    if current: lines.append(current.replace("/ ", "/"))
    return lines

def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cols, card_w, card_h, label_h, gap = 5, 254, 379, 126, 24
    tile_w = card_w + 20
    width = cols * tile_w + (cols + 1) * gap
    header_h, section_h = 220, 62
    sections = [("NATIVE WORD CARD TEMPLATES (11)", NATIVE),
                ("COMPLETED SAMPLE CARDS (20) — references, not templates", SAMPLES)]
    height = header_h + sum(section_h + ((len(items)+cols-1)//cols)*(card_h+label_h+gap)
                            for _, items in sections)
    canvas = Image.new("RGB", (width, height), "#15121b")
    draw = ImageDraw.Draw(canvas)
    draw.text((gap, 22), "WORD CARD — NATIVE SOURCE COLLAGE", font=font(34, True), fill="white")
    draw.text((gap, 76), "REQ-PPAUG-024 correction: exact repository faces only; no generated matrix cells",
              font=font(20), fill="#ddd5e4")
    draw.text((gap, 112), f"Authority commit: {AUTHORITY}", font=font(18, True), fill="#f1cc68")
    draw.text((gap, 146), "Every face is shown whole. Only uniform downscaling is applied; labels sit outside faces.",
              font=font(18), fill="#ddd5e4")
    cells, y = [], header_h
    for section, items in sections:
        draw.rounded_rectangle((gap, y, width-gap, y+46), 8, fill="#392346")
        draw.text((gap+14, y+9), section, font=font(21, True), fill="white")
        y += section_h
        for index, (path, role) in enumerate(items):
            row, col = divmod(index, cols)
            x = gap + col*(tile_w+gap); top = y + row*(card_h+label_h+gap)
            raw = git_bytes(path)
            source = Image.open(__import__("io").BytesIO(raw)).convert("RGB")
            source_w, source_h = source.size
            rendered = source.resize((card_w, card_h), Image.Resampling.LANCZOS)
            px = x + (tile_w-card_w)//2
            canvas.paste(rendered, (px, top))
            draw.rectangle((px-1, top-1, px+card_w, top+card_h), outline="#705b7d", width=1)
            label_y = top + card_h + 8
            role_face, path_face = font(12, True), font(10)
            role_lines = wrap(draw, role, tile_w, role_face)
            for line_no, line in enumerate(role_lines):
                draw.text((x, label_y+line_no*16), line, font=role_face, fill="#f1cc68")
            path_y = label_y + len(role_lines)*16 + 4
            for line_no, line in enumerate(wrap(draw, path, tile_w, path_face)):
                draw.text((x, path_y+line_no*14), line, font=path_face, fill="white")
            cells.append({"cell": len(cells)+1, "section": section, "role": role, "repository_path": path,
                          "authority_commit": AUTHORITY, "git_blob_sha": subprocess.run(
                              ["git", "-C", str(ROOT), "rev-parse", f"{AUTHORITY}:{path}"],
                              check=True, capture_output=True, text=True).stdout.strip(),
                          "source_byte_sha256": sha256(raw), "source_dimensions": [source_w, source_h],
                          "transform": {"operation": "uniform full-face resize", "crop": False,
                                        "resampling": "Pillow LANCZOS", "rendered_dimensions": [card_w, card_h]},
                          "rendered_rgb_sha256": sha256(rendered.tobytes()),
                          "collage_face_bbox_xywh": [px, top, card_w, card_h]})
        y += ((len(items)+cols-1)//cols)*(card_h+label_h+gap)
    output = OUT / "visual_acceptance_review_5x4.png"
    canvas.save(output, "PNG", optimize=False)
    manifest = {
        "requirement": "REQ-PPAUG-024", "artifact": output.relative_to(ROOT).as_posix(),
        "repository_remote": REMOTE, "authority_commit": AUTHORITY,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "policy": "Read-only collage of exact existing repository faces; no image model, generation, repaint, approximation, overlay, or crop.",
        "scope": {"native_template_cells": len(NATIVE), "completed_sample_cells": len(SAMPLES),
                  "excluded": ["generated/reconstructed type-by-rarity candidates", "Lot cards", "card backs", "reference palettes"]},
        "proof_method": "For each bbox, RGB pixels equal the recorded deterministic full-face LANCZOS resize of the authority blob.",
        "collage_byte_sha256": sha256(output.read_bytes()), "cells": cells,
    }
    (OUT / "visual_acceptance_review_5x4.provenance.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    build()
