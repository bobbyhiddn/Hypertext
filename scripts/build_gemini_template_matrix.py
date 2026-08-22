#!/usr/bin/env python3
"""Build the frozen 20-cell word-template matrix as review-only Gemini candidates."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = "e50961ad0f4d66f398f81706f092a7d0ea9cb0f4"
OUTPUT_ROOT = ROOT / "operator_review/constructed/e50961ad0f4d"
MODEL = "gemini-3.1-flash-image"
TYPES = ("noun", "verb", "adjective", "name", "title")
RARITIES = ("common", "uncommon", "rare", "glorious")
BASE = "templates/card/v001/base/template_1024x1536.png"
TYPE_PATH = "templates/card/v001/{key}/template_1024x1536.png"
RARITY_PATH = "templates/card/v001/{key}/template_1024x1536.png"
PALETTES = (
    "templates/palettes/type_symbols_palette.png",
    "templates/palettes/rarity_diamonds_palette.png",
)
EXPECTED_BLOBS = {
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
    PALETTES[0]: "078be48cf5de2da4460494ee1a1a61a45f4ae04f",
    PALETTES[1]: "77b370eec358476894a9fe5ec73a4c92e1c901c4",
}


def git(*args: str, binary: bool = False):
    result = subprocess.run(("git", *args), cwd=ROOT, check=True, capture_output=True)
    return result.stdout if binary else result.stdout.decode().strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frozen_inputs(output: Path) -> dict[str, dict[str, str]]:
    refs = output / "references"
    refs.mkdir(parents=True, exist_ok=True)
    records = {}
    for repo_path, expected in EXPECTED_BLOBS.items():
        actual = git("rev-parse", f"{AUTHORITY}:{repo_path}")
        if actual != expected:
            raise RuntimeError(f"authority blob mismatch for {repo_path}: {actual}")
        data = git("show", f"{AUTHORITY}:{repo_path}", binary=True)
        target = refs / repo_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        records[repo_path] = {"blob": actual, "snapshot": str(target.relative_to(ROOT))}
    return records


def prompt(word_type: str, rarity: str) -> str:
    rarity_rules = {
        "common": "one white diamond with navy outline and no card ornament",
        "uncommon": "one green #2E8B57 diamond with navy outline and no card ornament",
        "rare": "one gold #C9A44C diamond with navy outline, a small plus, and exactly one card ornament",
        "glorious": "one orange #F28C28 diamond with navy outline, a small plus, and exactly two card ornaments",
    }
    icons = {"noun": "closed book", "verb": "slanted pencil", "adjective": "sparkle pencil with two four-pointed stars", "name": "feather quill", "title": "ornate empty frame"}
    return f"""Create a blank Hypertext face template for {word_type.upper()} / {rarity.upper()}.
Use the base reference as absolute authority for canvas geometry, border, typography placement, panels, and all non-identity pixels. Make only two semantic corrections: the top-left navy circle contains the centered white {icons[word_type]} icon from the type reference, and the rarity tab contains {rarity_rules[rarity]} from the rarity reference. Do not add words, example-card content, artwork, glow, captions, watermarks, or new ornaments. Preserve the complete border and every panel position exactly."""


def normalize(raw: Path, candidate: Path) -> tuple[int, int, str]:
    with Image.open(raw) as image:
        image.load()
        normalized = image.convert("RGB").resize((848, 1264), Image.Resampling.LANCZOS)
    candidate.parent.mkdir(parents=True, exist_ok=True)
    normalized.save(candidate, "PNG", optimize=False, compress_level=9)
    return (*normalized.size, normalized.mode)


def contact_sheet(output: Path, records: list[dict]) -> Path:
    card_size, label_height = (212, 316), 24
    sheet = Image.new("RGB", (4 * card_size[0], 5 * (card_size[1] + label_height)), "white")
    draw = ImageDraw.Draw(sheet)
    for index, record in enumerate(records):
        with Image.open(ROOT / record["candidate"]) as source:
            card = source.convert("RGB").resize(card_size, Image.Resampling.LANCZOS)
        x, y = (index % 4) * card_size[0], (index // 4) * (card_size[1] + label_height)
        sheet.paste(card, (x, y))
        draw.text((x + 5, y + card_size[1] + 4), f'{record["type"]} / {record["rarity"]}', fill="black")
    path = output / "contact_sheet.png"
    sheet.save(path, "PNG", optimize=False, compress_level=9)
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    output = args.output_root.resolve()
    if ROOT not in output.parents or output == ROOT or "operator_review" not in output.parts:
        raise RuntimeError("output must be a review-only location under this repository")
    if git("branch", "--show-current") != "revival/gemini-migration-eval":
        raise RuntimeError("matrix generation is restricted to revival/gemini-migration-eval")

    from hypertext.gemini.style import generate_with_styles

    inputs = frozen_inputs(output)
    records = []
    for row, word_type in enumerate(TYPES, 1):
        for column, rarity in enumerate(RARITIES, 1):
            name = f"{word_type}__{rarity}"
            case = output / "raw" / name
            raw = case / "gemini.png"
            candidate = output / f"{name}.png"
            refs = [BASE, TYPE_PATH.format(key=word_type), RARITY_PATH.format(key=rarity), *PALETTES]
            snapshots = [output / "references" / item for item in refs]
            if not (args.resume and raw.exists()):
                case.mkdir(parents=True, exist_ok=True)
                (case / "prompt.txt").write_text(prompt(word_type, rarity) + "\n")
                generate_with_styles(prompt(word_type, rarity), [str(x) for x in snapshots], str(raw), model=MODEL, aspect_ratio="2:3", target_rarity=rarity, fix_mode=False)
            width, height, mode = normalize(raw, candidate)
            records.append({"cell": (row - 1) * 4 + column, "type": word_type, "rarity": rarity,
                            "candidate": str(candidate.relative_to(ROOT)), "candidate_sha256": sha256(candidate),
                            "raw": str(raw.relative_to(ROOT)), "raw_sha256": sha256(raw),
                            "generation": str((case / "generation.json").relative_to(ROOT)),
                            "prompt": str((case / "prompt.txt").relative_to(ROOT)),
                            "references": refs, "width": width, "height": height, "mode": mode, "format": "PNG"})
    manifest = {"schema_version": 1, "status": "review-candidates-only", "authority_commit": AUTHORITY,
                "branch": "revival/gemini-migration-eval", "model": MODEL,
                "request": {"workflow": "hypertext.gemini.style.generate_with_styles", "aspect_ratio": "2:3", "image_size": "2K", "response_modalities": ["IMAGE"], "reference_count": 5},
                "normalization": {"source": "raw Gemini response", "format": "PNG", "mode": "RGB", "width": 848, "height": 1264, "resampling": "Pillow LANCZOS"},
                "inputs": inputs, "outputs": records}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    sheet = contact_sheet(output, records)
    expected_keys = {(word_type, rarity) for word_type in TYPES for rarity in RARITIES}
    actual_keys = {(record["type"], record["rarity"]) for record in records}
    canonical_clean = not git("diff", "--name-only", "--", "templates/")
    checks = {
        "authority_input_identity": {"pass": len(inputs) == len(EXPECTED_BLOBS), "verified_blobs": len(inputs)},
        "cardinality": {"pass": len(records) == 20 and actual_keys == expected_keys, "count": len(records)},
        "raster_contract": {"pass": all((x["width"], x["height"], x["mode"], x["format"]) == (848, 1264, "RGB", "PNG") for x in records)},
        "provenance": {"pass": all((ROOT / x["generation"]).is_file() and (ROOT / x["prompt"]).is_file() for x in records)},
        "canonical_immutability": {"pass": canonical_clean, "git_diff_templates_empty": canonical_clean},
        "contact_sheet": {"pass": sheet.is_file(), "path": str(sheet.relative_to(ROOT)), "sha256": sha256(sheet)},
        "human_visual_review_required": True,
    }
    (output / "checks.json").write_text(json.dumps(checks, indent=2) + "\n")
    if not all(item["pass"] for item in checks.values() if isinstance(item, dict) and "pass" in item):
        raise RuntimeError("matrix build checks failed")
    print(f"built {len(records)} Gemini review candidates at {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
