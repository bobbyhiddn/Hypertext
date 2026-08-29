from hypertext.cards.word_weight import check_word_weight, rarity_floor


def test_floors():
    assert rarity_floor(5) == "GLORIOUS" and rarity_floor(4) == "RARE" and rarity_floor(3) == "COMMON"


def test_heavy_word_below_its_floor_is_rejected():
    issues = check_word_weight(4, "UNCOMMON", "the destroyer of Exodus 12")
    assert issues and "at least RARE" in issues[0]


def test_heavy_word_at_or_above_its_floor_passes():
    assert check_word_weight(4, "RARE", "Sodom") == []
    assert check_word_weight(4, "GLORIOUS", "Sodom") == []
    assert check_word_weight(2, "COMMON", "a plain word") == []


def test_weight_needs_a_rationale_and_a_range():
    assert check_word_weight(3, "COMMON", "") == ["weight_rationale is required: say why the word carries this weight"]
    assert check_word_weight(6, "COMMON", "x") == ["weight=6 is outside 1-5"]
    assert check_word_weight(None, "COMMON", "x") == ["weight is missing or not an integer (1-5)"]
