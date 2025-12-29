#!/usr/bin/env python3
"""
Renderer for Hypertext Lot (Phase) cards using Gemini with style references.

Uses the same Gemini style reference approach as the main card pipeline.
Generates LOT cards that match the established visual style.

Card Layout:
  +-------------------------------------+
  | [LOT]                    [X-CARD]   |  <- Header badges
  |                                     |
  |            PHASE NAME               |  <- Large serif title
  |     Italic flavor subtitle          |  <- Smaller italic
  |                                     |
  | +----------------------------------+ |
  | |      REWARD: X Points           | |  <- Navy banner
  | |   Wreath Bonus: +2 Points       | |
  | +----------------------------------+ |
  |                                     |
  | +----------------------------------+ |
  | |  [book] + [pen] + [star] + ...  | |  <- Type icons
  | |  NOUN + VERB + ADJ + NAME + TITLE |  <- Type labels
  | +----------------------------------+ |
  |                                     |
  | +----------------------------------+ |
  | |           CONTEXT               | |  <- Context panel
  | |    Educational paragraph        | |
  | +----------------------------------+ |
  |                                     |
  | SERIES: 2026-Q1 Lots                |  <- Footer
  +-------------------------------------+
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

# Package paths
PACKAGE_DIR = Path(__file__).resolve().parent.parent
TOOLS_DIR = PACKAGE_DIR.parent
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

    Returns refs ordered: TEMPLATE FIRST, then examples.
    This matches gemini/style.py's expectation that [1] is the template.

    Looks for (in order):
    1. PNG files in series/lots/refs/ directory (series-specific refs - preferred)
    2. PNG files in templates/lots/ directory (global refs)
    3. Legacy LOT template (templates/lot_template.png)
    4. Existing LOT card images in the series
    5. Falls back to main card template if no LOT-specific refs exist
    """
    templates: list[str] = []
    examples: list[str] = []
    seen_names: set[str] = set()  # Track filenames to avoid duplicates

    def add_ref(png_path: Path, source: str) -> bool:
        """Add a ref, categorizing as template or example. Returns True if added."""
        if png_path.name in seen_names:
            return False
        seen_names.add(png_path.name)
        path_str = str(png_path)
        # Templates go first, examples after
        if "template" in png_path.name.lower():
            templates.append(path_str)
            _log(f"  Style ref ({source}): {png_path.name} [TEMPLATE]")
        else:
            examples.append(path_str)
            _log(f"  Style ref ({source}): {png_path.name} [EXAMPLE]")
        return True

    # First, check series-specific refs directory
    series_refs_dir = series_dir / "lots" / "refs"
    if series_refs_dir.exists():
        for png_file in sorted(series_refs_dir.glob("*.png")):
            add_ref(png_file, "series")
            if len(templates) + len(examples) >= 4:
                break

    # Then check templates/lots/ directory for style reference PNGs
    if len(templates) + len(examples) < 4 and LOT_STYLES_DIR.exists():
        for png_file in sorted(LOT_STYLES_DIR.glob("*.png")):
            add_ref(png_file, "templates")
            if len(templates) + len(examples) >= 4:
                break

    # Combine: templates first, then examples
    refs = templates + examples

    # Legacy: single template file
    if not refs and DEFAULT_LOT_TEMPLATE.exists():
        refs.append(str(DEFAULT_LOT_TEMPLATE))

    # Look for existing LOT cards in this series as additional style references
    lots_dir = series_dir / "lots"
    if lots_dir.exists() and len(refs) < 4:
        for lot_dir in sorted(lots_dir.iterdir()):
            if not lot_dir.is_dir() or lot_dir.name == "refs":
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


def _build_lot_prompt(card_data: dict[str, Any], style_refs: list[str] | None = None) -> str:
    """
    Build a detailed prompt for Gemini to generate a LOT card.

    Follows the multi-image reference specification with explicit image labeling.

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
    from pathlib import Path

    pid = card_data.get("id", 0)
    name = card_data.get("name", "UNKNOWN")
    cards = card_data.get("cards", 5)
    points = card_data.get("points", 8)
    display = card_data.get("display", "")
    composition = card_data.get("composition", [])
    flavor = card_data.get("flavor", "")
    context = card_data.get("context", "")
    series = card_data.get("series", "2026-Q1")

    # Build composition WITHOUT brackets (brackets are wrong)
    comp_parts = []
    if composition:
        for card_type in composition:
            comp_parts.append(card_type)  # No brackets!
    comp_display = " + ".join(comp_parts) if comp_parts else display

    # Build image role labels (refs are ordered: template first, then examples)
    image_roles = []
    if style_refs:
        for i, ref_path in enumerate(style_refs, 1):
            ref_name = Path(ref_path).stem  # filename without extension
            if "template" in ref_name.lower():
                image_roles.append(f"[{i}] {ref_name}: Card template showing structure, borders, and text zones")
            else:
                image_roles.append(f"[{i}] {ref_name}: Completed example card showing target style and finish")

    roles_text = "\n".join(image_roles) if image_roles else "Reference images provided for style matching"

    prompt = f"""IMAGE ROLES:
{roles_text}

TASK:
Generate a new LOT card using the structural layout from the template image.
Apply the visual style, coloring, shading, and artistic finish from the example cards.

CARD CONTENT:
- Title: "{name}"
- Subtitle (italic): "{flavor}"
- Top left badge: "LOT"
- Top right: "CARD COUNT" label (small) above "{cards}-CARD" value (larger)
- Reward banner: "REWARD: {points} Points"
- Wreath bonus: "Wreath Bonus: +2 Points (First to record)"
- Composition: {comp_display}
- Context header: "CONTEXT"
- Context body: "{context}"
- Footer left: "SERIES: {series} Lots"

PRESERVATION:
- Exact border structure and double-frame from template
- Navy tab badge shape for "LOT" (top-left)
- Navy rectangle with gold border for card count (top-right)
- Navy ribbon banner with gold trim for reward section
- Decorative corner flourishes on composition box
- Navy "CONTEXT" header bar above context text

STYLE MATCHING:
- Match color palette: Navy (#102030), Gold (#C0A060), Parchment background
- Apply same artistic finish and texture as examples
- Use consistent serif typography
- Match icon style for card types (book, pen, quill, frame icons)
- Composition type labels WITHOUT square brackets (e.g., "NOUN + VERB", NOT "[NOUN] + [VERB]")

OUTPUT: 2:3 portrait, 1024x1536px

AVOID:
- Text rendering errors or garbled characters
- Border distortion or misalignment
- Missing sections or labels
- Wrong card count or points values
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
    # Get style references first (needed for prompt building)
    if style_refs is None:
        # Try to infer series_dir from out_path
        # out_path is typically: series/2026-Q1/lots/01-remnant/outputs/lot_1024x1536.png
        try:
            series_dir = out_path.parent.parent.parent.parent
            style_refs = _build_lot_style_refs(series_dir)
        except Exception:
            style_refs = []

    # Build prompt with image role labels
    prompt = _build_lot_prompt(card_data, style_refs=style_refs)

    # Write prompt to file (for debugging/reference)
    prompt_path = out_path.parent.parent / "prompt.txt"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(prompt)

    # Generate the image
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if style_refs:
        _log(f"  Using {len(style_refs)} style reference(s)")
        # Use subprocess like the main card pipeline does
        cmd = [
            sys.executable, "-m", "hypertext.gemini.style",
            "--prompt-file", str(prompt_path),
        ]
        for ref in style_refs:
            cmd.extend(["--style", ref])
        cmd.extend(["--out", str(out_path)])
        subprocess.check_call(cmd)
    else:
        # Fall back to basic image generation without style refs
        try:
            from hypertext.gemini.image import generate_image
        except ImportError:
            sys.path.insert(0, str(TOOLS_DIR))
            try:
                from gemini_image import generate_image
            except ImportError:
                raise RuntimeError(
                    "No style references found and gemini_image not available. "
                    "Create a LOT template at templates/lot_template.png or generate some LOT cards first."
                )
        _log("  No style references found, using basic generation")
        generate_image(prompt, str(out_path), aspect_ratio="2:3")


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
