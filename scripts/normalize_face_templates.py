#!/usr/bin/env python3
"""Constrain Gemini subtype candidates to contract-approved exception regions."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

def normalize_card_subtypes():
    root = ROOT / "templates/card/v001"
    with Image.open(root/"base/template_1024x1536.png") as source:
        base = source.convert("RGB")
    for name in ("common","uncommon","rare","glorious","noun","verb","adjective","name","title"):
        path = root/name/"template_1024x1536.png"
        with Image.open(path) as source:
            candidate = source.convert("RGB")
        output = base.copy()
        # Deliberate exceptions only: top badges and the type-icon medallion.
        output.paste(candidate.crop((0, 0, 1024, 82)), (0, 0))
        output.paste(candidate.crop((18, 62, 190, 198)), (18, 62))
        output.save(path, "PNG")

if __name__ == "__main__": normalize_card_subtypes()
