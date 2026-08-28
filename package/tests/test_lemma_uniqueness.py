"""One lemma, one card: derivatives and shared lemmas are rejected."""
from hypertext.cards.lemma_uniqueness import english_stem, greek_key, hebrew_key, hebrew_root_key, lemma_conflicts


def _card(word, hebrew, translit, greek, card_type="NOUN"):
    return {"WORD": word, "CARD_TYPE": card_type, "HEBREW": hebrew, "HEBREW_TRANSLIT": translit, "GREEK": greek}


CHOOSE = _card("CHOOSE", "בָּחַר", "bachar", "ἐκλέγομαι")
CHOSEN = _card("CHOSEN", "בָּחִיר", "bachir", "ἐκλεκτός")
CONFUSE = _card("CONFUSE", "בָּלַל", "balal", "συγχέω")
BABBLE = _card("BABBLE", "בָּלַל", "balal", "συγχέω")
STONE = _card("STONE", "אֶבֶן", "eben", "λίθος")
BRICK = _card("BRICK", "לְבֵנָה", "levenah", "λίθος")
FIRE = _card("FIRE", "אֵשׁ", "esh", "πῦρ")
FAITHFUL = _card("FAITHFUL", "נֶאֱמָן", "neeman", "πιστός")


def test_keys_normalise_points_accents_and_final_sigma():
    assert hebrew_key("בָּחַר") == "בחר"
    assert greek_key("ἐκλέγομαι") == "εκλεγομαι"
    assert greek_key("λίθος") == greek_key("λιθοσ")
    assert hebrew_root_key("bachar") == hebrew_root_key("bachir") == "bCr"
    assert english_stem("CHOSEN") == english_stem("CHOOSE")
    assert english_stem("GATHERING") == english_stem("GATHER")


def test_derivative_of_an_existing_word_is_a_conflict():
    kinds = {c["kind"] for c in lemma_conflicts(CHOSEN, [("043-choose", CHOOSE)])}
    assert {"same-hebrew-root", "english-derivative"} <= kinds


def test_identical_lemmas_are_a_conflict():
    kinds = {c["kind"] for c in lemma_conflicts(BABBLE, [("006-confuse", CONFUSE)])}
    assert {"same-hebrew-lemma", "same-greek-lemma"} <= kinds


def test_shared_greek_lemma_alone_is_a_conflict():
    kinds = {c["kind"] for c in lemma_conflicts(BRICK, [("008-stone", STONE)])}
    assert kinds == {"same-greek-lemma"}


def test_distinct_lemmas_pass():
    assert lemma_conflicts(FAITHFUL, [("043-choose", CHOOSE), ("061-fire", FIRE), ("008-stone", STONE)]) == []


def test_a_card_never_conflicts_with_itself():
    assert lemma_conflicts(FIRE, [("061-fire", FIRE)]) == []


def test_a_proper_name_spelled_like_a_noun_is_a_homograph_not_a_derivative():
    name = _card("NAME", "שֵׁם", "shem", "ὄνομα")
    shem = _card("SHEM", "שֵׁם", "Shem", "Σήμ", card_type="NAME")
    assert lemma_conflicts(shem, [("010-name", name)]) == []
