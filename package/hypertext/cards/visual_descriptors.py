"""Machine-readable Hypertext visual grammar and deterministic prompt serialization."""
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

CONTENT_FIELDS = (
    "NUMBER", "CARD_TYPE", "RARITY", "WORD", "GLOSS", "ART_PROMPT",
    "STAT_LORE", "STAT_CONTEXT", "STAT_COMPLEXITY", "ABILITY_TEXT",
    "OT_VERSE_LINE", "NT_VERSE_LINE", "HEBREW", "HEBREW_TRANSLIT",
    "OT_REFS", "GREEK", "GREEK_TRANSLIT", "NT_REFS", "TRIVIA_BULLETS", "SERIES",
)


class DescriptorError(ValueError):
    """The descriptor or requested composition violates the visual grammar."""


def load_descriptors(path: Path = DESCRIPTORS_PATH) -> dict:
    descriptor = json.loads(path.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(descriptor), key=lambda e: list(e.path))
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.path) or "root"
        raise DescriptorError(f"invalid visual descriptor at {location}: {error.message}")
    return descriptor


def logical_word_card_descriptors(descriptor: dict | None = None) -> list[dict]:
    """Inherit one structure + one type + one rarity into the 5x4 logical matrix."""
    descriptor = descriptor or load_descriptors()
    result = []
    for card_type, rarity in product(TYPE_VALUES, RARITY_VALUES):
        result.append({
            "global": descriptor["HYPERTEXT_GLOBAL"],
            "structure": descriptor["structures"]["WORD_CARD"],
            "type": {"name": card_type, **descriptor["types"][card_type]},
            "rarity": {"name": rarity, **descriptor["rarities"][rarity]},
            "size": descriptor["HYPERTEXT_GLOBAL"]["canvas"],
        })
    return result


def _validate_request(card_type: str, rarity: str, mode: str, content: dict) -> None:
    if card_type not in TYPE_VALUES:
        raise DescriptorError(f"invalid TYPE {card_type!r}; expected one of {TYPE_VALUES}")
    if rarity not in RARITY_VALUES:
        raise DescriptorError(f"invalid RARITY {rarity!r}; expected one of {RARITY_VALUES}")
    if mode not in COMPOSITION_VALUES:
        raise DescriptorError(f"invalid composition {mode!r}; expected one of {COMPOSITION_VALUES}")
    missing = [key for key in CONTENT_FIELDS if key not in content]
    if missing:
        raise DescriptorError(f"missing exact-content fields: {', '.join(missing)}")
    if content["CARD_TYPE"] != card_type or content["RARITY"] != rarity:
        raise DescriptorError("content TYPE/RARITY must match the isolated descriptor treatments")
    for key in CONTENT_FIELDS:
        if not isinstance(content[key], (str, int, list)):
            raise DescriptorError(f"content field {key} must be exact serializable text")
    if not isinstance(content["TRIVIA_BULLETS"], list) or len(content["TRIVIA_BULLETS"]) != 3:
        raise DescriptorError("TRIVIA_BULLETS must contain exactly three canonical strings")


def serialize_word_card_prompt(*, card_type: str, rarity: str, content: dict,
                               mode: str = "EXPLICIT", descriptor: dict | None = None) -> str:
    """Serialize a stable prompt; content is JSON-quoted to preserve exact Unicode text."""
    descriptor = descriptor or load_descriptors()
    _validate_request(card_type, rarity, mode, content)
    structure = descriptor["structures"]["WORD_CARD"]
    split = structure["geometry"]["original_language_split"]
    if split != {"left": "OLD_TESTAMENT_HEBREW_ARAMAIC", "right": "NEW_TESTAMENT_GREEK"}:
        raise DescriptorError("original-language sides may not be swapped")

    exact = json.dumps({key: deepcopy(content[key]) for key in CONTENT_FIELDS}, ensure_ascii=False,
                       separators=(",", ":"))
    negatives = "; ".join(descriptor["HYPERTEXT_GLOBAL"]["negative"])
    pattern = "inherit GLOBAL + WORD_CARD + TYPE + RARITY" if mode == "PATTERN" else "apply every declared field explicitly"
    return "\n".join((
        "HYPERTEXT VISUAL DESCRIPTOR v1",
        f"COMPOSITION={mode}: {pattern}.",
        "CANVAS=1024x1536 (2:3). Output only one vertical Word Card.",
        descriptor["types"][card_type]["prompt"],
        descriptor["rarities"][rarity]["prompt"],
        "INVARIANT GEOMETRY=" + json.dumps(structure["geometry"], ensure_ascii=False, sort_keys=True),
        "ORIGINAL LANGUAGE PLACEMENT: LEFT is Old Testament HEB/ARAM with HEBREW, HEBREW_TRANSLIT, OT_REFS. RIGHT is New Testament GREEK with GREEK, GREEK_TRANSLIT, NT_REFS.",
        "REPEAT PLACEMENT: never swap languages; Old Testament is LEFT; New Testament is RIGHT.",
        "EXACT_CANONICAL_CONTENT_JSON=" + exact,
        "Copy every JSON string exactly; do not translate, normalize, paraphrase, add, omit, or correct text.",
        "NEGATIVE GRAMMAR: " + negatives + ".",
    ))
