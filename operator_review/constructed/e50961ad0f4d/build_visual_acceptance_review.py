from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
TYPES = ["noun", "verb", "adjective", "name", "title"]
RARITIES = ["common", "uncommon", "rare", "glorious"]

specific = {
    ("verb", "rare"): ["type label/icon identity drifts to NOUN"],
    ("verb", "glorious"): ["type label/icon identity drifts to NOUN"],
    ("adjective", "uncommon"): ["type label identity drifts to NOUN"],
    ("adjective", "rare"): ["type label identity drifts to NOUN"],
    ("name", "common"): ["wrong type icon: pencil substituted for feather quill"],
    ("name", "uncommon"): ["wrong type icon: pencil substituted for feather quill"],
    ("name", "rare"): ["wrong type icon: pencil substituted for feather quill"],
    ("name", "glorious"): ["wrong type icon: pencil substituted for feather quill"],
}

findings = []
for row, type_name in enumerate(TYPES, 1):
    for col, rarity in enumerate(RARITIES, 1):
        reasons = [
            "border and geometry drift outside controlled type/rarity regions",
            "shared-pixel invariance, type isolation, rarity isolation, border registration, and geometry registration evidence missing",
        ]
        reasons += specific.get((type_name, rarity), [])
        if rarity == "glorious":
            reasons.append("incorrect Glorious top-right cost: exactly two card icons are not legibly preserved")
        if rarity == "rare":
            reasons.append("Rare top-right cost is generative rather than exact controlled-region composition")
        findings.append({
            "cell": (row - 1) * 4 + col,
            "row": row,
            "column": col,
            "type": type_name,
            "rarity": rarity,
            "candidate": f"{type_name}__{rarity}.png",
            "decision": "reject",
            "reasons": reasons,
        })

report = {
    "schema_version": 1,
    "gate": "visual_acceptance",
    "authority_commit": "e50961ad0f4d66f398f81706f092a7d0ea9cb0f4",
    "build_commit": "f334220",
    "decision": "reject",
    "operator_visual_approval_required": True,
    "summary": {"expected_cells": 20, "present_cells": 20, "accepted": 0, "rejected": 20},
    "matrix_order": {"rows": TYPES, "columns": RARITIES},
    "global_findings": [
        "All 20 candidates are complete raster files with recorded source blobs, but all are full-frame Gemini redraws rather than controlled BASE + TYPE + RARITY compositions.",
        "Manifest omits required type/rarity masks, mask hashes, base landmarks, witness declarations, and determinism evidence.",
        "checks.json covers only input blobs, cardinality, raster decode, canonical immutability, and contact-sheet presence; it does not satisfy the 13-check acceptance contract.",
        "Visible border, typography, header, panel, and footer changes occur across the matrix; these are prohibited outside controlled masks.",
    ],
    "cells": findings,
}
(ROOT / "visual_acceptance_findings.json").write_text(json.dumps(report, indent=2) + "\n")

thumb_w, thumb_h = 424, 632
label_h, header_h = 54, 94
sheet = Image.new("RGB", (thumb_w * 4, header_h + (thumb_h + label_h) * 5), "#17131d")
draw = ImageDraw.Draw(sheet)
font = ImageFont.load_default()
draw.text((16, 12), "HYPERTEXT 20-CELL INTERNAL QUALITY GATE — REJECT 20/20", fill="#ffffff", font=font)
draw.text((16, 34), "Rows: noun, verb, adjective, name, title | Columns: common, uncommon, rare, glorious", fill="#d8cfe0", font=font)
draw.text((16, 56), "Operator visual approval remains final. Red labels are outside candidate pixels.", fill="#ffaaaa", font=font)
for item in findings:
    r, c = item["row"] - 1, item["column"] - 1
    img = Image.open(ROOT / item["candidate"]).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
    x, y = c * thumb_w, header_h + r * (thumb_h + label_h)
    sheet.paste(img, (x, y))
    draw.rectangle((x, y + thumb_h, x + thumb_w - 1, y + thumb_h + label_h - 1), fill="#8b1118")
    draw.text((x + 8, y + thumb_h + 7), f"CELL {item['cell']:02d}  {item['type'].upper()} / {item['rarity'].upper()}  — REJECT", fill="white", font=font)
    short = "border/geometry drift"
    if item["rarity"] == "glorious": short += "; wrong/illegible 2-card cost"
    elif item["rarity"] == "rare": short += "; uncontrolled rare cost"
    draw.text((x + 8, y + thumb_h + 27), short, fill="#ffe0e0", font=font)
sheet.save(ROOT / "visual_acceptance_review_5x4.png")
