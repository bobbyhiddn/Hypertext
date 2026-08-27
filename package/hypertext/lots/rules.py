"""Canonical Lot rules and presentation contract."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RULES_PATH = PROJECT_ROOT / "templates" / "phases.yml"
LOT_TEMPLATE_ROOT = PROJECT_ROOT / "templates" / "lot" / "v002"
# Babel Alpha Lot values by Lot size (see docs/rules.md, "Lot values by size").
CHAPTER_VALUE = {5: 8, 6: 10, 7: 14}     # points a Page scores; Pages are created by Recording the Chapter Lot
OWNER_LETTERS = {5: 2, 6: 2, 7: 3}       # Letters for Recording your own Portion Lot (no Page created)
VISITOR_LETTERS = {5: 1, 6: 1, 7: 2}     # Letters for Recording another player's Portion Lot (no Page created)
# Legacy aliases. v002 faces print "CHAPTER VALUE: n POINTS" and
# "PORTION VALUE: visitor/owner LETTERS"; archived v001 faces printed OWNER_LETTERS as "PAGE VALUE".
POINTS = CHAPTER_VALUE
OPPONENT_LETTERS = OWNER_LETTERS
IMAGE_MIME = "image/png"
IMAGE_DIMENSIONS = (1024, 1536)
SCHEMA_REVISION = "lot-rules-v2"

def card_count_label(cards: int) -> str:
    if cards not in POINTS:
        raise ValueError(f"unsupported Lot size: {cards}")
    return f"{cards}-CARD"

def composition_label(composition: list[str]) -> str:
    return " + ".join(str(x).replace("[", "").replace("]", "") for x in composition)

def subtype_reference(cards: int) -> Path:
    path = LOT_TEMPLATE_ROOT / f"{cards}-card" / "template_1024x1536.png"
    if cards not in POINTS or not path.is_file():
        raise ValueError(f"missing versioned face template for {cards}-card Lot: {path}")
    return path

def reference_manifest(cards: int) -> dict[str, Any]:
    """Describe the curated reference by content, never by its legacy suffix."""
    from PIL import Image
    path = subtype_reference(cards)
    with Image.open(path) as image:
        image.load()
        mime = Image.MIME.get(image.format)
        width, height = image.size
    return {"role": "face", "subtype": f"{cards}-card", "path": str(path),
            "mime_type": mime, "width": width, "height": height,
            "legacy_suffix": path.suffix, "immutable": True}

CARD_TYPES = ("NOUN", "VERB", "ADJECTIVE", "NAME", "TITLE")
GROUP_CONSTRAINTS = ("same_type", "one_type", "another_type", "any")
_ALL5PAIR_COMPOSITION = ["NOUN", "VERB", "ADJECTIVE", "NAME", "TITLE", "PAIR", "PAIR"]


def _derive(recipe: dict[str, Any], cards: int, name: str) -> tuple[list[str], str]:
    """Return the compatibility (composition, composition_label) pair for a typed recipe."""
    kind = recipe.get("kind")
    if kind == "fixed":
        composition = list(recipe.get("composition") or [])
        if len(composition) != cards or any(t not in CARD_TYPES for t in composition):
            raise ValueError(f"{name}: invalid fixed composition")
        return composition, composition_label(composition)
    if kind == "groups":
        groups = recipe.get("groups") or []
        if sum(g.get("count", 0) for g in groups) != cards:
            raise ValueError(f"{name}: group counts must sum to {cards}")
        composition, captions = [], []
        for g in groups:
            constraint = g.get("constraint")
            if constraint not in GROUP_CONSTRAINTS:
                raise ValueError(f"{name}: invalid group constraint {constraint!r}")
            if not g.get("caption"):
                raise ValueError(f"{name}: group caption is required")
            composition.extend([constraint.upper()] * g["count"])
            captions.append(g["caption"])
        return composition, " + ".join(captions)
    if kind == "all_types_plus_pair":
        if cards != 7:
            raise ValueError(f"{name}: all_types_plus_pair is a 7-card recipe")
        return list(_ALL5PAIR_COMPOSITION), "ALL 5 TYPES + PAIR"
    raise ValueError(f"{name}: unknown recipe kind {kind!r}")


def load_lot_rules(path: Path = RULES_PATH) -> list[dict[str, Any]]:
    phases = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("phases", [])
    if len(phases) != 30 or {p.get("id") for p in phases} != set(range(1, 31)):
        raise ValueError("Lot schema must contain IDs 1 through 30 exactly once")
    if "CONGREGATION" not in {p.get("name") for p in phases}:
        raise ValueError("Lot schema is missing CONGREGATION")
    result = []
    for raw in phases:
        p = dict(raw); cards = p.get("cards")
        if cards not in CHAPTER_VALUE:
            raise ValueError(f"{p.get('name')}: unsupported Lot size {cards!r}")
        recipe = p.get("recipe")
        if not isinstance(recipe, dict):
            raise ValueError(f"{p.get('name')}: missing typed recipe")
        composition, label = _derive(recipe, cards, str(p.get("name")))
        if not p.get("display"):
            raise ValueError(f"{p.get('name')}: missing display")
        p.update(points=CHAPTER_VALUE[cards], composition=composition,
                 opponent_letters=OWNER_LETTERS[cards], chapter_value=CHAPTER_VALUE[cards],
                 owner_letters=OWNER_LETTERS[cards], visitor_letters=VISITOR_LETTERS[cards],
                 card_count_label=card_count_label(cards),
                 composition_label=label, schema_revision=SCHEMA_REVISION)
        result.append(p)
    return result

def validate_phase(phase: dict[str, Any]) -> dict[str, Any]:
    canonical = {p["id"]: p for p in load_lot_rules()}[phase["id"]]
    for key in ("name", "cards", "points", "composition"):
        if phase.get(key) != canonical[key]:
            raise ValueError(f"Lot {phase['id']} {key} conflicts with canonical schema")
    return canonical
