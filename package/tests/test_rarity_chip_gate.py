"""The painted rarity chip is verified against the canonical template, never stamped."""
import json
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from hypertext.cards.rarity_chip_gate import REGION_CHIP, chip_geometry, inspect_rarity_chip, register
from hypertext.cards.template_matrix import resolve_template_record

ROOT = Path(__file__).resolve().parents[2]
BRICK = ROOT / "series/2026-Q1/cards/048-brick"


def _brick():
    if not (BRICK / "outputs/card_1024x1536.png").is_file():
        pytest.skip("BRICK face not checked out (git lfs)")
    card = json.loads((BRICK / "card.json").read_text(encoding="utf-8"))
    record = resolve_template_record("NOUN", "UNCOMMON", verify=True)
    return card, Path(record["path"])


def test_every_composed_template_chip_is_measurable():
    for card_type in ("NOUN", "VERB", "ADJECTIVE", "NAME", "TITLE"):
        for rarity in ("COMMON", "UNCOMMON", "RARE", "GLORIOUS"):
            record = resolve_template_record(card_type, rarity, verify=True)
            image = Image.open(record["path"]).convert("RGB").resize((1024, 1536), Image.Resampling.LANCZOS)
            geo = chip_geometry(image.crop(REGION_CHIP))
            assert geo and geo["diamond_colour"] and geo["word_width"] > 40, (card_type, rarity, geo)


def test_painted_chip_on_a_graded_face_passes():
    card, template = _brick()
    report = inspect_rarity_chip(BRICK / "outputs/card_1024x1536.png", template, card)
    assert report["passed"], report["defects"]
    assert report["observed"]["left_inset"] >= 6


def _face_with(edit, tmp_path):
    card, template = _brick()
    face = Image.open(BRICK / "outputs/card_1024x1536.png").convert("RGB")
    tmpl = Image.open(template).convert("RGB").resize((1024, 1536), Image.Resampling.LANCZOS)
    dx, dy = register(face, tmpl, REGION_CHIP)
    geo = chip_geometry(face.crop((REGION_CHIP[0] + dx, REGION_CHIP[1] + dy, REGION_CHIP[2] + dx, REGION_CHIP[3] + dy)))
    edit(ImageDraw.Draw(face), REGION_CHIP[0] + dx, REGION_CHIP[1] + dy, geo)
    out = tmp_path / "face.png"
    face.save(out)
    return inspect_rarity_chip(out, template, card), geo


def test_erased_word_is_rejected(tmp_path):
    def erase(draw, ox, oy, geo):
        x0, x1 = geo["word"]; y0, y1 = geo["word_rows"]
        draw.rectangle((ox + x0 - 2, oy + y0 - 2, ox + x1 + 2, oy + y1 + 2), fill=(26, 34, 64))
    report, _ = _face_with(erase, tmp_path)
    assert not report["passed"]
    assert {d["code"] for d in report["defects"]} & {"rarity-chip-missing", "rarity-word-width"}


def test_wrong_diamond_colour_is_rejected(tmp_path):
    def recolour(draw, ox, oy, geo):
        x0, x1 = geo["diamond"]; y0, y1 = geo["word_rows"]
        draw.rectangle((ox + x0, oy + y0, ox + x0 + 26, oy + y1), fill=(251, 148, 7))   # GLORIOUS orange on an UNCOMMON card
    report, _ = _face_with(recolour, tmp_path)
    assert not report["passed"]
    assert "rarity-diamond-colour" in {d["code"] for d in report["defects"]}


def test_word_touching_the_block_edge_is_rejected(tmp_path):
    def shift(draw, ox, oy, geo):
        x0, x1 = geo["word"]; y0, y1 = geo["word_rows"]
        bx0 = geo["block"][0]
        # slide the word left so it starts 2px from the block edge
        face = draw._image
        strip = face.crop((ox + x0, oy + y0, ox + x1, oy + y1))
        draw.rectangle((ox + x0, oy + y0, ox + x1, oy + y1), fill=(26, 34, 64))
        face.paste(strip, (ox + bx0 + 2, oy + y0))
    report, _ = _face_with(shift, tmp_path)
    assert not report["passed"]
    assert "rarity-word-clipped" in {d["code"] for d in report["defects"]}
