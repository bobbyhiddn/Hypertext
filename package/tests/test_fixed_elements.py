"""Deterministic fixed elements: pips, pill, chip, number, footer are stamped, not rolled."""
import json
import shutil
from pathlib import Path

from PIL import Image

from hypertext.cards.fixed_elements import apply_fixed_elements, register
from hypertext.cards.stat_pip_gate import inspect_card_stat_pips

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "series" / "2026-Q1" / "cards" / "048-brick"


def _copy_card(tmp_path: Path) -> Path:
    if not (SAMPLE / "outputs" / "card_1024x1536.png").is_file():
        import pytest
        pytest.skip("sample card face not available")
    dst = tmp_path / "048-brick"
    shutil.copytree(SAMPLE, dst, ignore=shutil.ignore_patterns("reference-inputs"))
    return dst


def test_register_recovers_a_known_shift():
    base = Image.new("RGB", (200, 200), (230, 210, 170))
    from PIL import ImageDraw
    ImageDraw.Draw(base).rectangle((60, 60, 140, 140), fill=(30, 30, 60))
    shifted = Image.new("RGB", (200, 200), (230, 210, 170))
    ImageDraw.Draw(shifted).rectangle((63, 55, 143, 135), fill=(30, 30, 60))
    assert register(shifted, base, (40, 40, 160, 160), search=10) == (3, -5)


def test_stamped_face_matches_card_json_pips_and_records_provenance(tmp_path):
    card_dir = _copy_card(tmp_path)
    card = json.loads((card_dir / "card.json").read_text(encoding="utf-8"))
    card["content"]["STAT_LORE"], card["content"]["STAT_CONTEXT"], card["content"]["STAT_COMPLEXITY"] = 2, 5, 1
    (card_dir / "card.json").write_text(json.dumps(card), encoding="utf-8")
    prov = apply_fixed_elements(card_dir)
    assert prov["contract"] == "hypertext.fixed-elements/v1"
    assert prov["regions"]["stat_pips"]["counts"] == (2, 5, 1)
    assert prov["face_sha256_before"] != prov["face_sha256_after"]
    assert (card_dir / "outputs" / "fixed-elements.json").is_file()
    report = inspect_card_stat_pips(card_dir)
    assert report["passed"], report["defects"]
    assert prov["regions"]["number"]["text"] == "#048"
    assert prov["regions"]["footer"]["text"].startswith("SERIES: ")


def test_restamping_is_stable_and_keeps_the_gate_green(tmp_path):
    """Stamps re-sample the face's own parchment and band, so a second pass is
    not byte-identical, but it must be visually stable and still pass the gate."""
    from PIL import ImageChops
    card_dir = _copy_card(tmp_path)
    apply_fixed_elements(card_dir)
    first = Image.open(card_dir / "outputs" / "card_1024x1536.png").convert("RGB")
    apply_fixed_elements(card_dir)
    second = Image.open(card_dir / "outputs" / "card_1024x1536.png").convert("RGB")
    diff = ImageChops.difference(first, second).convert("L").point(lambda v: 255 if v > 24 else 0)
    changed = sum(1 for v in diff.get_flattened_data() if v) / (1024 * 1536)
    assert changed < 0.002, changed
    assert inspect_card_stat_pips(card_dir)["passed"]


def test_chip_word_sits_inside_the_block_for_every_composed_template():
    """The UNCOMMON composed templates clip the rarity word at the block's left
    edge (template-package defect, 2026-08-28). The stamp must re-set the word
    inside a widened block for those and leave the other templates untouched."""
    import glob

    from hypertext.cards.fixed_elements import (
        CHIP_WORD_PAD, FACE_SIZE, REGION_CHIP, chip_geometry, correct_chip_patch, font_path,
    )

    paths = sorted(glob.glob(str(ROOT / "templates/card/v001/composed/*/*/template_1024x1536.png")))
    assert len(paths) == 20
    font = font_path()
    for path in paths:
        rarity = Path(path).parent.name
        template = Image.open(path).convert("RGB").resize(FACE_SIZE, Image.Resampling.LANCZOS)
        patch = template.crop(REGION_CHIP)
        before = chip_geometry(patch)
        assert before is not None, path
        assert before["clipped"] == (rarity == "uncommon"), path
        fixed, info = correct_chip_patch(patch, rarity.title(), font)
        assert info["word_rendered"] == (rarity == "uncommon"), path
        after = chip_geometry(fixed)
        assert after is not None and not after["clipped"], path
        assert after["left_pad"] >= CHIP_WORD_PAD - 8, (path, after)
        assert after["gap"] >= 6, (path, after)
