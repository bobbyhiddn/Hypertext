#!/usr/bin/env python3
"""
Export Hypertext lot (phase) cards for various print-on-demand and playtest platforms.

Supported platforms:
  - playingcards: Playingcards.io (web playtest) - 750x1050 @ 72 DPI
  - makeplayingcards: MakePlayingCards.com - 750x1050 @ 300 DPI + bleed
  - thegamecrafter: The Game Crafter - 825x1125 @ 300 DPI + bleed

Usage:
  python lot_exporter.py --series series/2026-Q1 --target playingcards
  python lot_exporter.py --series series/2026-Q1 --target makeplayingcards
  python lot_exporter.py --series series/2026-Q1 --target thegamecrafter
"""

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore


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


def export_for_platform(series_dir: Path, target: str) -> int:
    """
    Export all lot cards for the specified target platform.

    Args:
        series_dir: Path to series directory (e.g., series/2026-Q1)
        target: Platform name (playingcards, makeplayingcards, thegamecrafter)

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
    lots_dir = series_dir / "lots"

    if not lots_dir.exists():
        _log(f"Error: Lots directory not found: {lots_dir}")
        _log("Run --phase render first to generate lot cards.")
        return 1

    export_dir = series_dir / "exports" / target / "lots"
    export_dir.mkdir(parents=True, exist_ok=True)

    _log(f"Exporting for {spec['name']} ({spec['description']})")
    _log(f"  Output size: {spec['width']}x{spec['height']} @ {spec['dpi']} DPI")
    if spec['bleed'] > 0:
        _log(f"  Bleed: {spec['bleed']} pixels")

    exported_count = 0
    skipped_count = 0
    error_count = 0

    # Find all lot card directories
    lot_dirs = sorted([d for d in lots_dir.iterdir() if d.is_dir()])

    for lot_dir in lot_dirs:
        src_path = lot_dir / "outputs" / "lot_1024x1536.png"

        if not src_path.exists():
            _log(f"  Skipping {lot_dir.name}: no image found")
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
            # Extract lot number from directory name (e.g., "01-remnant" -> "01")
            lot_num = lot_dir.name.split("-")[0]
            out_name = f"lot_{lot_num}.png"
            out_path = export_dir / out_name

            # Save with DPI metadata
            img_final.save(out_path, "PNG", dpi=(spec["dpi"], spec["dpi"]))

            _log(f"  Exported {out_name}")
            exported_count += 1

        except Exception as e:
            _log(f"  Error exporting {lot_dir.name}: {e}")
            error_count += 1

    _log(f"\nExport complete: {export_dir}")
    _log(f"  Exported: {exported_count}")
    if skipped_count:
        _log(f"  Skipped: {skipped_count}")
    if error_count:
        _log(f"  Errors: {error_count}")

    return 0 if error_count == 0 else 1


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
        description="Export Hypertext lot cards for various platforms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python lot_exporter.py --series series/2026-Q1 --target playingcards
  python lot_exporter.py --series series/2026-Q1 --target makeplayingcards
  python lot_exporter.py --list-platforms
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

    return export_for_platform(series_dir, args.target)


if __name__ == "__main__":
    raise SystemExit(main())
