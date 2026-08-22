import copy

from hypertext.cards import template_matrix


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
