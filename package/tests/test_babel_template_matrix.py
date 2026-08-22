import copy
import hashlib
from pathlib import Path
import pytest

from hypertext.cards import template_matrix
from hypertext.pipeline import daily


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


def test_all_valid_combinations_resolve_to_byte_identical_accepted_assets():
    manifest = template_matrix.load_template_manifest()
    matrix = template_matrix.load_matrix()
    expected = {(item["type"], item["rarity"]) for item in matrix["valid_combinations"]}
    assert expected == {(item["type"], item["rarity"]) for item in manifest["outputs"]}
    assert len(manifest["outputs"]) == 20
    for item in manifest["outputs"]:
        canonical = template_matrix.resolve_template(item["type"], item["rarity"])
        candidate = template_matrix.ROOT / item["accepted_candidate"]
        assert canonical.read_bytes() == candidate.read_bytes()
        assert hashlib.sha256(canonical.read_bytes()).hexdigest() == item["sha256"]


@pytest.mark.parametrize("card_type,rarity", [("OTHER", "COMMON"), ("NOUN", "MYTHIC"), ("", "")])
def test_out_of_vocabulary_combinations_are_explicitly_rejected(card_type, rarity):
    with pytest.raises(ValueError, match="unsupported card template combination"):
        template_matrix.resolve_template(card_type, rarity)


def test_runtime_style_reference_consumes_promoted_type_rarity_treatment(tmp_path, monkeypatch):
    monkeypatch.chdir(template_matrix.ROOT)
    refs, labels, fix_mode = daily._build_style_refs(
        tmp_path, target_type="VERB", target_rarity="GLORIOUS"
    )
    assert Path(refs[-1]) == template_matrix.resolve_template("VERB", "GLORIOUS")
    assert set(labels.values()) <= {"GLORIOUS"}
    assert fix_mode is False


@pytest.mark.parametrize("card_type,rarity", [("OTHER", "COMMON"), ("NOUN", "MYTHIC"), (None, "COMMON")])
def test_runtime_style_reference_rejects_invalid_treatments(tmp_path, card_type, rarity):
    with pytest.raises(ValueError, match="unsupported card template combination"):
        daily._build_style_refs(tmp_path, target_type=card_type, target_rarity=rarity)
