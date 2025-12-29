#!/usr/bin/env python3
"""
Export Hypertext cards for various print-on-demand and playtest platforms.

Exports both main deck cards AND lot (phase) cards.

Supported platforms:
  - playingcards: Playingcards.io (web playtest) - 750x1050 @ 72 DPI
  - makeplayingcards: MakePlayingCards.com - 750x1050 @ 300 DPI + bleed
  - thegamecrafter: The Game Crafter - 825x1125 @ 300 DPI + bleed

Usage:
  python -m hypertext.lots.exporter --series series/2026-Q1 --target playingcards
  python -m hypertext.lots.exporter --series series/2026-Q1 --target playingcards --type cards
  python -m hypertext.lots.exporter --series series/2026-Q1 --target makeplayingcards --type all
  python -m hypertext.lots.exporter --series series/2026-Q1 --target playingcards --cards-source demo_cards --limit 90
  python -m hypertext.lots.exporter --series series/2026-Q1 --target playingcards --cards-source demo_cards --lots-source series/2026-Q1
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
CARD_BACK_PATH = TEMPLATES_DIR / "card_back.png"


def _log(msg: str) -> None:
    """Log a message to stderr."""
    print(msg, file=sys.stderr)


# Platform specifications
PLATFORMS: dict[str, dict[str, Any]] = {
    "playingcards": {
        "name": "Playingcards.io",
        "width": 750,
        "height": 1050,
        "dpi": 72,
        "bleed": 0,
        "description": "Web-based playtest platform",
    },
    "makeplayingcards": {
        "name": "MakePlayingCards.com",
        "width": 750,
        "height": 1050,
        "dpi": 300,
        "bleed": 36,  # pixels at 300 DPI (~0.12 inch)
        "description": "Print-on-demand card manufacturer",
    },
    "thegamecrafter": {
        "name": "The Game Crafter",
        "width": 825,
        "height": 1125,
        "dpi": 300,
        "bleed": 38,  # pixels at 300 DPI (1/8 inch)
        "description": "Print-on-demand game manufacturer",
    },
    "tabletopsimulator": {
        "name": "Tabletop Simulator",
        "width": 409,
        "height": 585,
        "dpi": 72,
        "bleed": 0,
        "description": "Steam workshop / TTS mod",
        "sprite_cols": 10,  # Cards per row in sprite sheet
        "sprite_rows": 10,  # Max rows (100 cards per sheet)
    },
}


def _add_bleed(img: Any, bleed_pixels: int) -> Any:
    """
    Add bleed to an image by extending edge pixels.

    For print-ready cards, bleed extends the image beyond the trim line
    to prevent white edges from cutting variations.
    """
    if Image is None:
        raise RuntimeError("Pillow required: pip install pillow")

    if bleed_pixels <= 0:
        return img

    orig_width, orig_height = img.size
    new_width = orig_width + bleed_pixels * 2
    new_height = orig_height + bleed_pixels * 2

    # Create new image with extended size
    new_img = Image.new("RGB", (new_width, new_height))

    # Paste original in center
    new_img.paste(img, (bleed_pixels, bleed_pixels))

    # Extend edges by mirroring edge pixels

    # Top edge
    top_strip = img.crop((0, 0, orig_width, 1))
    for y in range(bleed_pixels):
        new_img.paste(top_strip, (bleed_pixels, y))

    # Bottom edge
    bottom_strip = img.crop((0, orig_height - 1, orig_width, orig_height))
    for y in range(new_height - bleed_pixels, new_height):
        new_img.paste(bottom_strip, (bleed_pixels, y))

    # Left edge (including corners)
    left_strip = new_img.crop((bleed_pixels, 0, bleed_pixels + 1, new_height))
    for x in range(bleed_pixels):
        new_img.paste(left_strip, (x, 0))

    # Right edge (including corners)
    right_strip = new_img.crop((new_width - bleed_pixels - 1, 0, new_width - bleed_pixels, new_height))
    for x in range(new_width - bleed_pixels, new_width):
        new_img.paste(right_strip, (x, 0))

    return new_img


def _export_card_set(
    source_dir: Path,
    export_dir: Path,
    spec: dict,
    card_type: str,
    src_filename: str,
    limit: int = 0,
) -> tuple[int, int, int]:
    """
    Export a set of cards from source_dir to export_dir.

    Args:
        source_dir: Directory containing card subdirectories
        export_dir: Output directory for exported cards
        spec: Platform specification dict
        card_type: "card" or "lot" (for naming)
        src_filename: Source filename to look for (e.g., "card_1024x1536.png")
        limit: Maximum number of cards to export (0 = no limit)

    Returns:
        (exported_count, skipped_count, error_count)
    """
    export_dir.mkdir(parents=True, exist_ok=True)

    exported_count = 0
    skipped_count = 0
    error_count = 0

    # Find all card directories (skip non-directories and special dirs like "refs")
    card_dirs = sorted([
        d for d in source_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".") and d.name != "refs"
    ])

    # Apply limit if specified
    if limit > 0:
        card_dirs = card_dirs[:limit]

    for card_dir in card_dirs:
        src_path = card_dir / "outputs" / src_filename

        if not src_path.exists():
            skipped_count += 1
            continue

        try:
            # Load source image
            img = Image.open(src_path)

            # Calculate target dimensions
            target_w = spec["width"]
            target_h = spec["height"]
            bleed = spec["bleed"]

            # First resize to base dimensions (without bleed)
            img_resized = img.resize((target_w, target_h), Image.LANCZOS)

            # Add bleed if required
            if bleed > 0:
                img_final = _add_bleed(img_resized, bleed)
            else:
                img_final = img_resized

            # Generate output filename
            # Extract number from directory name (e.g., "001-magi" -> "001", "01-remnant" -> "01")
            card_num = card_dir.name.split("-")[0]
            out_name = f"{card_type}_{card_num}.png"
            out_path = export_dir / out_name

            # Save with DPI metadata
            img_final.save(out_path, "PNG", dpi=(spec["dpi"], spec["dpi"]))

            _log(f"    {out_name}")
            exported_count += 1

        except Exception as e:
            _log(f"    Error {card_dir.name}: {e}")
            error_count += 1

    return exported_count, skipped_count, error_count


def _create_sprite_sheet(
    card_images: list[Path],
    out_path: Path,
    card_width: int,
    card_height: int,
    cols: int = 10,
    max_rows: int = 7,
) -> tuple[int, int]:
    """
    Create a sprite sheet from individual card images.

    Args:
        card_images: List of card image paths (in order)
        out_path: Output path for sprite sheet
        card_width: Width of each card
        card_height: Height of each card
        cols: Number of columns in sprite sheet
        max_rows: Maximum rows per sheet

    Returns:
        (actual_cols, actual_rows) used in the sheet
    """
    if not card_images:
        return 0, 0

    num_cards = len(card_images)
    actual_cols = min(cols, num_cards)
    actual_rows = (num_cards + actual_cols - 1) // actual_cols

    if actual_rows > max_rows:
        _log(f"    Warning: {num_cards} cards exceeds max {cols * max_rows} per sheet")
        actual_rows = max_rows

    sheet_width = actual_cols * card_width
    sheet_height = actual_rows * card_height

    sheet = Image.new("RGB", (sheet_width, sheet_height), (0, 0, 0))

    for i, img_path in enumerate(card_images[:cols * actual_rows]):
        row = i // actual_cols
        col = i % actual_cols
        x = col * card_width
        y = row * card_height

        try:
            card_img = Image.open(img_path)
            card_img = card_img.resize((card_width, card_height), Image.LANCZOS)
            sheet.paste(card_img, (x, y))
        except Exception as e:
            _log(f"    Error loading {img_path.name}: {e}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, "PNG")

    return actual_cols, actual_rows


def _create_tts_token(
    nickname: str,
    color: dict,
    position: tuple[float, float, float] = (0, 1, 0),
) -> dict:
    """Create a TTS token/chip object."""
    return {
        "Name": "Chip_100",
        "Transform": {
            "posX": position[0],
            "posY": position[1],
            "posZ": position[2],
            "rotX": 0,
            "rotY": 0,
            "rotZ": 0,
            "scaleX": 1,
            "scaleY": 1,
            "scaleZ": 1,
        },
        "Nickname": nickname,
        "ColorDiffuse": color,
    }


def _create_tts_token_stack(
    nickname: str,
    color: dict,
    count: int,
    position: tuple[float, float, float] = (0, 1, 0),
) -> dict:
    """Create a stack of TTS tokens."""
    tokens = []
    for i in range(count):
        token = _create_tts_token(nickname, color, (0, 0, 0))
        tokens.append(token)

    return {
        "Name": "Chip_100",
        "Transform": {
            "posX": position[0],
            "posY": position[1],
            "posZ": position[2],
            "rotX": 0,
            "rotY": 0,
            "rotZ": 0,
            "scaleX": 1,
            "scaleY": 1,
            "scaleZ": 1,
        },
        "Nickname": nickname,
        "ColorDiffuse": color,
        "States": {str(i+1): tokens[i] for i in range(len(tokens))} if count > 1 else {},
    }


def _create_tts_deck_json(
    deck_name: str,
    face_url: str,
    back_url: str,
    num_cards: int,
    cols: int,
    rows: int,
) -> dict:
    """
    Create a Tabletop Simulator deck JSON object.

    Args:
        deck_name: Name of the deck
        face_url: URL to sprite sheet for card faces
        back_url: URL to card back image
        num_cards: Total number of cards
        cols: Columns in sprite sheet
        rows: Rows in sprite sheet

    Returns:
        TTS deck object dictionary
    """
    # Build card IDs (100, 101, 102, ... for deck 1)
    deck_ids = [100 + i for i in range(num_cards)]

    # Build contained objects (one per card)
    contained = []
    for i in range(num_cards):
        contained.append({
            "Name": "Card",
            "Transform": {
                "posX": 0, "posY": 0, "posZ": 0,
                "rotX": 0, "rotY": 180, "rotZ": 180,
                "scaleX": 1, "scaleY": 1, "scaleZ": 1,
            },
            "Nickname": "",
            "CardID": 100 + i,
            "CustomDeck": {
                "1": {
                    "FaceURL": face_url,
                    "BackURL": back_url,
                    "NumWidth": cols,
                    "NumHeight": rows,
                    "BackIsHidden": True,
                    "UniqueBack": False,
                }
            },
        })

    return {
        "Name": "DeckCustom",
        "Transform": {
            "posX": 0, "posY": 1, "posZ": 0,
            "rotX": 0, "rotY": 180, "rotZ": 180,
            "scaleX": 1, "scaleY": 1, "scaleZ": 1,
        },
        "Nickname": deck_name,
        "DeckIDs": deck_ids,
        "CustomDeck": {
            "1": {
                "FaceURL": face_url,
                "BackURL": back_url,
                "NumWidth": cols,
                "NumHeight": rows,
                "BackIsHidden": True,
                "UniqueBack": False,
            }
        },
        "ContainedObjects": contained,
    }


def _export_for_tts(
    series_dir: Path,
    cards_dir: Path | None,
    lots_dir: Path | None,
    spec: dict,
    card_type: str,
    limit: int,
    cards_source: Path | None,
    lots_source: Path | None,
    url_base: str | None = None,
) -> int:
    """
    Export for Tabletop Simulator with sprite sheets.

    Creates:
      - main_deck_sheet.png (sprite sheet of main cards)
      - lots_sheet.png (sprite sheet of lot cards)
      - card_back.png
      - Hypertext.json (TTS saved object)
    """
    export_dir = series_dir / "exports" / "tabletopsimulator"
    export_dir.mkdir(parents=True, exist_ok=True)

    card_width = spec["width"]
    card_height = spec["height"]
    cols = spec.get("sprite_cols", 10)
    max_rows = spec.get("sprite_rows", 7)

    decks = []

    # Export main deck cards
    if card_type in ("cards", "all") and cards_dir and cards_dir.exists():
        source_label = f" (from {cards_source.name})" if cards_source else ""
        _log(f"  Main deck{source_label}:")

        # Collect card images
        card_images = []
        card_dirs = sorted([
            d for d in cards_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".") and d.name != "refs"
        ])
        if limit > 0:
            card_dirs = card_dirs[:limit]

        for card_dir in card_dirs:
            img_path = card_dir / "outputs" / "card_1024x1536.png"
            if img_path.exists():
                card_images.append(img_path)

        if card_images:
            sheet_path = export_dir / "main_deck_sheet.png"
            actual_cols, actual_rows = _create_sprite_sheet(
                card_images, sheet_path, card_width, card_height, cols, max_rows
            )
            _log(f"    Created sprite sheet: {len(card_images)} cards ({actual_cols}x{actual_rows})")

            decks.append({
                "name": "Hypertext Main Deck",
                "sheet": "main_deck_sheet.png",
                "count": len(card_images),
                "cols": actual_cols,
                "rows": actual_rows,
            })

    # Export lot cards
    if card_type in ("lots", "all") and lots_dir and lots_dir.exists():
        source_label = f" (from {lots_source.name})" if lots_source else ""
        _log(f"  Lot cards{source_label}:")

        lot_images = []
        lot_dirs = sorted([
            d for d in lots_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".") and d.name != "refs"
        ])

        for lot_dir in lot_dirs:
            img_path = lot_dir / "outputs" / "lot_1024x1536.png"
            if img_path.exists():
                lot_images.append(img_path)

        if lot_images:
            sheet_path = export_dir / "lots_sheet.png"
            actual_cols, actual_rows = _create_sprite_sheet(
                lot_images, sheet_path, card_width, card_height, cols, max_rows
            )
            _log(f"    Created sprite sheet: {len(lot_images)} lots ({actual_cols}x{actual_rows})")

            decks.append({
                "name": "Hypertext Lots",
                "sheet": "lots_sheet.png",
                "count": len(lot_images),
                "cols": actual_cols,
                "rows": actual_rows,
            })

    # Export card back
    if CARD_BACK_PATH.exists():
        back_img = Image.open(CARD_BACK_PATH)
        back_img = back_img.resize((card_width, card_height), Image.LANCZOS)
        back_path = export_dir / "card_back.png"
        back_img.save(back_path, "PNG")
        _log(f"  Card back -> card_back.png")

    # Generate TTS JSON
    _log("")
    _log("  Generating TTS JSON...")

    # Determine URL base
    if url_base:
        base = url_base.rstrip("/")
        _log(f"  Using URL base: {base}")
    else:
        base = "YOUR_URL_HERE"
        _log("  NOTE: Update URLs in Hypertext.json before importing to TTS")

    tts_objects = []
    for i, deck in enumerate(decks):
        face_url = f"{base}/{deck['sheet']}"
        back_url = f"{base}/card_back.png"

        deck_obj = _create_tts_deck_json(
            deck["name"],
            face_url,
            back_url,
            deck["count"],
            deck["cols"],
            deck["rows"],
        )
        # Offset position for multiple decks
        deck_obj["Transform"]["posX"] = i * 3
        tts_objects.append(deck_obj)

    # Add Letter tokens (24 - one for each Greek letter, covers Hebrew's 22)
    # Blue color
    blue_color = {"r": 0.2, "g": 0.4, "b": 0.9}
    for i in range(24):
        letter_token = _create_tts_token(
            "Letter Token",
            blue_color,
            position=(8 + (i % 6) * 0.8, 1, -2 + (i // 6) * 0.8),
        )
        tts_objects.append(letter_token)
    _log(f"  Added 24 Letter tokens (blue)")

    # Add Wreath tokens (2)
    # Red color
    red_color = {"r": 0.9, "g": 0.2, "b": 0.2}
    for i in range(2):
        wreath_token = _create_tts_token(
            "Wreath Token",
            red_color,
            position=(8 + i * 1.2, 1, 2),
        )
        tts_objects.append(wreath_token)
    _log(f"  Added 2 Wreath tokens (red)")

    # Wrap in TTS save format
    tts_save = {
        "SaveName": "Hypertext",
        "GameMode": "",
        "Date": "",
        "Table": "",
        "Sky": "",
        "Note": "Hypertext card game. Main deck (90 cards), Lot deck (30 phases), 24 Letter tokens, 2 Wreath tokens.",
        "Rules": "",
        "PlayerTurn": "",
        "ObjectStates": tts_objects,
    }

    json_path = export_dir / "Hypertext.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(tts_save, f, indent=2)

    _log(f"  TTS save file -> Hypertext.json")
    _log("")
    _log(f"Export complete: {export_dir}")
    _log("")
    if url_base:
        _log("Next steps:")
        _log("  1. Commit and push the PNG files to your repo")
        _log("  2. Copy Hypertext.json to TTS Saved Objects folder")
        _log("  3. In TTS: Objects > Saved Objects > Spawn 'Hypertext'")
    else:
        _log("Next steps:")
        _log("  1. Host the PNG files (GitHub, Steam Cloud, or Imgur)")
        _log("  2. Edit Hypertext.json and replace YOUR_URL_HERE with actual URLs")
        _log("  3. Copy Hypertext.json to TTS Saved Objects folder")
        _log("  4. In TTS: Objects > Saved Objects > Spawn 'Hypertext'")

    return 0


def _export_card_back(export_dir: Path, spec: dict) -> bool:
    """
    Export the card back image to the export directory.

    Args:
        export_dir: Root export directory (e.g., series/2026-Q1/exports/playingcards)
        spec: Platform specification dict

    Returns:
        True if exported successfully, False otherwise
    """
    if not CARD_BACK_PATH.exists():
        _log(f"  Card back: not found at {CARD_BACK_PATH}")
        return False

    try:
        img = Image.open(CARD_BACK_PATH)

        # Calculate target dimensions
        target_w = spec["width"]
        target_h = spec["height"]
        bleed = spec["bleed"]

        # Resize to base dimensions
        img_resized = img.resize((target_w, target_h), Image.LANCZOS)

        # Add bleed if required
        if bleed > 0:
            img_final = _add_bleed(img_resized, bleed)
        else:
            img_final = img_resized

        # Save to export directory
        export_dir.mkdir(parents=True, exist_ok=True)
        out_path = export_dir / "card_back.png"
        img_final.save(out_path, "PNG", dpi=(spec["dpi"], spec["dpi"]))

        _log(f"  Card back -> {out_path.name}")
        return True

    except Exception as e:
        _log(f"  Card back error: {e}")
        return False


def export_for_platform(
    series_dir: Path,
    target: str,
    card_type: str = "all",
    limit: int = 0,
    cards_source: Path | None = None,
    lots_source: Path | None = None,
    url_base: str | None = None,
) -> int:
    """
    Export cards for the specified target platform.

    Args:
        series_dir: Path to series directory for output (e.g., series/2026-Q1)
        target: Platform name (playingcards, makeplayingcards, thegamecrafter, tabletopsimulator)
        card_type: What to export - "cards", "lots", or "all" (default)
        limit: Maximum number of cards to export (0 = no limit)
        cards_source: Override source for main deck cards (e.g., demo_cards)
        lots_source: Override source for lot cards
        url_base: Base URL for TTS image hosting (e.g., GitHub raw URL)

    Returns:
        0 on success, non-zero on error
    """
    if Image is None:
        _log("Error: Pillow required. Install with: pip install pillow")
        return 1

    if target not in PLATFORMS:
        _log(f"Error: Unknown platform '{target}'")
        _log(f"Available platforms: {', '.join(PLATFORMS.keys())}")
        return 1

    spec = PLATFORMS[target]

    _log(f"Exporting for {spec['name']} ({spec['description']})")
    _log(f"  Output size: {spec['width']}x{spec['height']} @ {spec['dpi']} DPI")
    if spec['bleed'] > 0:
        _log(f"  Bleed: {spec['bleed']} pixels")
    if limit > 0:
        _log(f"  Limit: first {limit} cards")
    _log("")

    # Determine card sources (needed before TTS branch)
    # Use override if provided, otherwise default to series_dir structure
    if cards_source:
        cards_dir = cards_source
        # Check if flat structure (cards directly in root)
        if not (cards_dir / "cards").exists():
            first_dir = next((d for d in sorted(cards_dir.iterdir()) if d.is_dir() and d.name[0].isdigit()), None)
            if first_dir and (first_dir / "outputs" / "card_1024x1536.png").exists():
                pass  # Use cards_dir as-is (flat structure)
            else:
                cards_dir = cards_source / "cards"
        else:
            cards_dir = cards_source / "cards"
    else:
        cards_dir = series_dir / "cards"
        # Check for flat structure in series_dir
        if not cards_dir.exists():
            first_dir = next((d for d in sorted(series_dir.iterdir()) if d.is_dir() and d.name[0].isdigit()), None)
            if first_dir and (first_dir / "outputs" / "card_1024x1536.png").exists():
                cards_dir = series_dir  # Flat structure

    if lots_source:
        lots_dir = lots_source / "lots" if (lots_source / "lots").exists() else lots_source
    else:
        lots_dir = series_dir / "lots"

    # TTS uses a special export path with sprite sheets
    if target == "tabletopsimulator":
        return _export_for_tts(
            series_dir, cards_dir, lots_dir, spec, card_type, limit,
            cards_source, lots_source, url_base
        )

    total_exported = 0
    total_skipped = 0
    total_errors = 0

    # Export main deck cards
    if card_type in ("cards", "all"):
        if cards_dir.exists():
            export_dir = series_dir / "exports" / target / "cards"
            source_label = f" (from {cards_source.name})" if cards_source else ""
            _log(f"  Main deck cards{source_label} -> {export_dir.name}/")
            exported, skipped, errors = _export_card_set(
                cards_dir, export_dir, spec, "card", "card_1024x1536.png", limit=limit
            )
            total_exported += exported
            total_skipped += skipped
            total_errors += errors
            _log(f"    ({exported} exported, {skipped} skipped)")
        else:
            _log(f"  Main deck cards: directory not found")

    # Export lot cards
    if card_type in ("lots", "all"):
        if lots_dir.exists():
            export_dir = series_dir / "exports" / target / "lots"
            source_label = f" (from {lots_source.name})" if lots_source else ""
            _log(f"  Lot cards{source_label} -> {export_dir.name}/")
            exported, skipped, errors = _export_card_set(
                lots_dir, export_dir, spec, "lot", "lot_1024x1536.png", limit=limit
            )
            total_exported += exported
            total_skipped += skipped
            total_errors += errors
            _log(f"    ({exported} exported, {skipped} skipped)")
        else:
            _log(f"  Lot cards: directory not found")

    # Export card back
    export_root = series_dir / "exports" / target
    _export_card_back(export_root, spec)

    _log("")
    _log(f"Export complete: {series_dir / 'exports' / target}")
    _log(f"  Total exported: {total_exported}")
    if total_skipped:
        _log(f"  Total skipped: {total_skipped}")
    if total_errors:
        _log(f"  Total errors: {total_errors}")

    return 0 if total_errors == 0 else 1


def list_platforms() -> None:
    """Print available platforms and their specifications."""
    print("Available export platforms:\n")
    for name, spec in PLATFORMS.items():
        print(f"  {name}")
        print(f"    Name: {spec['name']}")
        print(f"    Size: {spec['width']}x{spec['height']} @ {spec['dpi']} DPI")
        if spec['bleed'] > 0:
            print(f"    Bleed: {spec['bleed']} pixels")
        print(f"    Use: {spec['description']}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export Hypertext cards for various platforms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m hypertext.lots.exporter --series series/2026-Q1 --target playingcards
  python -m hypertext.lots.exporter --series series/2026-Q1 --target playingcards --type cards
  python -m hypertext.lots.exporter --series series/2026-Q1 --target makeplayingcards --type all
  python -m hypertext.lots.exporter --series series/2026-Q1 --target playingcards --cards-source demo_cards --limit 90
  python -m hypertext.lots.exporter --list-platforms
"""
    )
    parser.add_argument(
        "--series",
        help="Path to series directory (e.g., series/2026-Q1)"
    )
    parser.add_argument(
        "--target",
        choices=list(PLATFORMS.keys()),
        help="Target platform for export"
    )
    parser.add_argument(
        "--type",
        choices=["cards", "lots", "all"],
        default="all",
        help="What to export: cards (main deck), lots (phase cards), or all (default)"
    )
    parser.add_argument(
        "--cards-source",
        help="Override source directory for main deck cards (e.g., demo_cards)"
    )
    parser.add_argument(
        "--lots-source",
        help="Override source directory for lot cards"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Maximum number of cards to export (0 = no limit)"
    )
    parser.add_argument(
        "--url-base",
        help="Base URL for TTS image hosting (e.g., GitHub raw URL)"
    )
    parser.add_argument(
        "--list-platforms",
        action="store_true",
        help="List available export platforms"
    )
    args = parser.parse_args()

    if args.list_platforms:
        list_platforms()
        return 0

    if not args.series or not args.target:
        _log("Error: --series and --target are required for export")
        parser.print_help()
        return 1

    series_dir = Path(args.series)
    if not series_dir.exists():
        _log(f"Error: Series directory does not exist: {series_dir}")
        return 1

    # Parse source overrides
    cards_source = Path(args.cards_source) if args.cards_source else None
    lots_source = Path(args.lots_source) if args.lots_source else None

    return export_for_platform(
        series_dir,
        args.target,
        args.type,
        limit=args.limit,
        cards_source=cards_source,
        lots_source=lots_source,
        url_base=args.url_base,
    )


if __name__ == "__main__":
    raise SystemExit(main())
