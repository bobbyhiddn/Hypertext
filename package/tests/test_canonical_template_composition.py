import json
import hashlib
from pathlib import Path
from PIL import Image, ImageChops
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
    assert manifest["construction_evidence"] == [
        "operator_review/constrained/e50961ad0f4d/manifest.json",
        "operator_review/name-quill-recovery/manifest.json",
    ]
    assert manifest["bounded_regions"] == {"type": list(TYPE_BOX), "rarity": list(RARITY_BOX)}
    width, height = manifest["canvas"]
    for left, top, right, bottom in manifest["bounded_regions"].values():
        assert 0 <= left < right <= width
        assert 0 <= top < bottom <= height
    evidence_path = ROOT / manifest["construction_evidence"][0]
    evidence = json.loads(evidence_path.read_text())
    for kind, envelope in manifest["bounded_regions"].items():
        edits = [edit for edit in evidence["edits"] if edit["kind"] == kind]
        assert edits and {tuple(edit["box"]) for edit in edits} == {tuple(envelope)}
        with Image.open(evidence_path.parent / edits[0]["mask"]) as mask:
            left, top, right, bottom = mask.getbbox()
        outer_left, outer_top, outer_right, outer_bottom = envelope
        assert outer_left <= left < right <= outer_right
        assert outer_top <= top < bottom <= outer_bottom
    for item in manifest["outputs"]:
        output = Image.open(ROOT / item["path"]).convert("RGB")
        assert output.size == WORD_SIZE


def _name_quill_mask(witness, stage):
    mask = Image.new("L", witness.size, 0)
    source, selected = witness.load(), mask.load()
    left, top, right, bottom = stage["scan_box"]
    threshold = stage["pixel_selection"]
    for y in range(top, bottom):
        for x in range(left, right):
            pixel = source[x, y]
            if (min(pixel) >= threshold["minimum_channel_at_least"] and
                    max(pixel) - min(pixel) < threshold["channel_range_less_than"]):
                selected[x, y] = 255
    return mask


def _project_neutral_treatment(raw, mask, stage):
    source = raw.load()
    neutral = []
    left, top, right, bottom = stage["neutral_source_scan_box"]
    threshold = stage["pixel_selection"]
    for y in range(top, bottom):
        for x in range(left, right):
            pixel = source[x, y]
            if (min(pixel) >= threshold["minimum_channel_at_least"] and
                    max(pixel) - min(pixel) < threshold["neutral_source_channel_range_less_than"]):
                neutral.append((x, y, pixel))
    projected = raw.copy()
    output = projected.load()
    for y in range(mask.height):
        for x in range(mask.width):
            if mask.getpixel((x, y)):
                pixel = source[x, y]
                if (min(pixel) < threshold["minimum_channel_at_least"] or
                        max(pixel) - min(pixel) > threshold["replace_channel_range_greater_than"]):
                    output[x, y] = min(neutral, key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)[2]
    return projected


def test_manifest_evidence_reconstructs_every_promoted_face_exactly():
    manifest = json.loads((ROOT / "templates/card/v001/composed/manifest.json").read_text())
    evidence_root = ROOT / Path(manifest["construction_evidence"][0]).parent
    recovery = json.loads((ROOT / manifest["construction_evidence"][1]).read_text())
    recovery_by_rarity = {record["rarity"]: record for record in recovery["records"]}
    stages = manifest["construction_stages"]
    assert list(stages) == manifest["composition_order"]
    with Image.open(ROOT / manifest["base"]) as image:
        base = image.convert("RGB")
    assert base.size == tuple(manifest["canvas"])
    assert hashlib.sha256((ROOT / manifest["base"]).read_bytes()).hexdigest() == manifest["base_sha256"]
    with Image.open(evidence_root / "masks/type.png") as image:
        type_mask = image.convert("L")
    with Image.open(evidence_root / "masks/rarity.png") as image:
        rarity_mask = image.convert("L")
    evidence = json.loads((evidence_root / "manifest.json").read_text())
    edits = {(edit["kind"], edit["key"]): edit for edit in evidence["edits"]}
    evidence_outputs = {(item["type"], item["rarity"]): item for item in evidence["outputs"]}

    for item in manifest["outputs"]:
        card_type, rarity = item["type"].lower(), item["rarity"].lower()
        with Image.open(ROOT / edits[("type", card_type)]["witness"]) as image:
            type_witness = image.convert("RGB")
        with Image.open(ROOT / edits[("rarity", rarity)]["witness"]) as image:
            rarity_witness = image.convert("RGB")
        evidence_output = evidence_outputs[(card_type, rarity)]
        evidence_candidate = ROOT / evidence_output["candidate"]
        assert hashlib.sha256(evidence_candidate.read_bytes()).hexdigest() == evidence_output["sha256"]
        reconstructed = None
        for stage_name in manifest["composition_order"]:
            stage = stages[stage_name]
            if stage.get("applies_to_type", "").lower() not in ("", card_type):
                continue
            operation = stage["operation"]
            if operation == "copy_rgb":
                reconstructed = base.copy()
            elif operation == "paste_witness_through_mask":
                witness, mask = ((type_witness, type_mask) if stage["witness_edit_kind"] == "type"
                                 else (rarity_witness, rarity_mask))
                reconstructed.paste(witness, mask=mask)
            elif operation == "fill_white_through_mask_derived_from_type_witness":
                before = reconstructed.copy()
                reconstructed.paste(Image.new("RGB", reconstructed.size, tuple(stage["fill_rgb"])),
                                    mask=_name_quill_mask(type_witness, stage))
                changed = sum(1 for pixel in ImageChops.difference(before, reconstructed).get_flattened_data()
                              if pixel != (0, 0, 0))
                assert changed == stage["expected_changed_pixels_per_output"]
            elif operation == "nearest_neutral_pixel_projection":
                record = recovery_by_rarity[rarity]
                with Image.open(ROOT / record["target"]) as target:
                    assert ImageChops.difference(reconstructed, target.convert("RGB")).getbbox() is None
                with Image.open(evidence_candidate) as candidate:
                    assert ImageChops.difference(reconstructed, candidate.convert("RGB")).getbbox() is None
                with Image.open(ROOT / record["raw_output"]) as raw_image:
                    raw = raw_image.convert("RGB").resize(tuple(stage["raw_resize"]), Image.Resampling.LANCZOS)
                with Image.open(ROOT / stage["mask"]) as image:
                    recovery_mask = image.convert("L")
                reconstructed.paste(_project_neutral_treatment(raw, recovery_mask, stage), mask=recovery_mask)
            else:
                raise AssertionError(f"undeclared construction operation: {operation}")
        if card_type != "name":
            with Image.open(evidence_candidate) as candidate:
                assert ImageChops.difference(reconstructed, candidate.convert("RGB")).getbbox() is None

        with Image.open(ROOT / item["path"]) as promoted:
            assert ImageChops.difference(reconstructed, promoted.convert("RGB")).getbbox() is None

def test_shared_lots_are_only_actual_sizes_and_expose_both_values():
    manifest = json.loads((ROOT / "templates/lot/v001/shared/manifest.json").read_text())
    assert manifest["scope"] == "shared-across-all-sets"
    assert {(f'{x["cards"]}-card', x["role"]) for x in manifest["cells"]} == {
        (f"{cards}-card", role) for cards in (5, 6, 7) for role in ("chapter", "page")}
    assert len(manifest["references"]) == 3
    for item in manifest["cells"]:
        with Image.open(ROOT / item["path"]) as image:
            assert image.format == "PNG" and image.size == LOT_SIZE
        assert item["reward"] and item["recipe"]
        assert hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"]


def test_lot_representatives_are_exact_authoritative_phase_recipes():
    phases = {x["id"]: x for x in yaml.safe_load((ROOT / "templates/phases.yml").read_text())["phases"]}
    schema = json.loads((ROOT / "schema/lot_template_family.json").read_text())
    for subtype in schema["subtypes"]:
        phase = phases[subtype["representative"]["id"]]
        assert phase["cards"] == subtype["cards"]
        assert phase["name"] == subtype["representative"]["name"]
        assert phase["display"].upper() == subtype["representative"]["display"]

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
