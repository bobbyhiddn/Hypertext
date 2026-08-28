import json
import hashlib
from pathlib import Path
from PIL import Image, ImageChops
import pytest
import yaml
ROOT = Path(__file__).resolve().parents[2]

ARCHIVES = (ROOT / "templates/archive/pre-v002-lot-rework",
            ROOT / "templates/archive/matrix-provenance")

def resolve(relative):
    """Recorded paths predate the 2026-08 archive moves; fall back to the archives."""
    path = ROOT / relative
    if path.exists():
        return path
    for archive in ARCHIVES:
        candidate = archive / relative
        if candidate.exists():
            return candidate
    return path


EVIDENCE_PRESENT = (ROOT / "templates/archive").exists()
requires_evidence = pytest.mark.skipif(
    not EVIDENCE_PRESENT,
    reason="cold evidence archive not present - run scripts/fetch_evidence.sh")

WORD_SIZE = (848, 1264)
LOT_SIZE = (1024, 1536)
TYPE_BOX = (51, 77, 134, 162)
RARITY_BOX = (650, 10, 838, 162)

@requires_evidence
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
    evidence_path = resolve(manifest["construction_evidence"][0])
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
        output = Image.open(resolve(item["path"])).convert("RGB")
        assert output.size == WORD_SIZE


@requires_evidence
def test_every_matrix_row_uses_its_established_type_label_not_repeated_noun():
    """Compare pixels, not self-reported metadata, so an all-NOUN matrix fails."""
    manifest = json.loads((ROOT / "templates/card/v001/composed/manifest.json").read_text())
    label_box = tuple(manifest["type_label_box"])
    expected_types = ("NOUN", "VERB", "ADJECTIVE", "NAME", "TITLE")
    expected_rarities = ("COMMON", "UNCOMMON", "RARE", "GLORIOUS")
    by_key = {(item["type"], item["rarity"]): item for item in manifest["outputs"]}
    reference_regions = {}
    for card_type in expected_types:
        items = [by_key[(card_type, rarity)] for rarity in expected_rarities]
        assert len({item["type_label_source"] for item in items}) == 1
        witness = Image.open(resolve(items[0]["type_label_source"])).convert("RGB")
        expected = witness.crop(label_box)
        reference_regions[card_type] = expected.tobytes()
        for item in items:
            actual = Image.open(resolve(item["path"])).convert("RGB").crop(label_box)
            assert ImageChops.difference(actual, expected).getbbox() is None
    assert len(set(reference_regions.values())) == len(expected_types)


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


@requires_evidence
def test_manifest_evidence_reconstructs_every_promoted_face_exactly():
    manifest = json.loads((ROOT / "templates/card/v001/composed/manifest.json").read_text())
    evidence_root = resolve(manifest["construction_evidence"][0]).parent
    recovery = json.loads(resolve(manifest["construction_evidence"][1]).read_text())
    recovery_by_rarity = {record["rarity"]: record for record in recovery["records"]}
    stages = manifest["construction_stages"]
    assert list(stages) == manifest["composition_order"]
    with Image.open(resolve(manifest["base"])) as image:
        base = image.convert("RGB")
    assert base.size == tuple(manifest["canvas"])
    assert hashlib.sha256(resolve(manifest["base"]).read_bytes()).hexdigest() == manifest["base_sha256"]
    with Image.open(evidence_root / "masks/type.png") as image:
        type_mask = image.convert("L")
    with Image.open(evidence_root / "masks/rarity.png") as image:
        rarity_mask = image.convert("L")
    evidence = json.loads((evidence_root / "manifest.json").read_text())
    edits = {(edit["kind"], edit["key"]): edit for edit in evidence["edits"]}
    evidence_outputs = {(item["type"], item["rarity"]): item for item in evidence["outputs"]}

    for item in manifest["outputs"]:
        card_type, rarity = item["type"].lower(), item["rarity"].lower()
        with Image.open(resolve(edits[("type", card_type)]["witness"])) as image:
            type_witness = image.convert("RGB")
        with Image.open(resolve(edits[("rarity", rarity)]["witness"])) as image:
            rarity_witness = image.convert("RGB")
        evidence_output = evidence_outputs[(card_type, rarity)]
        evidence_candidate = resolve(evidence_output["candidate"])
        assert hashlib.sha256(evidence_candidate.read_bytes()).hexdigest() == evidence_output["sha256"]
        reconstructed = None
        for stage_name in manifest["composition_order"]:
            stage = stages[stage_name]
            if stage.get("applies_to_type", "").lower() not in ("", card_type):
                continue
            if stage.get("applies_to_rarity", "").lower() not in ("", rarity):
                continue
            operation = stage["operation"]
            if operation == "copy_rgb":
                reconstructed = base.copy()
            elif operation == "paste_rgb_patch":
                patch_path = resolve(stage["patch"])
                assert hashlib.sha256(patch_path.read_bytes()).hexdigest() == stage["patch_sha256"]
                with Image.open(patch_path) as patch:
                    left, top, right, bottom = stage["box"]
                    assert patch.size == (right - left, bottom - top)
                    reconstructed.paste(patch.convert("RGB"), (left, top))
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
                with Image.open(resolve(record["target"])) as target:
                    assert ImageChops.difference(reconstructed, target.convert("RGB")).getbbox() is None
                with Image.open(evidence_candidate) as candidate:
                    assert ImageChops.difference(reconstructed, candidate.convert("RGB")).getbbox() is None
                with Image.open(resolve(record["raw_output"])) as raw_image:
                    raw = raw_image.convert("RGB").resize(tuple(stage["raw_resize"]), Image.Resampling.LANCZOS)
                with Image.open(resolve(stage["mask"])) as image:
                    recovery_mask = image.convert("L")
                reconstructed.paste(_project_neutral_treatment(raw, recovery_mask, stage), mask=recovery_mask)
            elif operation == "paste_type_label_crop":
                label_box = tuple(stage["box"])
                label_source = resolve(item[stage["source_field"]])
                with Image.open(label_source) as source:
                    reconstructed.paste(source.convert("RGB").crop(label_box), label_box[:2])
            else:
                raise AssertionError(f"undeclared construction operation: {operation}")

        with Image.open(resolve(item["path"])) as promoted:
            assert ImageChops.difference(reconstructed, promoted.convert("RGB")).getbbox() is None

@requires_evidence
def test_shared_lots_are_only_actual_sizes_and_expose_both_values():
    manifest = json.loads(resolve("templates/lot/v001/shared/manifest.json").read_text())
    assert manifest["scope"] == "shared-across-all-sets"
    assert {f'{x["cards"]}-card' for x in manifest["cells"]} == {"5-card", "6-card", "7-card"}
    assert len(manifest["cells"]) == 3
    assert len(manifest["references"]) == 3
    for item in manifest["cells"]:
        with Image.open(resolve(item["path"])) as image:
            assert image.format == "PNG" and image.size == LOT_SIZE
        assert item["chapter_value"] and item["page_value"] and item["recipe"]
        assert hashlib.sha256(resolve(item["path"]).read_bytes()).hexdigest() == item["sha256"]


def test_lot_representatives_are_exact_authoritative_phase_recipes():
    phases = {x["id"]: x for x in yaml.safe_load((ROOT / "templates/phases.yml").read_text())["phases"]}
    schema = json.loads((ROOT / "schema/lot_template_family.json").read_text())
    for subtype in schema["subtypes"]:
        phase = phases[subtype["representative"]["id"]]
        assert phase["cards"] == subtype["cards"]
        assert phase["name"] == subtype["representative"]["name"]
        assert phase["display"].upper() == subtype["representative"]["display"]

@requires_evidence
def test_every_canonical_card_is_rendered_through_its_matrix_template():
    source = yaml.safe_load((ROOT / "series/2026-Q1/cards_index.yml").read_text())["cards"]
    manifest = json.loads(resolve("docs/evidence/deterministic-reconstruction/canonical-card-renders/manifest.json").read_text())
    # The reconstruction evidence is a frozen proof over the first 31 cards;
    # the set keeps growing past it.
    assert manifest["count"] == 31 <= len(source)
    assert {(x["number"], x["type"], x["rarity"]) for x in manifest["outputs"]} <= {
        (x["number"], x["type"], x["rarity"]) for x in source}
    assert all(Path(x["template"]).parts[:4] == ("templates", "card", "v001", "composed") for x in manifest["outputs"])

def test_congregation_and_assembly_use_the_typed_pattern_grammar():
    phases = yaml.safe_load((ROOT / "templates/phases.yml").read_text())["phases"]
    congregation = next(x for x in phases if x["name"] == "CONGREGATION")
    assembly = next(x for x in phases if x["name"] == "ASSEMBLY")
    assert congregation["cards"] == 6
    assert [(g["count"], g["constraint"]) for g in congregation["recipe"]["groups"]] == [
        (4, "same_type"), (2, "any")]
    assert [(g["count"], g["constraint"]) for g in assembly["recipe"]["groups"]] == [
        (3, "one_type"), (3, "another_type")]

def test_canonical_contract_contains_no_board_phase_language():
    paths = [ROOT / "schema", ROOT / "templates/card/v001/composed", ARCHIVES[0] / "templates/lot/v001/shared",
             ROOT / "package/hypertext/lots", ROOT / "package/tests"]
    offenders = []
    for root in paths:
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in {".py", ".json", ".yml", ".yaml", ".txt", ".md"}:
                forbidden = "board" + " phase"
                if forbidden in path.read_text(errors="ignore").lower(): offenders.append(str(path))
    assert not offenders
