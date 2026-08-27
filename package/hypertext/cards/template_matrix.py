"""Offline validation for the canonical Babel type-by-rarity template matrix."""
from __future__ import annotations

import json
import hashlib
import re
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


def resolve_template_record(
    card_type: str,
    rarity: str,
    *,
    verify: bool = True,
    manifest_path: Path = MANIFEST_PATH,
    root: Path = ROOT,
) -> dict:
    """Resolve and verify the one canonical template record for a type/rarity pair.

    The composed manifest is the only runtime authority.  In particular, this
    function never falls back to the legacy base, type-only, rarity-only, or SEE
    faces when a matrix cell is absent or fails its digest check.
    """
    key = (card_type.upper(), rarity.upper())
    manifest = load_template_manifest(manifest_path)
    if manifest.get("status") != "operator-accepted-canonical":
        raise ValueError("card template manifest is not operator-accepted-canonical")
    outputs = manifest.get("outputs")
    if not isinstance(outputs, list):
        raise ValueError("card template manifest outputs must be a list")
    if not all(isinstance(item, dict) for item in outputs):
        raise ValueError("card template manifest outputs must contain objects")
    entries = {(item.get("type"), item.get("rarity")): item for item in outputs}
    if len(entries) != len(outputs):
        raise ValueError("card template manifest contains duplicate type/rarity cells")
    try:
        entry = dict(entries[key])
    except KeyError as exc:
        raise ValueError(f"unsupported card template combination {key[0]}+{key[1]}") from exc
    if (entry.get("visible_type_label"), entry.get("visible_rarity_label")) != key:
        raise ValueError(
            f"canonical card template labels do not match requested cell {key[0]}+{key[1]}"
        )
    relative_path = Path(entry["path"])
    if relative_path.is_absolute():
        raise ValueError("canonical card template path must be repository-relative")
    lowered_parts = {part.lower() for part in relative_path.parts}
    forbidden_state = any(
        marker in part
        for marker in ("legacy", "rejected", "superseded", "noncanonical")
        for part in lowered_parts
    )
    if forbidden_state or lowered_parts & {"see", "base"}:
        raise ValueError(f"canonical card template points at a forbidden fallback: {entry['path']}")
    path = root / relative_path
    expected_digest = str(entry.get("sha256", "")).lower()
    if not re.fullmatch(r"[0-9a-f]{64}", expected_digest):
        raise ValueError(f"canonical card template lacks a valid SHA-256: {entry['path']}")
    if verify:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected_digest:
            raise ValueError(f"canonical card template failed integrity check: {entry['path']}")
    version = next((part for part in relative_path.parts if re.fullmatch(r"v\d{3}", part)), None)
    entry.update({
        "path": path,
        "repo_path": relative_path.as_posix(),
        "sha256": expected_digest,
        "template_version": version,
        "template_commit": manifest.get("authority_commit") or manifest.get("promotion_base_commit"),
        "manifest_schema_version": manifest.get("schema_version"),
        "manifest_status": manifest.get("status"),
        "manifest_path": manifest_path,
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
    })
    return entry


def resolve_template(card_type: str, rarity: str, *, verify: bool = True) -> Path:
    """Resolve a supported type/rarity pair, rejecting anything outside the matrix."""
    return resolve_template_record(card_type, rarity, verify=verify)["path"]


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
