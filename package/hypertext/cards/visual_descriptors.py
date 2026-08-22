"""Deterministic serialization of the machine-readable Hypertext visual grammar."""
from __future__ import annotations
import json
from copy import deepcopy
from itertools import product
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
DESCRIPTORS_PATH = ROOT / "schema" / "hypertext_visual_descriptors.json"
SCHEMA_PATH = ROOT / "schema" / "visual_descriptor.schema.json"
TYPE_VALUES = ("NOUN", "VERB", "ADJECTIVE", "NAME", "TITLE")
RARITY_VALUES = ("COMMON", "UNCOMMON", "RARE", "GLORIOUS")
COMPOSITION_VALUES = ("EXPLICIT", "PATTERN")
CONTENT_FIELDS = ("NUMBER", "CARD_TYPE", "RARITY_TEXT", "RARITY_ICON", "WORD", "GLOSS", "ART_PROMPT",
    "STAT_LORE", "STAT_CONTEXT", "STAT_COMPLEXITY", "ABILITY_TEXT", "OT_VERSE_LINE",
    "NT_VERSE_LINE", "HEBREW", "HEBREW_TRANSLIT", "OT_REFS", "GREEK",
    "GREEK_TRANSLIT", "NT_REFS", "TRIVIA_BULLETS", "SERIES")
TEXT_FIELDS = set(CONTENT_FIELDS) - {"NUMBER", "STAT_LORE", "STAT_CONTEXT",
                                    "STAT_COMPLEXITY", "TRIVIA_BULLETS"}

class DescriptorError(ValueError):
    """A descriptor or composition violates the visual grammar."""

def validate_descriptors(descriptor: dict) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(descriptor), key=lambda e: list(e.path))
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.path) or "root"
        raise DescriptorError(f"invalid visual descriptor at {location}: {error.message}")
    for family in ("WORD_CARD", "LOT"):
        if descriptor["structures"][family]["kind"] != family:
            raise DescriptorError(f"structure {family} kind must be {family}")
    if any(v["scope"] != "type_only" for v in descriptor["types"].values()):
        raise DescriptorError("type descriptors must have type_only scope")
    if any(v["scope"] != "rarity_only" for v in descriptor["rarities"].values()):
        raise DescriptorError("rarity descriptors must have rarity_only scope")

def load_descriptors(path: Path = DESCRIPTORS_PATH) -> dict:
    descriptor = json.loads(path.read_text(encoding="utf-8"))
    validate_descriptors(descriptor)
    return descriptor

def logical_word_card_descriptors(descriptor: dict | None = None) -> list[dict]:
    descriptor = descriptor or load_descriptors()
    validate_descriptors(descriptor)
    return [{"global": descriptor["HYPERTEXT_GLOBAL"],
             "structure": descriptor["structures"]["WORD_CARD"],
             "type": {"name": card_type, **descriptor["types"][card_type]},
             "rarity": {"name": rarity, **descriptor["rarities"][rarity]},
             "size": descriptor["HYPERTEXT_GLOBAL"]["canvas"]}
            for card_type, rarity in product(TYPE_VALUES, RARITY_VALUES)]

def _validate_request(card_type: str, rarity: str, mode: str, content: dict) -> None:
    if card_type not in TYPE_VALUES:
        raise DescriptorError(f"invalid TYPE {card_type!r}; expected one of {TYPE_VALUES}")
    if rarity not in RARITY_VALUES:
        raise DescriptorError(f"invalid RARITY {rarity!r}; expected one of {RARITY_VALUES}")
    if mode not in COMPOSITION_VALUES:
        raise DescriptorError(f"invalid composition {mode!r}; expected one of {COMPOSITION_VALUES}")
    missing, unexpected = set(CONTENT_FIELDS) - set(content), set(content) - set(CONTENT_FIELDS)
    if missing:
        raise DescriptorError("missing exact-content fields: " + ", ".join(sorted(missing)))
    if unexpected:
        raise DescriptorError("unexpected exact-content fields: " + ", ".join(sorted(unexpected)))
    if (content["CARD_TYPE"] != card_type or content["RARITY_TEXT"] != rarity
            or content["RARITY_ICON"] != rarity):
        raise DescriptorError("content CARD_TYPE and canonical RARITY_TEXT/RARITY_ICON must match isolated treatments")
    for key in TEXT_FIELDS:
        if not isinstance(content[key], str):
            raise DescriptorError(f"content field {key} must be a string")
    if not isinstance(content["NUMBER"], (str, int)) or isinstance(content["NUMBER"], bool):
        raise DescriptorError("content field NUMBER must be a string or integer")
    for key in ("STAT_LORE", "STAT_CONTEXT", "STAT_COMPLEXITY"):
        if not isinstance(content[key], int) or isinstance(content[key], bool) or not 0 <= content[key] <= 5:
            raise DescriptorError(f"content field {key} must be an integer from 0 through 5")
    trivia = content["TRIVIA_BULLETS"]
    if not isinstance(trivia, list) or not trivia or not all(isinstance(x, str) for x in trivia):
        raise DescriptorError("TRIVIA_BULLETS must be a non-empty array of canonical strings")

def canonical_prompt_content(content: dict) -> dict:
    """Copy the repository's canonical render fields and validate its rarity pair."""
    data = {key: deepcopy(content[key]) for key in CONTENT_FIELDS if key in content}
    if "RARITY_TEXT" in data or "RARITY_ICON" in data:
        text = data.get("RARITY_TEXT")
        icon = data.get("RARITY_ICON")
        if not isinstance(text, str) or not isinstance(icon, str):
            raise DescriptorError("RARITY_TEXT and RARITY_ICON must both be strings")
        text, icon = text.upper(), icon.upper()
        if text != icon or text not in RARITY_VALUES:
            raise DescriptorError("canonical RARITY_TEXT and RARITY_ICON must match a declared rarity")
        data["RARITY_TEXT"] = data["RARITY_ICON"] = text
    return data

def serialize_lot_prompt(*, content: dict, mode: str = "EXPLICIT",
                         descriptor: dict | None = None) -> str:
    """Serialize inherited global/LOT/size constraints ahead of exact Lot content."""
    descriptor = descriptor or load_descriptors()
    validate_descriptors(descriptor)
    if mode not in COMPOSITION_VALUES:
        raise DescriptorError(f"invalid composition {mode!r}; expected one of {COMPOSITION_VALUES}")
    cards = content.get("cards")
    size_name = f"LOT_{cards}"
    if size_name not in descriptor["sizes"]:
        raise DescriptorError(f"invalid Lot size {cards!r}; expected 5, 6, or 7")
    size = descriptor["sizes"][size_name]
    from hypertext.lots.rules import load_lot_rules
    canonical_phases = {phase["id"]: phase for phase in load_lot_rules()}
    phase_id = content.get("id")
    if phase_id not in size["phase_ids"]:
        raise DescriptorError(f"Lot {phase_id!r} is not mapped to {size_name}")
    canonical = canonical_phases[phase_id]
    if (content.get("points") != size["chapter_points"]
            or content.get("opponent_letters") != size["page_letters"]):
        raise DescriptorError("Lot reward values must match the selected Lot size")
    for key in ("name", "cards", "points", "composition", "display"):
        if content.get(key) != canonical[key]:
            raise DescriptorError(f"Lot {phase_id} {key} conflicts with canonical phase data")
    if content.get("constraint") != canonical.get("constraint"):
        raise DescriptorError(f"Lot {phase_id} constraint conflicts with canonical phase data")
    dump = lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    rule = ("materialize GLOBAL, LOT, and selected SIZE in full" if mode == "EXPLICIT" else
            "inherit GLOBAL -> LOT -> selected SIZE; serialized values below are authoritative")
    return "\n".join((
        "HYPERTEXT VISUAL DESCRIPTOR v1", f"COMPOSITION={mode}: {rule}.",
        f"INHERITANCE=HYPERTEXT_GLOBAL -> structures.LOT -> sizes.{size_name}",
        "GLOBAL=" + dump(descriptor["HYPERTEXT_GLOBAL"]),
        "STRUCTURE=" + dump(descriptor["structures"]["LOT"]), "SIZE=" + dump(size),
        "CONTENT_ORDER=" + dump(descriptor["structures"]["LOT"]["content_order"]),
        "EXACT_CANONICAL_CONTENT_JSON=" + dump(content),
        "Copy every JSON value exactly; do not translate, normalize, paraphrase, add, omit, or correct text.",
        "NEGATIVE GRAMMAR: " + "; ".join(descriptor["HYPERTEXT_GLOBAL"]["negative"]) + ".",
        "The Lot Reward descriptor is intentionally bounded at the supplied word 'trim'; infer no missing tail.",
        "Output only one vertical 1024x1536 Lot Card.",
    ))

def serialize_word_card_prompt(*, card_type: str, rarity: str, content: dict,
                               mode: str = "EXPLICIT", descriptor: dict | None = None) -> str:
    descriptor = descriptor or load_descriptors()
    structure = descriptor["structures"]["WORD_CARD"]
    if structure["geometry"]["original_language_split"] != {
            "left": "OLD_TESTAMENT_HEBREW_ARAMAIC", "right": "NEW_TESTAMENT_GREEK"}:
        raise DescriptorError("original-language sides may not be swapped")
    validate_descriptors(descriptor)
    _validate_request(card_type, rarity, mode, content)
    global_descriptor = descriptor["HYPERTEXT_GLOBAL"]
    dump = lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    rule = ("materialize GLOBAL, WORD_CARD, selected TYPE, and selected RARITY in full"
            if mode == "EXPLICIT" else
            "inherit GLOBAL -> WORD_CARD -> selected TYPE + selected RARITY; serialized values below are authoritative")
    return "\n".join((
        "HYPERTEXT VISUAL DESCRIPTOR v1", f"COMPOSITION={mode}: {rule}.",
        f"INHERITANCE=HYPERTEXT_GLOBAL -> structures.WORD_CARD -> types.{card_type} + rarities.{rarity}",
        "GLOBAL=" + dump(global_descriptor), "STRUCTURE=" + dump(structure),
        "TYPE=" + dump({"name": card_type, **descriptor["types"][card_type]}),
        "RARITY=" + dump({"name": rarity, **descriptor["rarities"][rarity]}),
        "CONTENT_ORDER=" + dump(structure["content_order"]),
        "ORIGINAL LANGUAGE PLACEMENT: LEFT is Old Testament HEB/ARAM with HEBREW, HEBREW_TRANSLIT, OT_REFS. RIGHT is New Testament GREEK with GREEK, GREEK_TRANSLIT, NT_REFS.",
        "REPEAT PLACEMENT: never swap languages; Old Testament is LEFT; New Testament is RIGHT.",
        "EXACT_CANONICAL_CONTENT_JSON=" + dump(content),
        "Copy every JSON value exactly; do not translate, normalize, paraphrase, add, omit, or correct text.",
        "NEGATIVE GRAMMAR: " + "; ".join(global_descriptor["negative"]) + ".",
        "Output only one vertical 1024x1536 Word Card.",
    ))
