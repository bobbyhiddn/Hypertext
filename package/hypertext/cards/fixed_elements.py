"""Deterministic stamping of the fixed card elements.

Principle (2026-08-28): anything that is pure data rendered in a fixed glyph is
set deterministically rather than asked of the image model. The model still
paints everything variable - art, title, gloss, ability, verses, languages,
trivia - and this module then stamps, from the hash-verified template and a
matched font, the elements that must be identical across the set:

* the stat pip row (template ring glyphs; filled interiors painted flat navy),
* the type pill (block copied from the card's own type-by-rarity template,
  word set from CARD_TYPE),
* the collector number and the series footer (rendered in Liberation Serif,
  the closest metric match to the template typography).

Every region is registered locally against the template (small dx/dy search)
so the stamps land on the face's actual frame, and a provenance record is
written beside the output.

Not stamped: the rarity chip (word, diamond) and the +CARD cost glyphs. The
model paints those better than a flat template copy, so they stay Gemini output
and are verified instead by rarity_chip_gate and cost_indicator_gate
(decision 2026-08-28 after the BRICK proof).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat

from hypertext.cards.stat_pip_gate import ROW_NAMES, _ROW_X, _ROW_Y
from hypertext.cards.template_matrix import resolve_template_record

CONTRACT = "hypertext.fixed-elements/v1"
FACE_SIZE = (1024, 1536)
PIP_RING = 27          # half-size of a pip glyph patch
PIP_FILL_RADIUS = 21   # interior painted flat navy for a filled pip
NAVY = (26, 34, 64)
NUMBER_COLOR = (44, 34, 74)
FOOTER_COLOR = (156, 146, 180)
FONT_FAMILY = "Liberation Serif"
PILL_FONT_FAMILY = "Liberation Serif:bold"
PILL_TEXT_COLOR = (238, 226, 228)

# Face-space regions (template coordinates after scaling to FACE_SIZE).
REGION_NUMBER = (58, 24, 140, 66)
REGION_PILL_SEARCH = (142, 24, 420, 84)
REGION_FOOTER_TEXT = (56, 1472, 700, 1514)
REGION_FOOTER_BLANK = (730, 1470, 960, 1518)
REGION_PARCHMENT = (290, 22, 380, 74)
SEARCH = 14


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def font_path(family: str = FONT_FAMILY) -> Path:
    out = subprocess.run(["fc-match", "-f", "%{file}", family], capture_output=True, text=True, check=True).stdout.strip()
    path = Path(out)
    if not path.is_file():
        raise RuntimeError(f"font not found for {family!r}: {out}")
    return path


def load_template(card_type: str, rarity: str) -> tuple[Image.Image, dict[str, Any]]:
    record = resolve_template_record(card_type.upper(), rarity.upper(), verify=True)
    image = Image.open(record["path"]).convert("RGB").resize(FACE_SIZE, Image.Resampling.LANCZOS)
    return image, record


def register(face: Image.Image, template: Image.Image, box: tuple[int, int, int, int], search: int = SEARCH) -> tuple[int, int]:
    """Find the (dx, dy) that best aligns the face to the template inside box."""
    ref = template.crop(box).convert("L")
    best, best_off = None, (0, 0)
    w, h = ref.size
    for dy in range(-search, search + 1, 2):
        for dx in range(-search, search + 1, 2):
            cand = face.crop((box[0] + dx, box[1] + dy, box[0] + dx + w, box[1] + dy + h)).convert("L")
            score = ImageStat.Stat(ImageChops.difference(ref, cand)).mean[0]
            if best is None or score < best:
                best, best_off = score, (dx, dy)
    # refine to single-pixel precision around the coarse optimum
    cx, cy = best_off
    for dy in range(cy - 1, cy + 2):
        for dx in range(cx - 1, cx + 2):
            cand = face.crop((box[0] + dx, box[1] + dy, box[0] + dx + w, box[1] + dy + h)).convert("L")
            score = ImageStat.Stat(ImageChops.difference(ref, cand)).mean[0]
            if score < best:
                best, best_off = score, (dx, dy)
    return best_off


def _dark_bbox(image: Image.Image, box: tuple[int, int, int, int], cutoff: int = 110) -> tuple[int, int, int, int] | None:
    region = image.crop(box).convert("L").point(lambda v: 255 if v < cutoff else 0)
    bbox = region.getbbox()
    if not bbox:
        return None
    return (box[0] + bbox[0], box[1] + bbox[1], box[0] + bbox[2], box[1] + bbox[3])


def _glyph_mask(patch: Image.Image, threshold: int = 48, feather: int = 1, min_luma: int = 0) -> Image.Image:
    """Mask of the pixels that differ from the patch's own background (its border ring)."""
    w, h = patch.size
    def median_of(points):
        return tuple(sorted(c[i] for c in points)[len(points) // 2] for i in range(3))
    # Two candidate backgrounds: the left column (parchment side) and the right
    # column (navy corner block on the rarity chip); a pixel is glyph only if
    # it differs from both, so a navy block is never re-pasted over the face's.
    bgs = [median_of([patch.getpixel((0, y)) for y in range(h)]), median_of([patch.getpixel((w - 1, y)) for y in range(h)])]
    mask = Image.new("L", patch.size, 0)
    px, mp = patch.load(), mask.load()
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if (r * 299 + g * 587 + b * 114) // 1000 < min_luma:
                continue
            if all(abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > threshold for bg in bgs):
                mp[x, y] = 255
    from PIL import ImageFilter
    mask = mask.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(5))
    if feather:
        mask = mask.filter(ImageFilter.GaussianBlur(feather))
    return mask


def _light_bbox(image: Image.Image, box: tuple[int, int, int, int], margin: int = 40) -> tuple[int, int, int, int] | None:
    region = image.crop(box).convert("L")
    base = ImageStat.Stat(region).median[0]
    bright = region.point(lambda v: 255 if v > base + margin else 0)
    bbox = bright.getbbox()
    if not bbox:
        return None
    return (box[0] + bbox[0], box[1] + bbox[1], box[0] + bbox[2], box[1] + bbox[3])


def stamp_stat_pips(face: Image.Image, template: Image.Image, counts: tuple[int, int, int], offset: tuple[int, int]) -> None:
    dx, dy = offset
    for row_x, count in zip(_ROW_X, counts):
        for slot, x in enumerate(row_x, start=1):
            patch = template.crop((x - PIP_RING, _ROW_Y - PIP_RING, x + PIP_RING, _ROW_Y + PIP_RING)).copy()
            if slot <= count:
                ImageDraw.Draw(patch).ellipse(
                    (PIP_RING - PIP_FILL_RADIUS, PIP_RING - PIP_FILL_RADIUS, PIP_RING + PIP_FILL_RADIUS, PIP_RING + PIP_FILL_RADIUS),
                    fill=NAVY,
                )
            face.paste(patch, (x + dx - PIP_RING, _ROW_Y + dy - PIP_RING))


def stamp_template_region(face: Image.Image, template: Image.Image, box: tuple[int, int, int, int], offset: tuple[int, int], min_luma: int = 0) -> None:
    """Paste only the template's glyph pixels (pill, chip, diamond, cost glyphs), never its parchment."""
    dx, dy = offset
    patch = template.crop(box)
    face.paste(patch, (box[0] + dx, box[1] + dy), _glyph_mask(patch, min_luma=min_luma))


def _median_rgb(points: list[tuple[int, int, int]]) -> tuple[int, int, int]:
    return tuple(sorted(c[i] for c in points)[len(points) // 2] for i in range(3))


def stamp_pill_text(face: Image.Image, template: Image.Image, pill_box: tuple[int, int, int, int], offset: tuple[int, int], word: str, font: ImageFont.FreeTypeFont) -> None:
    """Repaint the pill interior in the template's pill navy and set the type
    word from the card record. The TITLE composed templates carry a NOUN pill
    (template-package defect found 2026-08-28), so the word never comes from
    the template image itself."""
    dx, dy = offset
    tp = template.crop(pill_box); L = tp.convert("L")
    w, h = tp.size
    navy = [tp.getpixel((x, y)) for y in range(h) for x in range(w) if L.getpixel((x, y)) < 80]
    fill = tuple(sorted(c[i] for c in navy)[len(navy) // 2] for i in range(3)) if navy else NAVY
    box = (pill_box[0] + dx + 4, pill_box[1] + dy + 4, pill_box[2] + dx - 4, pill_box[3] + dy - 4)
    draw = ImageDraw.Draw(face)
    draw.rounded_rectangle(box, radius=(box[3] - box[1]) // 2, fill=fill)
    tb = draw.textbbox((0, 0), word, font=font)
    tx = (box[0] + box[2]) // 2 - (tb[2] - tb[0]) // 2 - tb[0]
    ty = (box[1] + box[3]) // 2 - (tb[3] - tb[1]) // 2 - tb[1]
    draw.text((tx, ty), word, font=font, fill=PILL_TEXT_COLOR)


def stamp_number(face: Image.Image, template: Image.Image, number: str, offset: tuple[int, int], font: ImageFont.FreeTypeFont, pill_box: tuple[int, int, int, int] | None = None) -> tuple[int, int, int, int]:
    dx, dy = offset
    x0, y0, x1, y1 = REGION_NUMBER
    if pill_box:
        x1 = min(x1 + 6, pill_box[0] - 3)
    # Cover the model's number with the face's OWN parchment from just right of
    # the pill. The pill's width depends on the type word (ADJECTIVE reaches
    # past x=320), so the source sits relative to the measured pill, never at a
    # fixed x - a fixed patch once pasted the tail of "ADJECTIVE" over the number.
    if pill_box:
        src = (pill_box[2] + 8 + dx, pill_box[1] + 6 + dy, pill_box[2] + 88 + dx, pill_box[3] - 6 + dy)
    else:
        src = (REGION_PARCHMENT[0] + dx, REGION_PARCHMENT[1] + dy, REGION_PARCHMENT[2] + dx, REGION_PARCHMENT[3] + dy)
    parchment = face.crop(src).resize((x1 - x0, y1 - y0), Image.Resampling.LANCZOS)
    from PIL import ImageFilter
    soft = Image.new("L", parchment.size, 0)
    ImageDraw.Draw(soft).rectangle((1, 1, parchment.width - 2, parchment.height - 2), fill=255)
    soft = soft.filter(ImageFilter.GaussianBlur(1.5))
    face.paste(parchment, (x0 + dx, y0 + dy), soft)
    anchor = _dark_bbox(template, (x0, y0, x1, y1)) or (x0, y0, x1, y1)
    text = f"#{number}"
    draw = ImageDraw.Draw(face)
    # Fit the font so the digits stand as tall as the template's #XXX.
    target_h = anchor[3] - anchor[1]
    size = 40
    for _ in range(6):
        tb = draw.textbbox((0, 0), text, font=ImageFont.truetype(font.path, size))
        h = tb[3] - tb[1]
        if abs(h - target_h) <= 1:
            break
        size = max(16, int(round(size * target_h / max(h, 1))))
    font = ImageFont.truetype(font.path, size)
    tb = draw.textbbox((0, 0), text, font=font)
    text_h = tb[3] - tb[1]
    tx = anchor[0] + dx - tb[0]
    center_y = ((pill_box[1] + pill_box[3]) // 2 + dy) if pill_box else (anchor[1] + anchor[3]) // 2 + dy
    ty = center_y - text_h // 2 - tb[1]
    draw.text((tx, ty), text, font=font, fill=NUMBER_COLOR)
    return (anchor[0] + dx, center_y - text_h // 2, anchor[2] + dx, center_y + text_h // 2)


def stamp_footer(face: Image.Image, template: Image.Image, series: str, offset: tuple[int, int], font: ImageFont.FreeTypeFont) -> tuple[int, int, int, int]:
    dx, dy = offset
    x0, y0, x1, y1 = REGION_FOOTER_TEXT
    # Cover the model's footer text with the face's OWN band pixels (same rows, text-free right side), tiled.
    tile = face.crop((REGION_FOOTER_BLANK[0] + dx, y0 + dy, REGION_FOOTER_BLANK[2] + dx, y1 + dy))
    x = x0 + dx
    while x < x1 + dx:
        face.paste(tile, (x, y0 + dy))
        x += tile.width
    draw = ImageDraw.Draw(face)
    anchor = _light_bbox(template, REGION_FOOTER_TEXT) or REGION_FOOTER_TEXT
    # The face's band may sit higher or lower than the template's: find its
    # top (first parchment row scanning upward) and bottom (frame line) at a
    # text-free column and center the text between them.
    # Start from where the template puts the text (registered), then expand
    # through the face's dark band rows around it. If the band merges into the
    # outer frame at the probe column (no light rule between them), the run is
    # implausibly tall and the registered template position is used as is.
    probe_x = 810 + dx
    col = face.convert("L")
    start = (anchor[1] + anchor[3]) // 2 + dy
    top = start
    while top > 1380 and col.getpixel((probe_x, top - 1)) < 110:
        top -= 1
    bottom = start
    while bottom < 1535 and col.getpixel((probe_x, bottom + 1)) < 110:
        bottom += 1
    if bottom - top > 70:
        band_top, band_bottom = start - 24, start + 24
    else:
        band_top, band_bottom = top, bottom
    text = f"SERIES: {series}"
    target_h = anchor[3] - anchor[1]
    size = 27
    for _ in range(6):
        tb = draw.textbbox((0, 0), text, font=ImageFont.truetype(font.path, size))
        h = tb[3] - tb[1]
        if abs(h - target_h) <= 1:
            break
        size = max(12, int(round(size * target_h / max(h, 1))))
    font = ImageFont.truetype(font.path, size)
    tb = draw.textbbox((0, 0), text, font=font)
    text_h = tb[3] - tb[1]
    tx = anchor[0] + dx - tb[0]
    center_y = (band_top + band_bottom) // 2
    ty = center_y - text_h // 2 - tb[1]
    draw.text((tx, ty), text, font=font, fill=FOOTER_COLOR)
    return (anchor[0] + dx, center_y - text_h // 2, anchor[2] + dx, center_y + text_h // 2)


def apply_fixed_elements(card_dir: str | Path, *, candidate_path: str | Path | None = None, write: bool = True) -> dict[str, Any]:
    """Stamp every fixed element onto the card's rendered face and record provenance."""
    card_dir = Path(card_dir)
    card = json.loads((card_dir / "card.json").read_text(encoding="utf-8"))
    content = card["content"]
    face_path = Path(candidate_path) if candidate_path else card_dir / "outputs" / "card_1024x1536.png"
    before_sha = _sha256(face_path)
    face = Image.open(face_path).convert("RGB")
    if face.size != FACE_SIZE:
        raise RuntimeError(f"face must be {FACE_SIZE}, got {face.size}")
    template, record = load_template(content["CARD_TYPE"], content["RARITY_TEXT"])
    fpath = font_path()
    number_font = ImageFont.truetype(str(fpath), 40)
    footer_font = ImageFont.truetype(str(fpath), 27)
    pill_font = ImageFont.truetype(str(font_path(PILL_FONT_FAMILY)), 28)

    pip_box = (_ROW_X[0][0] - 40, _ROW_Y - 40, _ROW_X[2][4] + 40, _ROW_Y + 40)
    regions: dict[str, Any] = {}
    off = register(face, template, pip_box)
    counts = tuple(int(content[name]) for name in ROW_NAMES)
    stamp_stat_pips(face, template, counts, off)
    regions["stat_pips"] = {"box": pip_box, "offset": off, "counts": counts}

    pill_box = _dark_bbox(template, REGION_PILL_SEARCH)
    if pill_box:
        pill_box = (pill_box[0] - 6, pill_box[1] - 6, pill_box[2] + 6, pill_box[3] + 6)
        off = register(face, template, pill_box)
        stamp_template_region(face, template, pill_box, off)
        stamp_pill_text(face, template, pill_box, off, str(content["CARD_TYPE"]).upper(), pill_font)
        regions["type_pill"] = {"box": pill_box, "offset": off, "text": str(content["CARD_TYPE"]).upper()}

    # The rarity chip is verified by hypertext.cards.rarity_chip_gate, never stamped:
    # the model paints it better than a template copy (decision 2026-08-28).

    off = register(face, template, (REGION_NUMBER[0], REGION_NUMBER[1], REGION_PILL_SEARCH[2], REGION_NUMBER[3]))
    regions["number"] = {"box": stamp_number(face, template, str(content["NUMBER"]), off, number_font, pill_box), "offset": off, "text": f"#{content['NUMBER']}"}

    off = register(face, template, (0, 1440, 1024, 1536))
    regions["footer"] = {"box": stamp_footer(face, template, str(content["SERIES"]), off, footer_font), "offset": off, "text": f"SERIES: {content['SERIES']}"}

    if write:
        face.save(face_path, format="PNG")
    provenance = {
        "contract": CONTRACT,
        "template": {"path": record["repo_path"], "sha256": record.get("sha256") or _sha256(Path(record["path"]))},
        "font": {"family": FONT_FAMILY, "path": str(fpath), "sha256": _sha256(fpath)},
        "regions": regions,
        "face_sha256_before": before_sha,
        "face_sha256_after": _sha256(face_path) if write else None,
    }
    if write:
        (card_dir / "outputs" / "fixed-elements.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    return provenance
