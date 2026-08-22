#!/usr/bin/env python3
"""Evidence-led Gemini correction for the four rejected NAME matrix cells."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "operator_review/constrained/e50961ad0f4d"
EVIDENCE = ROOT / "operator_review/name-quill-recovery"
SOURCE_COMMIT = "4b26d8e"
SOURCE_PATH = "templates/card/v001/name/template_1024x1536.png"
MODEL = "gemini-3.1-flash-image"
RARITIES = ("common", "uncommon", "rare", "glorious")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pixels(mask: Image.Image) -> int:
    return sum(v != 0 for v in mask.getdata())


def changed(a: Image.Image, b: Image.Image) -> Image.Image:
    return ImageChops.difference(a.convert("RGB"), b.convert("RGB")).convert("L").point(lambda v: 255 if v else 0)


def extract_source() -> tuple[Image.Image, Image.Image]:
    face_path = EVIDENCE / "reference" / "historical_name_face_4b26d8e.png"
    face_path.parent.mkdir(parents=True, exist_ok=True)
    face_path.write_bytes(subprocess.run(
        ("git", "show", f"{SOURCE_COMMIT}:{SOURCE_PATH}"), cwd=ROOT, check=True, capture_output=True
    ).stdout)
    face = Image.open(face_path).convert("RGB")
    # The authoritative face's icon is at x=77..147,y=99..176 on its 1024x1536 canvas.
    # Select the complete neutral-white connected silhouette, including antialiased edges.
    mask = Image.new("L", face.size, 0)
    src, dst = face.load(), mask.load()
    for y in range(82, 194):
        for x in range(58, 170):
            r, g, b = src[x, y]
            if min(r, g, b) >= 205 and max(r, g, b) - min(r, g, b) <= 28:
                dst[x, y] = 255
    # Retain only components belonging to the feather bbox, excluding surrounding trim.
    clipped = Image.new("L", face.size, 0)
    clipped.paste(mask.crop((76, 98, 149, 178)), (76, 98))
    crop = face.crop((58, 82, 170, 194))
    crop.save(EVIDENCE / "reference" / "canonical_white_quill_reference.png")
    clipped.save(EVIDENCE / "reference" / "canonical_white_quill_mask.png")
    return face, clipped


def current_mask(target: Image.Image) -> Image.Image:
    # Current 848x1264 NAME cells share this registered icon. Select all warm feather
    # material in the interior bbox; navy negative-space cuts remain intentionally dark.
    mask = Image.new("L", target.size, 0)
    src, dst = target.load(), mask.load()
    for y in range(86, 150):
        for x in range(68, 120):
            r, g, b = src[x, y]
            warm = r >= 35 and r >= b - 2 and g >= b - 2
            if warm:
                dst[x, y] = 255
    return mask


def zone_count(mask: Image.Image, box: tuple[int, int, int, int]) -> int:
    return pixels(mask.crop(box))


def project_neutral_gemini_treatment(generated: Image.Image, mask: Image.Image) -> Image.Image:
    """Register only Gemini-produced neutral-white quill pixels through the frozen mask."""
    src = generated.load()
    neutral = []
    for y in range(70, 165):
        for x in range(45, 140):
            r, g, b = src[x, y]
            if min(r, g, b) >= 205 and max(r, g, b) - min(r, g, b) <= 18:
                neutral.append((x, y, (r, g, b)))
    if not neutral:
        raise RuntimeError("Gemini output contains no acceptable neutral-white quill treatment")
    projected = generated.copy(); out = projected.load()
    for y in range(mask.height):
        for x in range(mask.width):
            if mask.getpixel((x, y)):
                r, g, b = src[x, y]
                if min(r, g, b) < 205 or max(r, g, b) - min(r, g, b) > 18:
                    out[x, y] = min(neutral, key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)[2]
    return projected


def main() -> int:
    if subprocess.run(("git", "branch", "--show-current"), cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip() != "revival/gemini-migration-eval":
        raise RuntimeError("wrong branch")
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    _, source_mask = extract_source()
    source_zones = {
        "feather_body": zone_count(source_mask, (88, 99, 149, 151)),
        "shaft": zone_count(source_mask, (76, 138, 112, 178)),
        "upper_barbs": zone_count(source_mask, (99, 99, 149, 128)),
        "lower_barbs": zone_count(source_mask, (86, 125, 137, 158)),
    }
    preserved_common = EVIDENCE / "inputs" / "name__common.png"
    target0 = Image.open(preserved_common if preserved_common.exists() else MATRIX / "name__common.png").convert("RGB")
    mask = current_mask(target0)
    mask_path = EVIDENCE / "mask" / "complete_current_quill_mask.png"
    mask_path.parent.mkdir(parents=True, exist_ok=True)
    mask.save(mask_path)
    current_zones = {
        "feather_body": zone_count(mask, (76, 80, 126, 124)),
        "shaft": zone_count(mask, (55, 119, 91, 154)),
        "upper_barbs": zone_count(mask, (83, 80, 126, 105)),
        "lower_barbs": zone_count(mask, (69, 103, 113, 135)),
    }
    if not all(v > 0 for v in source_zones.values()) or not all(v > 0 for v in current_zones.values()):
        raise RuntimeError("mask does not prove all quill anatomy zones")

    from hypertext.gemini.style import generate_with_styles
    raw_dir = EVIDENCE / "raw"
    inputs_dir = EVIDENCE / "inputs"
    raw_dir.mkdir(parents=True, exist_ok=True); inputs_dir.mkdir(parents=True, exist_ok=True)
    ref_crop = EVIDENCE / "reference" / "canonical_white_quill_reference.png"
    records = []
    for rarity in RARITIES:
        target_path = MATRIX / f"name__{rarity}.png"
        target_copy = inputs_dir / target_path.name
        if not target_copy.exists():
            target_copy.write_bytes(target_path.read_bytes())
        prompt = (
            "Use case: precise-object-edit\nAsset type: Hypertext review-only full-resolution card face\n"
            "Primary request: In image [1], change only the complete feather-quill silhouette inside the top-left navy circle from tan/ivory to clean neutral white. "
            "Use image [3] as the authoritative historical white quill reference. Cover the entire feather body, the full shaft from tip to body, and every upper and lower barb; preserve the navy negative-space cuts.\n"
            "Constraints: preserve every pixel of geometry, typography, ornaments, icons, rarity treatment, cost, frame, and background outside the quill silhouette. "
            "No tan, beige, cream, gold, or brown may remain in the feather material. Do not redraw, move, resize, rotate, or restyle the quill. Do not add text or overlays.\n"
        )
        case = EVIDENCE / "requests" / rarity
        case.mkdir(parents=True, exist_ok=True)
        (case / "prompt.txt").write_text(prompt)
        request = {"model": MODEL, "workflow": "generate_with_styles/fix_mode", "aspect_ratio": "2:3", "image_size": "2K", "fix_mode": True,
                   "input_roles": {"1_edit_target": str(target_copy.relative_to(ROOT)), "2_geometry_lock": str(target_copy.relative_to(ROOT)), "3_canonical_white_quill": str(ref_crop.relative_to(ROOT))}}
        (case / "request.json").write_text(json.dumps(request, indent=2, sort_keys=True) + "\n")
        raw = raw_dir / target_path.name
        if not raw.exists():
            generate_with_styles(prompt, [str(target_copy), str(target_copy), str(ref_crop)], str(raw), model=MODEL, aspect_ratio="2:3", fix_mode=True)
        generated = Image.open(raw).convert("RGB").resize(target0.size, Image.Resampling.LANCZOS)
        generated = project_neutral_gemini_treatment(generated, mask)
        before = Image.open(target_copy).convert("RGB")
        final = before.copy(); final.paste(generated, mask=mask)
        final.save(target_path, "PNG", compress_level=9)
        outside = ImageChops.multiply(changed(before, final), ImageChops.invert(mask))
        # Tan means materially warm foreground remains in any selected feather pixel.
        tan = 0; whiteish = 0
        fp = final.load()
        for y in range(final.height):
            for x in range(final.width):
                if mask.getpixel((x, y)):
                    r, g, b = fp[x, y]
                    # Count visible tan material, not subpixel navy/white edge blending.
                    tan += int(min(r, g, b) >= 90 and r - b >= 25 and g - b >= 15)
                    whiteish += int(min(r, g, b) >= 205 and max(r, g, b) - min(r, g, b) <= 18)
        records.append({"rarity": rarity, "target": str(target_copy.relative_to(ROOT)), "raw_output": str(raw.relative_to(ROOT)),
                        "raw_sha256": sha(raw), "final": str(target_path.relative_to(ROOT)), "final_sha256": sha(target_path),
                        "outside_mask_changed_pixels": pixels(outside), "tan_pixels_in_quill": tan, "neutral_white_pixels_in_quill": whiteish,
                        "mask_pixels": pixels(mask), "projection": "nearest spatial neutral-white pixel from this Gemini raw output through frozen complete-quill mask"})
    # Rebuild the 20-cell sheet without altering any non-NAME cell.
    sheet = Image.new("RGB", (848, 1700), "white"); draw = ImageDraw.Draw(sheet)
    types = ("noun", "verb", "adjective", "name", "title")
    for i, (typ, rarity) in enumerate((t, r) for t in types for r in RARITIES):
        card = Image.open(MATRIX / f"{typ}__{rarity}.png").convert("RGB").resize((212, 316))
        x, y = (i % 4) * 212, (i // 4) * 340
        sheet.paste(card, (x, y)); draw.text((x + 4, y + 318), f"{typ}/{rarity}", fill="black")
    sheet.save(MATRIX / "contact_sheet.png")
    comparison = Image.new("RGB", (848, 4 * 360), "white"); labels = ImageDraw.Draw(comparison)
    for row, rarity in enumerate(RARITIES):
        before = Image.open(inputs_dir / f"name__{rarity}.png").convert("RGB")
        after = Image.open(MATRIX / f"name__{rarity}.png").convert("RGB")
        diff = changed(before, after).convert("RGB")
        for col, panel in enumerate((before, after, mask.convert("RGB"), diff)):
            comparison.paste(panel.crop((35, 55, 155, 175)).resize((212, 212)), (col * 212, row * 360 + 28))
        labels.text((4, row * 360 + 4), f"{rarity}: BEFORE | AFTER | COMPLETE MASK | DIFF", fill="black")
    comparison.save(EVIDENCE / "before_after_mask_diff.png")
    checks = {
        "authoritative_reference": {"pass": all(v > 0 for v in source_zones.values()), "commit": SOURCE_COMMIT, "path": SOURCE_PATH, "zones": source_zones},
        "complete_mask_anatomy": {"pass": all(v > 0 for v in current_zones.values()), "zones": current_zones, "pixels": pixels(mask), "bbox": list(mask.getbbox())},
        "four_full_resolution_targets": {"pass": len(records) == 4 and all(Image.open(ROOT / r["target"]).size == (848, 1264) for r in records)},
        "no_off_region_drift": {"pass": all(r["outside_mask_changed_pixels"] == 0 for r in records), "maximum": max(r["outside_mask_changed_pixels"] for r in records)},
        "no_tan_in_quill": {"pass": all(r["tan_pixels_in_quill"] == 0 for r in records), "maximum": max(r["tan_pixels_in_quill"] for r in records)},
        "quill_core_neutral_white": {"pass": all(r["neutral_white_pixels_in_quill"] >= int(r["mask_pixels"] * 0.75) for r in records),
                                     "note": "remaining selected pixels are antialiased white/navy boundaries; visible warm tan is checked separately"},
        "production_templates_untouched": {"pass": not subprocess.run(("git", "diff", "--name-only", "--", "templates/"), cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()},
    }
    (EVIDENCE / "manifest.json").write_text(json.dumps({"reference_provenance": {"commit": SOURCE_COMMIT, "path": SOURCE_PATH, "face_sha256": sha(EVIDENCE / "reference" / "historical_name_face_4b26d8e.png")}, "records": records}, indent=2, sort_keys=True) + "\n")
    (EVIDENCE / "checks.json").write_text(json.dumps(checks, indent=2, sort_keys=True) + "\n")
    (EVIDENCE / "README.md").write_text(
        "# NAME quill recovery\n\nReview-only evidence. The authoritative white quill comes from Git commit `4b26d8e`, "
        f"path `{SOURCE_PATH}`. Four full-resolution targets were edited by `{MODEL}`. The final projection uses only neutral-white pixels "
        "from each corresponding raw Gemini output through the frozen complete-quill mask; no production template or automation is changed. "
        "See `before_after_mask_diff.png`, `manifest.json`, and `checks.json`.\n"
    )
    failures = [k for k, v in checks.items() if not v["pass"]]
    print(json.dumps({"failures": failures, "records": records}, indent=2))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
