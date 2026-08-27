import copy
import hashlib
from pathlib import Path
import pytest
from PIL import Image, ImageChops

from hypertext.cards import template_matrix
from hypertext.pipeline import daily


EVIDENCE_PRESENT = (template_matrix.ROOT / "templates/archive").exists()
requires_evidence = pytest.mark.skipif(
    not EVIDENCE_PRESENT,
    reason="cold evidence archive not present - run scripts/fetch_evidence.sh")


def test_every_canonical_babel_card_has_supported_type_rarity_mapping():
    assert template_matrix.validate_canonical_mappings() == []


def test_matrix_is_complete_and_counts_canonical_cards():
    matrix = template_matrix.load_matrix()
    combinations = matrix["valid_combinations"]
    assert len(matrix["word_types"]) == 5
    assert len(matrix["rarity_tiers"]) == 4
    assert len(combinations) == 20
    assert matrix["invalid_combinations"] == []
    assert sum(item["card_count"] for item in combinations) == 31
    assert {(item["type"], item["rarity"]) for item in combinations} == {
        (card_type, rarity)
        for card_type in matrix["word_types"]
        for rarity in matrix["rarity_tiers"]
    }


def test_missing_mapping_is_reported_with_canonical_card_identity():
    matrix = copy.deepcopy(template_matrix.load_matrix())
    matrix["valid_combinations"] = [
        item for item in matrix["valid_combinations"]
        if (item["type"], item["rarity"]) != ("NOUN", "COMMON")
    ]
    errors = template_matrix.validate_canonical_mappings(matrix)
    assert any("canonical card 1 GRACE lacks template mapping NOUN+COMMON" in error for error in errors)


@requires_evidence
def test_all_valid_combinations_resolve_to_label_only_corrections_of_accepted_assets():
    manifest = template_matrix.load_template_manifest()
    matrix = template_matrix.load_matrix()
    expected = {(item["type"], item["rarity"]) for item in matrix["valid_combinations"]}
    assert expected == {(item["type"], item["rarity"]) for item in manifest["outputs"]}
    assert len(manifest["outputs"]) == 20
    label_box = tuple(manifest["type_label_box"])
    for item in manifest["outputs"]:
        canonical = template_matrix.resolve_template(item["type"], item["rarity"])
        from hypertext.paths import resolve_recorded
        candidate = resolve_recorded(template_matrix.ROOT, item["accepted_candidate"])
        with Image.open(canonical) as current, Image.open(candidate) as accepted:
            difference = ImageChops.difference(current.convert("RGB"), accepted.convert("RGB"))
            changed = difference.getbbox()
            if changed is not None:
                assert label_box[0] <= changed[0] < changed[2] <= label_box[2]
                assert label_box[1] <= changed[1] < changed[3] <= label_box[3]
        assert hashlib.sha256(canonical.read_bytes()).hexdigest() == item["sha256"]


@pytest.mark.parametrize("card_type,rarity", [("OTHER", "COMMON"), ("NOUN", "MYTHIC"), ("", "")])
def test_out_of_vocabulary_combinations_are_explicitly_rejected(card_type, rarity):
    with pytest.raises(ValueError, match="unsupported card template combination"):
        template_matrix.resolve_template(card_type, rarity)


def test_runtime_style_reference_consumes_promoted_type_rarity_treatment(tmp_path, monkeypatch):
    monkeypatch.chdir(template_matrix.ROOT)
    pack = daily._build_style_refs(
        tmp_path, target_type="VERB", target_rarity="GLORIOUS"
    )
    refs, labels, fix_mode = pack
    assert Path(refs[0]) == template_matrix.resolve_template("VERB", "GLORIOUS")
    assert pack.references[0].role == "template"
    assert pack.references[0].gemini_label.startswith("[1] = TEMPLATE:")
    assert set(labels.values()) <= {"GLORIOUS"}
    assert fix_mode is False


@pytest.mark.parametrize(
    "card_type,rarity",
    [("OTHER", "COMMON"), ("NOUN", "MYTHIC"), (None, "COMMON"), ("NOUN", None), (None, None)],
)
def test_runtime_style_reference_rejects_invalid_treatments(tmp_path, card_type, rarity):
    with pytest.raises(ValueError, match="unsupported card template combination"):
        daily._build_style_refs(tmp_path, target_type=card_type, target_rarity=rarity)
