#!/usr/bin/env python3
"""Build one apples-to-apples SEE benchmark before replacing the 60-card set."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "package"))

from hypertext.gemini.config import image_model
from hypertext.gemini.style import generate_with_styles
from hypertext.pipeline.daily import build_prompt_text

OUT = ROOT / "operator_review/req-ppaug-030-see-benchmark"
CASE = OUT / "pilot-see-v4"
PRINTED_REFERENCE = OUT / "printed-see-reference-crop.png"
PRINTED_LANGUAGES_REFERENCE = OUT / "printed-see-languages-reference.png"
TEMPLATE = ROOT / "templates/card/v001/composed/verb/common/template_1024x1536.png"
CANONICAL_SEE = ROOT / "series/2026-Q1-dev/cards/009-see/outputs/card_1024x1536.png"
STYLE_EXAMPLE = ROOT / "templates/example_cards/005-redeem/outputs/card_1024x1536.png"
CLOSE_PILOT = OUT / "pilot-see-v2/outputs/card_1024x1536.png"
REJECTED_ANALOG = (
    ROOT
    / "operator_review/req-ppaug-029-full-card-gemini/individual/013-verb-common-v1/outputs/card_1024x1536.png"
)

# The operator identified this printed SEE face, including this Languages block,
# as the accepted benchmark. Content is transcribed from that supplied reference.
BENCHMARK_CONTENT = {
    "NUMBER": "017",
    "CARD_TYPE": "VERB",
    "RARITY_TEXT": "COMMON",
    "RARITY_ICON": "COMMON",
    "WORD": "SEE",
    "GLOSS": "To perceive with the eyes; to discern, understand, or witness.",
    "ART_PROMPT": (
        "A luminous eye-like opening formed by dark storm clouds, a single iris at its center, "
        "with restrained golden rays falling onto a narrow reflective river; symbolic biblical "
        "illustration, no human face, no portrait, and no people."
    ),
    "STAT_LORE": 2,
    "STAT_CONTEXT": 4,
    "STAT_COMPLEXITY": 1,
    "ABILITY_TEXT": "Look at the top 3 cards of the Tower, then return them in any order.",
    "OT_VERSE_LINE": (
        "Psalm 34:8 — “Taste and see that the LORD is good; blessed is the one who takes refuge in him.”"
    ),
    "NT_VERSE_LINE": "Matthew 5:8 — “Blessed are the pure in heart, for they will see God.”",
    "HEBREW": "רָאָה",
    "HEBREW_TRANSLIT": "ra'ah",
    "OT_REFS": "Gen 1:4 • Gen 16:13 • Ex 14:13 • 1 Sam 16:7",
    "GREEK": "ὁράω",
    "GREEK_TRANSLIT": "horaō",
    "NT_REFS": "John 1:39 • John 9:25 • Heb 12:14 • Rev 1:7",
    "TRIVIA_BULLETS": [
        "The Hebrew verb 'ra'ah' is the root of 'ro'eh' (seer), an early title for prophets.",
        "Hagar names God 'El Roi' (The God Who Sees Me) in Genesis 16, the only occurrence of this title.",
        "In the Bible, physical sight is often a metaphor for spiritual understanding or faith.",
        "The Greek 'horaō' implies not just catching sight of something, but mentally discerning it.",
    ],
    "SERIES": "2026-Q1 Babel",
}

OT_REFS_LINES = (
    "OT Refs: Gen 1:4 • Gen 16:13 •",
    "Ex 14:13 • 1 Sam 16:7",
)
NT_REFS_LINES = (
    "NT Refs: John 1:39 • John 9:25 •",
    "Heb 12:14 • Rev 1:7",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def output_path() -> Path:
    return CASE / "outputs/card_1024x1536.png"


def crop_reference(photo_path: Path) -> Path:
    """Perspective-normalize the operator's supplied photograph without altering it."""
    source = ImageOps.exif_transpose(Image.open(photo_path)).convert("RGB")
    width, height = source.size
    # Normalized corners, measured clockwise from the supplied 4032x3024 JPEG
    # after EXIF orientation: top-left, bottom-left, bottom-right, top-right.
    normalized = (
        (0.259, 0.195),
        (0.281, 0.715),
        (0.804, 0.699),
        (0.764, 0.193),
    )
    quad = tuple(value for x, y in normalized for value in (x * width, y * height))
    normalized_card = source.transform(
        (1024, 1536), Image.Transform.QUAD, quad, Image.Resampling.BICUBIC
    )
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "printed-see-reference-crop.png"
    normalized_card.save(target)
    # Isolate the operator-approved Languages treatment so it cannot pull the
    # generator away from the current header, icon, or stat contracts.
    languages = normalized_card.crop((48, 1164, 976, 1388))
    languages.save(PRINTED_LANGUAGES_REFERENCE)
    return target


def build_inputs(reference_photo: Path | None = None) -> tuple[str, list[Path]]:
    if not PRINTED_LANGUAGES_REFERENCE.is_file():
        raise RuntimeError(
            f"missing printed SEE Languages crop: {PRINTED_LANGUAGES_REFERENCE}; run --prepare first"
        )
    card = {
        "visual_descriptor_mode": "EXPLICIT",
        "content": BENCHMARK_CONTENT,
    }
    prompt = build_prompt_text(card)
    prompt += "\n" + "\n".join(
        (
            "BENCHMARK REFERENCE ROLES:",
            "Image [1] is the approved current VERB/COMMON geometry and type-icon template.",
            "Image [2] is the closest corrected SEE pilot. Preserve its visible white pencil icon in the navy circle, all fifteen stat pips, exact 2/4/1 fills, compact panel geometry, crisp typography, and symbolic non-portrait art direction.",
            "Image [3] is the clean original Babel SEE face: preserve its restrained print finish and Babel visual vocabulary.",
            "Image [4] is only the Languages-region crop from the operator-accepted printed SEE benchmark. It is authoritative only for that compact panel's hierarchy, line breaks, and density; do not infer or change any other card region from it.",
            "Render a wholly new full-card raster. Do not composite, trace, paste, or overlay visible pixels from any reference.",
            "TYPE CONTRACT: VERB must show a clearly visible white pencil icon centered inside the navy circular medallion at upper left. Do not omit the medallion or icon.",
            "STAT CONTRACT: render exactly five circular pips per stat. LORE is exactly 2 navy filled plus 3 empty. CONTEXT is exactly 4 navy filled plus 1 empty. COMPLEXITY is exactly 1 navy filled plus 4 empty.",
            "In the art panel, depict only the eye-like cloud opening, light, water, and atmosphere. No human head, face, portrait, or crowd.",
            "The Languages panel is compact. Print HEBREW/ARAMAIC and GREEK exactly; native scripts large; bare italic transliterations beneath; then OT Refs: and NT Refs: with the exact supplied reference strings.",
            "LANGUAGES PANEL VERBATIM GLYPH CONTRACT:",
            "Print the Hebrew transliteration exactly as ra'ah. The character between a and a is the straight ASCII apostrophe U+0027; never substitute a curly apostrophe, right single quotation mark, prime, or Hebrew punctuation.",
            "Print the Greek transliteration exactly as horaō, including the final Latin small letter o with macron U+014D.",
            "Render the OT reference block as exactly these two physical lines:",
            OT_REFS_LINES[0],
            OT_REFS_LINES[1],
            "Render the NT reference block as exactly these two physical lines:",
            NT_REFS_LINES[0],
            NT_REFS_LINES[1],
            "Every bullet above is the literal bullet character U+2022 and is required. A line break never replaces a bullet. Count three bullets in each complete reference block.",
        )
    )
    refs = [TEMPLATE, CLOSE_PILOT, CANONICAL_SEE, PRINTED_LANGUAGES_REFERENCE]
    CASE.mkdir(parents=True, exist_ok=True)
    (CASE / "card.json").write_text(
        json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (CASE / "prompt.txt").write_text(prompt + "\n", encoding="utf-8")
    request = {
        "semantic_source": "operator-accepted printed SEE benchmark",
        "visual_descriptor_version": 2,
        "model": image_model(),
        "workflow": "hypertext.gemini.style.generate_with_styles",
        "aspect_ratio": "2:3",
        "image_size": "2K",
        "response_modalities": ["IMAGE"],
        "full_face_generation_only": True,
        "references": [
            {"role": role, "path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
            for role, path in zip(
                (
                    "geometry",
                    "closest corrected SEE structure and typography",
                    "clean original Babel SEE art/style",
                    "operator-accepted printed SEE Languages-region benchmark",
                ),
                refs,
                strict=True,
            )
        ],
    }
    if reference_photo is not None:
        request["operator_reference_photo_sha256"] = sha256(reference_photo)
    (CASE / "request.json").write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")
    return prompt, refs


def archive_existing(path: Path) -> None:
    if not path.exists():
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive = path.parent / f"superseded-{stamp}"
    archive.mkdir()
    shutil.move(str(path), archive / path.name)
    metadata = path.with_name("generation.json")
    if metadata.exists():
        shutil.move(str(metadata), archive / metadata.name)


def generate(reference_photo: Path | None, force: bool) -> None:
    prompt, refs = build_inputs(reference_photo)
    target = output_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    if force:
        archive_existing(target)
    if target.exists():
        raise RuntimeError(f"pilot already exists: {target}; use --force for a versioned replacement")
    generate_with_styles(
        prompt,
        [str(path) for path in refs],
        str(target),
        model=image_model(),
        target_rarity="COMMON",
    )


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    name = "KaTeX_Main-Bold.ttf" if bold else "KaTeX_Main-Regular.ttf"
    path = ROOT / "operator_review/assets" / name
    return ImageFont.truetype(path, size) if path.exists() else ImageFont.load_default()


def comparison() -> Path:
    paths = [PRINTED_REFERENCE, CANONICAL_SEE, REJECTED_ANALOG, output_path()]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise RuntimeError("comparison inputs missing: " + ", ".join(missing))
    labels = (
        ("PRINTED BENCHMARK", "Operator-accepted SEE card and Languages treatment"),
        ("ORIGINAL BABEL SEE", "Closest clean source to the accepted printed reference"),
        ("REJECTED PATH", "Synthetic content and portrait-heavy drift"),
        ("CORRECTED PILOT", "SEE semantic contract + visual descriptor v2; not yet accepted"),
    )
    tile = (420, 630)
    gap = 36
    margin = 44
    header = 96
    footer = 92
    canvas = Image.new(
        "RGB",
        (margin * 2 + tile[0] * len(paths) + gap * (len(paths) - 1), header + tile[1] + footer),
        "#111628",
    )
    draw = ImageDraw.Draw(canvas)
    draw.text((margin, 22), "BABEL SEE — ACCEPTED vs REJECTED vs CORRECTED", font=_font(28, True), fill="#f1dfad")
    for index, (path, (title, note)) in enumerate(zip(paths, labels, strict=True)):
        x = margin + index * (tile[0] + gap)
        image = Image.open(path).convert("RGB")
        image = ImageOps.fit(image, tile, Image.Resampling.LANCZOS)
        canvas.paste(image, (x, header))
        draw.rectangle((x, header, x + tile[0] - 1, header + tile[1] - 1), outline="#d8bd78", width=2)
        draw.text((x, header + tile[1] + 12), title, font=_font(20, True), fill="#f1dfad")
        draw.text((x, header + tile[1] + 40), note, font=_font(14), fill="#e9e3d5")
    target = OUT / "comparison-accepted-rejected-corrected.png"
    canvas.save(target)
    return target


def validate(reference_photo: Path | None) -> dict:
    prompt, refs = build_inputs(reference_photo)
    exact = json.loads(prompt.split("EXACT_CANONICAL_CONTENT_JSON=", 1)[1].split("\n", 1)[0])
    checks = {
        "descriptor_v2": "HYPERTEXT VISUAL DESCRIPTOR v2" in prompt,
        "exact_content_round_trip": exact == BENCHMARK_CONTENT,
        "printed_language_headers": "LEFT header is exactly HEBREW/ARAMAIC" in prompt,
        "bare_transliterations": "bare italic HEBREW_TRANSLIT" in prompt,
        "verbatim_transliteration_glyphs": (
            "straight ASCII apostrophe U+0027" in prompt
            and "final Latin small letter o with macron U+014D" in prompt
        ),
        "verbatim_reference_lines": all(line in prompt for line in (*OT_REFS_LINES, *NT_REFS_LINES)),
        "literal_reference_bullet_count": prompt.count("literal bullet character U+2022") == 1,
        "type_icon_contract": "white pencil icon centered inside the navy circular medallion" in prompt,
        "stat_contract": "LORE is exactly 2 navy filled plus 3 empty" in prompt,
        "face_avoidance": "no recognizable human faces" in prompt and "no portrait likenesses" in prompt,
        "references_present": all(path.is_file() for path in refs),
        "output_present": output_path().is_file(),
    }
    if output_path().is_file():
        with Image.open(output_path()) as image:
            checks["output_dimensions"] = image.size == (1024, 1536)
    report = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "human_review_required": True,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["status"] != "PASS":
        raise RuntimeError("SEE benchmark validation failed")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-photo", type=Path)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--compare", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        if args.reference_photo is None:
            parser.error("--prepare requires --reference-photo")
        print(crop_reference(args.reference_photo))
    if args.generate:
        generate(args.reference_photo, args.force)
    if args.compare:
        print(comparison())
    if args.validate:
        validate(args.reference_photo)
    if not (args.prepare or args.generate or args.compare or args.validate):
        parser.error("choose --prepare, --generate, --compare, and/or --validate")


if __name__ == "__main__":
    main()
