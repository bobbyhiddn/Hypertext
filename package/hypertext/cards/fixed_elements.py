"""Deterministic stamping of the fixed card elements.

Principle (2026-08-28): anything that is pure data rendered in a fixed glyph is
set deterministically rather than asked of the image model. The model still
paints everything variable - art, title, gloss, ability, verses, languages,
trivia - and this module then stamps, from the hash-verified template and a
matched font, the elements that must be identical across the set:

* the stat pip row (template ring glyphs; filled interiors painted flat navy),
* the type pill and the rarity chip with its cost glyphs (copied from the
  card's own type-by-rarity template),
* the collector number and the series footer (rendered in Liberation Serif,
  the closest metric match to the template typography).

Every region is registered locally against the template (small dx/dy search)
so the stamps land on the face's actual frame, and a provenance record is
written beside the output.
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
REGION_CHIP = (736, 8, 1010, 112)
CHIP_GLYPH_LUMA = 110   # chip word / diamond pixels are lighter than this; the block is < 70
CHIP_WORD_PAD = 28   # rarity word inset from the chip block's left edge (COMMON/RARE/GLORIOUS templates)
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


def _prefill_chip_block(face: Image.Image, template: Image.Image, box: tuple[int, int, int, int], offset: tuple[int, int]) -> None:
    """Paint the face's chip block flat in its own navy (median of its dark pixels)
    wherever the template's block is navy, erasing the model's chip glyphs before
    the template's are stamped. Parchment and cost-glyph areas are untouched."""
    dx, dy = offset
    tpatch = template.crop(box)
    fbox = (box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy)
    fpatch = face.crop(fbox)
    tl, fl = tpatch.convert("L"), fpatch.convert("L")
    w, h = tpatch.size
    dark = [fpatch.getpixel((x, y)) for y in range(h) for x in range(w) if tl.getpixel((x, y)) < 70 and fl.getpixel((x, y)) < 90]
    if len(dark) < 50:
        return
    navy = tuple(sorted(c[i] for c in dark)[len(dark) // 2] for i in range(3))
    block = tl.point(lambda v: 255 if v < 70 else 0)
    from PIL import ImageFilter
    block = block.filter(ImageFilter.MinFilter(3))   # stay inside the block edge
    fill = Image.new("RGB", (w, h), navy)
    face.paste(fill, fbox[:2], block)


def _median_rgb(points: list[tuple[int, int, int]]) -> tuple[int, int, int]:
    return tuple(sorted(c[i] for c in points)[len(points) // 2] for i in range(3))


def chip_geometry(patch: Image.Image) -> dict[str, Any] | None:
    """Measure the rarity chip inside a template (or face) patch: the navy block,
    the rarity word's glyph run, and the diamond, all in patch coordinates.

    The block is the tallest band of mostly-dark rows that does not start at the
    patch edge (the card's frame lines do); the light runs inside it are the word
    (all but the last) and the diamond (the last). `clipped` is true when the
    word starts short of the set's left inset - the UNCOMMON composed templates
    ship that way (template-package defect, 2026-08-28)."""
    L = patch.convert("L")
    w, h = patch.size
    px = L.load()
    lefts_all = []
    for y in range(h):
        dark = [x for x in range(w) if px[x, y] < 70]
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
    upper = [lefts_all[y] for y in range(y0, y0 + max(6, (y1 - y0) * 6 // 10))]
    x0 = sorted(upper)[len(upper) // 2]
    x1 = w - 12   # the block runs into the right frame; the outline lives beyond this
    # Only rows where the block is at full width count (its lower-left corner is bevelled).
    full = [y for y in range(y0, y1) if lefts_all[y] is not None and lefts_all[y] <= x0 + 3]
    ys0, ys1 = min(full) + 2, max(full) - 1
    cols = [any(px[x, y] > CHIP_GLYPH_LUMA for y in range(ys0, ys1)) for x in range(w)]
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
    diamond = tuple(light_runs[-1])
    word = (light_runs[0][0], light_runs[-2][1])
    rows = [y for y in range(ys0 - 1, ys1 + 1) if any(px[x, y] > CHIP_GLYPH_LUMA for x in range(word[0], word[1]))]
    word_rows = (min(rows), max(rows) + 1) if rows else (y0, y1)
    return {
        "block": (x0, y0, x1, y1),
        "word": word,
        "word_rows": word_rows,
        "diamond": diamond,
        "gap": diamond[0] - word[1],
        "left_pad": word[0] - x0,
        "clipped": word[0] - x0 < CHIP_WORD_PAD - 8,
    }


def _fit_font(path: Path, text: str, target_height: int, lo: int = 14, hi: int = 60) -> ImageFont.FreeTypeFont:
    best, best_err = None, None
    for size in range(lo, hi + 1):
        font = ImageFont.truetype(str(path), size)
        bb = font.getbbox(text)
        err = abs((bb[3] - bb[1]) - target_height)
        if best is None or err < best_err:
            best, best_err = font, err
    return best


def correct_chip_patch(tpatch: Image.Image, word: str, font_file: Path) -> tuple[Image.Image, dict[str, Any]]:
    """Return a copy of the template chip patch whose rarity word sits inside
    the block at the set's inset. When the template's own word is clipped, the
    block is extended to the left (edge strip and an interior column cloned from
    the template) and the word is re-set in the matched font at the template's
    glyph height, colour, and cap line. Otherwise the patch is returned untouched."""
    geo = chip_geometry(tpatch)
    info: dict[str, Any] = {"word": word, "word_rendered": False, "block_extended_px": 0}
    if not geo or not geo["clipped"]:
        return tpatch.copy(), info
    bx0, by0, bx1, by1 = geo["block"]
    w, h = tpatch.size
    wy0, wy1 = geo["word_rows"]
    font = _fit_font(font_file, word, wy1 - wy0)
    tb = font.getbbox(word)
    text_w = tb[2] - tb[0]
    gap = max(geo["gap"], 6)
    text_left = geo["diamond"][0] - gap - text_w
    new_left = text_left - CHIP_WORD_PAD
    delta = max(0, bx0 - new_left)
    if new_left < 6:
        raise RuntimeError(f"chip region too narrow to extend the block by {delta}px")
    out = tpatch.copy()
    band = (max(0, by0 - 1), min(h, by1 + 4))
    edge = tpatch.crop((bx0 - 5, band[0], bx0 + 3, band[1]))
    column = tpatch.crop((bx0 + 20, band[0], bx0 + 21, band[1]))
    # Interior first (erases the old word and the clipped fragment), then the edge.
    for x in range(new_left + 3, geo["diamond"][0] - 3):
        out.paste(column, (x, band[0]))
    out.paste(edge, (new_left - 5, band[0]))
    lum = tpatch.convert("L").load()
    src = tpatch.load()
    light = [src[x, y] for y in range(wy0, wy1) for x in range(geo["word"][0], geo["word"][1]) if lum[x, y] > CHIP_GLYPH_LUMA]
    colour = _median_rgb(light) if light else (190, 184, 204)
    ImageDraw.Draw(out).text((text_left - tb[0], wy0 - tb[1]), word, font=font, fill=colour)
    info.update({"word_rendered": True, "block_extended_px": delta, "font_size": font.size, "template_defect": "rarity word clipped by the chip block"})
    return out, info


def stamp_chip(face: Image.Image, template: Image.Image, box: tuple[int, int, int, int], offset: tuple[int, int], word: str = "", font_file: Path | None = None) -> dict[str, Any]:
    """Stamp the whole rarity chip (block, word, diamond, cost glyphs) from the
    template, with the block's navy recolored to the face's own navy so the
    model's chip is fully covered and the block edges merge into the frame.
    A clipped template word is re-set inside a widened block (see
    correct_chip_patch), and whatever the model painted of its own chip outside
    the stamped chip is covered with the face's own parchment."""
    dx, dy = offset
    tpatch, info = correct_chip_patch(template.crop(box), word, font_file or font_path())
    fbox = (box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy)
    fpatch = face.crop(fbox)
    tl, fl = tpatch.convert("L"), fpatch.convert("L")
    w, h = tpatch.size
    dark = [fpatch.getpixel((x, y)) for y in range(h) for x in range(w) if tl.getpixel((x, y)) < 70 and fl.getpixel((x, y)) < 90]
    if len(dark) >= 50:
        navy = _median_rgb(dark)
        tp = tpatch.load()
        for y in range(h):
            for x in range(w):
                if tl.getpixel((x, y)) < 70:
                    tp[x, y] = navy
    # Everything that is not the template's parchment (left-edge background) is
    # part of the chip: the block, its word, the diamond, and any cost glyphs.
    parch = _median_rgb([template.crop(box).getpixel((0, y)) for y in range(h)])
    mask = Image.new("L", (w, h), 0)
    src, mp = tpatch.load(), mask.load()
    for y in range(h):
        for x in range(w):
            r, g, b = src[x, y]
            if abs(r - parch[0]) + abs(g - parch[1]) + abs(b - parch[2]) > 48:
                mp[x, y] = 255
    from PIL import ImageFilter
    mask = mask.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(5))
    # Ghost cleanup: the model's chip may be wider than the stamped one. Any face
    # pixel in this region that is neither the face's parchment nor under the
    # stamp is covered with the face's own parchment from just left of the chip.
    src_box = (box[0] - 60 + dx, box[1] + dy, box[0] - 10 + dx, box[3] + dy)
    parch_src = face.crop(src_box)
    face_parch = _median_rgb([parch_src.getpixel((x, y)) for y in range(0, parch_src.height, 3) for x in range(0, parch_src.width, 3)])
    ghost = Image.new("L", (w, h), 0)
    fp, gp, cover = fpatch.load(), ghost.load(), mask.filter(ImageFilter.MaxFilter(5)).load()
    for y in range(h):
        for x in range(w):
            if cover[x, y]:
                continue
            r, g, b = fp[x, y]
            if abs(r - face_parch[0]) + abs(g - face_parch[1]) + abs(b - face_parch[2]) > 90:
                gp[x, y] = 255
    ghost = ghost.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1))
    tile = Image.new("RGB", (w, h))
    for x in range(0, w, parch_src.width):
        tile.paste(parch_src, (x, 0))
    face.paste(tile, fbox[:2], ghost)
    info["ghost_pixels"] = sum(1 for v in ghost.getdata() if v > 127)
    face.paste(tpatch, fbox[:2], mask.filter(ImageFilter.GaussianBlur(1)))
    return info


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
    # Cover the model's number with the face's OWN parchment from just right of the pill.
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

    off = register(face, template, REGION_CHIP)
    chip_info = stamp_chip(face, template, REGION_CHIP, off, str(content["RARITY_TEXT"]).title(), fpath)
    regions["rarity_chip"] = {"box": REGION_CHIP, "offset": off, **chip_info}

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
