import json
from pathlib import Path

import pytest
from PIL import Image

from hypertext.lots.generation import _staged_render
from hypertext.lots.renderer import _build_lot_prompt, _build_lot_style_refs
from hypertext.lots.rules import (CHAPTER_VALUE, IMAGE_DIMENSIONS, OPPONENT_LETTERS,
                                  OWNER_LETTERS, POINTS, VISITOR_LETTERS,
                                  load_lot_rules, subtype_reference)
from hypertext.lots.rules import reference_manifest
from hypertext.gemini import style

ROOT = Path(__file__).resolve().parents[2]

def test_all_30_rules_and_variants_are_canonical():
    rules = load_lot_rules()
    assert len(rules) == 30
    assert {p["name"] for p in rules} >= {"CONGREGATION"}
    assert {p["cards"] for p in rules} == {5, 6, 7}
    for p in rules:
        assert p["points"] == POINTS[p["cards"]]
        assert p["opponent_letters"] == OPPONENT_LETTERS[p["cards"]]
        assert "[" not in p["composition_label"]
        assert p["card_count_label"] == f'{p["cards"]}-CARD'
        assert p["chapter_value"] == CHAPTER_VALUE[p["cards"]] == p["points"]
        assert p["owner_letters"] == OWNER_LETTERS[p["cards"]] == p["opponent_letters"]
        assert p["visitor_letters"] == VISITOR_LETTERS[p["cards"]]


def test_babel_alpha_lot_values_match_rulebook():
    assert CHAPTER_VALUE == {5: 8, 6: 10, 7: 14}
    assert OWNER_LETTERS == {5: 2, 6: 2, 7: 3}
    assert VISITOR_LETTERS == {5: 1, 6: 1, 7: 2}
    rules = Path(ROOT / "docs" / "rules.md").read_text(encoding="utf-8")
    for size in (5, 6, 7):
        row = (f"| {size}-card | {CHAPTER_VALUE[size]} points | {OWNER_LETTERS[size]} | "
               f"{VISITOR_LETTERS[size]} |")
        assert row in rules, row


@pytest.mark.parametrize("cards,points,letters", [(5, 8, 2), (6, 10, 2), (7, 14, 3)])
def test_source_subtype_prompt_and_reference_agree(tmp_path, cards, points, letters):
    phase = next(p for p in load_lot_rules() if p["cards"] == cards)
    phase.update(flavor="f", context="c", series="test", verse="Genesis 1:1")
    refs = _build_lot_style_refs(tmp_path, cards)
    assert refs[0] == str(subtype_reference(cards))
    assert all(Path(p).name.lower() != "lot_back.png" for p in refs)
    prompt = _build_lot_prompt(phase, refs)
    payload = json.loads(prompt.split("EXACT_CANONICAL_CONTENT_JSON=", 1)[1].split("\n", 1)[0])
    assert payload["composition"] == phase["composition"]
    assert f"sizes.LOT_{cards}" in prompt
    assert "GLOBAL=" in prompt and "STRUCTURE=" in prompt and "SIZE=" in prompt
    assert "no generated watermark" in prompt
    assert "infer no missing tail" in prompt
    assert f"Chapter Value: {points} Points" in prompt
    assert f"Page Value: {letters} Letters" in prompt
    assert f'"{cards}-CARD"' in prompt
    subtype_prompt = (subtype_reference(cards).parent / "prompt.txt").read_text()
    assert f"{points} Points / {letters} Letters" in subtype_prompt

def test_reference_manifest_sniffs_curated_files_without_rewriting(tmp_path):
    for cards in (5, 6, 7):
        ref = subtype_reference(cards)
        before = ref.read_bytes()
        manifest = reference_manifest(cards)
        with Image.open(ref) as image:
            assert manifest["mime_type"] == Image.MIME[image.format]
            assert (manifest["width"], manifest["height"]) == image.size
        assert manifest["role"] == "face" and manifest["immutable"] is True
        assert ref.read_bytes() == before

def test_versioned_reference_is_sent_with_sniffed_mime(monkeypatch):
    captured = {}
    class Part:
        @staticmethod
        def from_bytes(data, mime_type):
            captured["mime_type"] = mime_type
            return object()
    monkeypatch.setattr(style, "types", type("Types", (), {"Part": Part}))
    style._image_part_from_bytes(subtype_reference(7).read_bytes())
    assert captured["mime_type"] == reference_manifest(7)["mime_type"]

def test_failed_staged_replacement_preserves_prior(tmp_path):
    out = tmp_path / "lot" / "outputs" / "lot_1024x1536.png"
    out.parent.mkdir(parents=True)
    Image.new("RGB", IMAGE_DIMENSIONS, "red").save(out)
    before = out.read_bytes()
    def fail(card_data, staged, series_dir):
        Image.new("RGB", (10, 10), "blue").save(staged)
    with pytest.raises(RuntimeError, match="invalid Lot output"):
        _staged_render(fail, {}, out, tmp_path)
    assert out.read_bytes() == before
    assert not (out.parent.parent / "revisions.json").exists()

def test_successful_staged_replacement_records_revision(tmp_path):
    out = tmp_path / "lot" / "outputs" / "lot_1024x1536.png"
    def render(card_data, staged, series_dir):
        Image.new("RGB", IMAGE_DIMENSIONS, "green").save(staged)
    assert _staged_render(render, {}, out, tmp_path) == 1
    record = json.loads((out.parent.parent / "revisions.json").read_text())[0]
    assert (record["mime_type"], record["width"], record["height"]) == ("image/png", 1024, 1536)
