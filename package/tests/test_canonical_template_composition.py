import json
from pathlib import Path
from PIL import Image
import yaml
ROOT = Path(__file__).resolve().parents[2]
WORD_SIZE = (848, 1264)
LOT_SIZE = (1024, 1536)
TYPE_BOX = (51, 77, 134, 162)
RARITY_BOX = (650, 10, 838, 162)

def test_word_manifest_is_exact_matrix_cross_product_and_bounded():
    matrix = json.loads((ROOT / "schema/babel_template_matrix.json").read_text())
    manifest = json.loads((ROOT / "templates/card/v001/composed/manifest.json").read_text())
    expected = {(x["type"], x["rarity"]) for x in matrix["valid_combinations"]}
    assert {(x["type"], x["rarity"]) for x in manifest["outputs"]} == expected
    assert len(manifest["outputs"]) == 20
    assert all(x["visible_type_label"] == x["type"] for x in manifest["outputs"])
    assert all(x["visible_rarity_label"] == x["rarity"] for x in manifest["outputs"])
    assert manifest["construction_evidence"] == "operator_review/constrained/e50961ad0f4d/manifest.json"
    assert manifest["bounded_regions"] == {"type": list(TYPE_BOX), "rarity": list(RARITY_BOX)}
    width, height = manifest["canvas"]
    for left, top, right, bottom in manifest["bounded_regions"].values():
        assert 0 <= left < right <= width
        assert 0 <= top < bottom <= height
    evidence = json.loads((ROOT / manifest["construction_evidence"]).read_text())
    for kind, envelope in manifest["bounded_regions"].items():
        edits = [edit for edit in evidence["edits"] if edit["kind"] == kind]
        assert edits and {tuple(edit["box"]) for edit in edits} == {tuple(envelope)}
        with Image.open(ROOT / Path(manifest["construction_evidence"]).parent / edits[0]["mask"]) as mask:
            left, top, right, bottom = mask.getbbox()
        outer_left, outer_top, outer_right, outer_bottom = envelope
        assert outer_left <= left < right <= outer_right
        assert outer_top <= top < bottom <= outer_bottom
    for item in manifest["outputs"]:
        output = Image.open(ROOT / item["path"]).convert("RGB")
        assert output.size == WORD_SIZE

def test_shared_lots_are_only_actual_sizes_and_expose_both_values():
    manifest = json.loads((ROOT / "templates/lot/v001/shared/manifest.json").read_text())
    assert manifest["scope"] == "shared-across-all-sets"
    assert {x["subtype"] for x in manifest["outputs"]} == {"5-card", "6-card", "7-card"}
    for item in manifest["outputs"]:
        with Image.open(ROOT / item["path"]) as image:
            assert image.format == "PNG" and image.size == LOT_SIZE
        assert item["chapter_value"]["points"] and item["page_value"]["letters"]
        assert item["chapter_value"]["visible_label"].startswith("CHAPTER:")
        assert item["page_value"]["visible_label"].startswith("PAGE:")

def test_every_canonical_card_is_rendered_through_its_matrix_template():
    source = yaml.safe_load((ROOT / "series/2026-Q1/cards_index.yml").read_text())["cards"]
    manifest = json.loads((ROOT / "docs/evidence/deterministic-reconstruction/canonical-card-renders/manifest.json").read_text())
    assert manifest["count"] == len(source) == 31
    assert {(x["number"], x["type"], x["rarity"]) for x in manifest["outputs"]} == {
        (x["number"], x["type"], x["rarity"]) for x in source}
    assert all(Path(x["template"]).parts[:4] == ("templates", "card", "v001", "composed") for x in manifest["outputs"])

def test_congregation_is_the_canonical_any_mix_six_card_lot():
    phases = yaml.safe_load((ROOT / "templates/phases.yml").read_text())["phases"]
    congregation = next(x for x in phases if x["name"] == "CONGREGATION")
    assembly = next(x for x in phases if x["name"] == "ASSEMBLY")
    assert congregation["cards"] == 6 and congregation["display"] == "6 any mix"
    assert assembly["display"] == "3 + 3 (two types)"

def test_canonical_contract_contains_no_board_phase_language():
    paths = [ROOT / "schema", ROOT / "templates/card/v001/composed", ROOT / "templates/lot/v001/shared",
             ROOT / "package/hypertext/lots", ROOT / "package/tests"]
    offenders = []
    for root in paths:
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in {".py", ".json", ".yml", ".yaml", ".txt", ".md"}:
                forbidden = "board" + " phase"
                if forbidden in path.read_text(errors="ignore").lower(): offenders.append(str(path))
    assert not offenders
