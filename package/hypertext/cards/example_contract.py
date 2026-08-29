"""Versioned, repository-authoritative input contract for Word examples."""
from __future__ import annotations

import json
import hashlib
from copy import deepcopy
from pathlib import Path

TYPES = ("noun", "verb", "adjective", "name", "title")


class ExampleContractError(ValueError):
    """The example input is not an exact projection of canonical card data."""


def load_contract(root: Path) -> dict:
    path = root / "schema/word_example_generation_contract.v2.json"
    contract = json.loads(path.read_text(encoding="utf-8"))
    if contract.get("contract_version") != 2:
        raise ExampleContractError("unsupported example contract version")
    if tuple(contract["variants"]) != TYPES:
        raise ExampleContractError("contract must define exactly the five Word types")
    if contract.get("rarities") != ["common", "uncommon", "rare", "glorious"]:
        raise ExampleContractError("contract rarity order must be common through glorious")
    if any(len(contract["variants"][kind]) != 3 for kind in TYPES):
        raise ExampleContractError("each Word type must have exactly three variants")
    slugs = [slug for kind in TYPES for slug in contract["variants"][kind]]
    if len(set(slugs)) != 15:
        raise ExampleContractError("the fifteen canonical variant sources must be unique")
    if set(contract.get("source_projection_sha256", {})) != set(slugs):
        raise ExampleContractError("every canonical variant must have one frozen projection digest")
    excluded = {item["card"] for item in contract.get("source_defects_excluded", [])}
    if excluded.intersection(slugs):
        raise ExampleContractError("a known-defective canonical source cannot seed an example")
    return contract


def _projection_digest(projected: dict) -> str:
    payload = json.dumps(
        projected, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def canonical_projection(root: Path, contract: dict, kind: str, variant: int) -> tuple[dict, str]:
    if kind not in TYPES or not isinstance(variant, int) or isinstance(variant, bool) or not 1 <= variant <= 3:
        raise ExampleContractError(f"invalid example variant {kind!r}/{variant!r}")
    slug = contract["variants"][kind][variant - 1]
    path = root / contract["canonical_series"] / "cards" / slug / "card.json"
    source = json.loads(path.read_text(encoding="utf-8"))["content"]
    if source["CARD_TYPE"].lower() != kind:
        raise ExampleContractError(f"{slug}: canonical CARD_TYPE is not {kind}")
    projected = {key: deepcopy(source[key]) for key in contract["authoritative_fields"]}
    digest = _projection_digest(projected)
    if digest != contract["source_projection_sha256"][slug]:
        raise ExampleContractError(
            f"{slug}: canonical projection changed; audit and version the input contract"
        )
    return projected, str(path.relative_to(root))


def validate_projection(root: Path, contract: dict, record: dict) -> None:
    if record.get("rarity") not in contract["rarities"]:
        raise ExampleContractError(f"card {record.get('id')}: invalid rarity")
    expected, source = canonical_projection(root, contract, record["type"], record["variant"])
    if record.get("canonical_source") != source:
        raise ExampleContractError(f"card {record.get('id')}: canonical source mismatch")
    actual = record.get("authoritative_content", {})
    if set(actual) != set(expected):
        raise ExampleContractError(
            f"card {record.get('id')}: authoritative field ownership mismatch"
        )
    for field, value in expected.items():
        if actual.get(field) != value:
            raise ExampleContractError(
                f"card {record.get('id')}: {field} diverges from {source}; "
                "approximate/decorative translation is forbidden"
            )
