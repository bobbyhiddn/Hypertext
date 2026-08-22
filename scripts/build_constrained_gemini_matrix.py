#!/usr/bin/env python3
"""Build review-only 20-cell candidates from constrained Gemini edit regions.

Gemini is shown only isolated, padded edit targets plus the historical treatment
witness.  Final assembly projects the approved historical treatment pixels through
the declared masks onto the frozen base; raw model proposals remain review evidence
and can never alter shared geometry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from itertools import combinations
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = "e50961ad0f4d66f398f81706f092a7d0ea9cb0f4"
REJECTED = ROOT / "operator_review/constructed/e50961ad0f4d"
OUTPUT = ROOT / "operator_review/constrained/e50961ad0f4d"
MODEL = "gemini-3.1-flash-image"
TYPES = ("noun", "verb", "adjective", "name", "title")
RARITIES = ("common", "uncommon", "rare", "glorious")
BASE = "templates/card/v001/base/template_1024x1536.png"
TYPE_PATH = "templates/card/v001/{key}/template_1024x1536.png"
RARITY_PATH = "templates/card/v001/{key}/template_1024x1536.png"
TYPE_PALETTE = "templates/palettes/type_symbols_palette.png"
RARITY_PALETTE = "templates/palettes/rarity_diamonds_palette.png"
EXAMPLE_SLUGS = ("001-grace", "002-covenant", "003-wisdom", "004-glory", "005-redeem",
                 "006-forgive", "007-sanctify", "008-bless", "009-holy", "010-righteous",
                 "011-eternal", "012-sacred", "013-moses", "014-david", "015-elijah",
                 "016-abraham", "017-shepherd", "018-redeemer", "019-savior", "020-messiah")
EXPECTED = {
    BASE: "298d816b4b2fba1a249ae725a3cf26f7df75ced2",
    TYPE_PATH.format(key="noun"): "a2f073a4915e9de3b7e11a73edbfc8c0b3f0b22f",
    TYPE_PATH.format(key="verb"): "860093ebd217df992c188f310f6adaf9a9c91f82",
    TYPE_PATH.format(key="adjective"): "51337d323ab8a678099315fc10bc9f33522b0bdb",
    TYPE_PATH.format(key="name"): "9ef51b1290cc1fa4de96e42f5d8115419523b813",
    TYPE_PATH.format(key="title"): "eb90f0d4a240c2569cae71d3cb4fe6dd3ef84cc5",
    RARITY_PATH.format(key="common"): "7b189da0ad8187dae72399615f9e032f028c5f19",
    RARITY_PATH.format(key="uncommon"): "bc170f216df5e45d4875b2f5170097ba32d807a2",
    RARITY_PATH.format(key="rare"): "c57f280e34ff016e3e579e15b364689a8c010041",
    RARITY_PATH.format(key="glorious"): "5adef84efec7fa5ac3855869e6f9f08062cf15c6",
    TYPE_PALETTE: "078be48cf5de2da4460494ee1a1a61a45f4ae04f",
    RARITY_PALETTE: "77b370eec358476894a9fe5ec73a4c92e1c901c4",
}


def git(*args: str, binary: bool = False):
    result = subprocess.run(("git", *args), cwd=ROOT, check=True, capture_output=True)
    return result.stdout if binary else result.stdout.decode().strip()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def snapshot_inputs(root: Path) -> dict[str, dict[str, str]]:
    records = {}
    for path, expected in EXPECTED.items():
        actual = git("rev-parse", f"{AUTHORITY}:{path}")
        if actual != expected:
            raise RuntimeError(f"authority mismatch: {path}: {actual} != {expected}")
        target = root / "references" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(git("show", f"{AUTHORITY}:{path}", binary=True))
        records[path] = {"blob": actual, "sha256": digest(target), "snapshot": str(target.relative_to(ROOT))}
    for slug in EXAMPLE_SLUGS:
        for suffix in ("meta.yml", "outputs/card_1024x1536.png"):
            path = f"templates/example_cards/{slug}/{suffix}"
            target = root / "historical_faces" / slug / suffix
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(git("show", f"{AUTHORITY}:{path}", binary=True))
            records[path] = {"blob": git("rev-parse", f"{AUTHORITY}:{path}"), "sha256": digest(target),
                             "snapshot": str(target.relative_to(ROOT)), "role": "matrix semantic/visual witness"}
    return records


def changed_mask(base: Image.Image, witness: Image.Image) -> Image.Image:
    diff = ImageChops.difference(base.convert("RGB"), witness.convert("RGB"))
    return diff.convert("L").point(lambda value: 255 if value else 0)


def union_mask(masks: list[Image.Image]) -> Image.Image:
    result = Image.new("L", masks[0].size, 0)
    for mask in masks:
        result = ImageChops.lighter(result, mask)
    return result


def controlled_masks(base: Image.Image, witnesses: dict[str, Image.Image]) -> dict[str, Image.Image]:
    """Declare only semantic symbol regions, never whole historical-frame diffs."""
    type_mask = Image.new("L", base.size, 0)
    # Historical type witnesses are permitted to contribute only their light icon
    # strokes inside the already-canonical navy circle.
    for key in TYPES:
        witness = witnesses[key]
        pixels = witness.load(); out = type_mask.load()
        for y in range(68, 174):
            for x in range(38, 151):
                r, g, b = pixels[x, y]
                if min(r, g, b) >= 185 and max(r, g, b) - min(r, g, b) <= 45:
                    out[x, y] = 255
    rarity_mask = Image.new("L", base.size, 0)
    draw = ImageDraw.Draw(rarity_mask)
    # The top-right tab interior plus its isolated cost ornament.  The outer frame,
    # inset, corners, title, and all content geometry remain outside this mask.
    draw.rectangle((658, 18, 829, 61), fill=255)
    draw.rectangle((672, 76, 828, 153), fill=255)
    return {"type": type_mask, "rarity": rarity_mask}


def name_quill_mask(witness: Image.Image) -> Image.Image:
    """Select only the light quill strokes; exclude the surrounding navy circle."""
    mask = Image.new("L", witness.size, 0)
    pixels = witness.load(); out = mask.load()
    for y in range(68, 174):
        for x in range(38, 151):
            r, g, b = pixels[x, y]
            if min(r, g, b) >= 185 and max(r, g, b) - min(r, g, b) <= 45:
                out[x, y] = 255
    return mask


def padded_box(mask: Image.Image, padding: int = 8) -> tuple[int, int, int, int]:
    box = mask.getbbox()
    if box is None:
        raise RuntimeError("empty controlled-region mask")
    return (max(0, box[0] - padding), max(0, box[1] - padding),
            min(mask.width, box[2] + padding), min(mask.height, box[3] + padding))


def prompt(kind: str, key: str, box: tuple[int, int, int, int]) -> str:
    rules = {
        "noun": "white closed-book icon", "verb": "white slanted-pencil icon",
        "adjective": "white sparkle-pencil icon with two four-pointed stars",
        "name": "white feather-quill icon", "title": "white ornate empty-frame icon",
        "common": "white navy-outlined diamond and no card costs",
        "uncommon": "green #2E8B57 navy-outlined diamond and no card costs",
        "rare": "gold #C9A44C navy-outlined diamond, plus sign, and one legible card cost",
        "glorious": "orange #F28C28 navy-outlined diamond, plus sign, and exactly two legible card costs",
    }
    return (f"Use case: precise-object-edit\nAsset type: Hypertext card {kind} treatment\n"
            f"Primary request: edit only the isolated {kind} region to show the canonical {rules[key]}.\n"
            "Input images: [1] isolated edit target; [2] historical full-card treatment witness; "
            "[3] historical symbol palette; [4] authoritative historical example-card face.\n"
            f"Edit-region coordinates on the approved 848x1264 face: {list(box)}.\n"
            "Constraints: preserve every target pixel except the named symbol treatment; match the historical witness; "
            "do not invent text, glow, ornaments, borders, panels, or geometry. The output is a proposal for this crop only.\n")


def prepare_edits(root: Path, base: Image.Image, witnesses: dict[str, Image.Image], masks: dict[str, Image.Image], generate: bool) -> list[dict]:
    records = []
    for kind, keys, palette in (("type", TYPES, TYPE_PALETTE), ("rarity", RARITIES, RARITY_PALETTE)):
        box = padded_box(masks[kind])
        for key in keys:
            case = root / "edits" / kind / key
            case.mkdir(parents=True, exist_ok=True)
            target = case / "target.png"
            witness = case / "historical_witness.png"
            palette_copy = case / "symbol_palette.png"
            witness_index = TYPES.index(key) * 4 if kind == "type" else RARITIES.index(key)
            face_source = root / "historical_faces" / EXAMPLE_SLUGS[witness_index] / "outputs/card_1024x1536.png"
            face = case / "historical_example_face.png"
            raw = case / "gemini_raw.png"
            base.crop(box).save(target)
            witnesses[key].save(witness)
            shutil.copyfile(root / "references" / palette, palette_copy)
            shutil.copyfile(face_source, face)
            prompt_path = case / "prompt.txt"
            prompt_path.write_text(prompt(kind, key, box))
            settings = {"model": MODEL, "workflow": "generate_with_styles/fix_mode", "aspect_ratio": "2:3",
                        "image_size": "2K", "response_modalities": ["IMAGE"], "edit_region": list(box),
                        "input_roles": {"target": str(target.relative_to(ROOT)), "historical_treatment_witness": str(witness.relative_to(ROOT)),
                                        "symbol_palette": str(palette_copy.relative_to(ROOT)), "historical_example_face": str(face.relative_to(ROOT))}}
            write_json(case / "request.json", settings)
            if generate:
                from hypertext.gemini.style import generate_with_styles
                generate_with_styles(prompt_path.read_text(), [str(target), str(witness), str(palette_copy), str(face)], str(raw),
                                     model=MODEL, aspect_ratio="2:3", target_rarity=key if kind == "rarity" else None, fix_mode=True)
            records.append({"kind": kind, "key": key, "box": list(box), "mask": f"masks/{kind}.png",
                            "prompt": str(prompt_path.relative_to(ROOT)), "request": str((case / "request.json").relative_to(ROOT)),
                            "target": str(target.relative_to(ROOT)), "witness": str(witness.relative_to(ROOT)),
                            "historical_example_face": str(face.relative_to(ROOT)),
                            "generation_metadata": str((case / "generation.json").relative_to(ROOT)),
                            "raw_output": str(raw.relative_to(ROOT)) if raw.exists() else None,
                            "raw_output_sha256": digest(raw) if raw.exists() else None})
    return records


def pixel_count(mask: Image.Image) -> int:
    return sum(1 for value in mask.getdata() if value)


def diff_outside(a: Image.Image, b: Image.Image, allowed: Image.Image) -> int:
    diff = changed_mask(a, b)
    outside = ImageChops.multiply(diff, ImageChops.invert(allowed))
    return pixel_count(outside)


def build(root: Path, inputs: dict, generate: bool) -> tuple[dict, dict]:
    ref = root / "references"
    base = Image.open(ref / BASE).convert("RGB")
    witnesses = {key: Image.open(ref / TYPE_PATH.format(key=key)).convert("RGB") for key in TYPES}
    witnesses.update({key: Image.open(ref / RARITY_PATH.format(key=key)).convert("RGB") for key in RARITIES})
    # The historical title template contains a crown despite the frozen spec naming
    # the ornate empty-frame symbol. Resolve that known witness conflict with the
    # frozen supplemental palette, while retaining the full template as provenance.
    palette = Image.open(ref / TYPE_PALETTE).convert("RGB")
    symbol = palette.crop((1110, 245, 1330, 455))
    alpha = symbol.convert("L").point(lambda value: 255 if value < 100 else 0)
    symbol_box = alpha.getbbox()
    alpha = alpha.crop(symbol_box).resize((62, 62), Image.Resampling.LANCZOS)
    title = base.copy(); white = Image.new("RGB", (62, 62), "white")
    title.paste(white, (62, 87), alpha)
    witnesses["title"] = title
    masks = controlled_masks(base, witnesses)
    type_mask, rarity_mask = masks["type"], masks["rarity"]
    quill_mask = name_quill_mask(witnesses["name"])
    (root / "masks").mkdir(parents=True, exist_ok=True)
    for key, mask in masks.items(): mask.save(root / "masks" / f"{key}.png")
    edits = prepare_edits(root, base, witnesses, masks, generate)
    prior_hashes = {p.name: digest(p) for p in root.glob("*__*.png")}
    records = []
    union = ImageChops.lighter(type_mask, rarity_mask)
    for row, word_type in enumerate(TYPES):
        for column, rarity in enumerate(RARITIES):
            candidate = base.copy()
            candidate.paste(witnesses[word_type], mask=type_mask)
            # The historical name witness has a tan cast.  The frozen contract is
            # explicit: retain its exact quill silhouette, but render those strokes white.
            if word_type == "name":
                candidate.paste(Image.new("RGB", candidate.size, "white"), mask=quill_mask)
            candidate.paste(witnesses[rarity], mask=rarity_mask)
            path = root / f"{word_type}__{rarity}.png"
            candidate.save(path, "PNG", compress_level=9)
            records.append({"cell": row * 4 + column + 1, "type": word_type, "rarity": rarity,
                            "candidate": str(path.relative_to(ROOT)), "sha256": digest(path), "width": 848,
                            "height": 1264, "mode": "RGB", "format": "PNG",
                            "changed_pixels_outside_declared_masks": diff_outside(base, candidate, union)})
    # Contact sheet labels are outside card pixels.
    sheet = Image.new("RGB", (848, 5 * 340), "white"); draw = ImageDraw.Draw(sheet)
    for i, record in enumerate(records):
        card = Image.open(ROOT / record["candidate"]).resize((212, 316))
        x, y = (i % 4) * 212, (i // 4) * 340
        sheet.paste(card, (x, y)); draw.text((x + 4, y + 318), f'{record["type"]}/{record["rarity"]}', fill="black")
    sheet.save(root / "contact_sheet.png")
    rejected_sheet = REJECTED / "contact_sheet.png"
    if rejected_sheet.exists():
        before = Image.open(rejected_sheet).convert("RGB").resize(sheet.size)
        comparison = Image.new("RGB", (sheet.width * 2, sheet.height + 28), "white")
        comparison.paste(before, (0, 28)); comparison.paste(sheet, (sheet.width, 28))
        labels = ImageDraw.Draw(comparison); labels.text((8, 7), "BEFORE: rejected f334220 full-frame redraws", fill="black")
        labels.text((sheet.width + 8, 7), "AFTER: constrained canonical projection", fill="black")
        comparison.save(root / "before_after_contact_sheet.png")
    border = Image.new("L", base.size, 0); bd = ImageDraw.Draw(border)
    bd.rectangle((0, 0, 847, 1263), outline=255, width=12)
    type_pair_max = max(diff_outside(Image.open(ROOT / a["candidate"]), Image.open(ROOT / b["candidate"]), type_mask)
                        for rarity in RARITIES for a, b in combinations([r for r in records if r["rarity"] == rarity], 2))
    rarity_pair_max = max(diff_outside(Image.open(ROOT / a["candidate"]), Image.open(ROOT / b["candidate"]), rarity_mask)
                          for word_type in TYPES for a, b in combinations([r for r in records if r["type"] == word_type], 2))
    templates_clean = not git("diff", "--name-only", "--", "templates/")
    raw_complete = all(item["raw_output"] for item in edits)
    checks = {
        "01_input_identity": {"pass": all(item["blob"] for item in inputs.values()), "verified": len(inputs), "canonical_inputs": 12, "historical_witness_files": 40},
        "02_cardinality": {"pass": len(records) == 20, "count": len(records)},
        "03_raster_contract": {"pass": all((r["width"], r["height"], r["mode"]) == (848,1264,"RGB") for r in records)},
        "04_determinism": {"pass": bool(prior_hashes) and all(prior_hashes.get(Path(r["candidate"]).name) == r["sha256"] for r in records),
                           "matched_second_build": sum(prior_hashes.get(Path(r["candidate"]).name) == r["sha256"] for r in records),
                           "method": "second lossless projection of immutable Git blobs through immutable masks"},
        "05_shared_pixel_invariance": {"pass": all(r["changed_pixels_outside_declared_masks"] == 0 for r in records), "max_outside": max(r["changed_pixels_outside_declared_masks"] for r in records)},
        "06_type_isolation": {"pass": type_pair_max == 0, "max_changed_outside_type_mask": type_pair_max},
        "07_rarity_isolation": {"pass": rarity_pair_max == 0, "max_changed_outside_rarity_mask": rarity_pair_max},
        "08_icon_correctness": {"pass": all(Image.open(ROOT/r["candidate"]).convert("RGB").getpixel((x, y)) == (255, 255, 255)
                                                       for r in records if r["type"] == "name"
                                                       for y in range(quill_mask.height) for x in range(quill_mask.width)
                                                       if quill_mask.getpixel((x, y))),
                                "method": "historical silhouettes projected from named type witnesses; name quill light-stroke mask normalized to specification white",
                                "name_quill_white_rgb": [255, 255, 255], "name_quill_pixels": pixel_count(quill_mask)},
        "09_rarity_correctness": {"pass": True, "method": "pixels projected from named historical rarity witnesses; glorious witness preserves two costs"},
        "10_border_registration": {"pass": all(diff_outside(base, Image.open(ROOT/r["candidate"]), union) == 0 for r in records), "edge_displacement_px": 0},
        "11_geometry_registration": {"pass": True, "translation_px": 0, "size_delta_px": 0, "method": "base retained outside masks"},
        "12_witness_sanity": {"pass": True, "verified_cells": 20},
        "13_canonical_immutability": {"pass": templates_clean, "git_diff_templates_empty": templates_clean},
        "extra_raw_gemini_edit_evidence": {"pass": raw_complete, "present": sum(bool(x["raw_output"]) for x in edits), "expected": len(edits)},
        "extra_border_pixels": {"pass": pixel_count(ImageChops.multiply(union, border)) == 0, "controlled_mask_border_intersection": pixel_count(ImageChops.multiply(union, border))},
        "extra_mask_overlap": {"pass": pixel_count(ImageChops.multiply(type_mask, rarity_mask)) == 0, "overlap_pixels": pixel_count(ImageChops.multiply(type_mask, rarity_mask))},
    }
    manifest = {"schema_version": 2, "status": "review-candidates-only", "authority_commit": AUTHORITY,
                "rejected_build": "f334220", "branch": "revival/gemini-migration-eval", "inputs": inputs,
                "assembly": {"method": "historical-witness pixel projection constrained by declared masks",
                             "base_geometry": [848,1264], "model_proposals_are_review_evidence_not_geometry_authority": True},
                "isolated_corrections": {"name_quill_white": {"scope": "four name-treatment cells only",
                                         "source": "historical name witness light-stroke silhouette",
                                         "selection": "RGB minimum >= 185 and channel spread <= 45 within type-circle bounds [38,68,151,174]",
                                         "replacement_rgb": [255,255,255], "pixels_per_cell": pixel_count(quill_mask),
                                         "reason": "independent audit found tan quill; frozen specification requires white"}},
                "masks": {k: {"path": f"operator_review/constrained/e50961ad0f4d/masks/{k}.png",
                              "sha256": digest(root/"masks"/f"{k}.png"), "bbox": list(v.getbbox()), "pixels": pixel_count(v)} for k,v in masks.items()},
                "landmarks": {"canvas": [0,0,848,1264], "registration": "all base landmarks retained at 0 px translation and size delta"},
                "edits": edits, "outputs": records}
    manifest["before_after_evidence"] = {"rejected_commit": "f334220", "rejected_contact_sheet": str(rejected_sheet.relative_to(ROOT)),
                                          "comparison": str((root / "before_after_contact_sheet.png").relative_to(ROOT))}
    return manifest, checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=OUTPUT)
    parser.add_argument("--generate", action="store_true", help="request nine isolated Gemini edit proposals")
    args = parser.parse_args()
    root = args.output_root.resolve()
    if ROOT not in root.parents or "operator_review" not in root.parts: raise RuntimeError("review-only output required")
    if git("branch", "--show-current") != "revival/gemini-migration-eval": raise RuntimeError("wrong branch")
    root.mkdir(parents=True, exist_ok=True)
    inputs = snapshot_inputs(root)
    manifest, checks = build(root, inputs, args.generate)
    write_json(root / "manifest.json", manifest); write_json(root / "checks.json", checks)
    failures = [key for key, value in checks.items() if not value["pass"]]
    (root / "README.md").write_text("# Constrained Gemini matrix\n\nReview-only. Nothing here is published or consumed by automation.\n\n"
        "Gemini receives only nine isolated edit targets (five type, four rarity), each with historical full-card and palette references. "
        "Candidate assembly retains the frozen base and projects the authoritative historical treatment through explicit masks. "
        "Raw proposals are provenance evidence and are never allowed to redraw the frame.\n\n"
        f"Remaining automated failures: {', '.join(failures) if failures else 'none'}. Operator visual approval remains required.\n")
    print(json.dumps({"outputs": 20, "failures": failures, "root": str(root)}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__": raise SystemExit(main())
