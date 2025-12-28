#!/usr/bin/env python3
"""
Renderer for Hypertext Lot (Phase) cards using Gemini with style references.

Uses the same Gemini style reference approach as the main card pipeline.
Generates LOT cards that match the established visual style.

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
from pathlib import Path
from typing import Any

TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TOOLS_DIR.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"

# Default style template directory and file for LOT cards
LOT_STYLES_DIR = TEMPLATES_DIR / "lots"
DEFAULT_LOT_TEMPLATE = TEMPLATES_DIR / "lot_template.png"  # Legacy single-file location

# Type icon descriptions for the prompt
TYPE_ICONS = {
    "NOUN": "closed book icon",
    "VERB": "writing pen icon",
    "ADJECTIVE": "pen with sparkles icon",
    "NAME": "person silhouette icon",
    "TITLE": "framed diamond/portrait icon",
    "ANY": "star/wildcard icon",
    "MATCH": "matching pair icon",
}


def _log(msg: str) -> None:
    """Log a message to stderr."""
    print(msg, file=sys.stderr)


def _build_lot_style_refs(series_dir: Path) -> list[str]:
    """
    Build list of style reference paths for LOT cards.

    Looks for (in order):
    1. PNG files in templates/lots/ directory (primary style refs)
    2. Legacy LOT template (templates/lot_template.png)
    3. Existing LOT card images in the series
    4. Falls back to main card template if no LOT-specific refs exist
    """
    refs: list[str] = []

    # First, check templates/lots/ directory for style reference PNGs
    if LOT_STYLES_DIR.exists():
        for png_file in sorted(LOT_STYLES_DIR.glob("*.png")):
            refs.append(str(png_file))
            _log(f"  Style ref: {png_file.name}")
            # Use up to 4 style references from templates/lots/
            if len(refs) >= 4:
                break

    # Legacy: single template file
    if not refs and DEFAULT_LOT_TEMPLATE.exists():
        refs.append(str(DEFAULT_LOT_TEMPLATE))

    # Look for existing LOT cards in this series as additional style references
    lots_dir = series_dir / "lots"
    if lots_dir.exists() and len(refs) < 4:
        for lot_dir in sorted(lots_dir.iterdir()):
            if not lot_dir.is_dir():
                continue
            lot_img = lot_dir / "outputs" / "lot_1024x1536.png"
            if lot_img.exists():
                refs.append(str(lot_img))
                if len(refs) >= 4:
                    break

    # If no LOT refs found, try the main card template
    if not refs:
        main_template = TEMPLATES_DIR / "clean_template.png"
        if main_template.exists():
            refs.append(str(main_template))

        # Also look for existing main deck cards as style reference
        cards_dir = series_dir / "cards"
        if cards_dir.exists():
            for card_dir in sorted(cards_dir.iterdir()):
                if not card_dir.is_dir():
                    continue
                card_img = card_dir / "outputs" / "card_1024x1536.png"
                if card_img.exists():
                    refs.append(str(card_img))
                    break  # Just one main card for reference

    return refs


def _build_lot_prompt(card_data: dict[str, Any]) -> str:
    """
    Build a detailed prompt for Gemini to generate a LOT card.

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
    pid = card_data.get("id", 0)
    name = card_data.get("name", "UNKNOWN")
    cards = card_data.get("cards", 5)
    points = card_data.get("points", 8)
    display = card_data.get("display", "")
    composition = card_data.get("composition", [])
    flavor = card_data.get("flavor", "")
    context = card_data.get("context", "")
    series = card_data.get("series", "2026-Q1")

    # Build composition description with icons
    comp_desc_parts = []
    for card_type in composition:
        icon_desc = TYPE_ICONS.get(card_type, f"{card_type} icon")
        comp_desc_parts.append(f"{card_type} ({icon_desc})")
    comp_description = " + ".join(comp_desc_parts) if comp_desc_parts else display

    prompt = f"""Generate a LOT (Phase) card for the Hypertext Biblical trading card game.

This is a PHASE CARD that players collect to score points. It shows what combination of cards they need to complete this phase.

CARD SPECIFICATIONS:
- Orientation: Portrait (2:3 aspect ratio, taller than wide)
- Size: 1024 x 1536 pixels
- Style: Elegant Biblical/theological aesthetic with navy (#0a192f), gold (#c5a059), and parchment (#f1e9d2) colors

EXACT LAYOUT (top to bottom):

1. HEADER BADGES (top of card):
   - Left badge: Navy rounded rectangle with "LOT" in parchment/cream text
   - Right badge: Navy rounded rectangle with "{cards}-CARD" in parchment/cream text

2. PHASE NAME (large, centered):
   - Title: "{name}" in large elegant serif font, dark ink color
   - Subtitle below: "{flavor}" in smaller italic text

3. REWARD BANNER (navy background strip):
   - Main text: "REWARD: {points} Points" in gold
   - Below that: "Wreath Bonus: +2 Points (First to record)" in smaller parchment text

4. COMPOSITION PANEL (bordered box):
   - Header: "REQUIRED COMPOSITION" centered
   - Gold separator line
   - Show the required card types: {display}
   - Visual representation with small icons for each type:
     {comp_description}

5. CONTEXT PANEL (bordered box, lower portion):
   - Header: "CONTEXT" centered in navy
   - Gold separator line
   - Educational text: "{context}"

6. FOOTER:
   - Left: "SERIES: {series} Lots"
   - Right: "#{pid:02d}"

DECORATIVE ELEMENTS:
- Navy outer border with gold inner accent border
- Gold decorative corner elements (L-shaped brackets in each corner)
- Elegant, clean typography throughout

CRITICAL REQUIREMENTS:
- DO NOT include any brackets [] in the output
- DO NOT include placeholder text - use the exact values provided
- Maintain the elegant Biblical/seminary aesthetic
- All text must be clearly legible
- Match the navy/gold/parchment color scheme exactly
"""

    return prompt


def render_lot_card(card_data: dict[str, Any], out_path: Path, style_refs: list[str] | None = None) -> None:
    """
    Render a single lot card to PNG using Gemini with style references.

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

    style_refs: Optional list of style reference image paths.
                If not provided, will attempt to find LOT templates/examples.
    """
    # Import gemini_style from the same tools directory
    sys.path.insert(0, str(TOOLS_DIR))
    try:
        from gemini_style import generate_with_styles
    except ImportError as e:
        raise RuntimeError(f"Could not import gemini_style: {e}")

    # Build prompt
    prompt = _build_lot_prompt(card_data)

    # Get style references if not provided
    if style_refs is None:
        # Try to infer series_dir from out_path
        # out_path is typically: series/2026-Q1/lots/01-remnant/outputs/lot_1024x1536.png
        try:
            series_dir = out_path.parent.parent.parent.parent
            style_refs = _build_lot_style_refs(series_dir)
        except Exception:
            style_refs = []

    # Write prompt to file (for debugging/reference)
    prompt_path = out_path.parent.parent / "prompt.txt"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(prompt)

    # Generate the image
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if style_refs:
        _log(f"  Using {len(style_refs)} style reference(s)")
        generate_with_styles(
            prompt_text=prompt,
            style_image_paths=style_refs,
            out_path=str(out_path),
            aspect_ratio="2:3",
        )
    else:
        # Fall back to basic image generation without style refs
        try:
            from gemini_image import generate_image
            _log("  No style references found, using basic generation")
            generate_image(prompt, str(out_path), aspect_ratio="2:3")
        except ImportError:
            raise RuntimeError(
                "No style references found and gemini_image not available. "
                "Create a LOT template at templates/lot_template.png or generate some LOT cards first."
            )


def render_lot_card_with_series(
    card_data: dict[str, Any],
    out_path: Path,
    series_dir: Path,
) -> None:
    """
    Render a LOT card with explicit series directory for finding style refs.

    This is the preferred method when calling from lot_generation.py.
    """
    style_refs = _build_lot_style_refs(series_dir)
    render_lot_card(card_data, out_path, style_refs=style_refs)


def main() -> int:
    """CLI for testing individual card rendering."""
    import argparse

    parser = argparse.ArgumentParser(description="Render a test lot card using Gemini")
    parser.add_argument("--out", default="test_lot.png", help="Output path")
    parser.add_argument("--name", default="REMNANT", help="Phase name")
    parser.add_argument("--id", type=int, default=1, help="Phase ID")
    parser.add_argument("--cards", type=int, default=5, help="Card count")
    parser.add_argument("--points", type=int, default=8, help="Point value")
    parser.add_argument("--style", action="append", help="Style reference image (repeatable)")
    parser.add_argument("--series", help="Series directory for finding style refs")
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

    style_refs = args.style
    if args.series and not style_refs:
        style_refs = _build_lot_style_refs(Path(args.series))

    try:
        render_lot_card(test_data, Path(args.out), style_refs=style_refs)
        print(f"Rendered test card to {args.out}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
