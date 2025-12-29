#!/usr/bin/env python3
"""
Composite card generator for Hypertext.

Uses a static template image as the base, generates art-only via Gemini,
and renders all text programmatically for 100% consistent geometry.
"""
import argparse
import json
import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None
    ImageDraw = None
    ImageFont = None

# Card dimensions
CARD_WIDTH = 1024
CARD_HEIGHT = 1536

# Color palette (from style guide)
COLORS = {
    "navy": "#0B1F3B",
    "gold": "#C9A44C",
    "parchment": "#F3E7C8",
    "ink": "#111111",
    "orange_mythic": "#F28C28",
    "green_uncommon": "#2E8B57",
    "white": "#FFFFFF",
}

# Layout regions - measured from raw_template.png (1024x1536)
# Format varies: (x, y, w, h) for boxes, (center_x, y) for centered text
REGIONS = {
    # Header elements (top bar)
    "number_badge": (28, 22),               # x, y for "#001"
    "type_badge": (118, 22),                # x, y for "NOUN" (centered in badge)
    "rarity_icon": (895, 22),               # x, y for rarity icon center
    "rarity_text": (918, 18),               # x, y for rarity text

    # Title area (centered)
    "word_title": (512, 52),                # center_x, y for WORD
    "gloss_subtitle": (512, 105),           # center_x, y for gloss

    # Art panel (inner area where art goes)
    "art_panel": (58, 140, 908, 330),       # x, y, width, height

    # Stats row - labels and pips
    "stat_lore_label": (165, 488),          # center_x, y for "LORE"
    "stat_context_label": (512, 488),       # center_x, y for "CONTEXT"
    "stat_complexity_label": (858, 488),    # center_x, y for "COMPLEXITY"
    "pip_row_y": 522,                       # Y center for pip circles
    "pip_lore_x": 82,                       # Starting X for LORE pips (leftmost pip center)
    "pip_context_x": 428,                   # Starting X for CONTEXT pips
    "pip_complexity_x": 775,                # Starting X for COMPLEXITY pips
    "pip_spacing": 34,                      # Space between pip centers
    "pip_radius": 13,                       # Pip circle radius

    # Content panels - section headers and text areas
    # ABILITY box
    "ability_header": (512, 565),           # center_x, y for "ABILITY" label
    "ability_text": (65, 590, 894, 45),     # x, y, width, height for text

    # OT VERSE box
    "ot_header": (512, 648),                # center_x, y for "OT VERSE" label
    "ot_verse_text": (65, 673, 894, 38),    # x, y, width, height

    # NT VERSE box
    "nt_header": (512, 725),                # center_x, y for "NT VERSE" label
    "nt_verse_text": (65, 750, 894, 38),    # x, y, width, height

    # Greek/Hebrew split panel
    "greek_header": (270, 805),             # center_x, y for "GREEK" label
    "greek_word": (270, 835),               # center_x, y for Greek text
    "greek_translit": (270, 865),           # center_x, y for transliteration
    "nt_refs": (270, 892),                  # center_x, y for NT refs

    "hebrew_header": (754, 805),            # center_x, y for "HEB/ARAM" label
    "hebrew_word": (754, 835),              # center_x, y for Hebrew text
    "hebrew_translit": (754, 865),          # center_x, y for transliteration
    "ot_refs": (754, 892),                  # center_x, y for OT refs

    # Trivia box
    "trivia_header": (512, 935),            # center_x, y for "TRIVIA" label
    "trivia_area": (65, 960, 894, 110),     # x, y, width, height for bullets

    # Footer
    "series_text": (28, 1498),              # x, y for "SERIES: 2026-Q1"
}

# Rarity icon shapes and colors
RARITY_ICONS = {
    "COMMON": {"shape": "circle", "fill": COLORS["white"], "outline": COLORS["navy"]},
    "UNCOMMON": {"shape": "square", "fill": COLORS["green_uncommon"], "outline": COLORS["navy"]},
    "RARE": {"shape": "hexagon", "fill": COLORS["gold"], "outline": COLORS["navy"]},
    "GLORIOUS": {"shape": "rhombus", "fill": COLORS["orange_mythic"], "outline": COLORS["navy"]},
}


def _load_font(name: str, size: int):
    """Try to load a font, falling back to default if not found."""
    font_paths = [
        # Windows
        f"C:/Windows/Fonts/{name}.ttf",
        f"C:/Windows/Fonts/{name}.otf",
        # Common locations
        f"/usr/share/fonts/truetype/{name}.ttf",
        f"/usr/share/fonts/{name}.ttf",
        # Local fonts folder
        str(Path(__file__).parent.parent.parent / "fonts" / f"{name}.ttf"),
    ]

    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue

    # Try by name directly (system font)
    try:
        return ImageFont.truetype(name, size)
    except Exception:
        pass

    # Fallback to default
    try:
        return ImageFont.load_default()
    except Exception:
        return None


def _get_fonts():
    """Load all required fonts."""
    return {
        "title": _load_font("times", 52) or _load_font("Georgia", 52),
        "subtitle": _load_font("timesi", 24) or _load_font("Georgia-Italic", 24),
        "label": _load_font("timesbd", 16) or _load_font("Georgia-Bold", 16),
        "body": _load_font("times", 18) or _load_font("Georgia", 18),
        "small": _load_font("times", 14) or _load_font("Georgia", 14),
        "greek": _load_font("times", 22) or _load_font("Georgia", 22),
        "hebrew": _load_font("times", 22) or _load_font("Georgia", 22),
        "badge": _load_font("timesbd", 14) or _load_font("Georgia-Bold", 14),
    }


def draw_centered_text(draw, text: str, center_x: int, y: int, font, fill: str, max_width: int = None):
    """Draw text centered at a given X position."""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = center_x - text_width // 2
    draw.text((x, y), text, font=font, fill=fill)


def draw_left_text(draw, text: str, x: int, y: int, font, fill: str, max_width: int = None):
    """Draw text left-aligned, with optional wrapping."""
    if max_width and font:
        # Simple word wrap
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))

        line_height = font.size + 4 if hasattr(font, 'size') else 20
        for i, line in enumerate(lines):
            draw.text((x, y + i * line_height), line, font=font, fill=fill)
    else:
        draw.text((x, y), text, font=font, fill=fill)


def draw_stat_pips(draw, x: int, y: int, filled: int, total: int = 5):
    """Draw stat pips (filled circles for value, empty for remainder)."""
    spacing = REGIONS["pip_spacing"]
    radius = REGIONS["pip_radius"]

    for i in range(total):
        cx = x + i * spacing
        cy = y
        bbox = (cx - radius, cy - radius, cx + radius, cy + radius)

        if i < filled:
            # Filled pip: navy fill, gold outline
            draw.ellipse(bbox, fill=COLORS["navy"], outline=COLORS["gold"], width=2)
        else:
            # Empty pip: parchment fill, navy outline
            draw.ellipse(bbox, fill=COLORS["parchment"], outline=COLORS["navy"], width=2)


def draw_rarity_icon(draw, x: int, y: int, rarity: str, size: int = 20):
    """Draw the rarity icon shape."""
    config = RARITY_ICONS.get(rarity.upper(), RARITY_ICONS["COMMON"])
    shape = config["shape"]
    fill = config["fill"]
    outline = config["outline"]

    half = size // 2

    if shape == "circle":
        draw.ellipse((x - half, y - half, x + half, y + half), fill=fill, outline=outline, width=2)
    elif shape == "square":
        draw.rectangle((x - half, y - half, x + half, y + half), fill=fill, outline=outline, width=2)
    elif shape == "rhombus":
        # Diamond shape
        points = [(x, y - half), (x + half, y), (x, y + half), (x - half, y)]
        draw.polygon(points, fill=fill, outline=outline, width=2)
    elif shape == "hexagon":
        # Simple hexagon
        import math
        points = []
        for i in range(6):
            angle = math.pi / 6 + i * math.pi / 3
            px = x + half * math.cos(angle)
            py = y + half * math.sin(angle)
            points.append((px, py))
        draw.polygon(points, fill=fill, outline=outline, width=2)


def draw_debug_rects(draw, regions: dict):
    """Draw debug rectangles for all defined regions."""
    for name, region in regions.items():
        if len(region) == 4:  # x, y, w, h
            x, y, w, h = region
            draw.rectangle((x, y, x + w, y + h), outline="red", width=2)
            draw.text((x, y), name, fill="red")
        elif len(region) == 2:  # x, y
            x, y = region
            draw.ellipse((x - 5, y - 5, x + 5, y + 5), outline="blue", width=2)
            draw.text((x + 10, y), name, fill="blue")


def composite_card(
    template_path: str,
    art_path: str | None,
    out_path: str,
    content: dict,
    debug: bool = False,
) -> None:
    """
    Composite a card from template + art + content.

    Args:
        template_path: Path to the base template PNG (raw_template.png)
        art_path: Path to the generated art PNG (or None to leave art panel empty)
        out_path: Output path for the final card
        content: Dict with card content (WORD, GLOSS, ABILITY_TEXT, etc.)
        debug: If True, draw debug outlines instead of normal rendering
    """
    if Image is None:
        raise RuntimeError("Pillow is required. Install with: pip install Pillow")

    # Load template
    card = Image.open(template_path).convert("RGBA")
    if card.size != (CARD_WIDTH, CARD_HEIGHT):
        card = card.resize((CARD_WIDTH, CARD_HEIGHT), Image.Resampling.LANCZOS)

    draw = ImageDraw.Draw(card)
    fonts = _get_fonts()

    if debug:
        draw_debug_rects(draw, REGIONS)
        # Save output
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        card.save(out_path, "PNG")
        return

    # Helper to clear a region with parchment color before writing
    def clear_region(r_name: str, margin: int = 0):
        if r_name not in REGIONS:
            return
        r = REGIONS[r_name]
        if len(r) == 4:
            x, y, w, h = r
            draw.rectangle((x - margin, y - margin, x + w + margin, y + h + margin), fill=COLORS["parchment"])
        # For point regions (2 coords), we can't easily clear without dimensions

    # Paste art into art panel if provided
    if art_path and os.path.exists(art_path):
        art = Image.open(art_path).convert("RGBA")
        ax, ay, aw, ah = REGIONS["art_panel"]
        art_resized = art.resize((aw, ah), Image.Resampling.LANCZOS)
        card.paste(art_resized, (ax, ay))

    # Draw header elements
    # Number badge - clear and draw
    number = content.get("NUMBER", "001")
    nx, ny = REGIONS["number_badge"]
    # Manually clear number area
    draw.rectangle((nx - 5, ny - 5, nx + 50, ny + 25), fill=COLORS["parchment"])
    draw.text((nx, ny), f"#{number}", font=fonts["badge"], fill=COLORS["ink"])

    # Type badge
    card_type = content.get("CARD_TYPE", "NOUN")
    tx, ty = REGIONS["type_badge"]
    draw_centered_text(draw, card_type, tx, ty, fonts["badge"], COLORS["ink"])

    # Rarity icon + text
    rarity = content.get("RARITY_TEXT", "COMMON")
    rix, riy = REGIONS["rarity_icon"]
    # Clear rarity area
    draw.rectangle((rix - 20, riy - 20, rix + 120, riy + 20), fill=COLORS["parchment"])
    draw_rarity_icon(draw, rix, riy, rarity, size=16)
    rtx, rty = REGIONS["rarity_text"]
    draw.text((rtx, rty), rarity, font=fonts["badge"], fill=COLORS["ink"])

    # Title (WORD) - clear wide area
    word = content.get("WORD", "WORD")
    wcx, wy = REGIONS["word_title"]
    draw.rectangle((wcx - 300, wy - 10, wcx + 300, wy + 55), fill=COLORS["parchment"])
    draw_centered_text(draw, word, wcx, wy, fonts["title"], COLORS["ink"])

    # Subtitle (GLOSS)
    gloss = content.get("GLOSS", "")
    gcx, gy = REGIONS["gloss_subtitle"]
    draw.rectangle((gcx - 300, gy - 5, gcx + 300, gy + 35), fill=COLORS["parchment"])
    draw_centered_text(draw, gloss, gcx, gy, fonts["subtitle"], COLORS["ink"])

    # Clear Stat labels area
    draw.rectangle((50, 480, 950, 510), fill=COLORS["parchment"])

    # Stat labels
    lcx, ly = REGIONS["stat_lore_label"]
    draw_centered_text(draw, "LORE", lcx, ly, fonts["label"], COLORS["ink"])
    ccx, cy = REGIONS["stat_context_label"]
    draw_centered_text(draw, "CONTEXT", ccx, cy, fonts["label"], COLORS["ink"])
    cpcx, cpy = REGIONS["stat_complexity_label"]
    draw_centered_text(draw, "COMPLEXITY", cpcx, cpy, fonts["label"], COLORS["ink"])

    # Stats pips
    pip_y = REGIONS["pip_row_y"]
    # Clear pips area
    draw.rectangle((50, pip_y - 20, 950, pip_y + 20), fill=COLORS["parchment"])
    draw_stat_pips(draw, REGIONS["pip_lore_x"], pip_y, int(content.get("STAT_LORE", 3)))
    draw_stat_pips(draw, REGIONS["pip_context_x"], pip_y, int(content.get("STAT_CONTEXT", 3)))
    draw_stat_pips(draw, REGIONS["pip_complexity_x"], pip_y, int(content.get("STAT_COMPLEXITY", 3)))

    # Section headers - clear and draw
    headers = [
        ("ability_header", "ABILITY"),
        ("ot_header", "OT VERSE"),
        ("nt_header", "NT VERSE"),
        ("greek_header", "GREEK"),
        ("hebrew_header", "HEB/ARAM"),
        ("trivia_header", "TRIVIA"),
    ]

    for key, text in headers:
        hx, hy = REGIONS[key]
        draw.rectangle((hx - 60, hy - 10, hx + 60, hy + 25), fill=COLORS["parchment"])
        draw_centered_text(draw, text, hx, hy, fonts["label"], COLORS["ink"])

    # Content areas - clear and draw

    # Ability text
    ability = content.get("ABILITY_TEXT", "")
    ax, ay, aw, ah = REGIONS["ability_text"]
    clear_region("ability_text")
    draw_left_text(draw, ability, ax, ay, fonts["body"], COLORS["ink"], max_width=aw)

    # OT Verse
    ot_line = content.get("OT_VERSE_LINE", "")
    ox, oy, ow, oh = REGIONS["ot_verse_text"]
    clear_region("ot_verse_text")
    draw_left_text(draw, ot_line, ox, oy, fonts["small"], COLORS["ink"], max_width=ow)

    # NT Verse
    nt_line = content.get("NT_VERSE_LINE", "")
    ntx, nty, ntw, nth = REGIONS["nt_verse_text"]
    clear_region("nt_verse_text")
    draw_left_text(draw, nt_line, ntx, nty, fonts["small"], COLORS["ink"], max_width=ntw)

    # Greek
    greek = content.get("GREEK", "")
    gx, gy = REGIONS["greek_word"]
    draw.rectangle((gx - 100, gy - 10, gx + 100, gy + 30), fill=COLORS["parchment"])
    draw_centered_text(draw, greek, gx, gy, fonts["greek"], COLORS["ink"])

    greek_translit = content.get("GREEK_TRANSLIT", "")
    gtx, gty = REGIONS["greek_translit"]
    draw.rectangle((gtx - 100, gty - 10, gtx + 100, gty + 20), fill=COLORS["parchment"])
    draw_centered_text(draw, greek_translit, gtx, gty, fonts["small"], COLORS["ink"])

    nt_refs = content.get("NT_REFS", "")
    nrx, nry = REGIONS["nt_refs"]
    draw.rectangle((nrx - 100, nry - 10, nrx + 100, nry + 20), fill=COLORS["parchment"])
    draw_centered_text(draw, nt_refs, nrx, nry, fonts["small"], COLORS["ink"])

    # Hebrew (note: proper RTL would need more work)
    hebrew = content.get("HEBREW", "")
    hx, hy = REGIONS["hebrew_word"]
    draw.rectangle((hx - 100, hy - 10, hx + 100, hy + 30), fill=COLORS["parchment"])
    draw_centered_text(draw, hebrew, hx, hy, fonts["hebrew"], COLORS["ink"])

    hebrew_translit = content.get("HEBREW_TRANSLIT", "")
    htx, hty = REGIONS["hebrew_translit"]
    draw.rectangle((htx - 100, hty - 10, htx + 100, hty + 20), fill=COLORS["parchment"])
    draw_centered_text(draw, hebrew_translit, htx, hty, fonts["small"], COLORS["ink"])

    ot_refs = content.get("OT_REFS", "")
    orx, ory = REGIONS["ot_refs"]
    draw.rectangle((orx - 100, ory - 10, orx + 100, ory + 20), fill=COLORS["parchment"])
    draw_centered_text(draw, ot_refs, orx, ory, fonts["small"], COLORS["ink"])

    # Trivia bullets
    trivia = content.get("TRIVIA_BULLETS", [])
    trx, try_, trw, trh = REGIONS["trivia_area"]
    clear_region("trivia_area")
    line_height = 22
    for i, item in enumerate(trivia[:5]):  # Max 5 items
        bullet_text = f"• {item}"
        draw.text((trx, try_ + i * line_height), bullet_text, font=fonts["small"], fill=COLORS["ink"])

    # Series footer
    series = content.get("SERIES", "2026-Q1")
    sx, sy = REGIONS["series_text"]
    # Clear footer area
    draw.rectangle((sx, sy, sx + 200, sy + 30), fill=COLORS["parchment"])
    draw.text((sx, sy), f"SERIES: {series}", font=fonts["badge"], fill=COLORS["parchment"])

    # Save output
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    card.save(out_path, "PNG")


def main() -> int:
    parser = argparse.ArgumentParser(description="Composite a Hypertext card from template + art + content")
    parser.add_argument("--template", default=str(Path(__file__).parent.parent.parent / "raw_template.png"),
                        help="Path to base template PNG")
    parser.add_argument("--art", default=None, help="Path to art-only PNG (optional)")
    parser.add_argument("--card-json", required=True, help="Path to card.json with content")
    parser.add_argument("--out", required=True, help="Output path for final card PNG")
    parser.add_argument("--debug", action="store_true", help="Draw debug rectangles for calibration")

    args = parser.parse_args()

    with open(args.card_json, "r", encoding="utf-8") as f:
        card_data = json.load(f)

    content = card_data.get("content", card_data)

    composite_card(
        template_path=args.template,
        art_path=args.art,
        out_path=args.out,
        content=content,
        debug=args.debug,
    )

    print(f"Generated: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
