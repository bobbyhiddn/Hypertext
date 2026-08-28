#!/usr/bin/env python3
"""Verify the immutable 20-cell blank type-by-rarity template package."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_REL = PurePosixPath(
    "templates/card/v001/composed/persistence-manifest.json"
)
SOURCE_MANIFEST_REL = PurePosixPath(
    "templates/card/v001/composed/manifest.json"
)
PACKAGE_ROOT = PurePosixPath("templates/card/v001/composed")
PACKAGE_PARTS = PACKAGE_ROOT.parts
TEMPLATE_FILENAME = "template_1024x1536.png"
TYPE_ORDER = ("NOUN", "VERB", "ADJECTIVE", "NAME", "TITLE")
RARITY_ORDER = ("COMMON", "UNCOMMON", "RARE", "GLORIOUS")
EXPECTED_PAIRS = {
    (card_type, rarity)
    for card_type in TYPE_ORDER
    for rarity in RARITY_ORDER
}
EXPECTED_DIMENSIONS = (848, 1264)
EXPECTED_SOURCE_MANIFEST_SHA256 = (
    "bb0f6beabbff74f76789cfa73a81ce03"
    "2f80b5cbfb36af907857497e2bf368d3"
)
EXPECTED_PACKAGING_HEAD = "ee071060c4ff075f081de53af73d7d2dccd0b9b4"
EXPECTED_CORRECTING_COMMIT = "ae62d3b39808aab8b1cd71761d85295488b52c46"
EXPECTED_AUTHORITY_COMMIT = "e50961ad0f4d66f398f81706f092a7d0ea9cb0f4"
EXPECTED_PROVENANCE_COMPOSITE = (
    "50ec1ee1601d5b58e1249e529f65e5b7"
    "04b238c6570a6f6fb886269dddbf7853"
)
ASSET_SET_ALGORITHM = (
    "SHA-256 of UTF-8 lines TYPE<TAB>RARITY<TAB>PATH<TAB>SHA256"
    "<TAB>WIDTHxHEIGHT<LF>, ordered by type_order then rarity_order"
)
DELIVERY_COMPOSITE_ALGORITHM = (
    "SHA-256 of concatenated lowercase SHA-256 hex digests of raw delivered "
    "file bytes, with file paths sorted lexicographically"
)
SHA256_RE = re.compile(r"[0-9a-f]{64}")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _error(errors: list[str], message: str) -> None:
    errors.append(message)


def _expected_path(card_type: str, rarity: str) -> str:
    return (
        PACKAGE_ROOT
        / card_type.lower()
        / rarity.lower()
        / TEMPLATE_FILENAME
    ).as_posix()


def _safe_relative_path(value: Any) -> PurePosixPath | None:
    if not isinstance(value, str) or not value or "\\" in value:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value:
        return None
    if any(part in {"", ".", ".."} for part in path.parts):
        return None
    return path


def _substitution_kind(path: PurePosixPath) -> str | None:
    parts = path.parts
    if (
        parts[:1] == ("series",)
        or "historical_faces" in parts
        or path.name.startswith("card_")
    ):
        return "finished-card substitution"
    if parts[:1] == ("operator_review",):
        return "review-only asset substitution"
    if parts[:2] == ("templates", "card") and parts[:4] != PACKAGE_PARTS:
        return "legacy fallback"
    if parts[:4] != PACKAGE_PARTS:
        return "path outside stable template package"
    return None


def _read_png(path: Path) -> tuple[str, tuple[int, int], str, str]:
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if len(data) < 33 or data[:8] != PNG_SIGNATURE:
        raise ValueError("not a PNG")
    ihdr_length = struct.unpack(">I", data[8:12])[0]
    if ihdr_length != 13 or data[12:16] != b"IHDR":
        raise ValueError("missing canonical PNG IHDR")
    width, height, bit_depth, color_type, compression, filtering, interlace = (
        struct.unpack(">IIBBBBB", data[16:29])
    )
    if (bit_depth, color_type, compression, filtering, interlace) != (
        8,
        2,
        0,
        0,
        0,
    ):
        raise ValueError(
            "PNG is not non-interlaced 8-bit RGB with standard compression/filter"
        )
    return digest, (width, height), "RGB", "PNG"


def _asset_set_digest(entries: list[dict[str, Any]]) -> str:
    by_pair: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in entries:
        pair = (entry["type"], entry["rarity"])
        if pair in by_pair:
            raise ValueError(f"duplicate mapping {pair[0]}+{pair[1]}")
        by_pair[pair] = entry
    if set(by_pair) != EXPECTED_PAIRS:
        raise ValueError("asset set is not the exact 5x4 matrix")

    lines: list[str] = []
    for card_type in TYPE_ORDER:
        for rarity in RARITY_ORDER:
            entry = by_pair[(card_type, rarity)]
            width, height = entry["dimensions"]
            lines.append(
                f"{card_type}\t{rarity}\t{entry['path']}\t"
                f"{entry['sha256']}\t{width}x{height}\n"
            )
    return hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()


def _load_json(path: Path, errors: list[str], label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        _error(errors, f"{label} unreadable: {exc}")
        return {}
    if not isinstance(value, dict):
        _error(errors, f"{label} must be a JSON object")
        return {}
    return value


def _check_header(manifest: dict[str, Any], errors: list[str]) -> None:
    expected = {
        "schema_version": 1,
        "requirement_id": "REQ-PPAUG-036",
        "package_kind": "blank-type-by-rarity-templates",
        "template_version": "v001/composed",
        "stable_source_path": PACKAGE_ROOT.as_posix(),
        "template_count": 20,
        "type_order": list(TYPE_ORDER),
        "rarity_order": list(RARITY_ORDER),
        "dimensions": list(EXPECTED_DIMENSIONS),
        "pixel_mode": "RGB",
        "format": "PNG",
        "asset_set_sha256_algorithm": ASSET_SET_ALGORITHM,
    }
    for key, wanted in expected.items():
        if manifest.get(key) != wanted:
            _error(
                errors,
                f"manifest {key} mismatch: expected {wanted!r}, "
                f"got {manifest.get(key)!r}",
            )

    source = manifest.get("source")
    if not isinstance(source, dict):
        _error(errors, "manifest source must be an object")
        source = {}
    expected_source = {
        "plm_product_id": "2a013f5d71406d4a",
        "repository": "Hypertext",
        "remote": "http://localhost:23234/Hypertext",
        "branch": "feature/visual-descriptor-grammar",
        "correcting_commit": EXPECTED_CORRECTING_COMMIT,
        "branch_head_at_packaging": EXPECTED_PACKAGING_HEAD,
        "construction_authority_commit": EXPECTED_AUTHORITY_COMMIT,
        "manifest_path": SOURCE_MANIFEST_REL.as_posix(),
        "manifest_sha256": EXPECTED_SOURCE_MANIFEST_SHA256,
    }
    for key, wanted in expected_source.items():
        if source.get(key) != wanted:
            _error(
                errors,
                f"source {key} mismatch: expected {wanted!r}, "
                f"got {source.get(key)!r}",
            )

    provenance = manifest.get("provenance")
    if not isinstance(provenance, dict):
        _error(errors, "manifest provenance must be an object")
        provenance = {}
    expected_provenance = {
        "task_id": "363b064b54134649",
        "delivery_artifact_id": 213,
        "delivery_composite_sha256": EXPECTED_PROVENANCE_COMPOSITE,
        "delivery_composite_sha256_algorithm": DELIVERY_COMPOSITE_ALGORITHM,
    }
    for key, wanted in expected_provenance.items():
        if provenance.get(key) != wanted:
            _error(
                errors,
                f"provenance {key} mismatch: expected {wanted!r}, "
                f"got {provenance.get(key)!r}",
            )

    review_gate = manifest.get("review_gate")
    if not isinstance(review_gate, dict):
        _error(errors, "manifest review_gate must be an object")
        review_gate = {}
    if review_gate.get("requirement_id") != "REQ-PPAUG-006":
        _error(errors, "review gate must remain REQ-PPAUG-006")
    if review_gate.get("status") != "isolated-pending-human-review":
        _error(errors, "review gate status must remain isolated-pending-human-review")
    if review_gate.get("default_branch_merge_authorized") is not False:
        _error(errors, "default-branch merge must remain unauthorized")


def verify_package(
    root: Path = REPO_ROOT,
    manifest_path: Path | None = None,
) -> list[str]:
    """Return all deterministic package errors; an empty list means PASS."""

    root = root.resolve()
    manifest_path = manifest_path or root / MANIFEST_REL
    errors: list[str] = []
    manifest = _load_json(manifest_path, errors, "persistence manifest")
    if not manifest:
        return errors
    _check_header(manifest, errors)

    source_path = root / SOURCE_MANIFEST_REL
    source_manifest = _load_json(source_path, errors, "source manifest")
    source_by_pair: dict[tuple[str, str], dict[str, Any]] = {}
    if source_manifest:
        try:
            source_digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
        except OSError as exc:
            _error(errors, f"source manifest unreadable for hashing: {exc}")
        else:
            if source_digest != EXPECTED_SOURCE_MANIFEST_SHA256:
                _error(errors, "source manifest digest drift")
        if source_manifest.get("schema_version") != 3:
            _error(errors, "source manifest schema must remain 3")
        if source_manifest.get("authority_commit") != EXPECTED_AUTHORITY_COMMIT:
            _error(errors, "source manifest construction authority drift")
        outputs = source_manifest.get("outputs")
        if not isinstance(outputs, list):
            _error(errors, "source manifest outputs must be a list")
        else:
            for item in outputs:
                if isinstance(item, dict):
                    pair = (item.get("type"), item.get("rarity"))
                    if pair in source_by_pair:
                        _error(
                            errors,
                            f"source manifest duplicate mapping {pair[0]}+{pair[1]}",
                        )
                    source_by_pair[pair] = item
            if set(source_by_pair) != EXPECTED_PAIRS:
                _error(errors, "source manifest is not the exact 20-pair matrix")

    entries = manifest.get("templates")
    if not isinstance(entries, list):
        _error(errors, "manifest templates must be a list")
        return errors
    if len(entries) != 20:
        _error(errors, f"template count mismatch: expected 20, got {len(entries)}")

    pair_counter: Counter[tuple[Any, Any]] = Counter()
    path_counter: Counter[str] = Counter()
    digest_counter: Counter[str] = Counter()
    expected_disk_paths: set[str] = set()

    for index, entry in enumerate(entries):
        label = f"templates[{index}]"
        if not isinstance(entry, dict):
            _error(errors, f"{label} must be an object")
            continue

        card_type = entry.get("type")
        rarity = entry.get("rarity")
        pair = (card_type, rarity)
        pair_counter[pair] += 1
        if pair not in EXPECTED_PAIRS:
            _error(errors, f"{label} has unsupported pair {card_type}+{rarity}")

        path_value = entry.get("path")
        relative = _safe_relative_path(path_value)
        if relative is None:
            _error(errors, f"{label} has unsafe or noncanonical path {path_value!r}")
            continue
        path_counter[relative.as_posix()] += 1

        substitution = _substitution_kind(relative)
        if substitution is not None:
            _error(errors, f"{label} rejected {substitution}: {relative}")

        if pair in EXPECTED_PAIRS:
            wanted_path = _expected_path(card_type, rarity)
            expected_disk_paths.add(wanted_path)
            if relative.as_posix() != wanted_path:
                _error(
                    errors,
                    f"{label} path mismatch for {card_type}+{rarity}: "
                    f"expected {wanted_path}, got {relative}",
                )

        if entry.get("content_kind") != "blank-type-by-rarity-template":
            _error(errors, f"{label} is not declared as a blank template")
        if entry.get("dimensions") != list(EXPECTED_DIMENSIONS):
            _error(errors, f"{label} dimensions metadata drift")
        if entry.get("pixel_mode") != "RGB":
            _error(errors, f"{label} pixel mode metadata drift")
        if entry.get("format") != "PNG":
            _error(errors, f"{label} format metadata drift")

        recorded_digest = entry.get("sha256")
        if not isinstance(recorded_digest, str) or not SHA256_RE.fullmatch(
            recorded_digest
        ):
            _error(errors, f"{label} has invalid SHA-256")
            recorded_digest = ""
        else:
            digest_counter[recorded_digest] += 1

        source_item = source_by_pair.get(pair)
        if source_item is not None:
            if source_item.get("path") != path_value:
                _error(errors, f"{label} path differs from pinned source manifest")
            if source_item.get("sha256") != recorded_digest:
                _error(errors, f"{label} digest differs from pinned source manifest")
            source_record = entry.get("source_record")
            expected_record = {
                "accepted_candidate": source_item.get("accepted_candidate"),
                "type_label_source": source_item.get("type_label_source"),
                "visible_type_label": source_item.get("visible_type_label"),
                "visible_rarity_label": source_item.get("visible_rarity_label"),
            }
            if source_record != expected_record:
                _error(errors, f"{label} source provenance drift")

        if substitution is not None:
            continue
        asset_path = root / relative
        package_path = (root / PACKAGE_ROOT).resolve()
        try:
            resolved_asset = asset_path.resolve(strict=True)
        except OSError as exc:
            _error(errors, f"{label} missing template: {relative} ({exc})")
            continue
        if asset_path.is_symlink() or not resolved_asset.is_relative_to(package_path):
            _error(errors, f"{label} template escapes package through a symlink")
            continue
        try:
            digest, dimensions, mode, image_format = _read_png(resolved_asset)
        except (OSError, ValueError, struct.error) as exc:
            _error(errors, f"{label} invalid PNG: {relative} ({exc})")
            continue
        if digest != recorded_digest:
            _error(errors, f"{label} digest drift: {relative}")
        if dimensions != EXPECTED_DIMENSIONS:
            _error(
                errors,
                f"{label} decoded dimensions drift: expected "
                f"{EXPECTED_DIMENSIONS}, got {dimensions}",
            )
        if mode != "RGB" or image_format != "PNG":
            _error(errors, f"{label} decoded image contract drift")

    actual_pairs = set(pair_counter)
    for card_type, rarity in sorted(EXPECTED_PAIRS - actual_pairs):
        _error(errors, f"missing pair {card_type}+{rarity}")
    for pair, count in sorted(pair_counter.items(), key=lambda item: repr(item[0])):
        if count > 1:
            _error(errors, f"duplicate mapping {pair[0]}+{pair[1]} ({count} entries)")
    for path, count in sorted(path_counter.items()):
        if count > 1:
            _error(errors, f"duplicate path mapping {path} ({count} entries)")
    for digest, count in sorted(digest_counter.items()):
        if count > 1:
            _error(errors, f"duplicate asset digest {digest} ({count} entries)")

    # Repair patches declared by the manifest (paste_rgb_patch stages and the
    # repaired TITLE witness) are package PNGs too: expected on disk and
    # digest-pinned, like every composed output.
    declared_patches: list[tuple[str, str | None, str]] = []
    for stage_name, stage in (source_manifest.get("construction_stages") or {}).items():
        if isinstance(stage, dict) and stage.get("patch"):
            declared_patches.append((str(stage["patch"]), stage.get("patch_sha256"), f"stages.{stage_name}.patch"))
    for index, repair in enumerate(source_manifest.get("repairs") or []):
        witness = repair.get("title_type_label_witness") if isinstance(repair, dict) else None
        if isinstance(witness, dict) and witness.get("path"):
            declared_patches.append((str(witness["path"]), witness.get("sha256"), f"repairs[{index}].title_type_label_witness"))
    for rel_path, digest, label in declared_patches:
        expected_disk_paths.add(rel_path)
        patch_file = root / rel_path
        if not patch_file.is_file():
            _error(errors, f"{label} missing on disk: {rel_path}")
        elif digest and hashlib.sha256(patch_file.read_bytes()).hexdigest() != digest:
            _error(errors, f"{label} digest mismatch: {rel_path}")

    package_path = root / PACKAGE_ROOT
    if package_path.is_dir():
        actual_disk_paths = {
            path.relative_to(root).as_posix()
            for path in package_path.rglob("*.png")
            if path.is_file()
        }
        for path in sorted(expected_disk_paths - actual_disk_paths):
            _error(errors, f"missing package PNG {path}")
        for path in sorted(actual_disk_paths - expected_disk_paths):
            _error(errors, f"unexpected package PNG {path}")
    else:
        _error(errors, f"stable package path missing: {PACKAGE_ROOT}")

    if manifest.get("asset_set_sha256_algorithm") == ASSET_SET_ALGORITHM:
        try:
            asset_set_digest = _asset_set_digest(entries)
        except (KeyError, TypeError, ValueError) as exc:
            _error(errors, f"cannot compute asset-set digest: {exc}")
        else:
            recorded_set_digest = manifest.get("asset_set_sha256")
            if not isinstance(recorded_set_digest, str) or not SHA256_RE.fullmatch(
                recorded_set_digest
            ):
                _error(errors, "asset_set_sha256 is invalid")
            elif recorded_set_digest != asset_set_digest:
                _error(errors, "asset-set digest drift")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="repository root (default: inferred from this script)",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="alternate persistence manifest, used by mutation tests",
    )
    args = parser.parse_args(argv)
    errors = verify_package(args.root, args.manifest)
    if errors:
        for message in errors:
            print(f"FAIL: {message}", file=sys.stderr)
        print(f"template package verification failed: {len(errors)} error(s)", file=sys.stderr)
        return 1
    print(
        "PASS: 20 exact blank type-by-rarity templates; "
        "digests, dimensions, mapping, source, and provenance verified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
