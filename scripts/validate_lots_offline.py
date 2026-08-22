#!/usr/bin/env python3
"""Produce deterministic, quota-free Lot contract evidence."""
from __future__ import annotations
import json
from pathlib import Path
from PIL import Image, ImageDraw
from hypertext.lots.renderer import _build_lot_prompt
from hypertext.lots.rules import IMAGE_DIMENSIONS, load_lot_rules, reference_manifest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "evidence" / "lot-contract-offline"

def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    rules = load_lot_rules()
    cases = []
    for cards in (5, 6, 7):
        phase = next(p for p in rules if p["cards"] == cards)
        data = {**phase, "flavor": "Deterministic offline validation",
                "context": "No Gemini request was made.", "series": "offline", "verse": ""}
        prompt = _build_lot_prompt(data, [reference_manifest(cards)["path"]])
        image = Image.new("RGB", IMAGE_DIMENSIONS, "#eee2c4")
        draw = ImageDraw.Draw(image)
        draw.text((64, 64), f'{phase["name"]} | {phase["card_count_label"]}', fill="#102030")
        draw.text((64, 100), f'{phase["points"]} Points / {phase["opponent_letters"]} Letters', fill="#102030")
        out = EVIDENCE / f"{cards}-card.png"
        image.save(out, "PNG")
        with Image.open(out) as check:
            passed = (check.format == "PNG" and check.size == IMAGE_DIMENSIONS and
                      f'{phase["points"]} Points' in prompt and
                      f'{phase["opponent_letters"]} Letters' in prompt)
        reference = reference_manifest(cards)
        reference["path"] = str(Path(reference["path"]).relative_to(ROOT))
        cases.append({"cards": cards, "phase": phase["name"], "score": 100 if passed else 0,
                      "passed": passed, "output": str(out.relative_to(ROOT)),
                      "reference": reference})
    report = {"mode": "offline-deterministic", "gemini_calls": 0,
              "definitions": len(rules), "cases": cases}
    (EVIDENCE / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return 0 if all(case["passed"] for case in cases) else 1

if __name__ == "__main__":
    raise SystemExit(main())
