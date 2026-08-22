"""Canonical Lot rules and presentation contract."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RULES_PATH = PROJECT_ROOT / "templates" / "phases.yml"
LOT_TEMPLATE_ROOT = PROJECT_ROOT / "templates" / "lot" / "v001"
POINTS = {5: 8, 6: 10, 7: 14}
OPPONENT_LETTERS = {5: 2, 6: 2, 7: 3}
IMAGE_MIME = "image/png"
IMAGE_DIMENSIONS = (1024, 1536)
SCHEMA_REVISION = "lot-rules-v1"

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

def load_lot_rules(path: Path = RULES_PATH) -> list[dict[str, Any]]:
    phases = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("phases", [])
    if len(phases) != 30 or {p.get("id") for p in phases} != set(range(1, 31)):
        raise ValueError("Lot schema must contain IDs 1 through 30 exactly once")
    if "CONGREGATION" not in {p.get("name") for p in phases}:
        raise ValueError("Lot schema is missing CONGREGATION")
    result = []
    for raw in phases:
        p = dict(raw); cards = p.get("cards")
        if p.get("points") != POINTS.get(cards):
            raise ValueError(f"{p.get('name')}: invalid points")
        if not isinstance(p.get("composition"), list) or len(p["composition"]) != cards:
            raise ValueError(f"{p.get('name')}: invalid composition")
        p.update(opponent_letters=OPPONENT_LETTERS[cards], card_count_label=card_count_label(cards),
                 composition_label=composition_label(p["composition"]), schema_revision=SCHEMA_REVISION)
        result.append(p)
    return result

def validate_phase(phase: dict[str, Any]) -> dict[str, Any]:
    canonical = {p["id"]: p for p in load_lot_rules()}[phase["id"]]
    for key in ("name", "cards", "points", "composition"):
        if phase.get(key) != canonical[key]:
            raise ValueError(f"Lot {phase['id']} {key} conflicts with canonical schema")
    return canonical
