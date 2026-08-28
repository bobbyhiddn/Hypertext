"""Every current-contract ability is nameable in the grammar."""
from pathlib import Path

from hypertext.cards.ability_grammar import classify, load_grammar, load_series_abilities

ROOT = Path(__file__).resolve().parents[2]


def test_grammar_loads_with_the_four_tiers_and_core_productions():
    g = load_grammar()
    assert set(g["tiers"]) == {"COMMON", "UNCOMMON", "RARE", "GLORIOUS"}
    assert {"draw", "look_take", "recover", "gain_letter", "scale_structure", "activate_sheol"} <= set(g["productions"]["CORE"])


def test_examples_classify_into_the_expected_productions():
    c = classify("Choose one Page belonging to another player. Add up to five cards from Sheol to your hand, one card of each card type in that chosen Page.")
    assert c["core"] == "scale_structure" and c["interact"] == "read_page"
    c = classify("Gain one Letter. Then discard three cards from your hand into Sheol.")
    assert c["core"] == "gain_letter" and c["cost"] == "discard_n"
    c = classify("Spend one Letter and choose up to three cards in Sheol. Add those chosen cards to your hand.")
    assert c["core"] == "recover" and c["cost"] == "spend_letter"
    c = classify("Look at the top three cards of the Tower. Add one of those cards to your hand and put the other cards on the bottom of the Tower.")
    assert c["core"] == "look_take" and c["kicker"] == "rest_bottom"
    c = classify("Reveal one card from the top of the Tower and put that revealed card into Sheol. If that revealed card is a VERB, gain one Letter.")
    assert c["core"] == "reveal_test" and c["condition"] == "revealed_is_type" and c["filter"] == "type"


def test_every_current_contract_ability_is_classified():
    rows = [r for r in load_series_abilities(ROOT / "series/2026-Q1") if int(r[0][:3]) >= 32]
    if not rows:
        import pytest
        pytest.skip("series not checked out")
    missing = [(label, text) for label, _, text in rows if classify(text)["unclassified"]]
    assert not missing, missing
