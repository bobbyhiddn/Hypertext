"""Offline validation for the canonical Babel type-by-rarity template matrix."""
from __future__ import annotations

import json
import hashlib
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
MATRIX_PATH = ROOT / "schema" / "babel_template_matrix.json"
MANIFEST_PATH = ROOT / "templates" / "card" / "v001" / "composed" / "manifest.json"


def load_matrix(path: Path = MATRIX_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_template_manifest(path: Path = MANIFEST_PATH) -> dict:
    """Load the authoritative, audited face-template package."""
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_template(card_type: str, rarity: str, *, verify: bool = True) -> Path:
    """Resolve a supported type/rarity pair, rejecting anything outside the matrix."""
    key = (card_type.upper(), rarity.upper())
    entries = {(item["type"], item["rarity"]): item for item in load_template_manifest()["outputs"]}
    try:
        entry = entries[key]
    except KeyError as exc:
        raise ValueError(f"unsupported card template combination {key[0]}+{key[1]}") from exc
    path = ROOT / entry["path"]
    if verify:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != entry["sha256"]:
            raise ValueError(f"canonical card template failed integrity check: {entry['path']}")
    return path


def load_canonical_cards(matrix: dict | None = None) -> list[dict]:
    matrix = matrix or load_matrix()
    source = ROOT / matrix["canonical_card_source"]
    return yaml.safe_load(source.read_text(encoding="utf-8"))["cards"]


def validate_canonical_mappings(matrix: dict | None = None) -> list[str]:
    """Return durable errors when canonical data and supported mappings diverge."""
    matrix = matrix or load_matrix()
    cards = load_canonical_cards(matrix)
    supported = {
        (entry["type"], entry["rarity"]): entry["card_count"]
        for entry in matrix["valid_combinations"]
    }
    actual = Counter((card["type"], card["rarity"]) for card in cards)
    errors = []
    for card in cards:
        key = (card["type"], card["rarity"])
        if key not in supported:
            errors.append(
                f"canonical card {card['number']} {card['word']} lacks template mapping "
                f"{key[0]}+{key[1]}"
            )
    for key, count in sorted(supported.items()):
        if actual[key] != count:
            errors.append(
                f"matrix count {key[0]}+{key[1]}={count}, canonical data={actual[key]}"
            )
    unexpected = sorted(set(actual) - set(supported))
    for card_type, rarity in unexpected:
        errors.append(f"unsupported canonical combination {card_type}+{rarity}")
    return errors
