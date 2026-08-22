import json
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw
import yaml
ROOT = Path(__file__).resolve().parents[2]
SIZE = (1024, 1536)
TYPE_BOX = (45, 0, 345, 205)
RARITY_BOX = (785, 0, 1008, 205)

def test_word_manifest_is_exact_matrix_cross_product_and_bounded():
    matrix = json.loads((ROOT / "schema/babel_template_matrix.json").read_text())
    manifest = json.loads((ROOT / "templates/card/v001/composed/manifest.json").read_text())
    expected = {(x["type"], x["rarity"]) for x in matrix["valid_combinations"]}
    assert {(x["type"], x["rarity"]) for x in manifest["outputs"]} == expected
    assert len(manifest["outputs"]) == 20
    assert all(x["visible_type_label"] == x["type"] for x in manifest["outputs"])
    assert all(x["visible_rarity_label"] == x["rarity"] for x in manifest["outputs"])
    base = Image.open(ROOT / matrix["layers"]["base"]).convert("RGB")
    mask = Image.new("1", SIZE, 255)
    for box in (TYPE_BOX, RARITY_BOX): ImageDraw.Draw(mask).rectangle(box, fill=0)
    for item in manifest["outputs"]:
        output = Image.open(ROOT / item["path"]).convert("RGB")
        assert output.size == SIZE
        assert ImageChops.difference(base, output).getbbox() is not None
        outside = Image.composite(output, base, mask)
        assert ImageChops.difference(base, outside).getbbox() is None

def test_shared_lots_are_only_actual_sizes_and_expose_both_values():
    manifest = json.loads((ROOT / "templates/lot/v001/shared/manifest.json").read_text())
    assert manifest["scope"] == "shared-across-all-sets"
    assert {x["subtype"] for x in manifest["outputs"]} == {"5-card", "6-card", "7-card"}
    for item in manifest["outputs"]:
        with Image.open(ROOT / item["path"]) as image:
            assert image.format == "PNG" and image.size == SIZE
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
