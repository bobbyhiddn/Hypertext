import copy
import json

import pytest
from jsonschema import ValidationError, validate

from hypertext.cards.visual_descriptors import (
    DescriptorError, SCHEMA_PATH, load_descriptors, logical_word_card_descriptors,
    canonical_prompt_content, serialize_word_card_prompt,
    serialize_lot_prompt,
)
from hypertext.pipeline.daily import build_prompt_text
from hypertext.lots.renderer import _build_lot_prompt
from hypertext.lots.rules import load_lot_rules
from hypertext.watermark.crypto import build_svg, canonical_payload, compute_signature_hex, load_card_identity


@pytest.fixture
def content():
    return {
        "NUMBER": 7, "CARD_TYPE": "NOUN", "RARITY_TEXT": "RARE", "RARITY_ICON": "RARE", "WORD": "חֶסֶד — χάρις",
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
    content.update(CARD_TYPE=card_type, RARITY_TEXT=rarity, RARITY_ICON=rarity)
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
    assert "LEFT header is exactly HEBREW/ARAMAIC" in prompt
    assert "RIGHT header is exactly GREEK" in prompt
    assert "bare italic HEBREW_TRANSLIT" in prompt
    assert "'OT Refs:' plus OT_REFS" in prompt
    assert "'NT Refs:' plus NT_REFS" in prompt


def test_printed_see_language_layout_is_machine_readable_and_compact():
    word = load_descriptors()["structures"]["WORD_CARD"]
    layout = word["original_language_layout"]
    assert word["geometry"]["art_panel_height_fraction"] == 0.16
    assert layout["left_header"] == "HEBREW/ARAMAIC"
    assert layout["right_header"] == "GREEK"
    assert layout["left_refs"].startswith("OT Refs:")
    assert layout["right_refs"].startswith("NT Refs:")
    assert "no TRANSLIT label" in layout["transliteration"]
    assert "compact" in layout["density"]


def test_babel_art_direction_avoids_people_faces_and_uses_known_symbols(content):
    word = load_descriptors()["structures"]["WORD_CARD"]
    assert "what they are known for" in word["art_direction"]["subject_rule"]
    assert "recognizable face" in word["art_direction"]["figure_rule"]
    for card_type in ("NOUN", "VERB", "ADJECTIVE", "NAME", "TITLE"):
        item = dict(content, CARD_TYPE=card_type)
        prompt = serialize_word_card_prompt(card_type=card_type, rarity="RARE", content=item)
        assert "no recognizable human faces" in prompt
        assert "no portrait likenesses" in prompt
        assert "Represent people through what they are known for" in prompt


def test_generated_watermark_is_always_forbidden(content):
    for card_type in ("NOUN", "VERB", "ADJECTIVE", "NAME", "TITLE"):
        for rarity in ("COMMON", "UNCOMMON", "RARE", "GLORIOUS"):
            item = dict(content, CARD_TYPE=card_type, RARITY_TEXT=rarity, RARITY_ICON=rarity)
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
    assert payload["RARITY_ICON"] == card["content"]["RARITY_ICON"]
    assert payload["TRIVIA_BULLETS"] == card["content"]["TRIVIA_BULLETS"]
    assert "GLOBAL=" in prompt and "STRUCTURE=" in prompt and "CONTENT_ORDER=" in prompt
    assert "closed book" not in prompt  # real card is VERB
    assert '"icon":"pencil"' in prompt
    assert "no generated watermark" in prompt


def test_real_generation_keeps_deterministic_watermark_as_post_processing(monkeypatch):
    root = SCHEMA_PATH.parents[1]
    card_dir = root / "series/2026-Q1-dev/cards/006-redeem"
    card = json.loads((card_dir / "card.json").read_text())
    prompt = build_prompt_text(card)
    assert "hypertext_sig" not in prompt and "<svg" not in prompt
    monkeypatch.setenv("HYPERTEXT_SIGNING_KEY", "descriptor-regression-key")
    payload = canonical_payload(load_card_identity(card_dir))
    first = build_svg(sig_hex=compute_signature_hex(payload), payload=payload)
    second = build_svg(sig_hex=compute_signature_hex(payload), payload=payload)
    assert first == second
    assert "hypertext_sig" in first


@pytest.mark.parametrize("mutation", [
    lambda d: d["structures"]["WORD_CARD"].update(kind="LOT"),
    lambda d: d["structures"]["LOT"].update(kind="WORD_CARD"),
    lambda d: d["types"]["NOUN"].update(scope="rarity_only"),
    lambda d: d["rarities"]["RARE"].update(scope="type_only"),
    lambda d: d["types"]["NOUN"].update(unexpected=True),
    lambda d: d["types"]["NOUN"].update(icon="pencil"),
    lambda d: d["rarities"]["COMMON"].update(diamond_fill="gold"),
    lambda d: d["rarities"]["RARE"].update(card_bonus=2),
    lambda d: d["HYPERTEXT_GLOBAL"].update(unexpected=True),
    lambda d: d["structures"]["WORD_CARD"]["geometry"].update(unexpected=True),
    lambda d: d["structures"]["WORD_CARD"]["geometry"].update(art_panel_height_fraction=0.44),
    lambda d: d["structures"]["WORD_CARD"]["original_language_layout"].update(left_header="HEB/ARAM"),
    lambda d: d["structures"]["WORD_CARD"]["art_direction"].update(unexpected=True),
    lambda d: d["sizes"]["LOT_5"].update(card_count="5"),
    lambda d: d["types"]["TITLE"].update(icon="crown"),
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


def test_repository_rarity_pair_is_normalized_but_mismatch_is_rejected(content):
    content.update(RARITY_TEXT="rare", RARITY_ICON="Rare")
    assert canonical_prompt_content(content)["RARITY_ICON"] == "RARE"
    content["RARITY_ICON"] = "COMMON"
    with pytest.raises(DescriptorError, match="must match"):
        canonical_prompt_content(content)


def test_lot_sizes_map_every_canonical_phase_exactly_once():
    sizes = load_descriptors()["sizes"]
    phases = load_lot_rules()
    mapped = [phase_id for size in sizes.values() for phase_id in size["phase_ids"]]
    assert mapped == [phase["id"] for phase in phases]
    assert len(mapped) == len(set(mapped)) == 30
    for name, size in sizes.items():
        assert all(next(p for p in phases if p["id"] == phase_id)["cards"] == size["card_count"]
                   for phase_id in size["phase_ids"]), name
    assert [(sizes[k]["chapter_points"], sizes[k]["page_letters"]) for k in sizes] == [(8, 2), (10, 2), (14, 3)]


@pytest.mark.parametrize("mode", ["EXPLICIT", "PATTERN"])
@pytest.mark.parametrize("phase_id", range(1, 31))
def test_real_lot_production_path_serializes_canonical_phase(mode, phase_id):
    phase = next(p for p in load_lot_rules() if p["id"] == phase_id)
    phase.update(flavor="canonical flavor", context="canonical context", series="2026-Q1",
                 verse="", visual_descriptor_mode=mode)
    prompt = _build_lot_prompt(phase)
    payload = json.loads(prompt.split("EXACT_CANONICAL_CONTENT_JSON=", 1)[1].split("\n", 1)[0])
    assert payload["composition"] == phase["composition"]
    assert payload["constraint"] == phase.get("constraint")
    assert f'COMPOSITION={mode}' in prompt
    assert "no generated watermark" in prompt


def test_lot_serializer_rejects_unmapped_or_noncanonical_composition():
    phase = next(p for p in load_lot_rules() if p["id"] == 2)
    content = {key: phase.get(key) for key in ("id", "name", "cards", "points", "display",
                                                "composition", "constraint")}
    content.update(opponent_letters=phase["opponent_letters"], flavor="f", context="c",
                   series="s", verse="")
    bad_id = dict(content, id=15)
    with pytest.raises(DescriptorError, match="not mapped"):
        serialize_lot_prompt(content=bad_id)
    bad_composition = dict(content, composition=["NOUN"] * 5)
    with pytest.raises(DescriptorError, match="composition conflicts"):
        serialize_lot_prompt(content=bad_composition)


def test_real_lot_production_path_rejects_phase_composition_drift():
    phase = next(p for p in load_lot_rules() if p["id"] == 2)
    phase.update(flavor="canonical flavor", context="canonical context", series="2026-Q1", verse="")
    phase["composition"] = ["NOUN"] * phase["cards"]
    with pytest.raises(ValueError, match="composition conflicts"):
        _build_lot_prompt(phase)


def test_real_word_generation_path_serializes_exact_title_treatment():
    root = SCHEMA_PATH.parents[1]
    card = json.loads((root / "series/2026-Q1-dev/cards/001-magi/card.json").read_text())
    assert card["content"]["CARD_TYPE"] == "TITLE"
    prompt = build_prompt_text(card)
    title = load_descriptors()["types"]["TITLE"]
    assert title == {
        "scope": "type_only",
        "icon": "ornate empty rectangular frame",
        "prompt": ("TYPE label is exactly TITLE; icon concept is an ornate empty rectangular frame; "
                   "style is a simple white silhouette."),
    }
    serialized = json.loads(prompt.split("TYPE=", 1)[1].split("\n", 1)[0])
    assert serialized == {"name": "TITLE", **title}
    assert "crown" not in prompt.lower()


def test_real_word_generation_path_rejects_title_crown(monkeypatch):
    root = SCHEMA_PATH.parents[1]
    card = json.loads((root / "series/2026-Q1-dev/cards/001-magi/card.json").read_text())
    descriptor = copy.deepcopy(load_descriptors())
    descriptor["types"]["TITLE"].update(icon="crown", prompt="TYPE is exactly TITLE; crown.")
    monkeypatch.setattr("hypertext.cards.visual_descriptors.load_descriptors", lambda: descriptor)
    with pytest.raises(DescriptorError, match="invalid visual descriptor"):
        build_prompt_text(card)
