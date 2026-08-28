"""Template-relative acceptance for the painted rarity chip.

Decision (2026-08-28): the rarity chip is verified, never stamped. The image
model paints the chip better than a template copy - soft gradient, doubled
outline, halo on the word - and a flat stamped chip reads as pasted on. So the
chip stays a Gemini output, and this gate makes it deterministic the other way:
it measures the chip on the candidate face and on the hash-verified canonical
template of the same type and rarity, and rejects the face when the block, the
rarity word, or the diamond disagree with the template's geometry and colour.
The +CARD cost glyphs below the chip are covered by the cost indicator gate.

Measured on the candidate and the template (patch coordinates inside
REGION_CHIP): the navy block (tallest band of mostly-dark rows that does not
start at the patch edge), the rarity word (light runs inside the block, all but
the last) and the diamond (the last light run).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageStat

CONTRACT = "hypertext.template-relative-rarity-chip-gate/v1"
REFERENCE_SIZE = (1024, 1536)
REGION_CHIP = (736, 8, 1010, 112)   # face-space; block, word, diamond and the frame corner
SEARCH = 14
BLOCK_LUMA = 70          # block pixels are darker than this
GLYPH_LUMA = 110         # word / diamond pixels are lighter than this
WORD_WIDTH_TOLERANCE = (-0.12, 0.16)   # painted "Uncommon" is up to 11% wider than the clipped template word
MIN_WORD_INSET = 6       # px between the block's left edge and the word (never clipped)
MIN_WORD_GAP = 5         # px between the word and the diamond
MAX_EXTRA_GAP = 25
CAP_HEIGHT_TOLERANCE = 0.35
DIAMOND_COLOUR_DISTANCE = 90.0
_RARITIES = ("COMMON", "UNCOMMON", "RARE", "GLORIOUS")

Box = tuple[int, int, int, int]


class RarityChipGateError(ValueError):
    """The candidate, card record, or canonical template cannot be evaluated."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _median_rgb(points: list[tuple[int, int, int]]) -> tuple[int, int, int]:
    return tuple(sorted(c[i] for c in points)[len(points) // 2] for i in range(3))


def _load(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB")
    if image.size != REFERENCE_SIZE:
        image = image.resize(REFERENCE_SIZE, Image.Resampling.LANCZOS)
    return image


def register(face: Image.Image, template: Image.Image, box: Box, search: int = SEARCH) -> tuple[int, int]:
    """Find the (dx, dy) that best aligns the face to the template inside box."""
    ref = template.crop(box).convert("L")
    w, h = ref.size
    best, best_off = None, (0, 0)
    for dy in range(-search, search + 1, 2):
        for dx in range(-search, search + 1, 2):
            cand = face.crop((box[0] + dx, box[1] + dy, box[0] + dx + w, box[1] + dy + h)).convert("L")
            score = ImageStat.Stat(ImageChops.difference(ref, cand)).mean[0]
            if best is None or score < best:
                best, best_off = score, (dx, dy)
    cx, cy = best_off
    for dy in range(cy - 1, cy + 2):
        for dx in range(cx - 1, cx + 2):
            cand = face.crop((box[0] + dx, box[1] + dy, box[0] + dx + w, box[1] + dy + h)).convert("L")
            score = ImageStat.Stat(ImageChops.difference(ref, cand)).mean[0]
            if score < best:
                best, best_off = score, (dx, dy)
    return best_off


def chip_geometry(patch: Image.Image) -> dict[str, Any] | None:
    """Measure block, rarity word and diamond inside a chip patch (patch coordinates)."""
    L = patch.convert("L")
    w, h = patch.size
    px = L.load()
    lefts_all: list[int | None] = []
    for y in range(h):
        dark = [x for x in range(w) if px[x, y] < BLOCK_LUMA]
        lefts_all.append(dark[0] if len(dark) >= 60 and dark[0] >= 20 else None)
    bands: list[list[int]] = []
    for y, left in enumerate(lefts_all):
        if left is not None:
            if bands and bands[-1][1] == y:
                bands[-1][1] = y + 1
            else:
                bands.append([y, y + 1])
    if not bands:
        return None
    y0, y1 = max(bands, key=lambda b: b[1] - b[0])
    if y1 - y0 < 12:
        return None
    upper = [lefts_all[y] for y in range(y0, y0 + max(6, (y1 - y0) * 6 // 10)) if lefts_all[y] is not None]
    x0 = sorted(upper)[len(upper) // 2]
    x1 = w - 12   # the block runs into the right frame; the outline lives beyond this
    full = [y for y in range(y0, y1) if lefts_all[y] is not None and lefts_all[y] <= x0 + 3]
    if len(full) < 8:
        return None
    ys0, ys1 = min(full) + 2, max(full) - 1
    cols = [any(px[x, y] > GLYPH_LUMA for y in range(ys0, ys1)) for x in range(w)]
    light_runs: list[list[int]] = []
    for x in range(x0 + 4, x1):
        if cols[x]:
            if light_runs and x - light_runs[-1][1] <= 6:
                light_runs[-1][1] = x + 1
            else:
                light_runs.append([x, x + 1])
    light_runs = [r for r in light_runs if r[1] - r[0] >= 8]   # drop outline slivers
    if len(light_runs) < 2:
        return None
    diamond = (light_runs[-1][0], light_runs[-1][1])
    word = (light_runs[0][0], light_runs[-2][1])
    rows = [y for y in range(ys0 - 1, ys1 + 1) if any(px[x, y] > GLYPH_LUMA for x in range(word[0], word[1]))]
    word_rows = (min(rows), max(rows) + 1) if rows else (ys0, ys1)
    src = patch.load()
    diamond_pixels = [src[x, y] for x in range(diamond[0], min(diamond[1], diamond[0] + 30)) for y in range(word_rows[0], word_rows[1]) if px[x, y] > GLYPH_LUMA]
    return {
        "block": (x0, y0, x1, y1),
        "word": word,
        "word_width": word[1] - word[0],
        "word_rows": word_rows,
        "cap_height": word_rows[1] - word_rows[0],
        "diamond": diamond,
        "diamond_colour": _median_rgb(diamond_pixels) if len(diamond_pixels) >= 20 else None,
        "gap": diamond[0] - word[1],
        "left_inset": word[0] - x0,
    }


def _distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def _sibling_diamond_colours(template_path: Path, rarity: str) -> dict[str, tuple[int, int, int]]:
    """Diamond colours of the other rarities' templates in the same type folder,
    for nearest-template classification of the painted diamond."""
    colours: dict[str, tuple[int, int, int]] = {}
    folder = template_path.parent.parent
    for other in _RARITIES:
        if other == rarity:
            continue
        candidate = folder / other.lower() / template_path.name
        if not candidate.is_file():
            continue
        geo = chip_geometry(_load(candidate).crop(REGION_CHIP))
        if geo and geo["diamond_colour"]:
            colours[other] = geo["diamond_colour"]
    return colours


def inspect_rarity_chip(candidate_path: Path, template_path: Path, card: dict[str, Any]) -> dict[str, Any]:
    """Reject a face whose painted rarity chip disagrees with the canonical template."""
    candidate_path, template_path = Path(candidate_path), Path(template_path)
    try:
        content = card["content"]
        rarity = str(content["RARITY_TEXT"]).upper()
        card_type = str(content["CARD_TYPE"]).upper()
    except (KeyError, TypeError) as exc:
        raise RarityChipGateError(f"card record lacks CARD_TYPE/RARITY_TEXT: {exc}") from exc
    if rarity not in _RARITIES:
        raise RarityChipGateError(f"unknown rarity {rarity!r}")
    if not candidate_path.is_file():
        raise RarityChipGateError(f"candidate missing: {candidate_path}")
    if not template_path.is_file():
        raise RarityChipGateError(f"template missing: {template_path}")

    face, template = _load(candidate_path), _load(template_path)
    expected = chip_geometry(template.crop(REGION_CHIP))
    if not expected:
        raise RarityChipGateError(f"canonical template chip could not be measured: {template_path}")
    offset = register(face, template, REGION_CHIP)
    box = (REGION_CHIP[0] + offset[0], REGION_CHIP[1] + offset[1], REGION_CHIP[2] + offset[0], REGION_CHIP[3] + offset[1])
    observed = chip_geometry(face.crop(box))

    defects: list[dict[str, Any]] = []
    if observed is None:
        defects.append({"code": "rarity-chip-missing", "detail": "no navy block with a word and a diamond inside the chip region"})
    else:
        lo, hi = WORD_WIDTH_TOLERANCE
        ratio = observed["word_width"] / expected["word_width"] - 1.0
        if not (lo <= ratio <= hi):
            defects.append({"code": "rarity-word-width", "detail": f"word width {observed['word_width']}px vs template {expected['word_width']}px ({ratio:+.0%}); wrong or missing rarity word"})
        if observed["left_inset"] < MIN_WORD_INSET:
            defects.append({"code": "rarity-word-clipped", "detail": f"word starts {observed['left_inset']}px from the block's left edge"})
        if observed["gap"] < MIN_WORD_GAP or observed["gap"] > expected["gap"] + MAX_EXTRA_GAP:
            defects.append({"code": "rarity-word-gap", "detail": f"word-to-diamond gap {observed['gap']}px vs template {expected['gap']}px"})
        cap = observed["cap_height"] / expected["cap_height"] - 1.0
        if abs(cap) > CAP_HEIGHT_TOLERANCE:
            defects.append({"code": "rarity-word-height", "detail": f"cap height {observed['cap_height']}px vs template {expected['cap_height']}px"})
        if observed["diamond_colour"] is None or expected["diamond_colour"] is None:
            defects.append({"code": "rarity-diamond-missing", "detail": "diamond glyph not found beside the word"})
        else:
            own = _distance(observed["diamond_colour"], expected["diamond_colour"])
            siblings = _sibling_diamond_colours(template_path, rarity)
            nearest = min(siblings.items(), key=lambda kv: _distance(observed["diamond_colour"], kv[1]), default=None)
            if own > DIAMOND_COLOUR_DISTANCE or (nearest and _distance(observed["diamond_colour"], nearest[1]) < own):
                detail = f"diamond colour {observed['diamond_colour']} is {own:.0f} from the {rarity} template"
                if nearest:
                    detail += f" and closer to {nearest[0]} {nearest[1]}"
                defects.append({"code": "rarity-diamond-colour", "detail": detail})

    return {
        "contract": CONTRACT,
        "passed": not defects,
        "defects": defects,
        "target": {"card_type": card_type, "rarity": rarity},
        "candidate": {"path": str(candidate_path), "sha256": _sha256(candidate_path)},
        "template": {"path": str(template_path), "sha256": _sha256(template_path)},
        "region": {"box": list(REGION_CHIP), "offset": list(offset)},
        "expected": {k: v for k, v in expected.items() if k != "block"},
        "observed": None if observed is None else {k: v for k, v in observed.items() if k != "block"},
    }


def defect_summary(report: dict[str, Any]) -> str:
    return "; ".join(f"{d['code']}: {d['detail']}" for d in report["defects"])


__all__ = ["CONTRACT", "REGION_CHIP", "RarityChipGateError", "chip_geometry", "inspect_rarity_chip", "defect_summary", "register"]
