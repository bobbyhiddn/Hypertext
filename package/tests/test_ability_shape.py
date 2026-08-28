"""No two cards share an ability shape."""
from hypertext.cards.ability_shape import ability_signature, shape_conflicts, signature_key

KINGDOM = "Each player adds one card from Sheol to their hand. Then add up to three cards from Sheol to your hand."
HOVER_V1 = "Each player draws one card from the Tower. Then choose up to three cards in Sheol and add those chosen cards to your hand."
HOVER_V2 = "Choose one Page belonging to another player. Add up to five cards from Sheol to your hand, one card of each card type in that chosen Page."
DEEP = "Choose up to three cards in Sheol that each have COMPLEXITY three or more. Add those chosen cards to your hand."
REDEEMER = "Spend one Letter and choose up to three cards in Sheol. Add those chosen cards to your hand."
HIGH = "Look at the top two cards of the Tower. Add one of those cards to your hand and put the other card on the bottom of the Tower."
TONGUE = "Look at the top three cards of the Tower. Add one of those cards to your hand and put the other cards on the bottom of the Tower."
SHEPHERD = "Look at the top three cards of the Tower. Add one of those cards to your hand and put the other cards on top of the Tower in any order."


def test_hover_v1_is_kingdom_with_a_different_verb():
    assert [c["with"] for c in shape_conflicts(HOVER_V1, [("039-kingdom", KINGDOM)])] == ["039-kingdom"]


def test_hover_v2_is_its_own_shape():
    assert shape_conflicts(HOVER_V2, [("039-kingdom", KINGDOM), ("035-deep", DEEP), ("047-redeemer", REDEEMER)]) == []


def test_filter_and_cost_distinguish_sheol_recoveries():
    keys = {signature_key(ability_signature(t)) for t in (KINGDOM, DEEP, REDEEMER)}
    assert len(keys) == 3


def test_look_count_and_rest_destination_distinguish_commons():
    keys = {signature_key(ability_signature(t)) for t in (HIGH, TONGUE, SHEPHERD)}
    assert len(keys) == 3


def test_signature_reads_core_reach_and_qualifiers():
    sig = ability_signature(HOVER_V2)
    assert sig["core"] == {"verb": "add", "zone": "Sheol", "qty": "up-to-5"}
    assert sig["another_player"] and sig["filter"] and not sig["every_player"]
