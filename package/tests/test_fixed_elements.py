"""Deterministic fixed elements: pips, pill, chip, number, footer are stamped, not rolled."""
import json
import shutil
from pathlib import Path

import pytest
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


def test_rarity_word_sits_inside_the_block_on_every_composed_template():
    """The package once shipped 'Uncommon' clipped by the block's left edge
    (repaired 2026-08-28); keep every cell's word inset from the block."""
    from hypertext.cards.template_matrix import MANIFEST_PATH, resolve_template_record

    if "repairs" not in json.loads(MANIFEST_PATH.read_text(encoding="utf-8")):
        pytest.skip("composed template repair not applied yet (scripts/templates/repair_composed_labels.py --apply)")
    block_left, edge_cols, word_rows = 658, (659, 666), (27, 49)   # stops short of the rounded corner at (658, 50)
    for card_type in ("NOUN", "VERB", "ADJECTIVE", "NAME", "TITLE"):
        for rarity in ("COMMON", "UNCOMMON", "RARE", "GLORIOUS"):
            record = resolve_template_record(card_type, rarity, verify=True)
            image = Image.open(record["path"]).convert("L")
            assert image.size == (848, 1264)
            edge = image.crop((edge_cols[0], word_rows[0], edge_cols[1], word_rows[1]))
            assert max(edge.getdata()) < 120, f"{card_type}/{rarity}: rarity word touches the block edge"
            word = image.crop((block_left + 8, word_rows[0], 786, word_rows[1]))
            assert max(word.getdata()) > 120, f"{card_type}/{rarity}: no rarity word inside the block"


def test_title_templates_carry_the_repaired_title_pill():
    """The historical TITLE witness was a NOUN card, so every TITLE cell shipped
    with a NOUN pill; the 2026-08-28 repair points them at a repaired witness."""
    from hypertext.cards.template_matrix import MANIFEST_PATH, ROOT, resolve_template_record

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if "repairs" not in manifest:
        pytest.skip("composed template repair not applied yet (scripts/templates/repair_composed_labels.py --apply)")
    witness_record = manifest["repairs"][0]["title_type_label_witness"]
    pill_box = tuple(manifest["type_label_box"])
    witness = Image.open(ROOT / witness_record["path"]).convert("RGB").crop(pill_box)
    noun = Image.open(resolve_template_record("NOUN", "COMMON", verify=True)["path"]).convert("RGB").crop(pill_box)
    assert witness.tobytes() != noun.tobytes()
    for rarity in ("COMMON", "UNCOMMON", "RARE", "GLORIOUS"):
        record = resolve_template_record("TITLE", rarity, verify=True)
        assert record["type_label_source"] == witness_record["path"]
        title = Image.open(record["path"]).convert("RGB").crop(pill_box)
        assert title.tobytes() == witness.tobytes()
