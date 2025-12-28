#!/usr/bin/env python3
"""
Programmatic renderer for Hypertext Lot (Phase) cards.
Uses PIL/Pillow to compose cards matching the established visual style.

Card Layout:
  ┌─────────────────────────────────────┐
  │ [LOT]                    [X-CARD]   │  <- Header badges
  │                                     │
  │            PHASE NAME               │  <- Large serif title
  │     Italic flavor subtitle          │  <- Smaller italic
  │                                     │
  │ ┌─────────────────────────────────┐ │
  │ │      REWARD: X Points           │ │  <- Navy banner
  │ │   Wreath Bonus: +2 Points       │ │
  │ └─────────────────────────────────┘ │
  │                                     │
  │ ┌─────────────────────────────────┐ │
  │ │  [📖] + [✏] + [✨] + [👤] + [◇] │ │  <- Type icons
  │ │  NOUN + VERB + ADJ + NAME + TITLE │  <- Type labels
  │ └─────────────────────────────────┘ │
  │                                     │
  │ ┌─────────────────────────────────┐ │
  │ │           CONTEXT               │ │  <- Context panel
  │ │    Educational paragraph        │ │
  │ └─────────────────────────────────┘ │
  │                                     │
  │ SERIES: 2026-Q1 Lots                │  <- Footer
  └─────────────────────────────────────┘
"""

import sys
import textwrap
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None  # type: ignore
    ImageDraw = None  # type: ignore
    ImageFont = None  # type: ignore

# Card dimensions (standard poker card ratio, high resolution)
CARD_WIDTH = 1024
CARD_HEIGHT = 1536

# Colors (from style guide)
NAVY = (10, 25, 47)          # #0a192f - primary dark color
GOLD = (197, 160, 89)        # #c5a059 - accent color
PARCHMENT = (241, 233, 210)  # #f1e9d2 - background
INK = (30, 30, 30)           # #1e1e1e - text color
WHITE = (255, 255, 255)

# Type abbreviations for display
TYPE_ABBREV = {
    "ADJECTIVE": "ADJ",
    "NOUN": "NOUN",
    "VERB": "VERB",
    "NAME": "NAME",
    "TITLE": "TITLE",
    "ANY": "ANY",
    "MATCH": "MATCH",
}


def _get_font(size: int, bold: bool = False, italic: bool = False) -> Any:
    """Get a font, falling back to default if custom fonts not available."""
    if ImageFont is None:
        raise RuntimeError("Pillow required: pip install pillow")

    # Try to load system fonts in order of preference
    font_candidates = []

    if bold and italic:
        font_candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf",
        ]
    elif bold:
        font_candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        ]
    elif italic:
        font_candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
        ]
    else:
        font_candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        ]

    for font_path in font_candidates:
        if Path(font_path).exists():
            try:
                return ImageFont.truetype(font_path, size)
            except OSError:
                continue

    # Fall back to default font
    try:
        return ImageFont.load_default()
    except Exception:
        return None


def _draw_rounded_rect(
    draw: Any,
    coords: tuple[int, int, int, int],
    radius: int,
    fill: tuple[int, int, int] | None = None,
    outline: tuple[int, int, int] | None = None,
    width: int = 1
) -> None:
    """Draw a rounded rectangle."""
    x1, y1, x2, y2 = coords

    if fill:
        # Draw filled rounded rectangle
        draw.rounded_rectangle(coords, radius=radius, fill=fill, outline=outline, width=width)
    elif outline:
        draw.rounded_rectangle(coords, radius=radius, outline=outline, width=width)


def _wrap_text(text: str, font: Any, max_width: int, draw: Any) -> list[str]:
    """Wrap text to fit within max_width pixels."""
    if not text:
        return []

    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        line_width = bbox[2] - bbox[0]

        if line_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def render_lot_card(card_data: dict[str, Any], out_path: Path) -> None:
    """
    Render a single lot card to PNG.

    card_data expects:
      - id: int
      - name: str
      - cards: int (5, 6, or 7)
      - points: int (8, 10, or 12)
      - display: str
      - composition: list[str]
      - flavor: str
      - context: str
      - series: str
      - theme: str (optional)
    """
    if Image is None or ImageDraw is None:
        raise RuntimeError("Pillow required: pip install pillow")

    # Load fonts
    font_title = _get_font(72, bold=True)
    font_flavor = _get_font(28, italic=True)
    font_reward = _get_font(42, bold=True)
    font_bonus = _get_font(24, italic=True)
    font_body = _get_font(22)
    font_badge = _get_font(24, bold=True)
    font_footer = _get_font(20)
    font_display = _get_font(26, bold=True)
    font_context_header = _get_font(28, bold=True)
    font_context = _get_font(20)

    # Create base image with parchment background
    img = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), PARCHMENT)
    draw = ImageDraw.Draw(img)

    # Draw navy outer border
    border_margin = 20
    border_width = 8
    draw.rectangle(
        [border_margin, border_margin, CARD_WIDTH - border_margin, CARD_HEIGHT - border_margin],
        outline=NAVY,
        width=border_width
    )

    # Draw gold inner accent border
    inner_margin = 32
    draw.rectangle(
        [inner_margin, inner_margin, CARD_WIDTH - inner_margin, CARD_HEIGHT - inner_margin],
        outline=GOLD,
        width=2
    )

    # Header badges
    badge_y_top = 50
    badge_y_bottom = 90
    badge_radius = 8

    # LOT badge (top left)
    lot_badge_left = 60
    lot_badge_right = 160
    _draw_rounded_rect(
        draw,
        (lot_badge_left, badge_y_top, lot_badge_right, badge_y_bottom),
        radius=badge_radius,
        fill=NAVY
    )
    lot_center_x = (lot_badge_left + lot_badge_right) // 2
    lot_center_y = (badge_y_top + badge_y_bottom) // 2
    draw.text((lot_center_x, lot_center_y), "LOT", font=font_badge, fill=PARCHMENT, anchor="mm")

    # X-CARD badge (top right)
    card_count = card_data.get("cards", 5)
    badge_text = f"{card_count}-CARD"
    card_badge_right = CARD_WIDTH - 60
    card_badge_left = CARD_WIDTH - 180
    _draw_rounded_rect(
        draw,
        (card_badge_left, badge_y_top, card_badge_right, badge_y_bottom),
        radius=badge_radius,
        fill=NAVY
    )
    card_center_x = (card_badge_left + card_badge_right) // 2
    card_center_y = (badge_y_top + badge_y_bottom) // 2
    draw.text((card_center_x, card_center_y), badge_text, font=font_badge, fill=PARCHMENT, anchor="mm")

    # Phase name (large centered title)
    name = card_data.get("name", "UNKNOWN")
    name_y = 160
    draw.text((CARD_WIDTH // 2, name_y), name, font=font_title, fill=INK, anchor="mm")

    # Flavor text (italic subtitle)
    flavor = card_data.get("flavor", "")
    if flavor:
        # Wrap flavor text if too long
        flavor_lines = _wrap_text(flavor, font_flavor, CARD_WIDTH - 120, draw)
        flavor_y = 235
        for line in flavor_lines[:2]:  # Max 2 lines
            draw.text((CARD_WIDTH // 2, flavor_y), line, font=font_flavor, fill=INK, anchor="mm")
            flavor_y += 32

    # Reward banner (navy background)
    banner_left = 60
    banner_right = CARD_WIDTH - 60
    banner_top = 310
    banner_bottom = 430
    draw.rectangle([banner_left, banner_top, banner_right, banner_bottom], fill=NAVY)

    # Reward text
    points = card_data.get("points", 8)
    reward_y = 350
    draw.text(
        (CARD_WIDTH // 2, reward_y),
        f"REWARD: {points} Points",
        font=font_reward,
        fill=GOLD,
        anchor="mm"
    )

    # Wreath bonus text
    bonus_y = 400
    draw.text(
        (CARD_WIDTH // 2, bonus_y),
        "Wreath Bonus: +2 Points (First to record)",
        font=font_bonus,
        fill=PARCHMENT,
        anchor="mm"
    )

    # Composition panel
    comp_left = 60
    comp_right = CARD_WIDTH - 60
    comp_top = 470
    comp_bottom = 620
    draw.rectangle([comp_left, comp_top, comp_right, comp_bottom], outline=NAVY, width=3)

    # Composition header
    comp_header_y = comp_top + 35
    draw.text(
        (CARD_WIDTH // 2, comp_header_y),
        "REQUIRED COMPOSITION",
        font=font_badge,
        fill=NAVY,
        anchor="mm"
    )

    # Draw horizontal separator line
    sep_y = comp_top + 60
    draw.line([(comp_left + 20, sep_y), (comp_right - 20, sep_y)], fill=GOLD, width=1)

    # Composition display (the formula)
    display = card_data.get("display", "")
    display_y = comp_top + 110
    draw.text(
        (CARD_WIDTH // 2, display_y),
        display,
        font=font_display,
        fill=INK,
        anchor="mm"
    )

    # Type icons representation (simplified text version)
    # Draw a visual representation of the composition
    composition = card_data.get("composition", [])
    if composition:
        # Create a simplified icon-like representation
        icon_y = comp_top + 150
        icon_spacing = min(80, (comp_right - comp_left - 80) // max(len(composition), 1))
        total_width = icon_spacing * (len(composition) - 1)
        start_x = (CARD_WIDTH - total_width) // 2

        for i, card_type in enumerate(composition[:7]):  # Max 7 icons
            x = start_x + i * icon_spacing
            # Draw a small box for each type
            box_size = 30
            box_half = box_size // 2
            draw.rounded_rectangle(
                [x - box_half, icon_y - box_half, x + box_half, icon_y + box_half],
                radius=4,
                outline=NAVY,
                width=2
            )
            # Draw abbreviated type letter
            abbrev = TYPE_ABBREV.get(card_type, card_type)
            letter = abbrev[0] if abbrev else "?"
            draw.text((x, icon_y), letter, font=font_badge, fill=NAVY, anchor="mm")

    # Context panel
    context_left = 60
    context_right = CARD_WIDTH - 60
    context_top = 1050
    context_bottom = 1420
    draw.rectangle([context_left, context_top, context_right, context_bottom], outline=NAVY, width=3)

    # Context header
    context_header_y = context_top + 40
    draw.text(
        (CARD_WIDTH // 2, context_header_y),
        "CONTEXT",
        font=font_context_header,
        fill=NAVY,
        anchor="mm"
    )

    # Draw separator line under context header
    ctx_sep_y = context_top + 65
    draw.line([(context_left + 20, ctx_sep_y), (context_right - 20, ctx_sep_y)], fill=GOLD, width=1)

    # Context body (word wrapped)
    context = card_data.get("context", "")
    if context:
        context_lines = _wrap_text(context, font_context, context_right - context_left - 60, draw)
        context_body_y = context_top + 95
        line_height = 28
        max_lines = 11  # Limit to prevent overflow

        for i, line in enumerate(context_lines[:max_lines]):
            draw.text(
                (CARD_WIDTH // 2, context_body_y + i * line_height),
                line,
                font=font_context,
                fill=INK,
                anchor="mm"
            )

    # Decorative corner elements
    corner_size = 20
    corner_offset = 45

    # Top-left corner
    draw.line([
        (corner_offset, corner_offset + corner_size),
        (corner_offset, corner_offset),
        (corner_offset + corner_size, corner_offset)
    ], fill=GOLD, width=3)

    # Top-right corner
    draw.line([
        (CARD_WIDTH - corner_offset - corner_size, corner_offset),
        (CARD_WIDTH - corner_offset, corner_offset),
        (CARD_WIDTH - corner_offset, corner_offset + corner_size)
    ], fill=GOLD, width=3)

    # Bottom-left corner
    draw.line([
        (corner_offset, CARD_HEIGHT - corner_offset - corner_size),
        (corner_offset, CARD_HEIGHT - corner_offset),
        (corner_offset + corner_size, CARD_HEIGHT - corner_offset)
    ], fill=GOLD, width=3)

    # Bottom-right corner
    draw.line([
        (CARD_WIDTH - corner_offset - corner_size, CARD_HEIGHT - corner_offset),
        (CARD_WIDTH - corner_offset, CARD_HEIGHT - corner_offset),
        (CARD_WIDTH - corner_offset, CARD_HEIGHT - corner_offset - corner_size)
    ], fill=GOLD, width=3)

    # Series footer
    series = card_data.get("series", "2026-Q1")
    footer_y = CARD_HEIGHT - 60
    draw.text(
        (80, footer_y),
        f"SERIES: {series} Lots",
        font=font_footer,
        fill=INK,
        anchor="lm"
    )

    # Phase ID badge (bottom right)
    pid = card_data.get("id", 0)
    draw.text(
        (CARD_WIDTH - 80, footer_y),
        f"#{pid:02d}",
        font=font_footer,
        fill=INK,
        anchor="rm"
    )

    # Save image
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG")


def main() -> int:
    """CLI for testing individual card rendering."""
    import argparse

    parser = argparse.ArgumentParser(description="Render a test lot card")
    parser.add_argument("--out", default="test_lot.png", help="Output path")
    parser.add_argument("--name", default="REMNANT", help="Phase name")
    parser.add_argument("--id", type=int, default=1, help="Phase ID")
    parser.add_argument("--cards", type=int, default=5, help="Card count")
    parser.add_argument("--points", type=int, default=8, help="Point value")
    args = parser.parse_args()

    test_data = {
        "id": args.id,
        "name": args.name,
        "cards": args.cards,
        "points": args.points,
        "display": "5 same type",
        "composition": ["NOUN", "NOUN", "NOUN", "NOUN", "NOUN"],
        "flavor": "The faithful few who remain through trial and tribulation.",
        "context": (
            "Throughout Scripture, God preserves a remnant - a small group who "
            "remain faithful when the majority falls away. From Noah's family "
            "to the 7,000 who never bowed to Baal, the remnant carries the "
            "promise forward into each new generation."
        ),
        "series": "2026-Q1",
        "theme": "Babel",
    }

    render_lot_card(test_data, Path(args.out))
    print(f"Rendered test card to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
