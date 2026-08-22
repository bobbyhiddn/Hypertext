import copy
import json

import pytest
from jsonschema import ValidationError, validate

from hypertext.cards.visual_descriptors import (
    DescriptorError, SCHEMA_PATH, load_descriptors, logical_word_card_descriptors,
    serialize_word_card_prompt,
)
from hypertext.pipeline.daily import build_prompt_text


@pytest.fixture
def content():
    return {
        "NUMBER": 7, "CARD_TYPE": "NOUN", "RARITY_TEXT": "RARE", "WORD": "חֶסֶד — χάρις",
        "GLOSS": "steadfast love & grace", "ART_PROMPT": "A lamp beside an ancient scroll.",
        "STAT_LORE": 3, "STAT_CONTEXT": 4, "STAT_COMPLEXITY": 2,
        "ABILITY_TEXT": "Keep “this” exact; don't normalize it.",
        "OT_VERSE_LINE": "Psalm 136:1 — כִּי לְעוֹלָם חַסְדּוֹ",
        "NT_VERSE_LINE": "John 1:17 — ἡ χάρις καὶ ἡ ἀλήθεια",
        "HEBREW": "חֶסֶד", "HEBREW_TRANSLIT": "ḥesed", "OT_REFS": "Ps 136:1",
        "GREEK": "χάρις", "GREEK_TRANSLIT": "charis", "NT_REFS": "Jn 1:17",
        "TRIVIA_BULLETS": ["First—exact.", "Second: exact.", "Third & exact.", "Fourth."], "SERIES": "2026-Q1",
    }


def test_inheritance_produces_twenty_logical_cards_from_ten_authored_descriptors():
    descriptor = load_descriptors()
    logical = logical_word_card_descriptors(descriptor)
    assert len(logical) == 20
    assert len(descriptor["structures"]) == 2
    assert len(descriptor["types"]) == 5
    assert len(descriptor["rarities"]) == 4
    assert len({(item["type"]["name"], item["rarity"]["name"]) for item in logical}) == 20


@pytest.mark.parametrize("card_type,rarity,mode", [("OTHER", "RARE", "EXPLICIT"), ("NOUN", "MYTHIC", "PATTERN"), ("NOUN", "RARE", "IMPLICIT")])
def test_invalid_enums_are_rejected(content, card_type, rarity, mode):
    content.update(CARD_TYPE=card_type, RARITY_TEXT=rarity)
    with pytest.raises(DescriptorError, match="invalid"):
        serialize_word_card_prompt(card_type=card_type, rarity=rarity, mode=mode, content=content)


def test_schema_rejects_unknown_type_enum():
    descriptor = load_descriptors()
    descriptor["types"]["OTHER"] = descriptor["types"]["NOUN"]
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    with pytest.raises(ValidationError):
        validate(descriptor, schema)


def test_language_swap_is_rejected(content):
    descriptor = copy.deepcopy(load_descriptors())
    split = descriptor["structures"]["WORD_CARD"]["geometry"]["original_language_split"]
    split["left"], split["right"] = split["right"], split["left"]
    with pytest.raises(DescriptorError, match="may not be swapped"):
        serialize_word_card_prompt(card_type="NOUN", rarity="RARE", content=content, descriptor=descriptor)


@pytest.mark.parametrize("mode", ["EXPLICIT", "PATTERN"])
def test_prompt_preserves_exact_canonical_unicode_and_redundant_language_sides(content, mode):
    prompt = serialize_word_card_prompt(card_type="NOUN", rarity="RARE", content=content, mode=mode)
    payload = prompt.split("EXACT_CANONICAL_CONTENT_JSON=", 1)[1].split("\n", 1)[0]
    assert json.loads(payload) == content
    assert "Old Testament is LEFT; New Testament is RIGHT" in prompt
    assert "LEFT is Old Testament HEB/ARAM" in prompt
    assert "RIGHT is New Testament GREEK" in prompt


def test_generated_watermark_is_always_forbidden(content):
    for card_type in ("NOUN", "VERB", "ADJECTIVE", "NAME", "TITLE"):
        for rarity in ("COMMON", "UNCOMMON", "RARE", "GLORIOUS"):
            item = dict(content, CARD_TYPE=card_type, RARITY_TEXT=rarity)
            prompt = serialize_word_card_prompt(card_type=card_type, rarity=rarity, content=item)
            assert "no generated watermark" in prompt
            assert "add watermark" not in prompt


def test_type_and_rarity_treatments_are_isolated(content):
    descriptor = load_descriptors()
    assert {value["scope"] for value in descriptor["types"].values()} == {"type_only"}
    assert {value["scope"] for value in descriptor["rarities"].values()} == {"rarity_only"}
    prompt = serialize_word_card_prompt(card_type="NOUN", rarity="RARE", content=content)
    assert descriptor["types"]["NOUN"]["prompt"] in prompt
    assert descriptor["rarities"]["RARE"]["prompt"] in prompt


def test_lot_reward_boundary_is_machine_readable_and_does_not_invent_fields():
    lot = load_descriptors()["structures"]["LOT"]
    assert lot["content_order"] == ["TITLE", "ART", "REWARD"]
    assert "ended after 'trim'" in lot["spec_boundary"]
    assert set(lot["geometry"]) == {"orientation", "frame"}


@pytest.mark.parametrize("mode", ["EXPLICIT", "PATTERN"])
def test_real_generation_path_serializes_real_canonical_card(mode):
    root = SCHEMA_PATH.parents[1]
    card = json.loads((root / "series/2026-Q1-dev/cards/006-redeem/card.json").read_text())
    card["visual_descriptor_mode"] = mode
    prompt = build_prompt_text(card)
    payload = json.loads(prompt.split("EXACT_CANONICAL_CONTENT_JSON=", 1)[1].split("\n", 1)[0])
    assert payload["RARITY_TEXT"] == card["content"]["RARITY_TEXT"]
    assert payload["TRIVIA_BULLETS"] == card["content"]["TRIVIA_BULLETS"]
    assert "GLOBAL=" in prompt and "STRUCTURE=" in prompt and "CONTENT_ORDER=" in prompt
    assert "closed book" not in prompt  # real card is VERB
    assert '"icon":"pencil"' in prompt
    assert "no generated watermark" in prompt


@pytest.mark.parametrize("mutation", [
    lambda d: d["structures"]["WORD_CARD"].update(kind="LOT"),
    lambda d: d["structures"]["LOT"].update(kind="WORD_CARD"),
    lambda d: d["types"]["NOUN"].update(scope="rarity_only"),
    lambda d: d["rarities"]["RARE"].update(scope="type_only"),
    lambda d: d["types"]["NOUN"].update(unexpected=True),
    lambda d: d["HYPERTEXT_GLOBAL"].update(unexpected=True),
    lambda d: d["structures"]["WORD_CARD"]["geometry"].update(unexpected=True),
    lambda d: d["sizes"]["LOT_5"].update(card_count="5"),
])
def test_schema_rejects_audited_inheritance_and_isolation_violations(mutation):
    descriptor = copy.deepcopy(load_descriptors())
    mutation(descriptor)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    with pytest.raises(ValidationError):
        validate(descriptor, schema)


@pytest.mark.parametrize("field,value", [
    ("STAT_LORE", "3"), ("STAT_CONTEXT", True), ("STAT_COMPLEXITY", 6),
    ("WORD", 7), ("TRIVIA_BULLETS", ["ok", 2]),
])
def test_canonical_content_rejects_wrong_value_types(content, field, value):
    content[field] = value
    with pytest.raises(DescriptorError):
        serialize_word_card_prompt(card_type="NOUN", rarity="RARE", content=content)


def test_canonical_content_rejects_unexpected_property(content):
    content["RARITY"] = content["RARITY_TEXT"]
    with pytest.raises(DescriptorError, match="unexpected"):
        serialize_word_card_prompt(card_type="NOUN", rarity="RARE", content=content)


def test_lot_sizes_have_distinct_canonical_compositions_and_values():
    sizes = load_descriptors()["sizes"]
    assert sizes["LOT_5"]["composition"] == ["NOUN", "NOUN", "VERB", "VERB", "ADJECTIVE"]
    assert sizes["LOT_6"]["composition"] == ["NOUN", "NOUN", "NOUN", "VERB", "VERB", "VERB"]
    assert sizes["LOT_7"]["composition"] == ["NOUN", "NOUN", "NOUN", "VERB", "VERB", "ADJECTIVE", "TITLE"]
    assert [(sizes[k]["chapter_points"], sizes[k]["page_letters"]) for k in sizes] == [(8, 2), (10, 2), (14, 3)]
